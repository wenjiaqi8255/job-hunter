/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0AEDC7',
        primaryHover: '#09dcb5',
        primaryLight: '#DBF2F0',
        pageBackground: '#F8FAF8',
        cardBackground: '#FFFFFF',
        sidebarBackground: '#FFFFFF',
        textPrimary: '#121717',
        textSecondary: '#6B827D',
        textMuted: '#6B827D',
        border: '#E5E8EB',
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
        info: '#1098F7',
        status: {
          applied: {
            bg: '#D1FAE5',
            text: '#065F46',
          },
          interviewing: {
            bg: '#DBEAFE',
            text: '#1E40AF',
          },
          offer: {
            bg: '#FEF3C7',
            text: '#92400E',
          },
          rejected: {
            bg: '#FEE2E2',
            text: '#991B1B',
          },
          viewed: {
            bg: '#BFDBFE',
            text: '#1E40AF',
          },
          not_applied: {
            bg: '#EBEBEB',
            text: '#121717',
          },
        },
      },
      spacing: {
        '14': '3.5rem', // 56px navbar height
      },
      borderRadius: {
        'xl': '1.25rem', // 20px
        'lg': '0.625rem', // 10px
      }
    },
  },
  plugins: [],
}
