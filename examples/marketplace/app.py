"""Agent Marketplace — a Streamlit marketplace demoing the solvapay-python SDK.

Every SDK call hits the real SolvaPay sandbox. Every agent call hits a real
Gemini LLM. The only "fake" things are per-agent display prices — all
agents bill the same real product (SOLVAPAY_PRODUCT_REF).

Run:
    pip install -r requirements.txt
    cp .env.example .env  # fill in real sandbox + Gemini keys
    streamlit run app.py
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("marketplace.app")

import streamlit as st
from solvapay import PaywallRequired, paywall
from solvapay.paywall_state import PaywallState

import sdk_gateway
from agents import AGENTS, AGENTS_BY_SLUG, Agent, example_input_for
from demo_customers import load_customers
from ui_components import (
    inject_global_css,
    render_agent_card,
    render_plan_badge,
    render_paywall_banner,
    render_success,
)

# --- page setup (must be first Streamlit command) --------------------------

st.set_page_config(
    page_title="Agent Marketplace — powered by SolvaPay",
    page_icon="🪙",
    layout="wide",
)
inject_global_css()


# --- one-time bootstrap ----------------------------------------------------

@st.cache_resource(show_spinner="Loading demo customers…")
def _bootstrap() -> dict:
    real_b_ref = sdk_gateway.bootstrap_customer_b()
    os.environ["SOLVAPAY_DEMO_BLOCKED_CUSTOMER_REF"] = real_b_ref
    return load_customers()


CUSTOMERS = _bootstrap()


# --- decorator-gated runner (Code Reviewer) --------------------------------

@paywall.require(
    product=sdk_gateway.product_ref(),
    customer_ref_arg="customer_ref",
    client=sdk_gateway.get_client(),
)
def run_code_reviewer_gated(*, customer_ref: str, diff: str) -> str:
    return AGENTS_BY_SLUG["code_reviewer"].run(diff)

if "active_customer" not in st.session_state:
    st.session_state.active_customer = "alice"
if "last_result" not in st.session_state:
    st.session_state.last_result = None


# --- sidebar ---------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🪙 Agent Marketplace")
    st.caption("Marketplace of paywalled AI agents — powered by SolvaPay.")

    st.markdown("---")
    st.markdown("**Install the SDK**")
    st.code("pip install solvapay-python", language="bash")
    st.caption(
        f"🌐 Hitting real SolvaPay sandbox · product `{sdk_gateway.product_ref()}` · "
        f"real Gemini `{os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')}`"
    )

    st.markdown("---")
    st.markdown("**Switch customer**")
    keys = list(CUSTOMERS.keys())

    # Fetch plan status for all customers to build dynamic labels
    plan_status: dict[str, bool] = {
        k: sdk_gateway.fetch_customer_plan(CUSTOMERS[k].customer_ref) is not None
        for k in keys
    }

    def _label(k: str) -> str:
        c = CUSTOMERS[k]
        suffix = "subscribed" if plan_status[k] else "no plan"
        return f"{c.name} — {suffix}"

    selected = st.radio(
        "Customer",
        keys,
        format_func=_label,
        index=keys.index(st.session_state.active_customer),
        label_visibility="collapsed",
    )
    if selected != st.session_state.active_customer:
        st.session_state.active_customer = selected
        st.session_state.last_result = None
        st.rerun()

    active = CUSTOMERS[st.session_state.active_customer]
    has_plan = plan_status[st.session_state.active_customer]
    note = (
        "Pre-existing sandbox customer with an active plan."
        if has_plan
        else "Pre-existing sandbox customer; no subscription → gated."
    )
    st.caption(note)
    render_plan_badge(has_plan=has_plan)
    try:
        within, remaining, meter = sdk_gateway.fetch_remaining(active.customer_ref)
        remaining_str = "unlimited" if remaining < 0 else f"{remaining:g} {meter or 'units'}"
        st.caption(
            f"📊 {remaining_str} remaining · "
            f"{'within limits' if within else '**OVER LIMIT**'}"
        )
    except Exception as e:
        st.caption(f"⚠️ check_limits error: {e}")

    st.markdown("---")
    if st.button("🔥 Burn 1 request (no LLM)", use_container_width=True,
                 help="Calls track_usage directly — use to exhaust free quota for demo"):
        sdk_gateway.record_usage(customer_ref=active.customer_ref)
        st.rerun()


# --- run dialog ------------------------------------------------------------

@st.dialog("Run agent")
def run_dialog(agent: Agent) -> None:
    customer = CUSTOMERS[st.session_state.active_customer]
    st.markdown(f"### {agent.icon} {agent.name}")
    st.caption(
        f"~${agent.price_usd:.2f}/call (display) · billed to **{customer.name}** · "
        f"product `{sdk_gateway.product_ref()}`"
    )

    user_input = st.text_area("Input", value=example_input_for(agent.slug), height=140)

    cols = st.columns([1, 1])
    with cols[0]:
        execute = st.button("Execute", type="primary", use_container_width=True)
    with cols[1]:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

    if not execute:
        return

    if agent.slug == "code_reviewer":
        # Decorator path: real check_limits via SDK; on block, raises PaywallRequired.
        try:
            with st.spinner("Calling LLM via @paywall.require…"):
                output = run_code_reviewer_gated(
                    customer_ref=customer.customer_ref, diff=user_input
                )
            sdk_gateway.record_usage(customer_ref=customer.customer_ref)
            st.session_state.last_result = ("ok", agent.slug, output, True)
            st.rerun()
            return
        except PaywallRequired:
            decision = sdk_gateway.check_and_decide(customer_ref=customer.customer_ref)
            log.info(
                "PAYWALL BLOCKED — no LLM call made | customer=%s | agent=%s | state=%s",
                customer.customer_ref, agent.slug, decision.state.name,
            )
            st.session_state.last_result = ("gated", agent.slug, decision, True)
            st.rerun()
            return

    # Explicit path: check_limits → decide() → branch UI.
    decision = sdk_gateway.check_and_decide(customer_ref=customer.customer_ref)
    if decision.state == PaywallState.OK:
        with st.spinner("Calling LLM…"):
            output = agent.run(user_input)
        sdk_gateway.record_usage(customer_ref=customer.customer_ref)
        st.session_state.last_result = ("ok", agent.slug, output, False)
    else:
        log.info(
            "PAYWALL BLOCKED — no LLM call made | customer=%s | agent=%s | state=%s",
            customer.customer_ref, agent.slug, decision.state.name,
        )
        st.session_state.last_result = ("gated", agent.slug, decision, False)
    st.rerun()


# --- main ------------------------------------------------------------------

st.markdown("# AI Agents")
st.markdown(
    "Browse, pick one, pay per call. Each agent is gated by the SolvaPay SDK. "
    "Switch customers in the sidebar to see `paywall_state.decide()` classify the gate."
)

cols = st.columns(2)
for i, agent in enumerate(AGENTS):
    with cols[i % 2]:
        if render_agent_card(agent):
            run_dialog(agent)

st.markdown("---")

result = st.session_state.last_result
if result is None:
    st.markdown(
        "<div style='color:#7c8a9b'>↑ Click <b>Run agent</b> on any tile. ",
        unsafe_allow_html=True,
    )
elif result[0] == "ok":
    _, slug, output, via_decorator = result
    agent = AGENTS_BY_SLUG[slug]
    render_success(agent, output)
    if via_decorator:
        st.caption("✔ Gated by `@paywall.require` — call passed the SDK's limit check.")
elif result[0] == "gated":
    _, slug, decision, via_decorator = result
    agent = AGENTS_BY_SLUG[slug]
    st.markdown(f"### {agent.icon} {agent.name} — blocked")
    render_paywall_banner(decision, via_decorator=via_decorator)
    active = CUSTOMERS[st.session_state.active_customer]
    with st.expander("Show the SDK call that produced this"):
        st.code(
            f"""from solvapay import SolvaPay
from solvapay.paywall_state import decide

client = SolvaPay()  # uses SOLVAPAY_SECRET_KEY
limits = client.check_limits(
    customer_ref="{active.customer_ref}",
    product_ref="{sdk_gateway.product_ref()}",
)
decision = decide(limits)
# decision.state        == PaywallState.{decision.state.name}
# decision.checkout_url == {decision.checkout_url!r}
# decision.message      == {decision.message!r}
""",
            language="python",
        )
