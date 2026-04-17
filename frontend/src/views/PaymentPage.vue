<template>
  <div class="payment-page" v-loading="loading">
    <div v-if="order" class="pay-card">
      <div class="pay-header">
        <h2>订单支付</h2>
        <span class="status-chip" :class="`s-${order.status}`">
          <span class="dot"></span>{{ statusLabel(order.status) }}
        </span>
      </div>

      <div class="order-info">
        <div class="row"><span>订单号</span><code>{{ order.order_no }}</code></div>
        <div class="row"><span>套餐</span><b>{{ order.plan?.name }}</b></div>
        <div class="row"><span>时长</span>{{ order.plan?.duration_days }} 天</div>
        <div class="row"><span>支付方式</span>{{ channelLabel(order.channel) }}</div>
        <div class="row amount-row">
          <span>应付金额</span>
          <b class="amount">¥ {{ (order.amount_cents / 100).toFixed(2) }}</b>
        </div>
        <div class="row hint-row"><span>订单有效期至</span>{{ formatDate(order.expires_at) }}</div>
      </div>

      <!-- Manual channel -->
      <div v-if="order.channel === 'manual' && ['pending', 'awaiting_confirm'].includes(order.status)" class="manual-panel">
        <div v-if="order.status === 'pending'" class="manual-hint">
          <p>{{ message || '请通过您熟悉的方式完成付款，然后点击下方按钮通知我们。' }}</p>
          <div class="steps">
            <div class="step"><span class="n">1</span>向管理员指定的收款账户转账 <b>¥ {{ (order.amount_cents / 100).toFixed(2) }}</b></div>
            <div class="step"><span class="n">2</span>转账附言中填写订单号 <code>{{ order.order_no }}</code></div>
            <div class="step"><span class="n">3</span>点击下方「我已完成支付」按钮</div>
            <div class="step"><span class="n">4</span>管理员会在 24 小时内确认并激活您的会员</div>
          </div>
          <button class="primary-btn" :disabled="acting" @click="markPaying">
            {{ acting ? '提交中…' : '我已完成支付' }}
          </button>
        </div>
        <div v-else class="waiting-state">
          <div class="state-icon">⏳</div>
          <h3>等待管理员确认</h3>
          <p>您的支付信息已提交，管理员会在 24 小时内完成确认并激活会员。</p>
          <p class="sub-hint">可在「我的订单」随时查看状态</p>
        </div>
      </div>

      <!-- Stripe -->
      <div v-else-if="order.channel === 'stripe' && order.status === 'pending'" class="channel-panel">
        <p class="channel-hint">即将跳转 Stripe 完成信用卡支付…</p>
        <a v-if="paymentUrl" :href="paymentUrl" class="primary-btn">打开 Stripe 支付页</a>
      </div>

      <!-- Alipay / Wechat -->
      <div v-else-if="['alipay', 'wechat'].includes(order.channel) && order.status === 'pending'" class="channel-panel">
        <p class="channel-hint">{{ message || '请使用对应 APP 扫码完成支付' }}</p>
        <div v-if="qrCodeUrl" class="qr-box">
          <img :src="qrCodeUrl" alt="Payment QR" />
        </div>
        <div v-else class="qr-placeholder">
          <span class="q-icon">📱</span>
          <p>二维码生成中…</p>
          <p class="sub-hint">（当前为占位符，真实渠道接入后将显示）</p>
        </div>
      </div>

      <!-- Paid -->
      <div v-else-if="order.status === 'paid'" class="success-state">
        <div class="state-icon success-icon">✓</div>
        <h3>支付成功</h3>
        <p>会员已激活！{{ paidAtText }}</p>
        <button class="primary-btn" @click="$router.push('/membership')">返回会员中心</button>
      </div>

      <div v-else-if="['canceled', 'refunded', 'failed'].includes(order.status)" class="fail-state">
        <div class="state-icon">⚠️</div>
        <h3>订单{{ statusLabel(order.status) }}</h3>
        <button class="primary-btn" @click="$router.push('/membership')">重新选择套餐</button>
      </div>

      <div class="footer-actions">
        <button class="link-btn" @click="$router.push('/orders')">我的订单</button>
        <button v-if="['pending'].includes(order.status)" class="link-btn danger" @click="cancelOrder">取消订单</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { paymentAPI } from '../api'

const route = useRoute()
const router = useRouter()

const order = ref(null)
const loading = ref(true)
const acting = ref(false)
const message = ref('')
const paymentUrl = ref('')
const qrCodeUrl = ref('')

const CHANNEL_LABELS = { stripe: '信用卡 (Stripe)', alipay: '支付宝', wechat: '微信支付', manual: '模拟支付' }
const STATUS_MAP = {
  pending:          '待支付',
  awaiting_confirm: '等待确认',
  paid:             '已支付',
  canceled:         '已取消',
  refunded:         '已退款',
  failed:           '失败',
}

function channelLabel(ch) { return CHANNEL_LABELS[ch] || ch }
function statusLabel(s) { return STATUS_MAP[s] || s }
function formatDate(s) { return s ? new Date(s).toLocaleString('zh-CN') : '' }

const paidAtText = computed(() =>
  order.value?.paid_at ? `支付时间 ${formatDate(order.value.paid_at)}` : ''
)

