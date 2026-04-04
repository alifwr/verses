export const useApi = () => {
  const { token, refresh, logout } = useAuth()
  const config = useRuntimeConfig()

  async function api<T>(path: string, options: any = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers || {}),
    }

    if (token.value) {
      headers['Authorization'] = `Bearer ${token.value}`
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
        const refreshed = await refresh()
        if (refreshed) {
          headers['Authorization'] = `Bearer ${token.value}`
          return await $fetch<T>(`${config.public.apiBase}${path}`, {
            ...options,
            headers,
          })
        }
        logout()
      }
      throw error
    }
  }

  return { api }
}
