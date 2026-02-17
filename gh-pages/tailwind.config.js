/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        'ln-pink':       'rgb(var(--ln-pink) / <alpha-value>)',
        'ln-pink-dim':   'rgb(var(--ln-pink-dim) / <alpha-value>)',
        'ln-surface':    'rgb(var(--ln-surface) / <alpha-value>)',
        'ln-card':       'rgb(var(--ln-card) / <alpha-value>)',
        'ln-card-hover': 'rgb(var(--ln-card-hover) / <alpha-value>)',
        'ln-border':     'rgb(var(--ln-border) / <alpha-value>)',
        'ln-text':       'rgb(var(--ln-text) / <alpha-value>)',
        'ln-muted':      'rgb(var(--ln-muted) / <alpha-value>)',
      },
      fontFamily: {
        mono:    ['JetBrains Mono', 'monospace'],
        display: ['Space Grotesk', 'sans-serif'],
      },
    },
  },
}
