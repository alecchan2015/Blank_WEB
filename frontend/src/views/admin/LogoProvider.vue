<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">Logo 生成器配置</h2>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-alert type="info" show-icon :closable="false" style="margin-bottom:16px">
      <template #default>
        选择 Logo 生成的主力服务商与回退服务商。当主力失败时自动降级到备选服务商，保证生成不中断。<br>
        <b>OpenAI (DALL-E 3 / GPT Image)</b> 综合质量最佳；<b>Ideogram V3</b> 擅长文字排版；<b>Recraft V4 SVG</b> 可输出矢量格式。
      </template>
    </el-alert>

    <!-- Provider status cards -->
    <div class="provider-grid" v-loading="loading">
      <el-card
        v-for="p in providers"
        :key="p.name"
        class="provider-card"
        :class="{ active: p.role === 'primary', fallback: p.role === 'fallback' }"
        shadow="hover"
      >
        <div class="pc-header">
          <span class="pc-icon">{{ iconOf(p.name) }}</span>
          <div class="pc-title">
            <div class="pc-label">{{ p.label }}</div>
            <div class="pc-name">{{ p.name }}</div>
          </div>
          <el-tag
            v-if="p.role === 'primary'"
            type="success" effect="dark" size="small"
          >主力</el-tag>
          <el-tag
            v-else-if="p.role === 'fallback'"
            type="warning" size="small"
          >备选</el-tag>
        </div>
        <div class="pc-status">
          <el-tag
            :type="p.available ? 'success' : 'info'"
            effect="light" size="small"
          >{{ p.available ? '已配置' : '未配置' }}</el-tag>
        </div>
        <div class="pc-actions">
          <el-button
            size="small"
            type="primary"
            :disabled="form.provider === p.name"
            @click="setRole(p.name, 'provider')"
          >设为主力</el-button>
          <el-button
            size="small"
            :disabled="form.fallback === p.name || form.provider === p.name"
            @click="setRole(p.name, 'fallback')"
          >设为备选</el-button>
          <el-button
            size="small"
            :loading="testing[p.name]"
            @click="runTest(p.name)"
          >连通测试</el-button>
        </div>
      </el-card>
    </div>

    <!-- Detail form -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <span class="card-title">参数配置</span>
      </template>

      <el-form :model="form" label-width="160px" label-position="left">
        <el-form-item label="主力服务商">
          <el-select v-model="form.provider" style="width:320px">
            <el-option label="OpenAI (DALL-E 3 / GPT Image)" value="openai" />
            <el-option label="Ideogram V3" value="ideogram" />
            <el-option label="Recraft V4 SVG" value="recraft" />
          </el-select>
        </el-form-item>
        <el-form-item label="回退服务商">
          <el-select v-model="form.fallback" style="width:320px">
            <el-option label="OpenAI (DALL-E 3 / GPT Image)" value="openai" />
            <el-option label="Ideogram V3" value="ideogram" />
            <el-option label="Recraft V4 SVG" value="recraft" />
          </el-select>
          <div class="hint">主力失败时自动使用备选服务商</div>
        </el-form-item>

        <el-divider content-position="left">OpenAI</el-divider>
        <el-form-item label="OpenAI API Key">
          <el-input
            v-model="form.openai_api_key"
            type="password" show-password
            :placeholder="form.openai_api_key_set ? '已保存，留空则不修改' : 'sk-...'"
            style="width:420px"
          />
          <div class="hint">用于 DALL-E 3 / GPT Image 图像生成</div>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input
            v-model="form.openai_model"
            placeholder="dall-e-3"
            style="width:420px"
          />
          <div class="hint">例如 dall-e-3、gpt-image-1 等</div>
        </el-form-item>

        <el-divider content-position="left">Ideogram</el-divider>
        <el-form-item label="Ideogram API Key">
          <el-input
            v-model="form.ideogram_api_key"
            type="password" show-password
            :placeholder="form.ideogram_api_key_set ? '已保存，留空则不修改' : 'api-...'"
            style="width:420px"
          />
          <div class="hint">从 Ideogram 开发者平台获取</div>
        </el-form-item>
        <el-form-item label="Ideogram 模型">
          <el-input
            v-model="form.ideogram_model"
            placeholder="V_3"
            style="width:420px"
          />
          <div class="hint">例如 V_3、V_2_TURBO 等</div>
        </el-form-item>

        <el-divider content-position="left">Recraft</el-divider>
        <el-form-item label="Recraft API Key">
          <el-input
            v-model="form.recraft_api_key"
            type="password" show-password
            :placeholder="form.recraft_api_key_set ? '已保存，留空则不修改' : 'fal-...'"
            style="width:420px"
          />
          <div class="hint">fal.ai API Key，用于 Recraft V4 矢量生成</div>
        </el-form-item>
        <el-form-item label="Recraft 模型">
          <el-input
            v-model="form.recraft_model"
            placeholder="fal-ai/recraft/v4/text-to-vector"
            style="width:420px"
          />
          <div class="hint">fal.ai 上的模型路径</div>
        </el-form-item>

        <el-divider content-position="left">通用设置</el-divider>
        <el-form-item label="Logo 风格">
          <el-select v-model="form.style" style="width:320px">
            <el-option label="现代 (modern)" value="modern" />
            <el-option label="极简 (minimal)" value="minimal" />
            <el-option label="奢华 (luxury)" value="luxury" />
            <el-option label="科技 (tech)" value="tech" />
            <el-option label="自然 (natural)" value="natural" />
            <el-option label="活泼 (playful)" value="playful" />
          </el-select>
        </el-form-item>
        <el-form-item label="包含文字">
          <el-switch v-model="form.include_text" />
          <div class="hint">生成的 Logo 中是否包含品牌名称文字</div>
        </el-form-item>
        <el-form-item label="生成变体数量">
          <el-input-number v-model="form.variant_count" :min="1" :max="4" />
          <div class="hint">每次生成的 Logo 变体数，1 ~ 4</div>
        </el-form-item>
        <el-form-item label="移除背景">
          <el-switch v-model="form.remove_background" />
          <div class="hint">自动移除生成图片的背景，输出透明 PNG</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
          <el-button @click="load">撤销</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { adminAPI } from '../../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving  = ref(false)
