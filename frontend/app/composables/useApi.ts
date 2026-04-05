export const useApi = () => {
  const { getAccessToken, logout } = useAuth()
  const config = useRuntimeConfig()

  async function api<T>(path: string, options: any = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers || {}),
    }

    const token = await getAccessToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
      options.body = JSON.stringify(options.body)
    }

    try {
      return await $fetch<T>(`${config.public.apiBase}${path}`, {
        ...options,
        headers,
      })
    } catch (error: any) {
      if (error?.status === 401 || error?.statusCode === 401) {
        await logout()
      }
      throw error
    }
  }

  return { api }
}
