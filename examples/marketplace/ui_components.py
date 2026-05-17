"""Streamlit render helpers. Keeps app.py focused on flow, not markup."""

from __future__ import annotations

import streamlit as st
from solvapay.paywall_state import GateDecision, PaywallState

from agents import Agent

_STATE_STYLE: dict[PaywallState, dict[str, str]] = {
    PaywallState.UPGRADE_REQUIRED: {
        "color": "#f6a623",
        "icon": "🔒",
        "title": "Upgrade required",
        "cta": "Upgrade plan",
    },
    PaywallState.TOPUP_REQUIRED: {
        "color": "#3aa0ff",
        "icon": "💸",
        "title": "Out of credits",
        "cta": "Top up balance",
    },
    PaywallState.ACTIVATION_REQUIRED: {
        "color": "#b266ff",
        "icon": "🆕",
        "title": "Activation required",
        "cta": "Activate plan",
    },
    PaywallState.REACTIVATION_REQUIRED: {
        "color": "#ff6b6b",
        "icon": "♻️",
        "title": "Reactivation required",
        "cta": "Manage account",
    },
}


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        .agent-card {
            border: 1px solid #2a2f3a;
            border-radius: 14px;
            padding: 18px 20px;
            background: #161a22;
            height: 100%;
        }
        .agent-card h3 { margin: 0 0 4px 0; font-size: 1.05rem; }
        .agent-card .price { color: #7c5cff; font-weight: 600; font-size: 0.95rem; }
        .agent-card .blurb { color: #a8b0bd; font-size: 0.88rem; margin: 4px 0 12px 0; }
        .balance-pill {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: #1d2230;
            border: 1px solid #2a2f3a;
            font-weight: 600;
        }
        .paywall-banner {
            border-left: 4px solid var(--bcolor);
            background: #161a22;
            padding: 16px 18px;
            border-radius: 8px;
            margin: 8px 0 14px 0;
        }
        .paywall-banner h4 { margin: 0 0 6px 0; }
        .state-chip {
            display: inline-block;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.78rem;
            padding: 2px 8px;
            border-radius: 6px;
            background: #0e1117;
            border: 1px solid #2a2f3a;
            color: #e6e9ef;
        }
        .success-box {
            border-left: 4px solid #4ade80;
            background: #161a22;
            padding: 16px 18px;
            border-radius: 8px;
            margin: 8px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_plan_badge(has_plan: bool) -> None:
    if has_plan:
        st.markdown(
            '<div class="balance-pill">✅ Pro Plan · subscribed</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="balance-pill">🆓 Free Tier · no subscription</div>',
            unsafe_allow_html=True,
        )


def render_agent_card(agent: Agent) -> bool:
    """Render an agent tile. Returns True if the user clicked Run."""
    with st.container(border=False):
        st.markdown(
            f"""
            <div class="agent-card">
              <h3>{agent.icon} {agent.name}</h3>
              <div class="price">${agent.price_usd:.2f} / call</div>
              <div class="blurb">{agent.blurb}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return st.button("Run agent", key=f"run_{agent.slug}", use_container_width=True)


def render_paywall_banner(decision: GateDecision, *, via_decorator: bool = False) -> None:
    style = _STATE_STYLE.get(decision.state, _STATE_STYLE[PaywallState.UPGRADE_REQUIRED])
    decorator_note = (
        "<div style='font-size:0.78rem;color:#7c8a9b;margin-top:6px'>"
        "↑ Triggered by <code>@paywall.require</code> decorator</div>"
        if via_decorator
        else ""
    )
    st.markdown(
        f"""
        <div class="paywall-banner" style="--bcolor:{style['color']}">
          <h4>{style['icon']} {style['title']}</h4>
          <span class="state-chip">paywall_state.{decision.state.name}</span>
          <div style="color:#a8b0bd;margin-top:10px">{decision.message}</div>
          {decorator_note}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if decision.checkout_url:
        st.link_button(style["cta"], decision.checkout_url, use_container_width=True)


def render_success(agent: Agent, output: str) -> None:
    st.markdown(
        f"""
        <div class="success-box">
          <h4>✅ {agent.icon} {agent.name} ran successfully</h4>
          <div style="color:#7c8a9b;font-size:0.85rem">
            1 request tracked via SolvaPay SDK
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(output)
