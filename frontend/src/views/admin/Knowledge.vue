<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">知识库管理</h2>
      <div class="header-actions">
        <el-button type="success" :icon="Download" @click="confirmImportSeed" :loading="importingSeeds">
          导入种子知识库
        </el-button>
        <el-button type="warning" :icon="Upload" @click="uploadDialogVisible = true">上传文档</el-button>
        <el-button type="primary" :icon="Plus" @click="openDialog()">添加知识条目</el-button>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="stats-overview" v-if="stats">
      <div class="stat-card">
        <div class="stat-number">{{ stats.total || 0 }}</div>
        <div class="stat-label">总条目</div>
      </div>
      <div class="stat-card" v-for="a in agents" :key="'stat-' + a.type">
        <div class="stat-number">{{ (stats.by_agent && stats.by_agent[a.type]) || 0 }}</div>
        <div class="stat-label">{{ a.icon }} {{ a.name }}</div>
      </div>
      <div class="stat-card" v-for="(count, type) in stats.by_type" :key="'type-' + type">
        <div class="stat-number">{{ count }}</div>
        <div class="stat-label">{{ knowledgeTypeLabel(type) }}</div>
      </div>
    </div>

    <el-alert title="知识库说明" type="success" show-icon :closable="false" style="margin-bottom:16px">
      <template #default>
        为每个 AI 专家输入行业知识、成功案例、专业方法论等，将作为专家的"经验"参与生成。<br>
        建议每个专家添加 3-10 条高质量知识，内容越具体，专家输出质量越高。
        支持上传 PDF、DOCX、TXT、MD、ZIP 文件，AI 将自动提取知识条目。
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
          <div class="item-title-row">
            <span class="item-title">{{ item.title }}</span>
            <el-tag v-if="item.knowledge_type" size="small" :type="knowledgeTypeTagType(item.knowledge_type)" style="margin-left: 8px;">
              {{ knowledgeTypeLabel(item.knowledge_type) }}
            </el-tag>
            <el-tag v-if="item.source" size="small" type="info" style="margin-left: 4px;">
              {{ sourceLabel(item.source) }}
            </el-tag>
          </div>
          <div class="item-actions">
            <el-button size="small" link @click="openDialog(item)">编辑</el-button>
            <el-button size="small" link type="danger" @click="deleteItem(item.id)">删除</el-button>
          </div>
        </div>
        <div class="item-content">{{ item.content }}</div>
        <div class="item-meta">
          <span>添加于 {{ new Date(item.created_at).toLocaleDateString('zh-CN') }}</span>
          <span v-if="item.tags" class="item-tags">
            <el-tag v-for="tag in item.tags.split(',')" :key="tag" size="small" effect="plain" style="margin-left: 4px;">
              {{ tag.trim() }}
            </el-tag>
          </span>
        </div>
      </div>
    </div>

    <!-- Add/Edit Dialog -->
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

    <!-- Upload Dialog -->
    <el-dialog v-model="uploadDialogVisible" title="上传文档提取知识" width="560px">
      <el-form label-position="top">
        <el-form-item label="适用专家">
          <el-select v-model="uploadAgentType" style="width:100%">
            <el-option v-for="a in agents" :key="a.type" :label="`${a.icon} ${a.name}`" :value="a.type" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :on-exceed="() => ElMessage.warning('只能上传一个文件')"
            accept=".pdf,.docx,.txt,.md,.zip"
          >
            <div class="upload-area">
              <el-icon class="el-icon--upload" :size="40"><Upload /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <div class="el-upload__tip">支持 PDF、DOCX、TXT、MD、ZIP 格式</div>
            </div>
          </el-upload>
        </el-form-item>
      </el-form>

      <!-- Upload progress/result -->
      <div v-if="uploading" class="upload-progress">
        <el-progress :percentage="100" status="warning" :indeterminate="true" />
        <p style="text-align:center;color:#999;margin-top:8px;">AI 正在提取知识，请稍候...</p>
      </div>
      <div v-if="uploadResult" class="upload-result">
        <el-alert
          :title="uploadResult.success ? `成功提取 ${uploadResult.entries_created} 条知识` : '提取失败'"
          :type="uploadResult.success ? 'success' : 'error'"
          :description="uploadResult.error || ''"
          show-icon :closable="false"
        />
      </div>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="doUpload">
          开始提取
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Upload, Download } from '@element-plus/icons-vue'
import { adminAPI } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeAgent = ref('strategy')
const items = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editId = ref(null)
const saving = ref(false)
const stats = ref(null)

