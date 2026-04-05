<script setup lang="ts">
definePageMeta({ layout: false })

const { api } = useApi()
const { user, fetchUser, logout } = useAuth()

const inviteCode = ref('')
const generatedCode = ref('')
const error = ref('')
const loading = ref(false)
const mode = ref<'choose' | 'create' | 'accept'>('choose')

async function createInvite() {
  loading.value = true
  error.value = ''
  try {
    const data = await api<{ code: string }>('/auth/invite', { method: 'POST' })
    generatedCode.value = data.code
    mode.value = 'create'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Failed to create invite'
  } finally {
    loading.value = false
  }
}

async function acceptInvite() {
  if (!inviteCode.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    await api('/auth/accept-invite', {
      method: 'POST',
      body: { code: inviteCode.value.trim() },
    })
    await fetchUser()
    navigateTo('/rules')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Invalid or expired invite code'
  } finally {
    loading.value = false
  }
}

async function copyCode() {
  await navigator.clipboard.writeText(generatedCode.value)
}

// If user already has partner, redirect
onMounted(async () => {
  await fetchUser()
  if (user.value?.has_partner) {
    navigateTo('/rules')
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
        <!-- Choose mode -->
        <div v-if="mode === 'choose'" class="space-y-4">
          <p class="text-sm text-verse-text text-center mb-4">Welcome, {{ user?.display_name }}! To get started, invite your partner or enter their invite code.</p>

          <button
            @click="createInvite"
            :disabled="loading"
            class="w-full py-2.5 bg-verse-slate text-white rounded-lg font-medium hover:bg-verse-slate/90 transition disabled:opacity-50"
          >
            Create invite code
          </button>

          <button
            @click="mode = 'accept'"
            class="w-full py-2.5 border border-verse-slate/20 text-verse-text rounded-lg font-medium hover:bg-gray-50 transition"
          >
            I have an invite code
          </button>
        </div>

        <!-- Show generated code -->
        <div v-else-if="mode === 'create'" class="space-y-4">
          <p class="text-sm text-verse-text text-center">Share this code with your partner:</p>
          <div class="flex items-center gap-2">
            <code class="flex-1 bg-gray-100 px-4 py-2.5 rounded-lg text-center font-mono text-lg tracking-wider">{{ generatedCode }}</code>
            <button @click="copyCode" class="px-3 py-2.5 bg-verse-slate text-white rounded-lg hover:bg-verse-slate/90 transition text-sm">
              Copy
            </button>
          </div>
          <p class="text-xs text-verse-slate text-center">Valid for 7 days. Waiting for your partner to enter this code.</p>
          <button @click="mode = 'choose'" class="w-full py-2 text-sm text-verse-slate hover:underline">Back</button>
        </div>

        <!-- Enter invite code -->
        <div v-else-if="mode === 'accept'" class="space-y-4">
          <p class="text-sm text-verse-text text-center">Enter the invite code from your partner:</p>
          <input
            v-model="inviteCode"
            type="text"
            placeholder="Paste invite code"
            class="w-full px-4 py-2.5 rounded-lg border border-verse-slate/20 bg-white focus:outline-none focus:ring-2 focus:ring-verse-slate/40 transition font-mono text-center tracking-wider"
          />
          <p v-if="error" class="text-red-500 text-sm text-center">{{ error }}</p>
          <button
            @click="acceptInvite"
            :disabled="loading || !inviteCode.trim()"
            class="w-full py-2.5 bg-verse-slate text-white rounded-lg font-medium hover:bg-verse-slate/90 transition disabled:opacity-50"
          >
            {{ loading ? 'Connecting...' : 'Connect' }}
          </button>
          <button @click="mode = 'choose'" class="w-full py-2 text-sm text-verse-slate hover:underline">Back</button>
        </div>
      </div>

      <div class="text-center mt-4">
        <button @click="logout" class="text-sm text-verse-slate hover:underline">Sign out</button>
      </div>
    </div>
  </div>
</template>
