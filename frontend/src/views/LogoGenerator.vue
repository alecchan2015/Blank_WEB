<template>
  <div class="logo-generator">
    <!-- Page Header -->
    <div class="page-header">
      <el-button text @click="$router.push('/dashboard')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <div class="header-info">
        <h2>Logo 智能生成</h2>
      </div>
    </div>

    <!-- Form Section -->
    <el-card v-if="!generationId || generationError" class="form-card" shadow="never">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleGenerate"
      >
        <!-- Brand Name -->
        <el-form-item label="品牌名称" prop="brandName">
          <el-input
            v-model="form.brandName"
            placeholder="请输入品牌名称"
            maxlength="40"
            show-word-limit
            clearable
          />
        </el-form-item>

        <!-- Industry -->
        <el-form-item label="所属行业" prop="industry">
          <el-select v-model="form.industry" placeholder="请选择行业" style="width: 100%">
            <el-option
              v-for="item in industries"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <!-- Style Picker -->
        <el-form-item label="设计风格" prop="style">
          <div class="style-grid">
            <div
              v-for="s in styles"
              :key="s.value"
              class="style-card"
              :class="{ selected: form.style === s.value }"
              @click="form.style = s.value"
            >
              <span class="style-icon">{{ s.icon }}</span>
              <span class="style-label">{{ s.label }}</span>
            </div>
          </div>
        </el-form-item>

        <!-- Colors -->
        <div class="color-row">
          <el-form-item label="主色调" class="color-item">
            <el-color-picker v-model="form.primaryColor" show-alpha />
          </el-form-item>
          <el-form-item label="辅助色（可选）" class="color-item">
            <el-color-picker v-model="form.secondaryColor" show-alpha />
          </el-form-item>
        </div>

        <!-- Include Text Toggle -->
        <el-form-item label="包含品牌名文字">
          <el-switch
            v-model="form.includeText"
            active-text="是"
            inactive-text="否"
          />
          <span class="form-hint">是否在 Logo 中包含品牌名文字</span>
        </el-form-item>

        <!-- Variant Count -->
        <el-form-item label="生成方案数量">
          <el-slider
            v-model="form.variantCount"
            :min="1"
            :max="4"
            :step="1"
            show-stops
            :marks="variantMarks"
            style="padding: 0 10px;"
          />
        </el-form-item>

        <!-- Credit Cost -->
        <div class="credit-info">
          <el-icon><Coin /></el-icon>
          <span>本次生成消耗 <strong>{{ creditCost }}</strong> 积分，当前余额: <strong>{{ userCredits }}</strong></span>
          <el-tag v-if="userCredits < creditCost" type="danger" size="small">余额不足</el-tag>
        </div>

        <!-- Generate Button -->
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="generating"
            :disabled="userCredits < creditCost"
            style="width: 100%; margin-top: 8px;"
            @click="handleGenerate"
          >
            <el-icon v-if="!generating"><MagicStick /></el-icon>
            {{ generating ? '生成中...' : '开始生成 Logo' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Progress Section -->
    <el-card v-if="generationId && !generationDone && !generationError" class="progress-card" shadow="never">
      <div class="progress-header">
        <el-icon class="spin"><Loading /></el-icon>
        <span>正在生成 Logo，请耐心等待...</span>
      </div>
      <el-progress
        :percentage="progress.percent"
        :stroke-width="10"
        striped
        striped-flow
        :duration="20"
        style="margin: 20px 0;"
      />
      <div class="progress-steps">
        <div
          v-for="(step, idx) in progressSteps"
          :key="idx"
          class="progress-step"
          :class="{
            active: progress.percent >= step.at && progress.percent < (progressSteps[idx + 1]?.at || 101),
            done: progress.percent >= (progressSteps[idx + 1]?.at || 101)
          }"
        >
          <span class="step-dot" />
          <span class="step-label">{{ step.label }}</span>
        </div>
      </div>
    </el-card>

    <!-- Error Alert -->
    <el-alert
      v-if="generationError"
      :title="generationError"
      type="error"
      show-icon
      closable
      style="margin-bottom: 16px;"
      @close="generationError = ''"
    />

    <!-- Result Section -->
    <el-card v-if="generationDone && variants.length" class="result-card" shadow="never">
      <div class="result-header">
        <h3>生成结果</h3>
        <div class="bg-toggle">
          <span class="bg-label">背景预览:</span>
          <el-radio-group v-model="previewBg" size="small">
            <el-radio-button value="transparent">透明</el-radio-button>
            <el-radio-button value="white">白色</el-radio-button>
            <el-radio-button value="black">黑色</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- Variant Grid -->
      <div class="variant-grid">
        <div
          v-for="(variant, idx) in variants"
          :key="idx"
          class="variant-item"
          :class="{ selected: selectedVariant === idx }"
          @click="selectedVariant = idx"
        >
          <div
            class="variant-preview"
            :class="`bg-${previewBg}`"
          >
            <img :src="variant.png_url || variant.thumbnail" :alt="`方案 ${idx + 1}`" />
          </div>
          <div class="variant-label">方案 {{ idx + 1 }}</div>
        </div>
      </div>

      <!-- Download Buttons -->
      <div class="download-section">
        <el-button
          type="primary"
          :icon="Download"
          @click="handleDownload('png')"
          :loading="downloading === 'png'"
        >
          下载 PNG（透明背景）
        </el-button>
        <el-button
          type="success"
          :icon="Download"
          @click="handleDownload('psd')"
          :loading="downloading === 'psd'"
        >
          下载 PSD（分层文件）
        </el-button>
        <el-button
          type="warning"
          :icon="Download"
          @click="handleDownload('zip')"
          :loading="downloading === 'zip'"
        >
          下载品牌包 ZIP（全格式）
        </el-button>
      </div>

      <!-- Regenerate -->
      <div class="regenerate-section">
        <el-button :icon="Refresh" round @click="handleReset">重新生成</el-button>
      </div>
    </el-card>

    <!-- History Section -->
    <el-card class="history-card" shadow="never">
      <template #header>
        <div class="history-header">
          <span class="history-title">📋 生成历史</span>
          <el-button size="small" text @click="loadHistory">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>
      <div v-if="historyLoading" v-loading="true" style="min-height:60px" />
      <el-empty v-else-if="!history.length" description="暂无生成记录" :image-size="60" />
      <div v-else class="history-list">
        <div
          v-for="item in history"
          :key="item.id"
          class="history-item"
          @click="viewHistoryItem(item)"
        >
          <div class="history-preview">
            <img
              v-if="item.variants?.length && item.variants[0].png_url"
              :src="item.variants[0].png_url"
              :alt="item.brand_name"
            />
            <div v-else class="history-placeholder">
              <span>{{ item.status === 'processing' ? '⏳' : '❌' }}</span>
            </div>
          </div>
          <div class="history-info">
            <div class="history-brand">{{ item.brand_name }}</div>
            <div class="history-meta">
              <el-tag :type="item.status === 'done' ? 'success' : item.status === 'failed' ? 'danger' : 'warning'" size="small">
                {{ item.status === 'done' ? '完成' : item.status === 'failed' ? '失败' : '生成中' }}
              </el-tag>
              <span class="history-style">{{ styleLabel(item.style) }}</span>
              <span class="history-time">{{ formatTime(item.created_at) }}</span>
            </div>
          </div>
          <div class="history-actions" v-if="item.status === 'done'">
            <el-button size="small" type="primary" text @click.stop="downloadHistory(item, 'png')">PNG</el-button>
            <el-button size="small" type="success" text @click.stop="downloadHistory(item, 'psd')">PSD</el-button>
            <el-button size="small" type="warning" text @click.stop="downloadHistory(item, 'zip')">ZIP</el-button>
          </div>
        </div>
      </div>
      <div v-if="historyTotal > history.length" class="history-more">
        <el-button text @click="loadMoreHistory">加载更多</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import { useUserStore } from '../store'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Loading,
  MagicStick,
  Coin,
  Download,
  Refresh,
} from '@element-plus/icons-vue'
import api, { logoAPI } from '../api'