const testing = reactive({})

const providers = ref([])
const form = ref({
  provider: 'openai',
  fallback: 'ideogram',
  openai_api_key: '',
  openai_api_key_set: false,
  openai_model: 'dall-e-3',
  ideogram_api_key: '',
  ideogram_api_key_set: false,
  ideogram_model: 'V_3',
  recraft_api_key: '',
  recraft_api_key_set: false,
  recraft_model: 'fal-ai/recraft/v4/text-to-vector',
  style: 'modern',
  include_text: true,
  variant_count: 2,
  remove_background: false,
})

function iconOf(name) {
  return { openai: '\uD83C\uDFA8', ideogram: '\uD83D\uDDBC\uFE0F', recraft: '\u270F\uFE0F' }[name] || '\uD83C\uDFAD'
}

async function load() {
  loading.value = true
  try {
    const data = await adminAPI.getLogoProvider()
    providers.value = data.providers
    // Do NOT overwrite the masked key into the input
    form.value = {
      ...data.config,
      openai_api_key: '',
      ideogram_api_key: '',
      recraft_api_key: '',
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function setRole(name, role) {
  form.value[role] = name
  if (role === 'provider' && form.value.fallback === name) {
    // Swap fallback to a different provider
    const others = ['openai', 'ideogram', 'recraft'].filter(n => n !== name)
    form.value.fallback = others[0]
  }
}

async function save() {
  saving.value = true
  try {
    const payload = { ...form.value }
    delete payload.openai_api_key_set
    delete payload.ideogram_api_key_set
    delete payload.recraft_api_key_set
    // If user left key blank, omit it so backend preserves existing
    if (!payload.openai_api_key) delete payload.openai_api_key
    if (!payload.ideogram_api_key) delete payload.ideogram_api_key
    if (!payload.recraft_api_key) delete payload.recraft_api_key
    const data = await adminAPI.saveLogoProvider(payload)
    providers.value = data.providers
    form.value = {
      ...data.config,
      openai_api_key: '',
      ideogram_api_key: '',
      recraft_api_key: '',
    }
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function runTest(name) {
  testing[name] = true
  ElMessage.info('Logo 生成测试中，请耐心等待...')
  try {
    const res = await adminAPI.testLogoProvider(name)
    if (res.ok) {
      ElMessage.success(`${name} 连通正常`)
    } else {
      ElMessage.error(`${name} 测试失败: ${res.error || '未知错误'}`)
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    testing[name] = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 20px; color: #1a1a2e; }
.card-title { font-size: 15px; font-weight: 600; color: #1a1a2e; }
.hint { font-size: 12px; color: #aaa; margin-top: 4px; }

.provider-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 16px; margin-bottom: 20px;
}
.provider-card { border: 2px solid transparent; transition: all .2s; }
.provider-card.active    { border-color: #67c23a; background: #f0f9eb; }
.provider-card.fallback  { border-color: #e6a23c; background: #fdf6ec; }

.pc-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.pc-icon { font-size: 28px; }
.pc-title { flex: 1; }
.pc-label { font-size: 15px; font-weight: 600; color: #1a1a2e; }
.pc-name { font-size: 12px; color: #888; margin-top: 2px; }
.pc-status { margin-bottom: 12px; }
.pc-actions { display: flex; gap: 6px; flex-wrap: wrap; }

.form-card { margin-top: 8px; }
</style>
