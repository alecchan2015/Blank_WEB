<template>
  <div>
    <div class="page-header">
      <h2>我的任务</h2>
      <el-button type="primary" @click="$router.push('/tasks/new')" :icon="Plus">
        新建品牌策划
      </el-button>
    </div>

    <!-- Empty State -->
    <div v-if="!tasks.length && !loading" class="empty-state">
      <div class="empty-icon">🎯</div>
      <h3>还没有任务</h3>
      <p>点击「新建品牌策划」开始使用 AI 专家团队</p>
      <el-button type="primary" @click="$router.push('/tasks/new')">立即开始</el-button>
    </div>

    <!-- Task List -->
    <div v-else class="task-grid">
      <el-card
        v-for="task in tasks" :key="task.id"
        class="task-card"
        shadow="hover"
        @click="$router.push(`/tasks/${task.id}`)"
      >
        <div class="task-card-header">
          <div class="task-agents">
            <el-tag
              v-for="a in task.agents_selected" :key="a"
              :type="agentTagType[a]" size="small" effect="light"
            >{{ agentNames[a] }}</el-tag>
          </div>
          <el-tag :type="statusType[task.status]" size="small">{{ statusLabel[task.status] }}</el-tag>
        </div>
        <div class="task-query">{{ task.query }}</div>
        <div class="task-meta">
          <span v-if="task.brand_name" class="brand-name">{{ task.brand_name }}</span>
          <span class="task-time">{{ formatTime(task.created_at) }}</span>
        </div>
        <div v-if="task.results?.length" class="task-files">
          <el-icon><Document /></el-icon>
          <span>{{ task.results.length }} 个文件</span>
        </div>
      </el-card>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Document } from '@element-plus/icons-vue'
import { tasksAPI } from '../api'

const tasks = ref([])
const loading = ref(false)

const agentNames = { strategy: '战略规划', brand: '品牌设计', operations: '运营实施' }
const agentTagType = { strategy: 'primary', brand: 'success', operations: 'warning' }
const statusType = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }
const statusLabel = { pending: '待处理', processing: '进行中', completed: '已完成', failed: '失败' }

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  loading.value = true
  try { tasks.value = await tasksAPI.list({ limit: 50 }) }
  finally { loading.value = false }
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 22px; color: #1a1a2e; }
.empty-state {
  text-align: center; padding: 80px 20px;
  background: #fff; border-radius: 12px;
}
.empty-icon { font-size: 64px; margin-bottom: 16px; }
.empty-state h3 { font-size: 18px; color: #333; margin-bottom: 8px; }
.empty-state p { color: #888; margin-bottom: 24px; }
.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.task-card { cursor: pointer; transition: transform 0.2s; }
.task-card:hover { transform: translateY(-2px); }
.task-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.task-agents { display: flex; gap: 4px; flex-wrap: wrap; }
.task-query { font-size: 15px; color: #222; margin-bottom: 10px; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.task-meta { display: flex; justify-content: space-between; align-items: center; }
.brand-name { font-size: 12px; color: #0f3460; font-weight: 600; background: #e8f0fe; padding: 2px 8px; border-radius: 4px; }
.task-time { font-size: 12px; color: #aaa; }
.task-files { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #888; margin-top: 8px; }
.loading-state { padding: 24px; }
</style>
