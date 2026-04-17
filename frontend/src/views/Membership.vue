<template>
  <div class="membership-page">
    <!-- Hero status -->
    <section class="hero" :class="`tier-bg-${me?.tier || 'regular'}`">
      <div class="hero-backdrop"></div>
      <div class="hero-inner">
        <div class="hero-left">
          <div class="tier-badge">
            <span class="tier-icon">{{ tierIcon(me?.tier) }}</span>
            <span class="tier-text">{{ me?.tier_label || '普通用户' }}</span>
          </div>
          <h1 v-if="me?.tier === 'regular'">解锁商业级品牌策略</h1>
          <h1 v-else>{{ me?.tier_label }} 会员 · 尊享体验</h1>
          <p v-if="me?.tier !== 'regular' && me?.tier_expires_at" class="expiry">
            有效期至 <b>{{ formatDate(me.tier_expires_at) }}</b>
            <span v-if="me?.days_remaining !== null" class="days-left"> · 剩余 {{ me.days_remaining }} 天</span>
          </p>
          <p v-else class="expiry-hint">升级后解锁 Gamma 商业级 PPT、高分辨率 Logo、专属服务等高端权益</p>
        </div>

        <div v-if="me?.support_info && me.tier !== 'regular'" class="support-box">
          <div class="support-label">专属服务</div>
          <div class="support-name">{{ me.support_info.name || '会员顾问' }}</div>
          <div v-if="me.support_info.wechat" class="support-contact">💬 {{ me.support_info.wechat }}</div>
          <div v-if="me.support_info.phone" class="support-contact">📞 {{ me.support_info.phone }}</div>
          <div v-if="me.support_info.email" class="support-contact">✉️ {{ me.support_info.email }}</div>
        </div>
      </div>
    </section>

    <!-- Active features -->
    <div v-if="me?.features?.length" class="active-features">
      <span class="feat-label">已解锁权益：</span>
      <span v-for="f in me.features" :key="f" class="feat-tag">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M2 5l2 2 4-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ me.feature_labels?.[f] || f }}
      </span>
    </div>

    <!-- Plans -->
    <div class="plans-section">
      <h2 class="section-title">选择会员套餐</h2>

      <div v-for="tier in ['vip', 'vvip', 'vvvip']" :key="tier" class="tier-group">
        <div class="tier-heading" :class="`heading-${tier}`">
          <span class="icon">{{ tierIcon(tier) }}</span>
          <span class="label">{{ tierLabel(tier) }}</span>
          <span class="tier-feats">
            <span v-for="f in tierFeatures(tier)" :key="f" class="feat-chip">
              {{ publicConfig.feature_labels?.[f] || f }}
            </span>
          </span>
        </div>

        <div class="plan-cards">
          <div
            v-for="plan in plansByTier(tier)"
            :key="plan.id"
            class="plan-card"
            :class="[`plan-${tier}`, { current: isCurrentPlan(plan) }]"
          >
            <div v-if="isCurrentPlan(plan)" class="current-ribbon">当前等级</div>

            <div class="plan-name">{{ plan.name }}</div>
            <div class="plan-price">
              <span class="currency">¥</span>
              <span class="amount">{{ (plan.price_cents / 100).toFixed(0) }}</span>
              <span class="duration">/ {{ plan.duration_days }} 天</span>
            </div>

            <div class="plan-benefits">
              <div class="benefit">
                <span class="b-icon">🎁</span>
                <span>开通赠送 <b>{{ plan.activation_credits }}</b> 积分</span>
              </div>
              <div class="benefit">
                <span class="b-icon">📅</span>
                <span>每月自动 <b>{{ plan.monthly_credits }}</b> 积分</span>
              </div>
            </div>

            <button class="buy-btn" :class="`btn-${tier}`" :disabled="buying" @click="selectPlan(plan)">
              立即升级
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M4 3l4 4-4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Payment modal -->
    <teleport to="body">
      <transition name="modal">
        <div v-if="showPayModal" class="modal-overlay" @click.self="showPayModal = false">
          <div class="modal-card">
            <button class="modal-close" @click="showPayModal = false">&times;</button>
            <h3>选择支付方式</h3>

            <div class="summary">
              <div class="sum-row"><span>套餐</span><b>{{ selectedPlan?.name }}</b></div>
              <div class="sum-row"><span>时长</span>{{ selectedPlan?.duration_days }} 天</div>
              <div class="sum-row amount-row"><span>金额</span>
                <b class="amt">¥ {{ (selectedPlan?.price_cents / 100).toFixed(2) }}</b>
              </div>
            </div>

            <div class="channel-list">
              <button
                v-for="ch in enabledChannels"
                :key="ch"
                class="channel-btn"
                :class="{ active: selectedChannel === ch }"
                @click="selectedChannel = ch"
              >
                <span class="ch-icon">{{ channelIcon(ch) }}</span>
                <span class="ch-label">{{ channelLabel(ch) }}</span>
                <span class="ch-check" :class="{ show: selectedChannel === ch }">✓</span>
              </button>
            </div>

            <button class="confirm-btn" :disabled="!selectedChannel || buying" @click="confirmPurchase">
              {{ buying ? '处理中…' : '确认支付' }}
            </button>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { membershipAPI, paymentAPI } from '../api'
