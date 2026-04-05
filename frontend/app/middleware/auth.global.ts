export default defineNuxtRouteMiddleware((to) => {
  // Skip auth checks during SSR — session only exists client-side
  if (import.meta.server) return

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
      // Save invite code so it survives the login redirect
      const code = to.query.code as string
      if (code) {
        localStorage.setItem('verse-invite-code', code)
      }
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
