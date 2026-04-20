// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  ssr: false,
  compatibilityDate: '2024-04-18',
  devtools: { enabled: false },
  css: ['./assets/css/main.css'],
  app: {
    head: {
      title: 'Grocery Store Management',
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap' }
      ]
    }
  },
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000'
    }
  }
})