import { useUserStore } from '../store'

const router = useRouter()
const store = useUserStore()

const me = ref(null)
const plans = ref([])
const publicConfig = ref({ tier_labels: {}, tier_features: {}, feature_labels: {} })
const enabledChannels = ref([])
const channelDescriptions = ref({})

const showPayModal = ref(false)
const selectedPlan = ref(null)
const selectedChannel = ref('')
const buying = ref(false)

const TIER_ICONS = { regular: '👤', vip: '⭐', vvip: '💎', vvvip: '👑' }
const TIER_LABELS_DEFAULT = { regular: '普通用户', vip: 'VIP', vvip: 'VVIP', vvvip: 'VVVIP' }
const CHANNEL_META = {
  stripe: { icon: '💳', label: '信用卡 (Stripe)' },
  alipay: { icon: '🅰️', label: '支付宝' },
  wechat: { icon: '💬', label: '微信支付' },
  manual: { icon: '🧾', label: '模拟支付 / 管理员确认' },
}

function tierIcon(t) { return TIER_ICONS[t] || '👤' }
function tierLabel(t) { return publicConfig.value.tier_labels?.[t] || TIER_LABELS_DEFAULT[t] || t }
function tierFeatures(t) { return publicConfig.value.tier_features?.[t] || [] }
function channelIcon(ch) { return CHANNEL_META[ch]?.icon || '💰' }
function channelLabel(ch) { return CHANNEL_META[ch]?.label || ch }
function plansByTier(t) { return plans.value.filter(p => p.tier === t && p.is_active) }
function isCurrentPlan(plan) { return me.value?.tier === plan.tier }
function formatDate(s) {
  if (!s) return ''
  return new Date(s).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function selectPlan(plan) {
  selectedPlan.value = plan
  selectedChannel.value = enabledChannels.value[0] || ''
  showPayModal.value = true
}

async function confirmPurchase() {
  if (!selectedPlan.value || !selectedChannel.value) return
  buying.value = true
  try {
    const res = await paymentAPI.createOrder({
      plan_id: selectedPlan.value.id,
      channel: selectedChannel.value,
    })
    showPayModal.value = false
    if (res.payment_url) window.location.href = res.payment_url
    else router.push(`/payment/${res.order.order_no}`)
  } catch (e) {
    ElMessage.error(e.message || '下单失败')
  } finally {
    buying.value = false
  }
}

async function loadAll() {
  try {
    const [meRes, plansRes, cfgRes, chRes] = await Promise.all([
      membershipAPI.me(),
      membershipAPI.plans(),
      membershipAPI.publicConfig(),
      paymentAPI.publicChannels(),
    ])
    me.value = meRes
    plans.value = plansRes
    publicConfig.value = cfgRes
    enabledChannels.value = chRes.enabled || []
    channelDescriptions.value = chRes.descriptions || {}
  } catch (e) {
    ElMessage.error('加载失败: ' + e.message)
  }
}

onMounted(loadAll)
</script>

<style scoped>
.membership-page { max-width: 1100px; margin: 0 auto; padding-bottom: 40px; color: var(--ybc-text); }

/* ── Hero ───────────────────────────────────── */
.hero {
  position: relative;
  padding: 32px 32px;
  border-radius: 20px;
  margin-bottom: 24px;
  overflow: hidden;
  border: 1px solid var(--ybc-border);
}
.hero-backdrop {
  position: absolute; inset: 0;
  pointer-events: none;
}
.tier-bg-regular {
  background: linear-gradient(135deg, #18181b, #09090b);
}
.tier-bg-regular .hero-backdrop {
  background: radial-gradient(ellipse 60% 80% at 70% 20%, rgba(99, 102, 241, 0.15), transparent);
}
.tier-bg-vip {
  background: linear-gradient(135deg, #1e293b 0%, #1e40af 100%);
  border-color: rgba(59, 130, 246, 0.3);
}
.tier-bg-vip .hero-backdrop {
  background: radial-gradient(ellipse 70% 100% at 100% 0%, rgba(99, 102, 241, 0.3), transparent);
}
.tier-bg-vvip {
  background: linear-gradient(135deg, #3b0764 0%, #831843 100%);
  border-color: rgba(168, 85, 247, 0.3);
}
.tier-bg-vvip .hero-backdrop {
  background: radial-gradient(ellipse 70% 100% at 100% 0%, rgba(236, 72, 153, 0.3), transparent);
}
.tier-bg-vvvip {
  background: linear-gradient(135deg, #78350f 0%, #7f1d1d 100%);
  border-color: rgba(245, 158, 11, 0.3);
}
.tier-bg-vvvip .hero-backdrop {
  background: radial-gradient(ellipse 70% 100% at 100% 0%, rgba(245, 158, 11, 0.3), transparent);
}

.hero-inner {
  position: relative;
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 20px;
  z-index: 1;
}
.hero-left { flex: 1; min-width: 0; }

.tier-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 100px;
  color: #fff;
  font-size: 12px; font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 12px;
  backdrop-filter: blur(8px);
}
.tier-icon { font-size: 16px; }

.hero h1 {
  font-size: 28px; font-weight: 800;
  color: #fff;
  letter-spacing: -0.5px;
  margin-bottom: 10px;
  line-height: 1.3;
}
.expiry, .expiry-hint {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}
.expiry b { color: #fff; }
.days-left { opacity: 0.7; }

.support-box {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(16px);
  border-radius: 14px;
  padding: 16px 18px;
  min-width: 220px;
  color: #fff;
}
.support-label {
  font-size: 10px; opacity: 0.6;
  letter-spacing: 1px; text-transform: uppercase;
}
.support-name {
  font-size: 15px; font-weight: 700;
  margin: 6px 0 8px;
}
.support-contact {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 4px;
}

/* ── Active features ─────────────────────── */
.active-features {
  margin-bottom: 28px;
  padding: 14px 18px;
  background: var(--ybc-surface-1);
  border: 1px solid var(--ybc-border);
  border-radius: 12px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.feat-label { font-size: 13px; color: var(--ybc-text-dim); margin-right: 6px; }
.feat-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.25);
  color: #86efac;
  border-radius: 100px;
  font-size: 12px; font-weight: 500;
}

/* ── Plans ─────────────────────────────── */
.section-title {
  font-size: 22px; font-weight: 800;
  color: var(--ybc-text-strong);
  margin: 0 0 20px;
  letter-spacing: -0.3px;
}

.tier-group { margin-bottom: 28px; }

.tier-heading {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 14px;
  padding: 10px 16px;
  border-radius: 12px;
  background: var(--ybc-surface-1);
  border: 1px solid var(--ybc-border);
  flex-wrap: wrap;
}
.tier-heading .icon { font-size: 22px; }
.tier-heading .label {
  font-size: 15px; font-weight: 700;
  letter-spacing: -0.2px;
}
.tier-heading.heading-vip .label   { color: #93c5fd; }
.tier-heading.heading-vvip .label  { color: #d8b4fe; }
.tier-heading.heading-vvvip .label { color: #fcd34d; }

.tier-feats {
  display: flex; gap: 6px; flex-wrap: wrap;
  margin-left: auto;
}
.feat-chip {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--ybc-text-dim);
  border-radius: 100px;
  border: 1px solid var(--ybc-border);
}

.plan-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.plan-card {
  position: relative;
  padding: 24px 22px;
  border-radius: 16px;
  background: var(--ybc-surface-1);
  border: 1px solid var(--ybc-border);
  display: flex; flex-direction: column; gap: 14px;
  transition: all 0.25s;
  overflow: hidden;
}
.plan-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  opacity: 0;
  transition: opacity 0.3s;
}
.plan-card:hover { transform: translateY(-4px); box-shadow: var(--ybc-shadow-md); }
.plan-card:hover::before { opacity: 1; }
.plan-vip::before   { background: linear-gradient(135deg, #3b82f6, #6366f1); }
.plan-vvip::before  { background: linear-gradient(135deg, #8b5cf6, #ec4899); }
.plan-vvvip::before { background: linear-gradient(135deg, #f59e0b, #ef4444); }

.plan-card.current {
  border-color: rgba(34, 197, 94, 0.4);
  background: rgba(34, 197, 94, 0.04);
}
.current-ribbon {
  position: absolute;
  top: 12px; right: -26px;
  transform: rotate(45deg);
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff;
  padding: 2px 30px;
  font-size: 10px; font-weight: 700;
  letter-spacing: 1px;
}

.plan-name {
  font-size: 15px; font-weight: 700;
  color: var(--ybc-text-strong);
}

.plan-price {
  display: flex; align-items: baseline; gap: 2px;
}
.plan-price .currency {
  font-size: 14px; font-weight: 600;
  color: var(--ybc-accent-light);
}
.plan-price .amount {
  font-size: 36px; font-weight: 800;
  color: var(--ybc-text-strong);
  letter-spacing: -1.5px;
  line-height: 1;
}
.plan-price .duration {
  font-size: 12px; color: var(--ybc-text-muted);
  margin-left: 6px;
}

.plan-benefits {
  display: flex; flex-direction: column; gap: 6px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
  border: 1px solid var(--ybc-border);
}
.benefit {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px;
  color: var(--ybc-text-dim);
}
.b-icon { font-size: 14px; }
.benefit b { color: #fcd34d; font-weight: 700; }

.buy-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 11px;
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
  font-family: inherit;
  margin-top: 4px;
}
.btn-vip   { background: linear-gradient(135deg, #3b82f6, #6366f1); }
.btn-vvip  { background: linear-gradient(135deg, #8b5cf6, #ec4899); }
.btn-vvvip { background: linear-gradient(135deg, #f59e0b, #ef4444); }
.buy-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
}
.buy-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Modal ─────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(12px);
  z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.modal-card {
  background: var(--ybc-surface-1);
  border: 1px solid var(--ybc-border);
  border-radius: 20px;
  padding: 32px;
  width: 100%;
  max-width: 420px;
  position: relative;
  color: var(--ybc-text);
  box-shadow: var(--ybc-shadow-lg);
}
.modal-close {
  position: absolute; top: 14px; right: 14px;
  background: none; border: none;
  font-size: 22px;
  cursor: pointer;
  color: var(--ybc-text-muted);
  width: 32px; height: 32px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { background: rgba(255, 255, 255, 0.06); color: var(--ybc-text); }
.modal-card h3 {
  margin: 0 0 18px;
  font-size: 18px; font-weight: 700;
  color: var(--ybc-text-strong);
}

.summary {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--ybc-border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 18px;
}
.sum-row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 4px 0;
  font-size: 13px;
  color: var(--ybc-text);
}
.sum-row > span:first-child { color: var(--ybc-text-muted); font-size: 12px; }
.amount-row { padding-top: 10px; margin-top: 6px; border-top: 1px solid var(--ybc-border); }
.amt { color: #fca5a5; font-size: 20px; font-weight: 700; }

.channel-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 18px; }
.channel-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--ybc-border);
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  transition: 0.15s;
  font-family: inherit;
}
.channel-btn:hover { border-color: rgba(99, 102, 241, 0.3); }
.channel-btn.active {
  border-color: var(--ybc-accent);
  background: rgba(99, 102, 241, 0.08);
}
.ch-icon { font-size: 18px; }
.ch-label { flex: 1; text-align: left; color: var(--ybc-text); font-weight: 500; }
.ch-check {
  color: var(--ybc-accent-light);
  opacity: 0;
  font-weight: 700;
  transition: 0.15s;
}
.ch-check.show { opacity: 1; }

.confirm-btn {
  width: 100%;
  padding: 12px;
  background: var(--ybc-gradient-primary);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px; font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: 0.2s;
}
.confirm-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

@media (max-width: 640px) {
  .hero { padding: 24px 20px; }
  .hero-inner { flex-direction: column; }
  .hero h1 { font-size: 22px; }
  .plan-cards { grid-template-columns: 1fr; }
  .tier-heading { flex-direction: column; align-items: flex-start; }
  .tier-feats { margin-left: 0; }
}
</style>
