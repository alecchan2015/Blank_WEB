<template>
  <div>
    <h2 class="page-title">用户管理</h2>
    <el-table :data="users" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="角色" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">{{ row.role === 'admin' ? '管理员' : '用户' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="积分" width="100" align="center">
        <template #default="{ row }">
          <span class="credits-val">{{ row.credits }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="160">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleDateString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" align="center">
        <template #default="{ row }">
          <el-button size="small" link @click="openCreditsDialog(row)">调整积分</el-button>
          <el-button size="small" link :type="row.is_active ? 'warning' : 'success'"
            @click="toggleStatus(row)">{{ row.is_active ? '禁用' : '启用' }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Credits Dialog -->
    <el-dialog v-model="creditsVisible" title="调整用户积分" width="400px">
      <div class="credits-info">
        <span>当前积分：<strong>{{ editUser?.credits }}</strong></span>
      </div>
      <el-form :model="creditsForm" label-width="80px" style="margin-top:16px">
        <el-form-item label="新积分值">
          <el-input-number v-model="creditsForm.credits" :min="0" :max="999999" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="creditsForm.reason" placeholder="调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="creditsVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCredits">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminAPI } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const users = ref([])
const loading = ref(false)
const creditsVisible = ref(false)
const editUser = ref(null)
const saving = ref(false)
const creditsForm = ref({ credits: 0, reason: '' })

function openCreditsDialog(user) {
  editUser.value = user
  creditsForm.value = { credits: user.credits, reason: '管理员调整' }
  creditsVisible.value = true
}

async function saveCredits() {
  saving.value = true
  try {
    await adminAPI.updateUserCredits(editUser.value.id, creditsForm.value)
    ElMessage.success('积分已更新')
    creditsVisible.value = false
    await loadUsers()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function toggleStatus(user) {
  const action = user.is_active ? '禁用' : '启用'
  await ElMessageBox.confirm(`确认${action}用户 ${user.username}？`, '操作确认', { type: 'warning' })
  await adminAPI.updateUserStatus(user.id, { is_active: !user.is_active })
  ElMessage.success(`已${action}`)
  await loadUsers()
}

async function loadUsers() {
  loading.value = true
  try { users.value = await adminAPI.getUsers() }
  finally { loading.value = false }
}

onMounted(loadUsers)
</script>

<style scoped>
.page-title { font-size: 20px; color: #1a1a2e; margin-bottom: 16px; }
.credits-val { font-weight: 700; color: #f5a623; }
.credits-info { font-size: 14px; color: #555; }
</style>
