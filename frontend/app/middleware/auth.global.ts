export default defineNuxtRouteMiddleware((to) => {
  const { isAuthenticated, hasPartner } = useAuth()

  const publicPages = ['/login', '/auth/callback']
  if (publicPages.includes(to.path)) {
    if (isAuthenticated.value && hasPartner.value) {
      return navigateTo('/rules')
    }
    return
  }

  if (to.path === '/invite') {
    if (!isAuthenticated.value) {
      return navigateTo('/login')
    }
    if (hasPartner.value) {
      return navigateTo('/rules')
    }
    return
  }

  if (!isAuthenticated.value) {
    return navigateTo('/login')
  }

  if (!hasPartner.value) {
    return navigateTo('/invite')
  }
})