// ── Store ────────────────────────────────────────────
const store = useUserStore()
const userCredits = computed(() => store.user?.credits ?? 0)

// ── Form ─────────────────────────────────────────────
const formRef = ref(null)

const form = reactive({
  brandName: '',
  industry: '',
  style: '',
  primaryColor: '#409EFF',
  secondaryColor: '',
  includeText: true,
  variantCount: 3,
})

const rules = {
  brandName: [
    { required: true, message: '请输入品牌名称', trigger: 'blur' },
    { max: 40, message: '品牌名称不超过40个字符', trigger: 'blur' },
  ],
  industry: [
    { required: true, message: '请选择行业', trigger: 'change' },
  ],
  style: [
    { required: true, message: '请选择设计风格', trigger: 'change' },
  ],
}

const industries = [
  { label: '美妆护肤', value: '美妆护肤' },
  { label: '家居家具', value: '家居家具' },
  { label: '科技智能', value: '科技智能' },
  { label: '食品饮料', value: '食品饮料' },
  { label: '服装时尚', value: '服装时尚' },
  { label: '教育培训', value: '教育培训' },
  { label: '医疗健康', value: '医疗健康' },
  { label: '其他', value: '其他' },
]

const styles = [
  { label: '现代简约', value: 'modern', icon: '\uD83D\uDD32' },
  { label: '极简主义', value: 'minimal', icon: '\u2B1C' },
  { label: '奢华高端', value: 'luxury', icon: '\uD83D\uDC8E' },
  { label: '科技未来', value: 'tech', icon: '\uD83D\uDD2E' },
  { label: '自然生态', value: 'natural', icon: '\uD83C\uDF3F' },
  { label: '活泼趣味', value: 'playful', icon: '\uD83C\uDF88' },
]

