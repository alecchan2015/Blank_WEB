<template>
  <div class="new-task-page">
    <div class="page-header">
      <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <h2>新建品牌策划任务</h2>
    </div>

    <div class="form-card">
      <!-- Brand Name -->
      <div class="form-section">
        <label class="section-label">品牌名称 <span class="optional">（选填）</span></label>
        <el-input v-model="form.brand_name" placeholder="例如：木语、原木家、品质居等" size="large" maxlength="50" show-word-limit />
      </div>

      <!-- Query -->
      <div class="form-section">
        <label class="section-label">您的需求 <span class="required">*</span></label>
        <el-input
          v-model="form.query" type="textarea" :rows="4" size="large"
          placeholder="例如：我想创建一个定位中高端消费者的北欧简约风格家具品牌，目标市场是25-40岁的城市精英群体，请帮我制定全套品牌战略方案。"
          maxlength="1000" show-word-limit
        />
      </div>

      <!-- Agent Selection -->
      <div class="form-section">
        <label class="section-label">选择 AI 专家 <span class="required">*</span></label>
        <p class="section-desc">可选单个或多个专家协作，多专家将按顺序分工合作</p>
        <div class="agent-grid">
          <div
            v-for="agent in agents" :key="agent.type"
            class="agent-card"
            :class="{ selected: form.agents_selected.includes(agent.type) }"
            @click="toggleAgent(agent.type)"
          >
            <div class="agent-icon">{{ agent.icon }}</div>
            <div class="agent-info">
              <div class="agent-name">{{ agent.name }}</div>
              <div class="agent-desc">{{ agentDesc[agent.type] }}</div>
            </div>
            <el-icon v-if="form.agents_selected.includes(agent.type)" class="check-icon"><Select /></el-icon>
          </div>
        </div>

        <!-- Quick Select -->
        <div class="quick-select">
          <el-button size="small" @click="selectAll">全选（三专家协作）</el-button>
          <el-button size="small" @click="form.agents_selected = []">清空</el-button>
        </div>
      </div>

      <!-- Collaboration Note -->
      <el-alert
        v-if="form.agents_selected.length > 1"
        title="多专家协作模式"
        :description="`将按顺序启动：${selectedAgentNames.join(' → ')}，后续专家会参考前序专家的输出`"
        type="info" show-icon :closable="false" style="margin-bottom:20px"
      />

      <el-button
        type="primary" size="large" :loading="submitting"
        :disabled="!form.query || !form.agents_selected.length"
        @click="submitTask" style="width:100%"
      >
        🚀 开始 AI 分析
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Select } from '@element-plus/icons-vue'
import { tasksAPI, agentsAPI } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const submitting = ref(false)
const agents = ref([])

const form = ref({ query: '', brand_name: '', agents_selected: [] })

const agentDesc = {
  strategy: '市场分析、竞争定位、品牌战略规划',
  brand: 'Logo概念、色彩体系、视觉物料规范',
  operations: '渠道策略、营销计划、执行路径',
}

const agentNames = { strategy: '战略规划', brand: '品牌设计', operations: '运营实施' }

const selectedAgentNames = computed(() =>
  ['strategy', 'brand', 'operations'].filter(a => form.value.agents_selected.includes(a)).map(a => agentNames[a])
)

function toggleAgent(type) {
  const idx = form.value.agents_selected.indexOf(type)
  if (idx > -1) form.value.agents_selected.splice(idx, 1)
  else form.value.agents_selected.push(type)
}

function selectAll() {
  form.value.agents_selected = agents.value.map(a => a.type)
}

async function submitTask() {
  if (!form.value.query.trim()) { ElMessage.warning('请输入需求'); return }
  if (!form.value.agents_selected.length) { ElMessage.warning('请选择至少一个专家'); return }
  submitting.value = true
  try {
    const task = await tasksAPI.create({
      query: form.value.query,
      brand_name: form.value.brand_name,
      agents_selected: form.value.agents_selected,
    })
    router.push(`/tasks/${task.id}`)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try { agents.value = await agentsAPI.list() }
  catch { agents.value = [
    { type: 'strategy', name: '战略规划专家', icon: '🎯' },
    { type: 'brand', name: '品牌设计专家', icon: '🎨' },
    { type: 'operations', name: '运营实施专家', icon: '🚀' },
  ]}
})
</script>

<style scoped>
.new-task-page { max-width: 720px; margin: 0 auto; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.page-header h2 { font-size: 20px; color: #1a1a2e; }
.form-card { background: #fff; border-radius: 12px; padding: 32px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.form-section { margin-bottom: 28px; }
.section-label { display: block; font-size: 15px; font-weight: 600; color: #222; margin-bottom: 10px; }
.section-desc { font-size: 13px; color: #888; margin-bottom: 12px; }
.required { color: #f56c6c; }
.optional { color: #aaa; font-weight: normal; font-size: 13px; }
.agent-grid { display: flex; flex-direction: column; gap: 12px; }
.agent-card {
  display: flex; align-items: center; gap: 16px;
  border: 2px solid #e4e7ed; border-radius: 10px; padding: 16px;
  cursor: pointer; transition: all 0.2s; position: relative;
  background: #fafafa;
}
.agent-card:hover { border-color: #409eff; background: #f0f7ff; }
.agent-card.selected { border-color: #409eff; background: #ecf5ff; }
.agent-icon { font-size: 32px; flex-shrink: 0; }
.agent-name { font-size: 15px; font-weight: 600; color: #222; margin-bottom: 4px; }
.agent-desc { font-size: 12px; color: #888; }
.check-icon { position: absolute; right: 16px; color: #409eff; font-size: 20px; }
.quick-select { margin-top: 12px; display: flex; gap: 8px; }
</style>
