<template>
  <div>
    <h2 class="page-title">数据概览</h2>
    <div class="stat-grid">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon">{{ s.icon }}</div>
        <div class="stat-value">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>
    <el-card class="tips-card" shadow="never">
      <template #header><span>🚀 快速开始</span></template>
      <ol class="tips-list">
        <li>前往 <strong>模型配置</strong> 添加大模型 API Key（OpenAI / Claude / 火山引擎）</li>
        <li>前往 <strong>知识库管理</strong> 为三个 AI 专家输入行业经验和案例</li>
        <li>邀请用户注册，在 <strong>用户管理</strong> 中分配积分</li>
        <li>用户可在前台创建品牌策划任务，下载 MD / PDF / PNG 材料</li>
      </ol>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminAPI } from '../../api'

const rawStats = ref({})

const stats = ref([
  { icon: '👥', label: '注册用户', value: '-' },
  { icon: '📋', label: '总任务数', value: '-' },
  { icon: '✅', label: '已完成', value: '-' },
  { icon: '🤖', label: '活跃模型配置', value: '-' },
  { icon: '📚', label: '知识库条目', value: '-' },
])

onMounted(async () => {
  try {
    const d = await adminAPI.stats()
    stats.value[0].value = d.total_users
    stats.value[1].value = d.total_tasks
    stats.value[2].value = d.completed_tasks
    stats.value[3].value = d.total_llm_configs
    stats.value[4].value = d.total_knowledge
  } catch {}
})
</script>

<style scoped>
.page-title { font-size: 22px; color: #1a1a2e; margin-bottom: 24px; }
.stat-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card {
  background: #fff; border-radius: 12px; padding: 24px 16px;
  text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.stat-icon { font-size: 32px; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: #1a1a2e; }
.stat-label { font-size: 13px; color: #888; margin-top: 4px; }
.tips-card { border-radius: 12px; }
.tips-list { padding-left: 20px; }
.tips-list li { margin-bottom: 10px; line-height: 1.7; color: #555; font-size: 14px; }
</style>
