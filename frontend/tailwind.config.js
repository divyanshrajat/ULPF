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
          // Repurposed as a light neutral tint (was a dark surface shade).
          // Only touches this one non-standard shade — Tailwind's real
          // slate-50..950 scale is untouched, so text-slate-400/500 etc.
          // elsewhere keep working as ordinary mid-grey text.
          850: '#EFF1EE',
        },
        brand: {
          // These are picked as the DARK/text-appropriate value for each
          // status. Every existing bg-brand-x/10, /20, /35 opacity usage
          // across Jobs/Sessions/Events/Rules/ApiKeys/Onboarding/Dashboard
          // automatically becomes a correct pale tint on the light page
          // background once these change — no per-page edits needed for
          // anything using these tokens.
          cyan: '#2B3350',   // Primary accent (was bright cyan)
          purple: '#5C4F7A', // AI / LLM accent (muted plum)
          green: '#2A4B3A',  // Verified / success
          amber: '#7A5D22',  // Pending / review / drift
          red: '#7C2E22',    // Failure / error / disabled
          blue: '#2B3350',   // Info — folded into the primary accent
        }
      },
      fontFamily: {
        sans: ['Public Sans', 'system-ui', 'sans-serif'],
        serif: ['Newsreader', 'serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'monospace'],
      }
    },
  },
  plugins: [],
}
