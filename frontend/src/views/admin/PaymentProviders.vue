<template>
  <div class="payment-providers" v-loading="loading">
    <h2 class="page-title">支付渠道配置</h2>

    <el-alert type="info" show-icon :closable="false" style="margin-bottom:16px">
      配置各支付渠道的商户凭证。模拟支付始终可用，其他渠道需要填写完整凭证并启用后生效。
    </el-alert>

    <el-tabs v-model="activeTab">
      <!-- Stripe -->
      <el-tab-pane label="Stripe 信用卡" name="stripe">
        <div class="section-card">
          <div class="section-header">
            <h3>Stripe Checkout</h3>
            <el-switch v-model="cfg.stripe.enabled" />
          </div>
          <p class="desc">
            在 <a href="https://dashboard.stripe.com/apikeys" target="_blank">Stripe Dashboard</a>
            获取 Secret Key 和 Publishable Key，然后配置 Webhook 端点 <code>/api/webhooks/stripe</code>。
          </p>
          <div class="form-grid">
            <div class="row">
              <label>模式</label>
              <el-select v-model="cfg.stripe.mode">
                <el-option label="测试模式 (test)" value="test" />
                <el-option label="正式模式 (live)" value="live" />
              </el-select>
            </div>
            <div class="row">
              <label>Secret Key</label>
              <el-input v-model="cfg.stripe.secret_key" type="password" show-password
                :placeholder="cfg.stripe.secret_key_set ? '已配置（留空保持不变）' : 'sk_...'" />
            </div>
            <div class="row">
              <label>Publishable Key</label>
              <el-input v-model="cfg.stripe.publishable_key" placeholder="pk_..." />
            </div>
            <div class="row">
              <label>Webhook Secret</label>
              <el-input v-model="cfg.stripe.webhook_secret" type="password" show-password
                :placeholder="cfg.stripe.webhook_secret_set ? '已配置' : 'whsec_...'" />
            </div>
            <div class="row">
              <label>成功回跳 URL</label>
              <el-input v-model="cfg.stripe.success_url" placeholder="https://yourdomain.com/payment/{order_no}?status=success" />
            </div>
            <div class="row">
              <label>取消回跳 URL</label>
              <el-input v-model="cfg.stripe.cancel_url" placeholder="https://yourdomain.com/payment/{order_no}?status=cancel" />
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Alipay -->
      <el-tab-pane label="支付宝" name="alipay">
        <div class="section-card">
          <div class="section-header">
            <h3>支付宝 · 电脑网站支付</h3>
            <el-switch v-model="cfg.alipay.enabled" />
          </div>
          <p class="desc">
            在
            <a href="https://open.alipay.com/platform/developerIndex.htm" target="_blank">支付宝开放平台</a>
            创建「电脑网站支付」应用，获取 AppID + 密钥。
          </p>
          <div class="form-grid">
            <div class="row">
              <label>模式</label>
              <el-select v-model="cfg.alipay.mode">
                <el-option label="沙箱 sandbox" value="sandbox" />
                <el-option label="正式 production" value="production" />
              </el-select>
            </div>
            <div class="row">
              <label>AppID</label>
              <el-input v-model="cfg.alipay.app_id" />
            </div>
            <div class="row full">
              <label>应用私钥（PEM）</label>
              <el-input v-model="cfg.alipay.private_key" type="textarea" :rows="4"
                :placeholder="cfg.alipay.private_key_set ? '已配置（留空保持不变）' : '-----BEGIN RSA PRIVATE KEY-----...'" />
            </div>
            <div class="row full">
              <label>支付宝公钥</label>
              <el-input v-model="cfg.alipay.alipay_public_key" type="textarea" :rows="3"
                :placeholder="cfg.alipay.alipay_public_key_set ? '已配置' : '-----BEGIN PUBLIC KEY-----...'" />
            </div>
            <div class="row">
              <label>notify_url（Webhook）</label>
              <el-input v-model="cfg.alipay.notify_url" placeholder="https://yourdomain.com/api/webhooks/alipay" />
            </div>
            <div class="row">
              <label>return_url（跳回）</label>
              <el-input v-model="cfg.alipay.return_url" placeholder="https://yourdomain.com/payment/{order_no}" />
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Wechat -->
      <el-tab-pane label="微信支付" name="wechat">
        <div class="section-card">
          <div class="section-header">
            <h3>微信支付 · Native 扫码</h3>
            <el-switch v-model="cfg.wechat.enabled" />
          </div>
          <p class="desc">
            在
            <a href="https://pay.weixin.qq.com/" target="_blank">微信支付商户平台</a>
            申请 API v3 证书（需企业商户号）。
          </p>
          <div class="form-grid">
            <div class="row">
              <label>模式</label>
              <el-select v-model="cfg.wechat.mode">
                <el-option label="沙箱" value="sandbox" />
                <el-option label="正式" value="production" />
              </el-select>
            </div>
            <div class="row">
              <label>商户号 (MCHID)</label>
              <el-input v-model="cfg.wechat.mchid" placeholder="例如 1234567890" />
            </div>
            <div class="row">
              <label>App ID</label>
              <el-input v-model="cfg.wechat.app_id" placeholder="wx..." />
            </div>
            <div class="row">
              <label>API v3 Key</label>
              <el-input v-model="cfg.wechat.api_v3_key" type="password" show-password
                :placeholder="cfg.wechat.api_v3_key_set ? '已配置' : ''" />
            </div>
            <div class="row">
              <label>证书序列号</label>
              <el-input v-model="cfg.wechat.cert_serial" />
            </div>
            <div class="row full">
              <label>商户证书私钥（PEM）</label>
              <el-input v-model="cfg.wechat.cert_private" type="textarea" :rows="4"
                :placeholder="cfg.wechat.cert_private_set ? '已配置' : '-----BEGIN PRIVATE KEY-----...'" />
            </div>
            <div class="row">
              <label>通知 URL</label>
              <el-input v-model="cfg.wechat.notify_url" placeholder="https://yourdomain.com/api/webhooks/wechat" />
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Manual -->
      <el-tab-pane label="模拟 / 人工" name="manual">
        <div class="section-card">
          <div class="section-header">
            <h3>人工确认支付</h3>
            <el-switch v-model="cfg.manual.enabled" />
          </div>
          <p class="desc">
            无需商户对接。用户下单后，管理员在「订单管理」中手动确认收款。适合测试环境或线下汇款场景。
          </p>
          <div class="form-grid">
            <div class="row full">
              <label>用户提示语</label>
              <el-input v-model="cfg.manual.hint" type="textarea" :rows="3"
                placeholder="请在此填写展示给用户的付款说明（收款账号、转账提示等）" />
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="save-bar">
      <el-button type="primary" :loading="saving" @click="save">保存全部配置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminAPI } from '../../api'

