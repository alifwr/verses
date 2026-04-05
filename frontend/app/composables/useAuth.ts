import { useSupabaseClient } from '~/utils/supabase'

interface Partner {
  id: number
  email: string
  display_name: string
  avatar_url: string | null
  is_online: boolean
}

interface User {
  id: number
  email: string
  display_name: string
  avatar_url: string | null
  has_partner: boolean
  partner: Partner | null
}

export const useAuth = () => {
  const user = useState<User | null>('auth-user', () => null)
  const config = useRuntimeConfig()

  const isAuthenticated = computed(() => !!user.value)
  const hasPartner = computed(() => !!user.value?.has_partner)

  async function getAccessToken(): Promise<string | null> {
    const supabase = useSupabaseClient()
    const { data } = await supabase.auth.getSession()
    return data.session?.access_token ?? null
  }

  async function signInWithGoogle(): Promise<void> {
    const supabase = useSupabaseClient()
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
  }

  async function fetchUser(): Promise<void> {
    const token = await getAccessToken()
    if (!token) return

    try {
      const data = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      user.value = data
    } catch {
      user.value = null
    }
  }

  async function logout(): Promise<void> {
    const supabase = useSupabaseClient()
    await supabase.auth.signOut()
    user.value = null
    navigateTo('/login')
  }

  return { user, isAuthenticated, hasPartner, getAccessToken, signInWithGoogle, fetchUser, logout }
}
