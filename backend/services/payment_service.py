"""
Payment service — order creation, confirmation, cancellation, refund.

Orchestrates MembershipPlan lookup, provider adapter calls, and downstream
tier activation via membership_service.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session


ORDER_TTL_HOURS = 24
PENDING_ORDER_LIMIT_PER_USER = 5   # simple anti-spam


def _generate_order_no() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d")
    suffix = secrets.token_hex(4).upper()
    return f"YBC-{ts}-{suffix}"


def create_order(db: Session, user, plan_id: int, channel: str) -> Dict[str, Any]:
    """Create a new order and prepare payment payload."""
    from models import MembershipPlan, PaymentOrder
    from services.payment_settings import load_payment_config
    from services import payment_providers

    plan = db.query(MembershipPlan).filter(
        MembershipPlan.id == plan_id,
        MembershipPlan.is_active == True,
    ).first()
    if not plan:
        raise HTTPException(404, "套餐不存在或已下架")

    payment_cfg = load_payment_config(db)
    available = payment_providers.available_channels(payment_cfg)
    if channel not in available:
        raise HTTPException(400, f"支付渠道不可用: {channel}")

    # Cap pending-order spam per user
    pending_count = (
        db.query(PaymentOrder)
        .filter(PaymentOrder.user_id == user.id)
        .filter(PaymentOrder.status.in_(["pending", "awaiting_confirm"]))
        .count()
    )
    if pending_count >= PENDING_ORDER_LIMIT_PER_USER:
        raise HTTPException(
            429,
            f"待支付订单过多（{pending_count}），请先完成或取消现有订单",
        )

    order = PaymentOrder(
        order_no=_generate_order_no(),
        user_id=user.id,
        plan_id=plan.id,
        channel=channel,
        amount_cents=plan.price_cents,
        currency=plan.price_currency or "CNY",
        status="pending",
        expires_at=datetime.utcnow() + timedelta(hours=ORDER_TTL_HOURS),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Build provider payload
    try:
        pay_payload = payment_providers.create_payment(channel, order, payment_cfg)
    except Exception as exc:                                             # noqa: BLE001
        # Mark order as failed so it's visible in admin
        order.status = "failed"
        order.admin_notes = f"渠道调用失败: {exc}"
        db.commit()
        raise HTTPException(500, f"创建支付失败: {exc}")

    # Persist external IDs if any
    if pay_payload.get("external_order_id"):
        order.external_order_id = pay_payload["external_order_id"]
        order.external_metadata = {k: v for k, v in pay_payload.items()
                                   if k not in ("message",) and v is not None}
        db.commit()

    return {
        "order":        order,
        "payment_url":  pay_payload.get("payment_url"),
        "qr_code_url":  pay_payload.get("qr_code_url"),
        "message":      pay_payload.get("message") or "",
    }


def mark_paying(db: Session, user, order_no: str) -> "PaymentOrder":
    """User-initiated state change: user clicked 'I paid' (manual channel)."""
    from models import PaymentOrder

    order = db.query(PaymentOrder).filter(
        PaymentOrder.order_no == order_no,
        PaymentOrder.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status not in ("pending",):
        raise HTTPException(400, f"订单当前状态（{order.status}）无法标记为已支付")
    if order.expires_at < datetime.utcnow():
        order.status = "canceled"
        order.canceled_at = datetime.utcnow()
        db.commit()
        raise HTTPException(400, "订单已过期，请重新下单")
    order.status = "awaiting_confirm"
    db.commit()
    db.refresh(order)
    return order


def cancel(db: Session, user, order_no: str) -> "PaymentOrder":
    from models import PaymentOrder
    order = db.query(PaymentOrder).filter(
        PaymentOrder.order_no == order_no,
        PaymentOrder.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status not in ("pending", "awaiting_confirm"):
        raise HTTPException(400, f"订单当前状态（{order.status}）无法取消")
    order.status = "canceled"
    order.canceled_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


def admin_confirm(db: Session, order_no: str, admin_user) -> "PaymentOrder":
    """Admin confirms a manual/awaiting order → activate membership."""
    from models import PaymentOrder, User
    from services import membership_service

    order = db.query(PaymentOrder).filter(PaymentOrder.order_no == order_no).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status in ("paid", "refunded"):
        raise HTTPException(400, f"订单已处理（{order.status}）")
    if order.status == "canceled":
        raise HTTPException(400, "订单已取消")

    user = db.query(User).filter(User.id == order.user_id).first()
    if not user:
        raise HTTPException(400, "订单关联用户不存在")

    order.status = "paid"
    order.paid_at = datetime.utcnow()
    order.admin_notes = (order.admin_notes or "") + f"\n[{datetime.utcnow().isoformat()}] 管理员 {admin_user.username} 手动确认收款"
    db.commit()

    membership_service.activate(db, user, order.plan)
    db.refresh(order)
    return order


def admin_refund(db: Session, order_no: str, admin_user, *, notes: str = "") -> "PaymentOrder":
    from models import PaymentOrder, User
    from services import membership_service

    order = db.query(PaymentOrder).filter(PaymentOrder.order_no == order_no).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status != "paid":
        raise HTTPException(400, f"仅已支付订单可退款（当前: {order.status}）")

    order.status = "refunded"
    order.refunded_at = datetime.utcnow()
    order.admin_notes = (order.admin_notes or "") + f"\n[{datetime.utcnow().isoformat()}] 管理员 {admin_user.username} 标记退款. {notes}"
    db.commit()

    # V1 policy: immediately downgrade user to regular on refund (no credit rollback)
    user = db.query(User).filter(User.id == order.user_id).first()
    if user:
        membership_service.downgrade(db, user, reason="会员退款")

    db.refresh(order)
    return order


def admin_cancel(db: Session, order_no: str, admin_user) -> "PaymentOrder":
    from models import PaymentOrder
    order = db.query(PaymentOrder).filter(PaymentOrder.order_no == order_no).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status in ("paid", "refunded"):
        raise HTTPException(400, "已支付订单请走退款流程")
    order.status = "canceled"
    order.canceled_at = datetime.utcnow()
    order.admin_notes = (order.admin_notes or "") + f"\n[{datetime.utcnow().isoformat()}] 管理员 {admin_user.username} 取消"
    db.commit()
    db.refresh(order)
    return order
