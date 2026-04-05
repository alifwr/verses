import { useSupabaseClient } from '~/utils/supabase'

export default defineNuxtPlugin(async () => {
  const supabase = useSupabaseClient()
  const { fetchUser } = useAuth()

  const { data } = await supabase.auth.getSession()
  if (data.session) {
    await fetchUser()
  }

  supabase.auth.onAuthStateChange(async (event) => {
    if (event === 'SIGNED_IN') {
      await fetchUser()
    } else if (event === 'SIGNED_OUT') {
      const { user } = useAuth()
      user.value = null
    }
  })
})