const variantMarks = { 1: '1', 2: '2', 3: '3', 4: '4' }

const creditCost = computed(() => 3)  // Fixed cost per generation

// ── Generation State ─────────────────────────────────
const generating = ref(false)
const generationId = ref('')
const generationDone = ref(false)
const generationError = ref('')
const variants = ref([])
const selectedVariant = ref(0)
const previewBg = ref('transparent')
const downloading = ref('')

const progress = reactive({ percent: 0, label: '' })
let eventSource = null

const progressSteps = [
  { label: '优化提示词', at: 10 },
  { label: '生成 Logo', at: 50 },
  { label: '去除背景', at: 70 },
  { label: '构建 PSD', at: 85 },
  { label: '打包品牌包', at: 95 },
  { label: '完成', at: 100 },
]

// ── Actions ──────────────────────────────────────────
async function handleGenerate() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (userCredits.value < creditCost.value) {
    ElMessage.warning('积分余额不足，请充值后再试')
    return
  }

  generating.value = true
  generationDone.value = false
  generationError.value = ''
  variants.value = []
  progress.percent = 0

  try {
    const res = await logoAPI.generate({
      brand_name: form.brandName,
      industry: form.industry,
      style: form.style,
      primary_color: form.primaryColor,
      secondary_color: form.secondaryColor || null,
      include_text: form.includeText,
      variant_count: form.variantCount,
    })

    generationId.value = res.generation_id
    startProgressPolling(res.generation_id)
  } catch (e) {
    generationError.value = e.message || '生成请求失败'
    ElMessage.error(generationError.value)
  } finally {
    generating.value = false
  }
}

function startProgressPolling(id) {
  closeEventSource()
  const token = localStorage.getItem('token')
  eventSource = new EventSource(logoAPI.progressUrl(id, token))

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)

      if (data.type === 'progress') {
        progress.percent = data.percent ?? progress.percent
        progress.label = data.label ?? ''
      } else if (data.type === 'done') {
        progress.percent = 100
        generationDone.value = true
        variants.value = data.variants || []
        selectedVariant.value = 0
        closeEventSource()
        store.fetchMe()
        loadHistory()
        ElMessage.success('Logo 生成完成')
      } else if (data.type === 'error') {
        generationError.value = data.message || '生成过程出错'
        closeEventSource()
        ElMessage.error(generationError.value)
      }
    } catch {
      // ignore malformed messages
    }
  }

  eventSource.onerror = () => {
    closeEventSource()
    if (!generationDone.value && !generationError.value) {
      generationError.value = '连接中断，请刷新页面重试'
    }
  }
}

function closeEventSource() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

function handleDownload(format) {
  if (downloading.value) return
  const variant = variants.value[selectedVariant.value]
  if (!variant) return

  const ext = format === 'zip' ? 'zip' : format
  const a = document.createElement('a')
  a.href = logoAPI.downloadUrl(generationId.value, format)
  a.download = `${form.brandName}_logo_${selectedVariant.value + 1}.${ext}`
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  ElMessage.success('已开始下载')
}

function handleReset() {
  generationId.value = ''
  generationDone.value = false
  generationError.value = ''
  variants.value = []
  progress.percent = 0
  selectedVariant.value = 0
}

