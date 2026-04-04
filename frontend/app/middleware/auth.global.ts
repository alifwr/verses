export default defineNuxtRouteMiddleware((to) => {
  const { isAuthenticated } = useAuth()

  if (to.path === '/login') {
    if (isAuthenticated.value) {
      return navigateTo('/rules')
    }
    return
  }

  if (!isAuthenticated.value) {
    return navigateTo('/login')
  }
})
