<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">知识库管理</h2>
      <el-button type="primary" :icon="Plus" @click="openDialog()">添加知识条目</el-button>
    </div>

    <el-alert title="知识库说明" type="success" show-icon :closable="false" style="margin-bottom:16px">
      <template #default>
        为每个 AI 专家输入行业知识、成功案例、专业方法论等，将作为专家的"经验"参与生成。<br>
        建议每个专家添加 3-10 条高质量知识，内容越具体，专家输出质量越高。
      </template>
    </el-alert>

    <el-tabs v-model="activeAgent" @tab-click="loadKnowledge">
      <el-tab-pane
        v-for="a in agents" :key="a.type"
        :label="`${a.icon} ${a.name}`" :name="a.type"
      />
    </el-tabs>

    <div class="knowledge-list">
      <div v-if="!items.length && !loading" class="empty-state">
        <div class="empty-icon">📚</div>
        <p>暂无知识条目，点击「添加知识条目」开始输入</p>
      </div>
      <div v-for="item in items" :key="item.id" class="knowledge-item">
        <div class="item-header">
          <span class="item-title">{{ item.title }}</span>
          <div class="item-actions">
            <el-button size="small" link @click="openDialog(item)">编辑</el-button>
            <el-button size="small" link type="danger" @click="deleteItem(item.id)">删除</el-button>
          </div>
        </div>
        <div class="item-content">{{ item.content }}</div>
        <div class="item-meta">添加于 {{ new Date(item.created_at).toLocaleDateString('zh-CN') }}</div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑知识条目' : '添加知识条目'" width="640px">
      <el-form :model="form" label-position="top">
        <el-form-item label="适用专家">
          <el-select v-model="form.agent_type" style="width:100%">
            <el-option v-for="a in agents" :key="a.type" :label="`${a.icon} ${a.name}`" :value="a.type" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="例如：北欧简约风品牌定位方法论" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content" type="textarea" :rows="10"
            placeholder="输入详细的知识内容、案例分析、方法论等..." show-word-limit maxlength="5000"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { adminAPI } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeAgent = ref('strategy')
const items = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editId = ref(null)
const saving = ref(false)

const agents = [
  { type: 'strategy', name: '战略规划专家', icon: '🎯' },
  { type: 'brand', name: '品牌设计专家', icon: '🎨' },
  { type: 'operations', name: '运营实施专家', icon: '🚀' },
]

const form = ref({ agent_type: 'strategy', title: '', content: '' })

function openDialog(item = null) {
  editId.value = item?.id || null
  form.value = item
    ? { agent_type: item.agent_type, title: item.title, content: item.content }
    : { agent_type: activeAgent.value, title: '', content: '' }
  dialogVisible.value = true
}

async function saveItem() {
  if (!form.value.title || !form.value.content) { ElMessage.warning('请填写标题和内容'); return }
  saving.value = true
  try {
    if (editId.value) {
      await adminAPI.updateKnowledge(editId.value, form.value)
    } else {
      await adminAPI.createKnowledge(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadKnowledge()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function deleteItem(id) {
  await ElMessageBox.confirm('确认删除此知识条目？', '警告', { type: 'warning' })
  await adminAPI.deleteKnowledge(id)
  ElMessage.success('已删除')
  await loadKnowledge()
}

async function loadKnowledge() {
  loading.value = true
  try { items.value = await adminAPI.getKnowledge(activeAgent.value) }
  finally { loading.value = false }
}

onMounted(loadKnowledge)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 20px; color: #1a1a2e; }
.knowledge-list { margin-top: 16px; display: flex; flex-direction: column; gap: 12px; }
.empty-state { text-align: center; padding: 60px; color: #aaa; background: #fff; border-radius: 8px; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.knowledge-item { background: #fff; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
.item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.item-title { font-size: 15px; font-weight: 600; color: #222; }
.item-content { font-size: 13px; color: #555; line-height: 1.7; white-space: pre-wrap;
  max-height: 80px; overflow: hidden; text-overflow: ellipsis; }
.item-meta { font-size: 11px; color: #aaa; margin-top: 8px; }
</style>
