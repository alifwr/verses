<script setup lang="ts">
definePageMeta({ layout: false })

const { signInWithGoogle, isAuthenticated } = useAuth()
const loading = ref(false)
const error = ref('')

async function handleGoogleLogin() {
  loading.value = true
  error.value = ''
  try {
    await signInWithGoogle()
  } catch {
    error.value = 'Failed to sign in. Please try again.'
    loading.value = false
  }
}

onMounted(() => {
  if (isAuthenticated.value) navigateTo('/rules')
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

      <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-8 border border-verse-slate/10">
        <p v-if="error" class="text-red-500 text-sm mb-4 text-center">{{ error }}</p>

        <button
          @click="handleGoogleLogin"
          :disabled="loading"
          class="w-full flex items-center justify-center gap-3 py-2.5 bg-white border border-verse-slate/20 rounded-lg font-medium hover:bg-gray-50 transition disabled:opacity-50"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          {{ loading ? 'Signing in...' : 'Sign in with Google' }}
        </button>
      </div>

      <div class="flex justify-center mt-6 gap-1.5">
        <span v-for="i in 5" :key="i" class="w-1.5 h-1.5 rounded-full bg-verse-slate/20" />
      </div>
    </div>
  </div>
</template>
