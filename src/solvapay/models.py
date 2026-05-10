"""Pydantic models for SolvaPay API request/response payloads.

API uses camelCase; we expose snake_case via Field aliases.
populate_by_name=True so users can construct with either form.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class CheckoutSession(_Base):
    """Response from POST /v1/sdk/checkout-sessions."""

    session_id: str = Field(alias="sessionId")
    checkout_url: str = Field(alias="checkoutUrl")
