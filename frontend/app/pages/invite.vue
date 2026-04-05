<script setup lang="ts">
definePageMeta({ layout: false })

const route = useRoute()
const { api } = useApi()
const { user, fetchUser, logout } = useAuth()

const generatedUrl = ref('')
const error = ref('')
const loading = ref(false)
const copied = ref(false)
const mode = ref<'choose' | 'create' | 'accepting'>('choose')

function inviteUrl(code: string): string {
  return `${window.location.origin}/invite?code=${code}`
}

async function createInvite() {
  loading.value = true
  error.value = ''
  try {
    const data = await api<{ code: string }>('/auth/invite', { method: 'POST' })
    generatedUrl.value = inviteUrl(data.code)
    mode.value = 'create'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Failed to create invite'
  } finally {
    loading.value = false
  }
}

async function acceptInvite(code: string) {
  loading.value = true
  error.value = ''
  mode.value = 'accepting'
  try {
    await api('/auth/accept-invite', {
      method: 'POST',
      body: { code },
    })
    await fetchUser()
    navigateTo('/rules')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Invalid or expired invite link'
    mode.value = 'choose'
  } finally {
    loading.value = false
  }
}

async function copyUrl() {
  await navigator.clipboard.writeText(generatedUrl.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

onMounted(async () => {
  await fetchUser()
  if (user.value?.has_partner) {
    navigateTo('/rules')
    return
  }

  // Auto-accept if opened via invite link
  const code = route.query.code as string
  if (code) {
    await acceptInvite(code)
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-verse-bg">
    <div class="w-full max-w-sm mx-4">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-serif text-verse-text tracking-wide">Verse</h1>
        <p class="text-verse-slate text-sm mt-2 font-light">Connect with your partner</p>
      </div>

      <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-8 border border-verse-slate/10">
        <!-- Accepting invite from URL -->
        <div v-if="mode === 'accepting'" class="text-center">
          <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
          <p v-else class="text-verse-slate text-sm">Connecting with your partner...</p>
        </div>

        <!-- Choose mode -->
        <div v-else-if="mode === 'choose'" class="space-y-4">
          <p class="text-sm text-verse-text text-center mb-4">Welcome, {{ user?.display_name }}! Invite your partner to get started.</p>

          <p v-if="error" class="text-red-500 text-sm text-center">{{ error }}</p>

          <button
            @click="createInvite"
            :disabled="loading"
            class="w-full py-2.5 bg-verse-slate text-white rounded-lg font-medium hover:bg-verse-slate/90 transition disabled:opacity-50"
          >
            Create invite link
          </button>
        </div>

        <!-- Show generated link -->
        <div v-else-if="mode === 'create'" class="space-y-4">
          <p class="text-sm text-verse-text text-center">Share this link with your partner:</p>
          <div class="bg-gray-100 px-4 py-3 rounded-lg break-all text-center text-sm font-mono text-verse-text/70">
            {{ generatedUrl }}
          </div>
          <button
            @click="copyUrl"
            class="w-full py-2.5 bg-verse-slate text-white rounded-lg font-medium hover:bg-verse-slate/90 transition"
          >
            {{ copied ? 'Copied!' : 'Copy link' }}
          </button>
          <p class="text-xs text-verse-slate text-center">Valid for 7 days.</p>
          <button @click="mode = 'choose'" class="w-full py-2 text-sm text-verse-slate hover:underline">Back</button>
        </div>
      </div>

      <div class="text-center mt-4">
        <button @click="logout" class="text-sm text-verse-slate hover:underline">Sign out</button>
      </div>
    </div>
  </div>
</template>
