<template>
  <div class="credits-config" v-loading="loading">
    <div class="page-header">
      <h2 class="page-title">积分消耗配置</h2>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <el-alert type="info" show-icon :closable="false" style="margin-bottom:16px">
      配置各类任务产物的积分消耗。修改后立即生效，<b>仅影响新生成的结果</b>；历史结果的积分扣费金额已经写入数据库，不会被追溯修改。
    </el-alert>

    <div class="section-card">
      <h3>任务下载消耗（按文件类型）</h3>
      <p class="section-desc">用户下载某个文件类型时扣除的积分。设置为 0 表示免费。</p>

      <div class="grid">
        <div v-for="field in taskFields" :key="field.key" class="field-row">
          <div class="field-label">
            <span class="emoji">{{ field.emoji }}</span>
            <div>
              <div class="name">{{ field.label }}</div>
              <div class="hint">{{ field.hint }}</div>
            </div>
          </div>
          <el-input-number
            v-model="cfg.download_credits[field.key]"
            :min="0" :max="999999" :step="5"
            style="width:140px"
          />
          <span class="unit">积分</span>
        </div>
      </div>
    </div>

    <div class="section-card">
      <h3>Logo 下载消耗</h3>
      <p class="section-desc">独立的 Logo 生成器产物的下载价格。</p>
      <div class="grid">
        <div v-for="field in logoDownloadFields" :key="field.key" class="field-row">
          <div class="field-label">
            <span class="emoji">{{ field.emoji }}</span>
            <div>
              <div class="name">{{ field.label }}</div>
              <div class="hint">{{ field.hint }}</div>
            </div>
          </div>
          <el-input-number
            v-model="cfg.download_credits[field.key]"
            :min="0" :max="999999" :step="1"
            style="width:140px"
          />
          <span class="unit">积分</span>
        </div>
      </div>
    </div>

    <div class="section-card">
      <h3>生成任务消耗</h3>
      <p class="section-desc">用户触发生成任务时立即扣费（未来可扩展按 agent 差异定价）。</p>
      <div class="grid">
        <div class="field-row">
          <div class="field-label">
            <span class="emoji">🎨</span>
            <div>
              <div class="name">Logo AI 生成</div>
              <div class="hint">每次调用 Logo 生成器立即扣除</div>
            </div>
          </div>
          <el-input-number
            v-model="cfg.logo_generation.per_generation"
            :min="0" :max="999999" :step="1"
            style="width:140px"
          />
          <span class="unit">积分</span>
        </div>
        <div class="field-row">
          <div class="field-label">
            <span class="emoji">🤖</span>
            <div>
              <div class="name">单 agent 任务（预留）</div>
              <div class="hint">每个专家运行的成本；当前为 0，后续可启用</div>
            </div>
          </div>
          <el-input-number
            v-model="cfg.task_generation.per_agent"
            :min="0" :max="999999" :step="1"
            style="width:140px"
          />
          <span class="unit">积分</span>
        </div>
      </div>
    </div>

    <div class="action-bar">
      <el-button @click="reset" :loading="saving">恢复默认</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI } from '../../api'

const loading = ref(false)
const saving = ref(false)

const cfg = reactive({
  download_credits: {
    md: 0, pdf: 10, pptx: 30, png: 5, psd: 20, zip: 15,
    logo_png: 3, logo_psd: 10, logo_zip: 15,
  },
  task_generation: { per_agent: 0 },
  logo_generation: { per_generation: 3 },
})

const taskFields = [
  { key: 'md',   emoji: '📝', label: 'Markdown 文本',  hint: '战略/品牌/运营的纯文本报告（一般免费）' },
  { key: 'pdf',  emoji: '📄', label: 'PDF 报告',        hint: '排版规整的 PDF 文件' },
  { key: 'pptx', emoji: '📊', label: 'PowerPoint 演示', hint: 'AI 生成的 PPT 幻灯片（Gamma / 本地）' },
  { key: 'png',  emoji: '🖼️', label: '品牌 VI 图',      hint: '品牌设计的视觉物料 PNG' },
  { key: 'psd',  emoji: '🎨', label: '品牌 PSD 源文件', hint: 'Photoshop 分层 PSD' },
  { key: 'zip',  emoji: '📦', label: 'ZIP 压缩包',      hint: '打包下载的综合材料' },
]

const logoDownloadFields = [
  { key: 'logo_png', emoji: '🖼️', label: 'Logo PNG',    hint: '标准分辨率 Logo' },
  { key: 'logo_psd', emoji: '🎨', label: 'Logo PSD',    hint: '可编辑分层源文件' },
  { key: 'logo_zip', emoji: '📦', label: '品牌 Logo 套件', hint: '多格式打包（PNG + SVG + PSD）' },
]

async function load() {
  loading.value = true
  try {
    const res = await adminAPI.getCreditsConfig()
    // Deep merge to preserve defaults when keys missing
    cfg.download_credits = { ...cfg.download_credits, ...(res.download_credits || {}) }
    cfg.task_generation = { ...cfg.task_generation, ...(res.task_generation || {}) }
    cfg.logo_generation = { ...cfg.logo_generation, ...(res.logo_generation || {}) }
  } catch (e) {
    ElMessage.error('加载失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await adminAPI.saveCreditsConfig({
      download_credits: cfg.download_credits,
      task_generation:  cfg.task_generation,
      logo_generation:  cfg.logo_generation,
    })
    ElMessage.success('积分配置已保存')
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function reset() {
  try {
    await ElMessageBox.confirm(
      '恢复为系统默认值？（md=0, pdf=10, pptx=30, png=5, psd=20, zip=15, logo_png=3, logo_psd=10, logo_zip=15）',
      '确认恢复',
      { type: 'warning' }
    )
    Object.assign(cfg.download_credits, {
      md: 0, pdf: 10, pptx: 30, png: 5, psd: 20, zip: 15,
      logo_png: 3, logo_psd: 10, logo_zip: 15,
    })
    cfg.task_generation.per_agent = 0
    cfg.logo_generation.per_generation = 3
    await save()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<style scoped>
.credits-config { max-width: 880px; }
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 20px; color: #1a1a2e; margin: 0; }

.section-card {
  background: #fff; border-radius: 12px;
  padding: 20px 24px; margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.section-card h3 { margin: 0 0 6px; font-size: 15px; color: #1a1a2e; font-weight: 600; }
.section-desc { margin: 0 0 16px; font-size: 13px; color: #888; }

.grid { display: flex; flex-direction: column; gap: 10px; }
.field-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: border-color 0.2s;
}
.field-row:hover { border-color: #e4e7ed; }
.field-label {
  flex: 1;
  display: flex; align-items: center; gap: 10px;
}
.field-label .emoji { font-size: 22px; width: 28px; text-align: center; }
.field-label .name { font-size: 14px; font-weight: 600; color: #333; }
.field-label .hint { font-size: 12px; color: #888; margin-top: 2px; }
.unit { font-size: 13px; color: #666; }

.action-bar {
  display: flex; justify-content: flex-end; gap: 8px;
  padding-top: 16px;
}
</style>
