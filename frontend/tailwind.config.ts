import type { Config } from 'tailwindcss'

export default {
  content: [
    './app/components/**/*.{vue,ts}',
    './app/layouts/**/*.vue',
    './app/pages/**/*.vue',
    './app/app.vue',
  ],
  theme: {
    extend: {
      colors: {
        verse: {
          bg: '#F5F5F5',
          slate: '#6B7FA3',
          gold: '#C5A55A',
          text: '#2D3748',
          rose: '#B07D8E',
          'slate-light': '#E8ECF1',
          'gold-light': '#F5ECD7',
        },
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
} satisfies Config
