<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { KeyRound, LockKeyhole, RotateCcw, Save, Trash2, UserRound } from 'lucide-vue-next'
import { adminResetPassword, changePassword, deleteAdminUser, deleteLongbridgeKey, fetchAdminUsers, fetchLongbridgeKey, saveLongbridgeKey, type AuthUser } from '../api'
import { useAppBindings } from '../appContext'

type AccountSection = 'longbridge' | 'password' | 'admin'

const { activeTab, currentUser, setError, showToast } = useAppBindings()
const activeSection = ref<AccountSection>('password')
const keyForm = ref({ app_key: '', app_secret: '', access_token: '', http_url: '' })
const passwordForm = ref({ old_password: '', new_password: '', confirm_password: '' })
const resetForm = ref({ username: '', new_password: '' })
const users = ref<AuthUser[]>([])
const keyStatus = ref('')
const loading = ref(false)
const userProfile = computed(() => currentUser?.value || currentUser)
const isAdmin = computed(() => String(userProfile.value?.role || '').trim().toLowerCase() === 'admin')
const sections = computed(() => [
  { id: 'password', label: '修改密码', icon: LockKeyhole },
  { id: 'longbridge', label: '长桥密钥', icon: KeyRound },
  ...(isAdmin.value ? [{ id: 'admin', label: '重置密码', icon: RotateCcw }] : [])
] as Array<{ id: AccountSection; label: string; icon: unknown }>)

async function loadKey() {
  try {
    const key = await fetchLongbridgeKey()
    keyStatus.value = key?.configured === false || !key?.id ? '未配置个人密钥，将使用系统密钥' : `已配置：${key.app_key || ''}`
  } catch (err) {
    setError(err, '加载密钥配置失败')
  }
}

async function saveKey() {
  loading.value = true
  try {
    await saveLongbridgeKey(keyForm.value)
    keyForm.value = { app_key: '', app_secret: '', access_token: '', http_url: '' }
    await loadKey()
    showToast('长桥密钥已保存')
  } catch (err) {
    setError(err, '保存密钥失败')
  } finally {
    loading.value = false
  }
}

async function removeKey() {
  loading.value = true
  try {
    await deleteLongbridgeKey()
    await loadKey()
    showToast('长桥密钥已删除')
  } catch (err) {
    setError(err, '删除密钥失败')
  } finally {
    loading.value = false
  }
}

async function submitPassword() {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    setError(new Error('两次输入的新密码不一致'), '修改密码失败')
    return
  }
  loading.value = true
  try {
    await changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
    showToast('密码已修改')
  } catch (err) {
    setError(err, '修改密码失败')
  } finally {
    loading.value = false
  }
}

async function submitReset() {
  loading.value = true
  try {
    await adminResetPassword({
      username: resetForm.value.username,
      new_password: resetForm.value.new_password
    })
    resetForm.value = { username: '', new_password: '' }
    showToast('用户密码已重置')
  } catch (err) {
    setError(err, '重置密码失败')
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  if (!isAdmin.value) return
  try {
    users.value = await fetchAdminUsers()
  } catch (err) {
    setError(err, '加载用户列表失败')
  }
}

function selectUser(username: string) {
  resetForm.value.username = username
}

async function removeUser(user: AuthUser) {
  if (user.id === userProfile.value?.id) {
    setError(new Error('不能删除当前登录用户'), '删除用户失败')
    return
  }
  if (!window.confirm(`确认删除用户「${user.username}」？`)) return
  loading.value = true
  try {
    await deleteAdminUser(user.id)
    if (resetForm.value.username === user.username) resetForm.value = { username: '', new_password: '' }
    await loadUsers()
    showToast('用户已删除')
  } catch (err) {
    setError(err, '删除用户失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadKey()
  loadUsers()
})
</script>

<template>
  <section v-if="activeTab === 'account'" class="research-layout">
    <aside class="panel research-controls">
      <div class="panel-title">
        <UserRound :size="17" />
        <span>账户设置</span>
      </div>
      <div class="account-summary">
        <strong>{{ currentUser.username }}</strong>
        <span>角色：{{ currentUser.role || '-' }}</span>
      </div>
      <div class="account-section-list">
        <button v-for="section in sections" :key="section.id" type="button" :class="{ active: activeSection === section.id }" @click="activeSection = section.id">
          <component :is="section.icon" :size="16" />
          <span>{{ section.label }}</span>
        </button>
      </div>
    </aside>

    <section class="main-panel research-panel">
      <div class="chart-head">
        <div>
          <h2>{{ sections.find((item) => item.id === activeSection)?.label }}</h2>
          <p v-if="activeSection === 'longbridge'">{{ keyStatus }}</p>
          <p v-else-if="activeSection === 'password'">修改当前登录账号的密码</p>
          <p v-else>管理员可以为其他用户设置新密码</p>
        </div>
      </div>

      <div v-if="activeSection === 'longbridge'" class="account-form-panel">
        <label>
          App Key
          <input v-model="keyForm.app_key" autocomplete="off" />
        </label>
        <label>
          App Secret
          <input v-model="keyForm.app_secret" autocomplete="off" type="password" />
        </label>
        <label>
          Access Token
          <input v-model="keyForm.access_token" autocomplete="off" type="password" />
        </label>
        <label>
          HTTP URL
          <input v-model="keyForm.http_url" autocomplete="off" placeholder="高级可选，通常留空" />
          <small>长桥 OpenAPI 的自定义服务地址。普通使用留空，会使用 SDK 默认地址。</small>
        </label>
        <div class="sync-actions">
          <button class="submit compact" :disabled="loading" @click="saveKey">
            <Save :size="15" />
            <span>保存</span>
          </button>
          <button class="submit danger compact" :disabled="loading" @click="removeKey">
            <Trash2 :size="15" />
            <span>删除</span>
          </button>
        </div>
      </div>

      <div v-else-if="activeSection === 'password'" class="account-form-panel">
        <label>
          原密码
          <input v-model="passwordForm.old_password" type="password" autocomplete="current-password" />
        </label>
        <label>
          新密码
          <input v-model="passwordForm.new_password" type="password" autocomplete="new-password" />
        </label>
        <label>
          确认新密码
          <input v-model="passwordForm.confirm_password" type="password" autocomplete="new-password" />
        </label>
        <div class="sync-actions">
          <button class="submit compact" :disabled="loading" @click="submitPassword">
            <Save :size="15" />
            <span>修改</span>
          </button>
        </div>
      </div>

      <div v-else class="account-form-panel">
        <div class="task-table account-user-table">
          <div class="account-user-row header">
            <span>用户名</span>
            <span>角色</span>
            <span>操作</span>
          </div>
          <div v-for="item in users" :key="item.id" class="account-user-row">
            <span>{{ item.username }}</span>
            <span>{{ item.role }}</span>
            <span class="account-user-actions">
              <button class="ghost compact" type="button" @click="selectUser(item.username)">选择</button>
              <button class="submit danger compact" type="button" :disabled="loading || item.id === currentUser.id" @click="removeUser(item)">
                <Trash2 :size="14" />
                <span>删除</span>
              </button>
            </span>
          </div>
        </div>
        <label>
          用户名
          <input v-model="resetForm.username" />
        </label>
        <label>
          新密码
          <input v-model="resetForm.new_password" type="password" autocomplete="new-password" />
        </label>
        <div class="sync-actions">
          <button class="submit compact" :disabled="loading" @click="submitReset">
            <RotateCcw :size="15" />
            <span>重置</span>
          </button>
        </div>
      </div>
    </section>
  </section>
</template>
