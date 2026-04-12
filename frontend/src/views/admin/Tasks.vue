<template>
  <div>
    <h2 class="page-title">任务记录</h2>
    <el-table :data="tasks" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="需求" min-width="200">
        <template #default="{ row }">
          <div class="query-cell">
            <span v-if="row.brand_name" class="brand-tag">{{ row.brand_name }}</span>
            {{ row.query }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="专家" width="200">
        <template #default="{ row }">
          <el-tag v-for="a in row.agents_selected" :key="a" size="small" :type="agentTagType[a]" style="margin:2px">
            {{ agentNames[a] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType[row.status]" size="small">{{ statusLabel[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="文件数" width="80" align="center">
        <template #default="{ row }">{{ row.results?.length || 0 }}</template>
      </el-table-column>
      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminAPI } from '../../api'

const tasks = ref([])
const loading = ref(false)

const agentNames = { strategy: '战略', brand: '品牌', operations: '运营' }
const agentTagType = { strategy: 'primary', brand: 'success', operations: 'warning' }
const statusType = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }
const statusLabel = { pending: '待处理', processing: '进行中', completed: '已完成', failed: '失败' }

onMounted(async () => {
  loading.value = true
  try { tasks.value = await adminAPI.getTasks({ limit: 100 }) }
  finally { loading.value = false }
})
</script>

<style scoped>
.page-title { font-size: 20px; color: #1a1a2e; margin-bottom: 16px; }
.query-cell { font-size: 13px; color: #444; line-height: 1.5; }
.brand-tag { background: #e8f0fe; color: #0f3460; font-size: 11px; padding: 1px 6px; border-radius: 3px; margin-right: 6px; }
</style>
