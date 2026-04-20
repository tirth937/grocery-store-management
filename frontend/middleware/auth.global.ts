export default defineNuxtRouteMiddleware((to, from) => {
  // If we are on the client side
  if (import.meta.client) {
    const token = localStorage.getItem('auth_token')
    
    // Allow access to login page
    if (to.path === '/login') {
      if (token) return navigateTo('/') // If already logged in, go to home
      return
    }

    // Protect all other routes
    if (!token) {
      console.log('No auth token found, redirecting to login...')
      return navigateTo('/login')
    }
  }
})
