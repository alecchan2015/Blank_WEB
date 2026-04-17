<template>
  <div class="membership-page">
    <!-- Current status -->
    <div class="status-hero" :class="`tier-${me?.tier || 'regular'}`">
      <div class="status-inner">
        <div class="status-left">
          <div class="tier-badge">
            <span class="tier-icon">{{ tierIcon(me?.tier) }}</span>
            <span class="tier-text">{{ me?.tier_label || '普通用户' }}</span>
          </div>
          <div v-if="me?.tier !== 'regular'" class="expiry-info">
            有效期至 {{ formatDate(me?.tier_expires_at) }}
            <span v-if="me?.days_remaining !== null" class="days-left">· 剩余 {{ me.days_remaining }} 天</span>
          </div>
          <div v-else class="expiry-info hint">升级后解锁商业级 PPT、高分辨率 Logo 等高级功能</div>
        </div>
        <div v-if="me?.support_info && me.tier !== 'regular'" class="support-box">
          <div class="support-label">专属服务</div>
          <div class="support-name">{{ me.support_info.name || '会员顾问' }}</div>
          <div v-if="me.support_info.wechat" class="support-contact">微信 · {{ me.support_info.wechat }}</div>
          <div v-if="me.support_info.phone" class="support-contact">电话 · {{ me.support_info.phone }}</div>
          <div v-if="me.support_info.email" class="support-contact">邮箱 · {{ me.support_info.email }}</div>
        </div>
      </div>
    </div>

    <!-- Active features -->
    <div v-if="me?.features?.length" class="active-features">
      <span class="feat-label">已解锁：</span>
      <el-tag v-for="f in me.features" :key="f" size="small" type="success" effect="light" style="margin-right:6px">
        ✓ {{ me.feature_labels?.[f] || f }}
      </el-tag>
    </div>

    <!-- Plans by tier -->
    <div class="plans-section">
      <h2 class="section-title">选择会员套餐</h2>
      <div v-for="tier in ['vip', 'vvip', 'vvvip']" :key="tier" class="tier-group">
        <h3 class="tier-heading" :class="`tier-${tier}`">
          <span>{{ tierIcon(tier) }}</span>
          <span>{{ tierLabel(tier) }}</span>
          <span class="tier-feats">
            <span v-for="f in tierFeatures(tier)" :key="f" class="feat-chip">
              {{ publicConfig.feature_labels?.[f] || f }}
            </span>
          </span>
        </h3>
        <div class="plan-cards">
          <div
            v-for="plan in plansByTier(tier)"
            :key="plan.id"
            class="plan-card"
            :class="{ current: isCurrentPlan(plan) }"
          >
            <div class="plan-name">{{ plan.name }}</div>
            <div class="plan-price">
              <span class="currency">¥</span>
              <span class="amount">{{ (plan.price_cents / 100).toFixed(0) }}</span>
              <span class="duration">/ {{ plan.duration_days }}天</span>
            </div>
            <div class="plan-credits">
              <div>🎁 开通赠送 <b>{{ plan.activation_credits }}</b> 积分</div>
              <div>📅 每月自动 <b>{{ plan.monthly_credits }}</b> 积分</div>
            </div>
            <button class="buy-btn" :disabled="buying" @click="selectPlan(plan)">
              立即升级
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
            <div class="pay-summary">
              <div><span>套餐</span><b>{{ selectedPlan?.name }}</b></div>
              <div><span>时长</span>{{ selectedPlan?.duration_days }} 天</div>
              <div><span>金额</span><b class="amt">¥{{ (selectedPlan?.price_cents / 100).toFixed(2) }}</b></div>
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
                <span class="ch-check">{{ selectedChannel === ch ? '✓' : '' }}</span>
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

function tierIcon(tier) { return TIER_ICONS[tier] || '👤' }
function tierLabel(tier) { return publicConfig.value.tier_labels?.[tier] || TIER_LABELS_DEFAULT[tier] || tier }
function tierFeatures(tier) { return publicConfig.value.tier_features?.[tier] || [] }
function channelIcon(ch) { return CHANNEL_META[ch]?.icon || '💰' }
function channelLabel(ch) { return CHANNEL_META[ch]?.label || ch }

function plansByTier(tier) {
  return plans.value.filter(p => p.tier === tier && p.is_active)
}

function isCurrentPlan(plan) {
  return me.value?.tier === plan.tier
}

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
    // Redirect by channel behavior
    if (res.payment_url) {
      window.location.href = res.payment_url
    } else {
      router.push(`/payment/${res.order.order_no}`)
    }
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
.membership-page { max-width: 1000px; margin: 0 auto; padding-bottom: 40px; }

.status-hero {
  border-radius: 16px;
  padding: 24px 28px;
  margin-bottom: 20px;
  color: #fff;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.status-hero.tier-regular { background: linear-gradient(135deg, #64748b 0%, #475569 100%); }
.status-hero.tier-vip     { background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); }
.status-hero.tier-vvip    { background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); }
.status-hero.tier-vvvip   { background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); }

