<script setup>
definePageMeta({
  layout: false // Hide sidebar layout on login page
})

const config = useRuntimeConfig()
const isLogin = ref(true)
const isLoading = ref(false)
const message = ref({ text: '', type: '' })

const form = reactive({
  email: '',
  password: '',
  full_name: ''
})

function toggleMode() {
  isLogin.value = !isLogin.value
  message.value = { text: '', type: '' }
}

async function handleSubmit() {
  isLoading.value = true
  message.value = { text: '', type: '' }
  
  const endpoint = isLogin.value ? '/login' : '/register'
  const payload = isLogin.value 
    ? { email: form.email, password: form.password }
    : { email: form.email, password: form.password, full_name: form.full_name }

  try {
    const response = await fetch(`${config.public.apiBase}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || 'Something went wrong')
    }
    
    if (isLogin.value) {
      // Store token and user data
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user_info', JSON.stringify(data.user))
      
      message.value = { text: 'Login successful! Redirecting...', type: 'success' }
      setTimeout(() => {
        navigateTo('/')
      }, 1000)
    } else {
      message.value = { text: 'Registration successful! Please login.', type: 'success' }
      isLogin.value = true
      form.full_name = ''
    }
  } catch (err) {
    message.value = { text: err.message, type: 'error' }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="background-blobs">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
    </div>

    <div class="auth-card glass-card">
      <div class="brand">
        <div class="ai-badge">AI</div>
        <div class="logo-text">
          <span class="main">Grocery</span>
          <span class="sub">Management</span>
        </div>
      </div>

      <div class="auth-header">
        <h2>{{ isLogin ? 'Welcome Back' : 'Create Account' }}</h2>
        <p>{{ isLogin ? 'Please enter your details to sign in.' : 'Join us to manage your food inventory smart.' }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div v-if="!isLogin" class="form-group">
          <label for="name">Full Name</label>
          <div class="input-wrapper">
            <span class="input-icon">👤</span>
            <input id="name" v-model="form.full_name" type="text" placeholder="John Doe" required />
          </div>
        </div>

        <div class="form-group">
          <label for="email">Email Address</label>
          <div class="input-wrapper">
            <span class="input-icon">✉️</span>
            <input id="email" v-model="form.email" type="email" placeholder="name@store.com" required />
          </div>
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input id="password" v-model="form.password" type="password" placeholder="••••••••" required />
          </div>
        </div>

        <div v-if="message.text" :class="['alert', message.type]">
          {{ message.text }}
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="isLoading">
          <span v-if="isLoading" class="loader-small"></span>
          <span v-else>{{ isLogin ? 'Sign In' : 'Create Account' }}</span>
        </button>
      </form>

      <div class="auth-footer">
        <p>
          {{ isLogin ? "Don't have an account?" : "Already have an account?" }}
          <button @click="toggleMode" class="btn-link">
            {{ isLogin ? 'Sign Up' : 'Sign In' }}
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: #0f172a;
  position: relative;
  overflow: hidden;
  font-family: 'Outfit', sans-serif;
}

/* Background Blobs */
.background-blobs {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
  animation: move 20s infinite alternate;
}

.blob-1 {
  width: 500px;
  height: 500px;
  background: var(--primary);
  top: -10%;
  left: -10%;
}

.blob-2 {
  width: 400px;
  height: 400px;
  background: #3b82f6;
  bottom: -10%;
  right: -5%;
  animation-delay: -5s;
}

.blob-3 {
  width: 300px;
  height: 300px;
  background: #f43f5e;
  top: 40%;
  right: 20%;
  animation-delay: -10s;
}

@keyframes move {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(100px, 50px) scale(1.1); }
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 2.5rem;
  z-index: 10;
  position: relative;
}

.brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

/* AI Badge matches the one in global style but can be tweaked if needed */
.ai-badge {
  background: var(--primary-gradient);
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 800;
  color: white;
  letter-spacing: 1px;
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
}

.auth-header p {
  color: var(--text-dim);
  font-size: 0.95rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-dim);
  margin-left: 0.25rem;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 1rem;
  font-size: 1.1rem;
  opacity: 0.6;
}

.input-wrapper input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 0.8rem 1rem 0.8rem 3rem;
  color: white;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
}

.input-wrapper input:focus {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 106, 61, 0.5);
  box-shadow: 0 0 0 4px rgba(255, 106, 61, 0.1);
}

.btn-block {
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.9rem;
  font-size: 1rem;
}

.auth-footer {
  margin-top: 1.5rem;
  text-align: center;
  color: var(--text-dim);
  font-size: 0.9rem;
}

.btn-link {
  background: none;
  border: none;
  color: var(--primary);
  font-weight: 700;
  cursor: pointer;
  padding: 0 0.25rem;
  text-decoration: underline;
  text-underline-offset: 4px;
}

.btn-link:hover {
  filter: brightness(1.2);
}

/* Alert styles */
.alert {
  padding: 0.8rem;
  border-radius: 10px;
  font-size: 0.85rem;
  text-align: center;
}

.alert.error {
  background: rgba(248, 113, 113, 0.15);
  border: 1px solid rgba(248, 113, 113, 0.3);
  color: #f87171;
}

.alert.success {
  background: rgba(52, 211, 153, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.3);
  color: #34d399;
}

.loader-small {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  display: inline-block;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