// ── History ─────────────────────────────────────────
const history = ref([])
const historyTotal = ref(0)
const historyLoading = ref(false)
const historyPage = ref(1)

async function loadHistory() {
  historyLoading.value = true
  historyPage.value = 1
  try {
    const res = await api.get('/logo/history', { params: { page: 1, page_size: 10 } })
    history.value = res.items || []
    historyTotal.value = res.total || 0
  } catch { /* ignore */ }
  finally { historyLoading.value = false }
}

async function loadMoreHistory() {
  historyPage.value++
  try {
    const res = await api.get('/logo/history', { params: { page: historyPage.value, page_size: 10 } })
    history.value.push(...(res.items || []))
  } catch { /* ignore */ }
}

function viewHistoryItem(item) {
  if (item.status === 'done' && item.variants?.length) {
    generationId.value = item.id
    generationDone.value = true
    variants.value = item.variants
    selectedVariant.value = 0
    generationError.value = ''
    progress.percent = 100
  } else if (item.status === 'processing') {
    generationId.value = item.id
    generationDone.value = false
    startProgressPolling(item.id)
  }
}

function downloadHistory(item, format) {
  const a = document.createElement('a')
  a.href = logoAPI.downloadUrl(item.id, format)
  a.download = `${item.brand_name}_logo.${format === 'zip' ? 'zip' : format}`
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function styleLabel(val) {
  const map = { modern: '现代简约', minimal: '极简主义', luxury: '奢华高端', tech: '科技未来', natural: '自然生态', playful: '活泼趣味' }
  return map[val] || val || ''
}

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// ── Lifecycle ────────────────────────────────────────
onMounted(() => {
  store.fetchMe()
  loadHistory()
})

onUnmounted(() => {
  closeEventSource()
})
</script>

<style scoped>
.logo-generator {
  max-width: 900px;
  margin: 0 auto;
  color: var(--ybc-text);
}

/* ── Page Header ─────────────────────────────── */
.page-header {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 20px;
}
.page-header :deep(.el-button) {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--ybc-border);
  border-radius: 8px;
  color: var(--ybc-text-dim);
  font-size: 13px;
}
.page-header :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.04);
  color: var(--ybc-text);
}
.header-info { flex: 1; }
.header-info h2 {
  font-size: 22px; font-weight: 800;
  color: var(--ybc-text-strong);
  letter-spacing: -0.3px;
  margin: 0;
}

/* ── Form Card ──────────────────────────────── */
.form-card,
.progress-card,
.result-card,
.history-card {
  background: var(--ybc-surface-1) !important;
  border: 1px solid var(--ybc-border) !important;
  border-radius: 16px !important;
  margin-bottom: 18px;
  box-shadow: var(--ybc-shadow-sm) !important;
}
.form-card :deep(.el-card__body),
.progress-card :deep(.el-card__body),
.result-card :deep(.el-card__body) {
  padding: 24px;
}
.form-card :deep(.el-form-item__label) {
  color: var(--ybc-text) !important;
  font-weight: 600;
  font-size: 13px;
  padding-bottom: 6px;
}

/* ── Style grid ─────────────────────────────── */
.style-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: 100%;
}
.style-card {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 16px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--ybc-border);
  border-radius: 12px;
  cursor: pointer;
  transition: 0.15s;
  user-select: none;
}
.style-card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.04);
}
.style-card.selected {
  border-color: var(--ybc-accent);
  background: rgba(99, 102, 241, 0.1);
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2);
}
.style-icon { font-size: 24px; }
.style-label {
  font-size: 12px; font-weight: 600;
  color: var(--ybc-text);
}

/* ── Colors + hint ──────────────────────────── */
.color-row { display: flex; gap: 24px; }
.color-item { flex: 1; }
.form-hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--ybc-text-muted);
}

