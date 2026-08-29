/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          850: '#151e2e',
          900: '#0f172a',
          950: '#0b0f19',
        },
        brand: {
          cyan: '#22d3ee',   // Primary accent
          purple: '#a855f7', // AI accent
          green: '#22c55e',  // Verified/Success
          amber: '#f59e0b',  // Review/Drift
          red: '#ef4444',    // Failure/Error
          blue: '#3b82f6',   // Info
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'ui-monospace', 'monospace'],
      }
    },
  },
  plugins: [],
}
