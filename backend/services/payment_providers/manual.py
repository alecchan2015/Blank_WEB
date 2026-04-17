"""
Manual / mock payment provider.

No external API call. Just returns a payload telling the user to wait for
admin confirmation after clicking "I paid". Admins confirm orders in the
admin Orders page, which triggers tier activation.
"""
from __future__ import annotations

from typing import Any, Dict


def is_ready(cfg: Dict[str, Any]) -> bool:
    return True


def create_payment(order, cfg: Dict[str, Any]) -> Dict[str, Any]:
    hint = cfg.get("hint") or "请联系管理员进行付款，付款后点击「我已完成支付」，管理员将在 24 小时内确认激活会员。"
    return {
        "payment_url":       None,
        "qr_code_url":       None,
        "external_order_id": None,
        "message":           hint,
    }