async function load() {
  loading.value = true
  try {
    order.value = await paymentAPI.getOrder(route.params.order_no)
  } catch (e) {
    ElMessage.error(e.message || '订单不存在')
    router.push('/membership')
  } finally { loading.value = false }
}

async function markPaying() {
  acting.value = true
  try {
    order.value = await paymentAPI.markPaying(route.params.order_no)
    ElMessage.success('已提交，等待管理员确认')
  } catch (e) { ElMessage.error(e.message || '提交失败') }
  finally { acting.value = false }
}

async function cancelOrder() {
  try {
    await ElMessageBox.confirm('确定要取消此订单吗？', '取消订单', { type: 'warning' })
    order.value = await paymentAPI.cancelOrder(route.params.order_no)
    ElMessage.success('订单已取消')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '取消失败')
  }
}

onMounted(load)
</script>

<style scoped>
.payment-page {
  max-width: 600px;
  margin: 20px auto;
  color: var(--ybc-text);
}

.pay-card {
  background: var(--ybc-surface-1);
  border: 1px solid var(--ybc-border);
  border-radius: 20px;
  padding: 32px;
  box-shadow: var(--ybc-shadow-md);
}

.pay-header {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 18px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--ybc-border);
}
.pay-header h2 {
  margin: 0;
  font-size: 18px; font-weight: 700;
  color: var(--ybc-text-strong);
}

.status-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px;
  border-radius: 100px;
  font-size: 11px; font-weight: 600;
}
.status-chip .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.s-pending,
.s-awaiting_confirm { background: rgba(245, 158, 11, 0.15); color: #fcd34d; }
.s-pending .dot,
.s-awaiting_confirm .dot { animation: ybc-pulse-dot 1s infinite; }
.s-paid { background: rgba(34, 197, 94, 0.15); color: #86efac; }
.s-canceled { background: rgba(255, 255, 255, 0.08); color: var(--ybc-text-muted); }
.s-refunded, .s-failed { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }

/* Order info */
.order-info {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--ybc-border);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 22px;
}
.order-info .row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 6px 0;
  font-size: 13px;
  color: var(--ybc-text);
}
.order-info .row > span:first-child { color: var(--ybc-text-muted); font-size: 12px; }
.order-info code {
  font-family: 'SF Mono', Menlo, monospace;
  font-size: 12px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--ybc-accent-light);
  padding: 2px 8px;
  border-radius: 4px;
}
.amount-row {
  padding-top: 14px !important;
  margin-top: 6px;
  border-top: 1px solid var(--ybc-border);
}
.amount-row .amount {
  color: #fca5a5;
  font-size: 24px;
  font-weight: 700;
}
.hint-row {
  font-size: 11px;
  color: var(--ybc-text-faint);
}

/* Manual panel */
.manual-hint > p {
  font-size: 14px;
  color: var(--ybc-text-dim);
  margin: 0 0 16px;
  line-height: 1.6;
}
.steps {
  background: rgba(245, 158, 11, 0.06);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 20px;
}
.step {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px;
  color: #fde68a;
  line-height: 1.8;
  padding: 4px 0;
}
.step .n {
  width: 20px; height: 20px;
  border-radius: 50%;
  background: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
  font-size: 11px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.step code {
  background: rgba(0, 0, 0, 0.3);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-family: 'SF Mono', Menlo, monospace;
}
.step b { color: #fcd34d; }

.primary-btn {
  display: block;
  width: 100%;
  padding: 14px;
  background: var(--ybc-gradient-primary);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 15px; font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  text-align: center;
  transition: 0.2s;
  font-family: inherit;
}
.primary-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(99, 102, 241, 0.35);
}
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* States */
.waiting-state, .success-state, .fail-state, .channel-panel {
  text-align: center;
  padding: 24px 0;
}
.state-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.success-icon {
  width: 72px; height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff;
  font-size: 36px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 12px 24px rgba(34, 197, 94, 0.35);
}
.waiting-state h3,
.success-state h3,
.fail-state h3 {
  color: var(--ybc-text-strong);
  margin: 10px 0;
  font-size: 20px;
}
.waiting-state p, .success-state p, .fail-state p {
  color: var(--ybc-text-dim);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
}
.sub-hint { color: var(--ybc-text-muted); font-size: 12px !important; }
.channel-hint {
  color: var(--ybc-text-dim);
  font-size: 14px;
  margin-bottom: 16px;
}

.qr-box, .qr-placeholder {
  width: 220px; height: 220px;
  margin: 20px auto;
  border-radius: 14px;
  background: #fff;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 14px;
}
.qr-placeholder {
  background: rgba(255, 255, 255, 0.04);
  border: 1px dashed var(--ybc-border);
}
.q-icon { font-size: 44px; color: var(--ybc-text-muted); }
.qr-placeholder p { color: var(--ybc-text-muted); font-size: 12px; margin-top: 8px; }
.qr-box img { width: 100%; height: 100%; object-fit: contain; }

.footer-actions {
  display: flex; justify-content: space-between;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--ybc-border);
}
.link-btn {
  background: none; border: none;
  font-size: 13px; cursor: pointer;
  padding: 4px 8px;
  color: var(--ybc-text-muted);
  font-family: inherit;
}
.link-btn:hover { color: var(--ybc-accent-light); }
.link-btn.danger:hover { color: #fca5a5; }
</style>
