<template>
  <div class="orders-page">
    <div class="page-header">
      <h2>我的订单</h2>
      <el-button :icon="Refresh" size="small" @click="load">刷新</el-button>
    </div>

    <el-empty v-if="!loading && !orders.length" description="还没有订单" />

    <el-table v-else :data="orders" v-loading="loading" border>
      <el-table-column prop="order_no" label="订单号" width="200">
        <template #default="{ row }">
          <code class="order-no">{{ row.order_no }}</code>
        </template>
      </el-table-column>
      <el-table-column label="套餐" min-width="160">
        <template #default="{ row }">
          <div class="plan-cell">
            <b>{{ row.plan?.name }}</b>
            <div class="plan-sub">{{ tierLabel(row.plan?.tier) }} · {{ row.plan?.duration_days }}天</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="金额" width="110" align="right">
        <template #default="{ row }">
          <b class="amount">¥{{ (row.amount_cents / 100).toFixed(2) }}</b>
        </template>
      </el-table-column>
      <el-table-column label="渠道" width="100" align="center">
        <template #default="{ row }">{{ channelLabel(row.channel) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" align="center">
        <template #default="{ row }">
          <el-button size="small" link @click="$router.push(`/payment/${row.order_no}`)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { paymentAPI } from '../api'

const orders = ref([])
const loading = ref(false)

const TIER_LABELS = { vip: 'VIP', vvip: 'VVIP', vvvip: 'VVVIP' }
const CHANNELS = { stripe: 'Stripe', alipay: '支付宝', wechat: '微信', manual: '模拟' }
const STATUS = {
  pending:          { label: '待支付',   type: 'warning' },
  awaiting_confirm: { label: '待确认', type: 'warning' },
  paid:             { label: '已支付',   type: 'success' },
  canceled:         { label: '已取消',   type: 'info' },
  refunded:         { label: '已退款',   type: 'danger' },
  failed:           { label: '失败',     type: 'danger' },
}

function tierLabel(t) { return TIER_LABELS[t] || t }
function channelLabel(c) { return CHANNELS[c] || c }
function statusLabel(s) { return STATUS[s]?.label || s }
function statusTag(s) { return STATUS[s]?.type || '' }
function formatDate(s) { return new Date(s).toLocaleString('zh-CN') }

async function load() {
  loading.value = true
  try {
    orders.value = await paymentAPI.myOrders()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.orders-page { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 20px; color: #1a1a2e; margin: 0; }
.order-no { font-family: 'SF Mono', Menlo, monospace; font-size: 12px; background: #f5f7fa; padding: 2px 6px; border-radius: 4px; }
.plan-cell b { font-size: 14px; color: #1a1a2e; }
.plan-sub { font-size: 12px; color: #888; margin-top: 2px; }
.amount { color: #ef4444; font-size: 15px; font-weight: 700; }
</style>
