"""
WeChat Pay (微信支付) Native QR provider stub.

Full implementation requires API v3 certificate authentication. Stub returns
a placeholder payload so the UI flow can be tested before merchant onboarding
completes.
"""
from __future__ import annotations

from typing import Any, Dict


def is_ready(cfg: Dict[str, Any]) -> bool:
    return bool(cfg.get("mchid") and cfg.get("app_id") and cfg.get("api_v3_key"))


def create_payment(order, cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not is_ready(cfg):
        raise RuntimeError("微信支付未配置完整（需 mchid + app_id + api_v3_key）")

    # Placeholder: real flow would POST to
    # https://api.mch.weixin.qq.com/v3/pay/transactions/native with a signed
    # request, yielding a code_url for QR display.
    return {
        "payment_url":       None,
        "qr_code_url":       f"/api/payment/qr/wechat/{order.order_no}",
        "external_order_id": None,
        "message":           "请使用微信扫码支付。（当前为占位符，完整集成待后续接入）",
    }