// Upload state
const uploadDialogVisible = ref(false)
const uploadAgentType = ref('strategy')
const uploadRef = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadResult = ref(null)
const importingSeeds = ref(false)

const agents = [
  { type: 'strategy', name: '战略规划专家', icon: '🎯' },
  { type: 'brand', name: '品牌设计专家', icon: '🎨' },
  { type: 'operations', name: '运营实施专家', icon: '🚀' },
]

const form = ref({ agent_type: 'strategy', title: '', content: '' })

const knowledgeTypeMap = {
  framework: '框架',
  case_study: '案例',
  market_data: '市场数据',
  methodology: '方法论',
  industry_report: '行业报告',
  general: '通用',
}

function knowledgeTypeLabel(type) {
  return knowledgeTypeMap[type] || type || '通用'
}

function knowledgeTypeTagType(type) {
  const map = {
    framework: '',
    case_study: 'success',
    market_data: 'warning',
    methodology: 'info',
    industry_report: 'danger',
    general: 'info',
  }
  return map[type] || 'info'
}

function sourceLabel(source) {
  const map = { seed: '种子', upload: '上传', crawl: '爬取', manual: '手动' }
  return map[source] || source || ''
}

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
    await loadStats()
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
  await loadStats()
}

async function loadKnowledge() {
  loading.value = true
  try { items.value = await adminAPI.getKnowledge(activeAgent.value) }
  finally { loading.value = false }
}

async function loadStats() {
  try { stats.value = await adminAPI.getKnowledgeStats() }
  catch (e) { console.warn('Failed to load stats', e) }
}

// Upload handlers
function onFileChange(uploadFile) {
  selectedFile.value = uploadFile?.raw || null
  uploadResult.value = null
}

async function doUpload() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadResult.value = null
  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)
    const result = await adminAPI.uploadKnowledge(fd, uploadAgentType.value)
    uploadResult.value = result
    if (result.success && result.entries_created > 0) {
      ElMessage.success(`成功提取 ${result.entries_created} 条知识`)
      await loadKnowledge()
      await loadStats()
    }
  } catch (e) {
    uploadResult.value = { success: false, entries_created: 0, error: e.message }
    ElMessage.error(e.message)
  } finally {
    uploading.value = false
  }
}

async function confirmImportSeed() {
  try {
    await ElMessageBox.confirm(
      '将导入预置的种子知识库（包含战略、品牌、运营相关方法论和框架），如已导入过则跳过。确认导入？',
      '导入种子知识库',
      { type: 'info', confirmButtonText: '确认导入', cancelButtonText: '取消' }
    )
  } catch { return }

  importingSeeds.value = true
  try {
    const result = await adminAPI.importSeedKnowledge()
    ElMessage.success(result.message || `导入完成，共 ${result.entries_created} 条`)
    await loadKnowledge()
    await loadStats()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    importingSeeds.value = false
  }
}

onMounted(() => {
  loadKnowledge()
  loadStats()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 20px; color: #1a1a2e; }
.header-actions { display: flex; gap: 8px; }

.stats-overview {
  display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;
}
.stat-card {
  background: #fff; border-radius: 10px; padding: 16px 20px; min-width: 120px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05); text-align: center; flex: 1;
}
.stat-number { font-size: 24px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 12px; color: #999; margin-top: 4px; }

.knowledge-list { margin-top: 16px; display: flex; flex-direction: column; gap: 12px; }
.empty-state { text-align: center; padding: 60px; color: #aaa; background: #fff; border-radius: 8px; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.knowledge-item { background: #fff; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
.item-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.item-title-row { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.item-title { font-size: 15px; font-weight: 600; color: #222; }
.item-content { font-size: 13px; color: #555; line-height: 1.7; white-space: pre-wrap;
  max-height: 80px; overflow: hidden; text-overflow: ellipsis; }
.item-meta { font-size: 11px; color: #aaa; margin-top: 8px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.item-tags { display: inline-flex; flex-wrap: wrap; gap: 2px; }

.upload-area { padding: 20px 0; text-align: center; }
.upload-progress { margin-top: 16px; }
.upload-result { margin-top: 16px; }
</style>