/* ── Credit info ────────────────────────────── */
.credit-info {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px;
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 10px;
  color: #fcd34d;
  font-size: 13px;
  margin: 8px 0 16px;
}
.credit-info strong { color: #fde68a; }

/* ── Progress ───────────────────────────────── */
.progress-header {
  display: flex; align-items: center; gap: 10px;
  font-size: 15px; font-weight: 600;
  color: var(--ybc-text-strong);
}
.progress-header :deep(.el-icon) { color: var(--ybc-accent-light); }

.progress-steps {
  display: flex; justify-content: space-between;
  margin-top: 20px;
  gap: 8px;
}
.progress-step {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  flex: 1;
  opacity: 0.5;
  transition: 0.3s;
}
.progress-step.active { opacity: 1; }
.progress-step.done { opacity: 0.9; }
.step-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  transition: 0.3s;
}
.progress-step.active .step-dot {
  background: var(--ybc-accent);
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.6);
  animation: ybc-pulse-dot 1.2s infinite;
}
.progress-step.done .step-dot { background: var(--ybc-success); }
.step-label {
  font-size: 11px;
  color: var(--ybc-text-dim);
  text-align: center;
}

/* ── Result Section ─────────────────────────── */
.result-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--ybc-border);
}
.result-header h3 {
  font-size: 18px; font-weight: 700;
  color: var(--ybc-text-strong);
  margin: 0;
}
.bg-toggle {
  display: flex; align-items: center; gap: 10px;
}
.bg-label {
  font-size: 12px;
  color: var(--ybc-text-muted);
}

.variant-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}
.variant-item {
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid var(--ybc-border);
  transition: 0.2s;
  background: rgba(255, 255, 255, 0.03);
}
.variant-item:hover {
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-2px);
}
.variant-item.selected {
  border-color: var(--ybc-accent);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
}
.variant-preview {
  aspect-ratio: 1 / 1;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
  background-image:
    linear-gradient(45deg, rgba(255,255,255,0.04) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(255,255,255,0.04) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.04) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.04) 75%);
  background-size: 16px 16px;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
}
.variant-preview.bg-white { background: #fff; }
.variant-preview.bg-black { background: #0a0a0f; }
.variant-preview img {
  max-width: 100%; max-height: 100%;
  object-fit: contain;
}
.variant-label {
  padding: 8px;
  text-align: center;
  font-size: 12px;
  color: var(--ybc-text-dim);
  background: var(--ybc-surface-2);
  font-weight: 500;
}

/* ── Download buttons ───────────────────────── */
.download-section {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding-top: 16px;
  border-top: 1px solid var(--ybc-border);
}
.download-section :deep(.el-button) {
  flex: 1;
  min-width: 180px;
  padding: 10px 14px;
  font-weight: 500;
}

.regenerate-section {
  margin-top: 14px;
  display: flex;
  justify-content: center;
}

/* ── History ────────────────────────────────── */
.history-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 0;
}
.history-title {
  font-size: 15px; font-weight: 700;
  color: var(--ybc-text-strong);
}
.history-card :deep(.el-card__header) {
  border-bottom: 1px solid var(--ybc-border);
  padding: 14px 18px;
}
.history-card :deep(.el-card__body) { padding: 14px 18px; }

.history-list {
  display: flex; flex-direction: column; gap: 8px;
}
.history-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--ybc-border);
  border-radius: 12px;
  cursor: pointer;
  transition: 0.15s;
}
.history-item:hover {
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.04);
}
.history-preview {
  width: 56px; height: 56px;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.history-preview img {
  width: 100%; height: 100%;
  object-fit: contain;
  padding: 4px;
}
.history-placeholder {
  font-size: 24px;
  color: var(--ybc-text-muted);
}
.history-info {
  flex: 1;
  min-width: 0;
}
.history-brand {
  font-size: 14px; font-weight: 600;
  color: var(--ybc-text-strong);
  margin-bottom: 4px;
}
.history-meta {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px;
  color: var(--ybc-text-muted);
  flex-wrap: wrap;
}
.history-style {
  padding: 1px 8px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 100px;
  color: var(--ybc-text-dim);
}
.history-time { color: var(--ybc-text-faint); }
.history-actions {
  display: flex; gap: 2px;
  flex-shrink: 0;
}

.history-more {
  text-align: center;
  margin-top: 12px;
}

/* ── Spinner ───────────────────────────────── */
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

/* ── Responsive ─────────────────────────────── */
@media (max-width: 640px) {
  .form-card :deep(.el-card__body) { padding: 18px; }
  .style-grid { grid-template-columns: repeat(2, 1fr); }
  .color-row { flex-direction: column; gap: 10px; }
  .result-header { flex-direction: column; align-items: flex-start; gap: 12px; }
  .download-section :deep(.el-button) { min-width: 100%; }
}
</style>
