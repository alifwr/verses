interface User {
  id: number
  username: string
  display_name: string
  partner: {
    id: number
    username: string
    display_name: string
    is_online: boolean
  } | null
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export const useAuth = () => {
  const user = useState<User | null>('auth-user', () => null)
  const token = useCookie('verse-token')
  const refreshToken = useCookie('verse-refresh-token')
  const config = useRuntimeConfig()

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  async function login(username: string, password: string): Promise<void> {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const data = await $fetch<LoginResponse>(`${config.public.apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    })

    token.value = data.access_token
    refreshToken.value = data.refresh_token
    await fetchUser()
  }

  async function fetchUser(): Promise<void> {
    if (!token.value) return
    try {
      const data = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      user.value = data
    } catch {
      token.value = null
      refreshToken.value = null
      user.value = null
    }
  }

  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const data = await $fetch<{ access_token: string }>(`${config.public.apiBase}/auth/refresh`, {
        method: 'POST',
        body: { refresh_token: refreshToken.value },
      })
      token.value = data.access_token
      await fetchUser()
      return true
    } catch {
      logout()
      return false
    }
  }

  function logout(): void {
    token.value = null
    refreshToken.value = null
    user.value = null
    navigateTo('/login')
  }

  return { user, token, isAuthenticated, login, logout, fetchUser, refresh }
}
