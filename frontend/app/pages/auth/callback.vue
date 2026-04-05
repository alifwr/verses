<script setup lang="ts">
import { useSupabaseClient } from '~/utils/supabase'

definePageMeta({ layout: false })

const { fetchUser } = useAuth()
const error = ref('')

onMounted(async () => {
  try {
    const supabase = useSupabaseClient()

    // Handle PKCE code exchange (default Supabase flow)
    const url = new URL(window.location.href)
    const code = url.searchParams.get('code')
    if (code) {
      const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)
      if (exchangeError) throw exchangeError
    }

    // Verify we have a session
    const { data, error: sessionError } = await supabase.auth.getSession()
    if (sessionError) throw sessionError
    if (!data.session) throw new Error('No session established')

    await fetchUser()

    const { user } = useAuth()
    if (user.value?.has_partner) {
      navigateTo('/rules')
    } else {
      // Restore invite code saved before login redirect
      const savedCode = localStorage.getItem('verse-invite-code')
      if (savedCode) {
        localStorage.removeItem('verse-invite-code')
        navigateTo(`/invite?code=${savedCode}`)
      } else {
        navigateTo('/invite')
      }
    }
  } catch (e: any) {
    error.value = e.message || 'Authentication failed'
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-verse-bg">
    <div class="text-center">
      <p v-if="error" class="text-red-500">{{ error }}</p>
      <p v-else class="text-verse-slate">Signing you in...</p>
    </div>
  </div>
</template>
