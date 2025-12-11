/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand - Modern Blue for a clean, professional feel
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb', // Primary Action
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
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
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02)',
      }
    },
  },
  plugins: [],
}
