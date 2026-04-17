<template>
  <div class="admin-orders" v-loading="loading">
    <div class="page-header">
      <h2>订单管理</h2>
      <div class="actions">
        <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width:160px" @change="load">
          <el-option label="待支付" value="pending" />
          <el-option label="等待确认" value="awaiting_confirm" />
          <el-option label="已支付" value="paid" />
          <el-option label="已取消" value="canceled" />
          <el-option label="已退款" value="refunded" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert v-if="pendingCount > 0" type="warning" :closable="false" show-icon style="margin-bottom:12px">
      当前有 <b>{{ pendingCount }}</b> 个订单等待确认收款。
    </el-alert>

    <el-table :data="orders" border>
      <el-table-column prop="order_no" label="订单号" width="180">
        <template #default="{ row }">
          <code class="ono">{{ row.order_no }}</code>
        </template>
      </el-table-column>
      <el-table-column label="用户" width="110">
        <template #default="{ row }">#{{ row.user_id }}</template>
      </el-table-column>
      <el-table-column label="套餐" min-width="150">
        <template #default="{ row }">
          <b>{{ row.plan?.name }}</b>
          <div class="sub">{{ row.plan?.tier?.toUpperCase() }} · {{ row.plan?.duration_days }}天</div>
        </template>
      </el-table-column>
      <el-table-column label="金额" width="100" align="right">
        <template #default="{ row }"><b>¥{{ (row.amount_cents / 100).toFixed(2) }}</b></template>
      </el-table-column>
      <el-table-column label="渠道" width="90" align="center">
        <template #default="{ row }">{{ channelLabel(row.channel) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="150">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" align="center">
        <template #default="{ row }">
          <el-button v-if="['pending', 'awaiting_confirm'].includes(row.status)"
            size="small" type="success" @click="confirmOrder(row)">确认收款</el-button>
          <el-button v-if="row.status === 'paid'"
            size="small" type="danger" plain @click="refundOrder(row)">退款</el-button>
          <el-button v-if="['pending', 'awaiting_confirm'].includes(row.status)"
            size="small" link type="danger" @click="cancelOrder(row)">取消</el-button>
          <el-button size="small" link @click="showDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="detailVisible" title="订单详情" width="520px">
      <div v-if="currentDetail" class="detail">
        <div class="row"><span>订单号</span><code>{{ currentDetail.order_no }}</code></div>
        <div class="row"><span>用户 ID</span>{{ currentDetail.user_id }}</div>
        <div class="row"><span>套餐</span>{{ currentDetail.plan?.name }}</div>
        <div class="row"><span>金额</span>¥{{ (currentDetail.amount_cents / 100).toFixed(2) }}</div>
        <div class="row"><span>渠道</span>{{ channelLabel(currentDetail.channel) }}</div>
        <div class="row"><span>状态</span>{{ statusLabel(currentDetail.status) }}</div>
        <div class="row"><span>创建</span>{{ formatDate(currentDetail.created_at) }}</div>
        <div class="row" v-if="currentDetail.paid_at"><span>支付</span>{{ formatDate(currentDetail.paid_at) }}</div>
        <div class="row" v-if="currentDetail.canceled_at"><span>取消</span>{{ formatDate(currentDetail.canceled_at) }}</div>
        <div class="row" v-if="currentDetail.refunded_at"><span>退款</span>{{ formatDate(currentDetail.refunded_at) }}</div>
        <div class="row" v-if="currentDetail.external_order_id"><span>第三方单号</span><code>{{ currentDetail.external_order_id }}</code></div>
        <div class="notes" v-if="currentDetail.admin_notes">
          <h4>管理员备注</h4>
          <pre>{{ currentDetail.admin_notes }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI } from '../../api'

const orders = ref([])
const loading = ref(false)
const statusFilter = ref('')
const detailVisible = ref(false)
const currentDetail = ref(null)

const CHANNELS = { stripe: 'Stripe', alipay: '支付宝', wechat: '微信', manual: '模拟' }
const STATUS = {
  pending:          { label: '待支付',   type: 'warning' },
  awaiting_confirm: { label: '待确认',   type: 'warning' },
  paid:             { label: '已支付',   type: 'success' },
  canceled:         { label: '已取消',   type: 'info' },
  refunded:         { label: '已退款',   type: 'danger' },
  failed:           { label: '失败',     type: 'danger' },
}

const pendingCount = computed(() =>
  orders.value.filter(o => o.status === 'awaiting_confirm').length
)

function channelLabel(c) { return CHANNELS[c] || c }
function statusLabel(s) { return STATUS[s]?.label || s }
function statusTag(s) { return STATUS[s]?.type || '' }
function formatDate(s) { return s ? new Date(s).toLocaleString('zh-CN') : '' }

async function load() {
  loading.value = true
  try {
    orders.value = await adminAPI.getOrders(statusFilter.value || undefined)
  } finally {
    loading.value = false
  }
}

async function confirmOrder(order) {
  try {
    await ElMessageBox.confirm(
      `确认收款？\n\n订单：${order.order_no}\n金额：¥${(order.amount_cents/100).toFixed(2)}\n\n确认后将立即激活用户会员。`,
      '手动确认收款',
      { type: 'success' }
    )
    await adminAPI.confirmOrder(order.order_no)
    ElMessage.success('已确认并激活会员')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

async function refundOrder(order) {
  try {
    const { value: notes } = await ElMessageBox.prompt('退款原因（可选）', '确认退款', { type: 'warning' })
    await adminAPI.refundOrder(order.order_no, notes)
    ElMessage.success('已退款，用户会员等级已恢复')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

async function cancelOrder(order) {
  try {
    await ElMessageBox.confirm(`取消订单 ${order.order_no}？`, '确认取消', { type: 'warning' })
    await adminAPI.cancelOrderAdmin(order.order_no)
    ElMessage.success('已取消')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

function showDetail(order) {
  currentDetail.value = order
  detailVisible.value = true
}

onMounted(load)
</script>

<style scoped>
.admin-orders { max-width: 1200px; }
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { font-size: 20px; color: #1a1a2e; margin: 0; }
.actions { display: flex; gap: 8px; }
.ono { font-family: 'SF Mono', Menlo, monospace; font-size: 12px; background: #f5f7fa; padding: 2px 6px; border-radius: 4px; }
.sub { font-size: 11px; color: #888; }
.detail .row {
  display: flex; justify-content: space-between; padding: 6px 0;
  font-size: 13px; border-bottom: 1px dashed #f0f0f0;
}
.detail .row > span:first-child { color: #888; }
.detail .row code { font-family: Menlo, monospace; background: #f5f7fa; padding: 2px 6px; border-radius: 3px; font-size: 12px; }
.notes { margin-top: 12px; background: #fffbea; padding: 12px; border-radius: 6px; }
.notes h4 { margin: 0 0 6px; font-size: 12px; color: #666; }
.notes pre { margin: 0; white-space: pre-wrap; font-size: 12px; color: #333; font-family: inherit; }
</style>