.status-inner { display: flex; justify-content: space-between; align-items: center; gap: 20px; }
.tier-badge {
  display: inline-flex; align-items: center; gap: 10px;
  background: rgba(255,255,255,0.2);
  padding: 8px 16px; border-radius: 100px;
  backdrop-filter: blur(8px);
  font-weight: 600;
}
.tier-icon { font-size: 22px; }
.tier-text { font-size: 16px; letter-spacing: 1px; }
.expiry-info { margin-top: 12px; font-size: 14px; opacity: 0.9; }
.expiry-info.hint { opacity: 0.8; }
.days-left { opacity: 0.75; margin-left: 6px; }

.support-box {
  background: rgba(255,255,255,0.15);
  border-radius: 12px; padding: 14px 18px;
  min-width: 200px;
  backdrop-filter: blur(8px);
}
.support-label { font-size: 11px; opacity: 0.7; letter-spacing: 1px; text-transform: uppercase; }
.support-name { font-size: 15px; font-weight: 600; margin-top: 4px; }
.support-contact { font-size: 12px; margin-top: 2px; opacity: 0.9; }

.active-features {
  margin-bottom: 24px;
  padding: 12px 16px;
  background: #f7f9fc;
  border-radius: 10px;
}
.feat-label { font-size: 13px; color: #666; margin-right: 8px; }

.plans-section { margin-top: 24px; }
.section-title { font-size: 20px; color: #1a1a2e; margin-bottom: 16px; }

.tier-group { margin-bottom: 28px; }
.tier-heading {
  display: flex; align-items: center; gap: 12px;
  font-size: 15px; font-weight: 600; margin-bottom: 12px;
  padding: 8px 14px;
  border-radius: 10px;
  background: #f7f9fc;
}
.tier-heading.tier-vip   { color: #3b82f6; }
.tier-heading.tier-vvip  { color: #8b5cf6; }
.tier-heading.tier-vvvip { color: #f59e0b; }
.tier-feats { display: flex; gap: 6px; flex-wrap: wrap; margin-left: auto; }
.feat-chip {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0,0,0,0.05);
  color: #666;
  border-radius: 4px;
  font-weight: 500;
}

.plan-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}
.plan-card {
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  padding: 20px;
  transition: all 0.2s;
  display: flex; flex-direction: column; gap: 12px;
}
.plan-card:hover {
  border-color: #6366f1;
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(99,102,241,0.15);
}
.plan-card.current { border-color: #22c55e; }
.plan-name { font-size: 15px; font-weight: 600; color: #1a1a2e; }
.plan-price {
  display: flex; align-items: baseline; gap: 2px; margin: 4px 0;
}
.plan-price .currency { font-size: 14px; color: #6366f1; font-weight: 600; }
.plan-price .amount { font-size: 32px; color: #1a1a2e; font-weight: 800; letter-spacing: -1px; }
.plan-price .duration { font-size: 13px; color: #999; margin-left: 4px; }
.plan-credits { font-size: 13px; color: #555; line-height: 1.6; }
.plan-credits b { color: #f59e0b; font-weight: 700; }

.buy-btn {
  margin-top: 4px;
  padding: 10px;
  background: #6366f1;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
  font-family: inherit;
}
.buy-btn:hover:not(:disabled) { background: #818cf8; }
.buy-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(6px);
  z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.modal-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  width: 100%;
  max-width: 420px;
  position: relative;
}
.modal-close {
  position: absolute; top: 12px; right: 12px;
  background: none; border: none;
  font-size: 24px; cursor: pointer; color: #999;
  width: 32px; height: 32px;
  border-radius: 8px;
}
.modal-close:hover { background: #f5f5f5; color: #333; }
.modal-card h3 { margin: 0 0 16px; font-size: 18px; color: #1a1a2e; }

.pay-summary {
  background: #f7f9fc; border-radius: 10px; padding: 14px 16px;
  margin-bottom: 18px;
}
.pay-summary > div {
  display: flex; justify-content: space-between;
  padding: 4px 0;
  font-size: 14px; color: #333;
}
.pay-summary > div > span { color: #888; }
.pay-summary .amt { color: #ef4444; font-size: 18px; }

.channel-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 18px; }
.channel-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px;
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  transition: 0.2s;
  font-family: inherit;
}
.channel-btn:hover { border-color: #6366f1; }
.channel-btn.active { border-color: #6366f1; background: #f0f1ff; }
.ch-icon { font-size: 20px; }
.ch-label { flex: 1; text-align: left; color: #333; font-weight: 500; }
.ch-check { color: #6366f1; font-weight: 700; }

.confirm-btn {
  width: 100%;
  padding: 12px;
  background: #6366f1;
  color: #fff; border: none; border-radius: 10px;
  font-size: 15px; font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: 0.2s;
}
.confirm-btn:hover:not(:disabled) { background: #818cf8; }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

@media (max-width: 640px) {
  .status-inner { flex-direction: column; align-items: flex-start; }
  .plan-cards { grid-template-columns: 1fr; }
}
</style>
