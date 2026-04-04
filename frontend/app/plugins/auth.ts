export default defineNuxtPlugin(async () => {
  const { fetchUser, token } = useAuth()
  if (token.value) {
    await fetchUser()
  }
})
