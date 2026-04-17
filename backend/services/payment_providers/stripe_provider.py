"""
Stripe Checkout Session provider (stub).

When Stripe credentials are configured, this creates a Checkout Session and
returns the hosted checkout URL. Users complete payment on Stripe's page,
then Stripe sends a webhook to /api/webhooks/stripe which confirms the order.

Without credentials, create_payment raises and the admin flow must use the
manual channel instead.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx


API_URL = "https://api.stripe.com/v1/checkout/sessions"


def is_ready(cfg: Dict[str, Any]) -> bool:
    return bool(cfg.get("secret_key"))


def create_payment(order, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper — Stripe API responds quickly (<1s)."""
    secret_key = cfg.get("secret_key", "")
    if not secret_key:
        raise RuntimeError("Stripe secret_key 未配置")

    success_url = cfg.get("success_url") or f"/payment/{order.order_no}?status=success"
    cancel_url  = cfg.get("cancel_url")  or f"/payment/{order.order_no}?status=cancel"

    currency = (order.currency or "CNY").lower()

    data = {
        "mode": "payment",
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": currency,
        "line_items[0][price_data][unit_amount]": str(order.amount_cents),
        "line_items[0][price_data][product_data][name]": order.plan.name if order.plan else "Membership",
        "success_url": success_url,
        "cancel_url":  cancel_url,
        "client_reference_id": order.order_no,
        "metadata[order_no]": order.order_no,
        "metadata[user_id]":  str(order.user_id),
    }

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    with httpx.Client(timeout=20, proxy=proxy) as client:
        r = client.post(
            API_URL,
            data=data,
            auth=(secret_key, ""),
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Stripe API 失败 [{r.status_code}]: {r.text[:300]}")
        resp = r.json()

    return {
        "payment_url":       resp.get("url"),
        "qr_code_url":       None,
        "external_order_id": resp.get("id"),
        "message":           "即将跳转至 Stripe 完成信用卡支付。",
    }
