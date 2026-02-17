export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],

  tailwindcss: {
    cssPath: '~/assets/css/global.css',
  },

  app: {
    baseURL: '/LNbitsBox/',
    head: {
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      title: 'LNbitsBox — Plug and play LNbits',
      meta: [
        {
          name: 'description',
          content:
            'LNbitsBox is plug-and-play LNbits in a box with self-custodial bitcoin use provided by Spark. It provides a simple, self-custodial way to accept Bitcoin payments with the Lightning Network.',
        },
        { property: 'og:title', content: 'LNbitsBox' },
        {
          property: 'og:description',
          content: 'LNbitsBox is plug-and-play LNbits in a box with self-custodial bitcoin use provided by Spark. It provides a simple, self-custodial way to accept Bitcoin payments with the Lightning Network.',
        },
        { name: 'color-scheme', content: 'light dark' },
        { name: 'theme-color', content: '#f8f8fc', media: '(prefers-color-scheme: light)' },
        { name: 'theme-color', content: '#0f0f14', media: '(prefers-color-scheme: dark)' },
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        {
          rel: 'preconnect',
          href: 'https://fonts.gstatic.com',
          crossorigin: 'anonymous',
        },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap',
        },
      ],
    },
  },

  devtools: { enabled: false },
  compatibilityDate: '2024-11-01',
})
