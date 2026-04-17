"""
Membership tier lifecycle: activation, expiry, monthly credit grant, feature
access gating.

All mutations commit to the DB. `lazy_check` is idempotent and cheap — safe
to call on every authenticated request from `get_current_user`.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session


# Tier ordering for comparisons (higher = better)
TIER_ORDER = {
    "regular": 0,
    "vip":     1,
    "vvip":    2,
    "vvvip":   3,
}


def tier_rank(tier: str) -> int:
    return TIER_ORDER.get(tier, 0)


# ──────────────────────────────────────────────────────────────────────────────
# Feature access gating
# ──────────────────────────────────────────────────────────────────────────────
def check_feature_access(db: Optional[Session], user, feature: str) -> bool:
    """Return True if `user` can access `feature` based on their current tier.

    Safe to call with user=None (returns False). Reads tier→features mapping
    from `membership_config` so admins can tune who gets what without redeploy.
    """
    if user is None:
        return False
    if user.role == "admin":
        return True
    tier = getattr(user, "tier", "regular") or "regular"
    expires = getattr(user, "tier_expires_at", None)
    if tier != "regular" and expires and expires < datetime.utcnow():
        # Tier has expired but lazy_check hasn't run yet — treat as regular
        tier = "regular"
    from services.payment_settings import load_membership_config
    cfg = load_membership_config(db)
    tier_features = cfg.get("tier_features", {})
    return feature in tier_features.get(tier, [])


# ──────────────────────────────────────────────────────────────────────────────
# Activation
# ──────────────────────────────────────────────────────────────────────────────
def activate(db: Session, user, plan) -> None:
    """Activate a plan for the user (called after successful payment).

    - Extends tier_expires_at if the user is already at same-or-higher tier
    - Switches tier + resets expiry if upgrading from a lower tier
    - Grants activation_credits immediately
    - Grants current-month credits if not already granted this month
    """
    from models import CreditTransaction

    now = datetime.utcnow()
    current_rank = tier_rank(user.tier or "regular")
    new_rank = tier_rank(plan.tier)

    if new_rank > current_rank:
        # Upgrade: start fresh from today
        user.tier = plan.tier
        user.tier_expires_at = now + timedelta(days=plan.duration_days)
    else:
        # Same-tier extension: add duration onto the later of (now, existing expiry)
        base = user.tier_expires_at if user.tier_expires_at and user.tier_expires_at > now else now
        user.tier = plan.tier
        user.tier_expires_at = base + timedelta(days=plan.duration_days)

    # Activation credits
    if plan.activation_credits and plan.activation_credits > 0:
        user.credits = (user.credits or 0) + plan.activation_credits
        db.add(CreditTransaction(
            user_id=user.id,
            amount=plan.activation_credits,
            reason=f"会员开通 · {plan.name} · 开通赠送",
        ))

    # Monthly credits — grant for the current period if we haven't yet
    if plan.monthly_credits and plan.monthly_credits > 0:
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not user.last_monthly_grant_at or user.last_monthly_grant_at < month_start:
            user.credits = (user.credits or 0) + plan.monthly_credits
            user.last_monthly_grant_at = now
            db.add(CreditTransaction(
                user_id=user.id,
                amount=plan.monthly_credits,
                reason=f"会员月度积分 · {plan.name}",
            ))

    db.commit()


def downgrade(db: Session, user, *, reason: str = "会员到期") -> None:
    """Explicitly downgrade a user to regular (used by refund flow)."""
    user.tier = "regular"
    user.tier_expires_at = None
    db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Lazy checks — called on every authenticated request
# ──────────────────────────────────────────────────────────────────────────────
def lazy_check(db: Session, user) -> None:
    """Cheap idempotent checks run on every authenticated request:

    1. If tier expired → reset to regular
    2. If current period > last monthly grant → grant this month's credits
    """
    if user is None:
        return
    now = datetime.utcnow()
    changed = False

    # 1) Expiry check
    if user.tier and user.tier != "regular" and user.tier_expires_at and user.tier_expires_at < now:
        user.tier = "regular"
        user.tier_expires_at = None
        changed = True

    # 2) Monthly credit grant (only if tier is active)
    if user.tier and user.tier != "regular" and (user.tier_expires_at is None or user.tier_expires_at > now):
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not user.last_monthly_grant_at or user.last_monthly_grant_at < month_start:
            # Find the most recent plan the user has purchased for this tier
            from models import PaymentOrder, MembershipPlan
            last_paid = (
                db.query(PaymentOrder)
                .join(MembershipPlan, PaymentOrder.plan_id == MembershipPlan.id)
                .filter(PaymentOrder.user_id == user.id)
                .filter(PaymentOrder.status == "paid")
                .filter(MembershipPlan.tier == user.tier)
                .order_by(PaymentOrder.paid_at.desc())
                .first()
            )
            monthly = last_paid.plan.monthly_credits if last_paid else 0
            if monthly and monthly > 0:
                from models import CreditTransaction
                user.credits = (user.credits or 0) + monthly
                user.last_monthly_grant_at = now
                db.add(CreditTransaction(
                    user_id=user.id,
                    amount=monthly,
                    reason=f"会员月度积分 · {user.tier.upper()}",
                ))
                changed = True

    if changed:
        try:
            db.commit()
        except Exception:                                               # noqa: BLE001
            db.rollback()


# ──────────────────────────────────────────────────────────────────────────────
# Admin manual tier adjustment
# ──────────────────────────────────────────────────────────────────────────────
def admin_set_tier(db: Session, user, tier: str, expires_at: Optional[datetime] = None) -> None:
    """Admin override — directly set a user's tier + expiry (no credit side-effects)."""
    if tier not in TIER_ORDER:
        raise ValueError(f"invalid tier: {tier}")
    user.tier = tier
    user.tier_expires_at = expires_at if tier != "regular" else None
    db.commit()
