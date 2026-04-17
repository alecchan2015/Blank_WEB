"""
Alipay (支付宝) provider stub.

Full implementation requires RSA2 signing against the configured app_id +
private_key. When credentials aren't yet provided, this raises a helpful
error — real integration can be added later.
"""
from __future__ import annotations

from typing import Any, Dict


def is_ready(cfg: Dict[str, Any]) -> bool:
    return bool(cfg.get("app_id") and cfg.get("private_key"))


def create_payment(order, cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not is_ready(cfg):
        raise RuntimeError("支付宝未配置完整（需 app_id + private_key）")

    # Placeholder: the real integration would generate a PC page/QR payment
    # URL via the alipay.trade.page.pay API and RSA2 signature.
    # For now we return a stub URL so the UI flow is exercisable end-to-end.
    return {
        "payment_url":       None,
        "qr_code_url":       f"/api/payment/qr/alipay/{order.order_no}",  # placeholder
        "external_order_id": None,
        "message":           "请使用支付宝扫码支付。（当前为占位符，完整集成待后续接入）",
    }
