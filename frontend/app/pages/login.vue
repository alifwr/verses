<script setup lang="ts">
definePageMeta({ layout: false })

const { login, isAuthenticated } = useAuth()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(username.value, password.value)
    navigateTo('/ledger')
  } catch {
    error.value = 'Invalid username or password'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (isAuthenticated.value) navigateTo('/ledger')
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-verse-bg">
    <!-- Mountain background SVG -->
    <div class="absolute inset-0 pointer-events-none">
      <svg class="absolute bottom-0 w-full" viewBox="0 0 1440 400" preserveAspectRatio="none">
        <path d="M0,400 L0,280 Q180,120 360,200 Q540,80 720,180 Q900,60 1080,160 Q1260,100 1440,220 L1440,400 Z" fill="#6B7FA3" opacity="0.15"/>
        <path d="M0,400 L0,320 Q200,180 400,260 Q600,140 800,240 Q1000,120 1200,200 Q1350,160 1440,260 L1440,400 Z" fill="#6B7FA3" opacity="0.08"/>
      </svg>
      <!-- Topographic lines -->
      <svg class="absolute top-0 left-0 w-full h-full opacity-[0.03]">
        <pattern id="topo" width="100" height="100" patternUnits="userSpaceOnUse">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
          <circle cx="50" cy="50" r="30" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
          <circle cx="50" cy="50" r="20" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
        </pattern>
        <rect width="100%" height="100%" fill="url(#topo)"/>
      </svg>
    </div>

    <!-- Login card -->
    <div class="relative z-10 w-full max-w-sm mx-4">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-serif text-verse-text tracking-wide">Verse</h1>
        <p class="text-verse-slate text-sm mt-2 font-light">A shared space for your journey together</p>
      </div>

      <form @submit.prevent="handleLogin" class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-8 border border-verse-slate/10">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-verse-text mb-1">Username</label>
            <input
              v-model="username"
              type="text"
              required
              class="w-full px-4 py-2.5 rounded-lg border border-verse-slate/20 bg-white focus:outline-none focus:ring-2 focus:ring-verse-slate/40 transition"
              placeholder="Enter your name"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-verse-text mb-1">Password</label>
            <input
              v-model="password"
              type="password"
              required
              class="w-full px-4 py-2.5 rounded-lg border border-verse-slate/20 bg-white focus:outline-none focus:ring-2 focus:ring-verse-slate/40 transition"
              placeholder="Enter your password"
            />
          </div>
        </div>

        <p v-if="error" class="text-red-500 text-sm mt-3">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full mt-6 py-2.5 bg-verse-slate text-white rounded-lg font-medium hover:bg-verse-slate/90 transition disabled:opacity-50"
        >
          {{ loading ? 'Entering...' : 'Enter the Verse' }}
        </button>
      </form>

      <!-- Geometric dot divider -->
      <div class="flex justify-center mt-6 gap-1.5">
        <span v-for="i in 5" :key="i" class="w-1.5 h-1.5 rounded-full bg-verse-slate/20" />
      </div>
    </div>
  </div>
</template>
