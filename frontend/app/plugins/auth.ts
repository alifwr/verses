export default defineNuxtPlugin(async () => {
  const { fetchUser, token, refresh, refreshToken } = useAuth()
  if (token.value) {
    await fetchUser()
  }
  if (!token.value && refreshToken.value) {
    await refresh()
  }
})
