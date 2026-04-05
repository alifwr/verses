<script setup lang="ts">
import { useSupabaseClient } from '~/utils/supabase'

definePageMeta({ layout: false })

const { fetchUser } = useAuth()
const error = ref('')

onMounted(async () => {
  try {
    const supabase = useSupabaseClient()

    // Supabase will parse the hash fragment automatically
    const { error: authError } = await supabase.auth.getSession()
    if (authError) throw authError

    await fetchUser()

    const { user } = useAuth()
    if (user.value?.has_partner) {
      navigateTo('/rules')
    } else {
      navigateTo('/invite')
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
