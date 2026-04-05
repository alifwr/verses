export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  modules: ['@nuxtjs/tailwindcss', '@nuxtjs/google-fonts'],

  css: ['~/assets/css/main.css'],

  tailwindcss: {
    cssPath: '~/assets/css/main.css',
  },

  googleFonts: {
    families: {
      'Playfair Display': [400, 600, 700],
      'Inter': [300, 400, 500, 600],
    },
  },

  runtimeConfig: {
    public: {
      apiBase: 'https://verse-api.alifpunya.com',
      supabaseUrl: '',
      supabaseAnonKey: '',
    },
  },
})
