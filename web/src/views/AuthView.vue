<script setup lang="ts">
import { LogIn, UserPlus } from 'lucide-vue-next'
import { useAppBindings } from '../appContext'
import ToastMessage from '../components/ToastMessage.vue'

const { authMode, authForm, authLoading, submitAuth, message, error } = useAppBindings()
</script>

<template>
  <main class="auth-shell">
    <ToastMessage :message="message" :error="error" />
    <section class="auth-card panel">
      <div class="brand auth-brand">
        <h1>量化研究台</h1>
        <p>登录后进入你的因子、策略和密钥空间</p>
      </div>
      <div class="auth-tabs">
        <button type="button" :class="{ active: authMode === 'login' }" @click="authMode = 'login'">登录</button>
        <button type="button" :class="{ active: authMode === 'register' }" @click="authMode = 'register'">注册</button>
      </div>
      <label>
        用户名
        <input v-model="authForm.username" autocomplete="username" placeholder="admin" @keyup.enter="submitAuth" />
      </label>
      <label>
        密码
        <input v-model="authForm.password" autocomplete="current-password" type="password" placeholder="admin" @keyup.enter="submitAuth" />
      </label>
      <button class="submit" :disabled="authLoading" @click="submitAuth">
        <LogIn v-if="authMode === 'login'" :size="17" />
        <UserPlus v-else :size="17" />
        <span>{{ authMode === 'login' ? '登录' : '创建账号' }}</span>
      </button>
    </section>
  </main>
</template>
