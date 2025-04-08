/** @type {import('tailwindcss').Config} */
export default {
    content: ['./src/**/*.{html,js,svelte}'],
    theme: {
      extend: {
        colors: {
          background: 'rgb(17, 17, 18)',
          surface: 'rgb(23, 23, 25)',
          accent: 'rgb(186, 108, 77)',
          border: '#2d3748',
          'nav-hover': '#1f2937',
          'nav-active': '#2d3748',
          'text-primary': '#f3f4f6',
          'text-secondary': '#9ca3af',
        },
      },
    },
    plugins: [],
  }