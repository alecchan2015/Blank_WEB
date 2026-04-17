"""
Payment provider factory. Each provider returns a payload the frontend uses
to complete the user-facing payment step (redirect URL, QR code, etc.).

Providers must implement:
    create_payment(order, cfg) -> dict
        Returns: {
            "payment_url":  str | None,    # where to redirect the user
            "qr_code_url":  str | None,    # for scan-to-pay flows
            "message":      str,           # human-readable hint shown to user
            "external_order_id": str | None,
        }
"""
from __future__ import annotations

from typing import Any, Dict

from . import manual, stripe_provider, alipay_provider, wechat_provider


_REGISTRY = {
    "manual": manual,
    "stripe": stripe_provider,
    "alipay": alipay_provider,
    "wechat": wechat_provider,
}


def create_payment(channel: str, order, payment_cfg: Dict[str, Any]) -> Dict[str, Any]:
    provider = _REGISTRY.get(channel)
    if not provider:
        raise ValueError(f"unknown payment channel: {channel}")
    cfg = payment_cfg.get(channel, {})
    if not cfg.get("enabled"):
        raise RuntimeError(f"{channel} 支付渠道未启用")
    return provider.create_payment(order, cfg)


def available_channels(payment_cfg: Dict[str, Any]) -> list[str]:
    """Return channels that are enabled AND have adequate credentials."""
    out = []
    for ch in ("stripe", "alipay", "wechat", "manual"):
        c = payment_cfg.get(ch, {})
        if not c.get("enabled"):
            continue
        provider = _REGISTRY.get(ch)
        if provider and hasattr(provider, "is_ready") and not provider.is_ready(c):
            continue
        out.append(ch)
    return out
