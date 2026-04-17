<template>
  <div class="payment-page" v-loading="loading">
    <div v-if="order" class="pay-card">
      <div class="pay-header">
        <h2>订单支付</h2>
        <el-tag :type="statusTag(order.status)" effect="dark">{{ statusLabel(order.status) }}</el-tag>
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

      <!-- Manual channel flow -->
      <div v-if="order.channel === 'manual' && ['pending', 'awaiting_confirm'].includes(order.status)" class="manual-panel">
        <div v-if="order.status === 'pending'" class="manual-hint">
          <p>{{ message || '请通过您熟悉的方式完成付款，然后点击下方按钮通知我们。' }}</p>
          <div class="steps">
            <div class="step">1. 向管理员指定的收款账户转账 <b>¥ {{ (order.amount_cents / 100).toFixed(2) }}</b></div>
            <div class="step">2. 转账附言中填写订单号 <code>{{ order.order_no }}</code></div>
            <div class="step">3. 点击下方「我已完成支付」按钮</div>
            <div class="step">4. 管理员会在 24 小时内确认并激活您的会员</div>
          </div>
          <button class="primary-btn" :disabled="acting" @click="markPaying">我已完成支付</button>
        </div>
        <div v-else class="waiting">
          <div class="waiting-icon">⏳</div>
          <h3>等待管理员确认</h3>
          <p>您的支付信息已提交，管理员会在 24 小时内完成确认并激活会员。</p>
          <p class="sub-hint">确认后您将自动获得对应等级，可在「我的订单」随时查看状态。</p>
        </div>
      </div>

      <!-- Stripe (redirect) -->
      <div v-else-if="order.channel === 'stripe' && order.status === 'pending'" class="channel-panel">
        <p>即将跳转 Stripe 完成信用卡支付…</p>
        <a v-if="paymentUrl" :href="paymentUrl" class="primary-btn">打开 Stripe 支付页</a>
      </div>

      <!-- Alipay / Wechat (QR) -->
      <div v-else-if="['alipay', 'wechat'].includes(order.channel) && order.status === 'pending'" class="channel-panel">
        <p>{{ message || '请使用对应 APP 扫码完成支付' }}</p>
        <div v-if="qrCodeUrl" class="qr-box">
          <img :src="qrCodeUrl" alt="Payment QR" />
        </div>
        <div v-else class="qr-placeholder">
          <span>📱</span>
          <p>二维码生成中…（当前为占位符，真实渠道接入后将显示）</p>
        </div>
      </div>

      <!-- Paid state -->
      <div v-else-if="order.status === 'paid'" class="success-panel">
        <div class="success-icon">✓</div>
        <h3>支付成功</h3>
        <p>会员已激活！{{ paidAtText }}</p>
        <button class="primary-btn" @click="$router.push('/membership')">返回会员中心</button>
      </div>

      <div v-else-if="['canceled', 'refunded', 'failed'].includes(order.status)" class="fail-panel">
        <h3>订单{{ statusLabel(order.status) }}</h3>
        <p v-if="order.admin_notes">{{ order.admin_notes }}</p>
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

const CHANNEL_LABELS = {
  stripe: '信用卡 (Stripe)',
  alipay: '支付宝',
  wechat: '微信支付',
  manual: '模拟支付',
}

const STATUS_MAP = {
  pending:          { label: '待支付',   type: 'warning' },
  awaiting_confirm: { label: '等待确认', type: 'warning' },
  paid:             { label: '已支付',   type: 'success' },
  canceled:         { label: '已取消',   type: 'info' },
  refunded:         { label: '已退款',   type: 'danger' },
  failed:           { label: '失败',     type: 'danger' },
}

function channelLabel(ch) { return CHANNEL_LABELS[ch] || ch }
function statusLabel(s) { return STATUS_MAP[s]?.label || s }
function statusTag(s) { return STATUS_MAP[s]?.type || '' }

function formatDate(s) {
  if (!s) return ''
  return new Date(s).toLocaleString('zh-CN')
}

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
  } finally {
    loading.value = false
  }
}

async function markPaying() {
  acting.value = true
  try {
    order.value = await paymentAPI.markPaying(route.params.order_no)
    ElMessage.success('已提交，等待管理员确认')
  } catch (e) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    acting.value = false
  }
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
.payment-page { max-width: 600px; margin: 40px auto; padding: 20px; }
.pay-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.pay-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #f0f0f0;
}
.pay-header h2 { margin: 0; font-size: 18px; color: #1a1a2e; }

.order-info {
  background: #f7f9fc;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 24px;
}
.order-info .row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 6px 0;
  font-size: 14px; color: #333;
}
.order-info .row > span:first-child { color: #888; font-size: 13px; }
.order-info .row code {
  font-family: 'SF Mono', Menlo, monospace;
  font-size: 13px;
  background: #fff; padding: 2px 8px; border-radius: 4px;
}
.amount-row { padding-top: 12px !important; border-top: 1px solid #e5e7eb; margin-top: 6px; }
.amount-row .amount { color: #ef4444; font-size: 22px; font-weight: 700; }
.hint-row { font-size: 12px; color: #999; }

.manual-panel .manual-hint > p { font-size: 14px; color: #555; margin: 0 0 16px; }
.steps {
  background: #fffbea; border: 1px solid #fde68a;
  border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;
}
.step { font-size: 13px; color: #78350f; line-height: 2; }
.step code { background: #fff; padding: 1px 6px; border-radius: 3px; font-size: 12px; }
.step b { color: #d97706; }

.primary-btn {
  width: 100%;
  padding: 12px;
  background: #6366f1;
  color: #fff; border: none; border-radius: 10px;
  font-size: 15px; font-weight: 600;
  cursor: pointer;
  display: block;
  text-align: center;
  text-decoration: none;
  font-family: inherit;
}
.primary-btn:hover:not(:disabled) { background: #818cf8; }
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.waiting, .success-panel, .fail-panel, .channel-panel {
  text-align: center; padding: 24px 0;
}
.waiting-icon, .success-icon { font-size: 48px; margin-bottom: 12px; }
.success-icon {
  color: #22c55e; background: #dcfce7;
  width: 64px; height: 64px; border-radius: 50%; margin: 0 auto 16px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700;
}
.waiting h3, .success-panel h3, .fail-panel h3 { color: #1a1a2e; margin: 12px 0; }
.waiting p, .success-panel p, .fail-panel p { color: #555; font-size: 14px; }
.waiting .sub-hint { color: #888; font-size: 13px; margin-top: 4px; }

.qr-box, .qr-placeholder {
  width: 200px; height: 200px; margin: 20px auto;
  background: #f7f9fc; border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.qr-placeholder span { font-size: 40px; }
.qr-placeholder p { font-size: 12px; color: #888; margin-top: 8px; }
.qr-box img { width: 100%; height: 100%; object-fit: contain; border-radius: 12px; }

.footer-actions {
  display: flex; justify-content: space-between; margin-top: 20px;
  padding-top: 16px; border-top: 1px solid #f0f0f0;
}
.link-btn {
  background: none; border: none; color: #666;
  font-size: 13px; cursor: pointer; padding: 4px 8px;
  font-family: inherit;
}
.link-btn:hover { color: #6366f1; }
.link-btn.danger:hover { color: #ef4444; }
</style>