const activeTab = ref('stripe')
const loading = ref(false)
const saving = ref(false)

const cfg = reactive({
  stripe: { enabled: false, mode: 'test', secret_key: '', publishable_key: '', webhook_secret: '', success_url: '', cancel_url: '' },
  alipay: { enabled: false, mode: 'sandbox', app_id: '', private_key: '', alipay_public_key: '', notify_url: '', return_url: '' },
  wechat: { enabled: false, mode: 'sandbox', mchid: '', app_id: '', api_v3_key: '', cert_serial: '', cert_private: '', notify_url: '' },
  manual: { enabled: true, hint: '' },
})

async function load() {
  loading.value = true
  try {
    const res = await adminAPI.getPaymentProviders()
    Object.keys(cfg).forEach(k => {
      if (res[k]) Object.assign(cfg[k], res[k])
    })
    // Don't surface masked placeholders in actual input fields
    ;['stripe', 'alipay', 'wechat'].forEach(ch => {
      Object.keys(cfg[ch]).forEach(f => {
        if (typeof cfg[ch][f] === 'string' && cfg[ch][f].includes('...')) {
          cfg[ch][f] = ''
        }
      })
    })
  } catch (e) {
    ElMessage.error('加载失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    // Strip empty sensitive fields so backend keeps existing values
    const payload = JSON.parse(JSON.stringify(cfg))
    const sensitiveFields = {
      stripe: ['secret_key', 'webhook_secret'],
      alipay: ['private_key', 'alipay_public_key'],
      wechat: ['api_v3_key', 'cert_private'],
    }
    Object.entries(sensitiveFields).forEach(([ch, fields]) => {
      fields.forEach(f => {
        if (!payload[ch][f]) delete payload[ch][f]
      })
    })
    const res = await adminAPI.savePaymentProviders(payload)
    Object.keys(cfg).forEach(k => {
      if (res[k]) Object.assign(cfg[k], res[k])
    })
    // Clear input buffers after save
    ;['stripe', 'alipay', 'wechat'].forEach(ch => {
      Object.keys(cfg[ch]).forEach(f => {
        if (typeof cfg[ch][f] === 'string' && cfg[ch][f].includes('...')) cfg[ch][f] = ''
      })
    })
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.payment-providers { max-width: 900px; }
.page-title { font-size: 20px; color: #1a1a2e; margin: 0 0 16px; }
.section-card {
  background: #fff; border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.section-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 6px;
}
.section-header h3 { margin: 0; font-size: 16px; color: #1a1a2e; }
.desc { margin: 0 0 20px; font-size: 13px; color: #888; line-height: 1.6; }
.desc code { background: #f5f7fa; padding: 1px 5px; border-radius: 3px; font-size: 12px; }
.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.row label { display: block; font-size: 13px; color: #555; margin-bottom: 6px; }
.row.full { grid-column: span 2; }
.save-bar { margin-top: 20px; text-align: right; }

@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
  .row.full { grid-column: span 1; }
}
</style>
