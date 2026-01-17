/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand - Green primary theme
        brand: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#4CA154', // Primary
          600: '#3d8b47',
          700: '#2f6e38',
          800: '#27592e',
          900: '#1e4423',
          950: '#142e17',
        },
        // Surface - Clean slates for backgrounds
        surface: {
          50: '#f8fafc',
          100: '#f1f5f9', // App Background
          200: '#e2e8f0', // Borders
          300: '#cbd5e1',
          400: '#94a3b8', // Icons/Muted Text
          500: '#64748b',
          600: '#475569', // Subtitles
          700: '#334155',
          800: '#1e293b', // Headings
          900: '#0f172a',
          950: '#020617',
        },
        // Iced Snow White - Elegant light theme
        snow: {
          50: '#fafbfc',
          100: '#f7f9fc',
          200: '#f3f6fa',
          300: '#eff3f8',
        },
        // Functional colors
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          700: '#15803d',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          700: '#b91c1c',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          700: '#b45309',
        }
      },
      fontFamily: {
        sans: [
          'Inter', 
          '-apple-system', 
          'BlinkMacSystemFont', 
          'Segoe UI', 
          'Roboto', 
          'Helvetica Neue', 
          'Arial', 
          'sans-serif'
        ],
      },
      boxShadow: {
        'soft': '0 2px 10px rgba(0, 0, 0, 0.03)',
        'card': '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.08)',
        'sidebar': '2px 0 8px rgba(0, 0, 0, 0.03)',
      }
    },
  },
  plugins: [],
}
