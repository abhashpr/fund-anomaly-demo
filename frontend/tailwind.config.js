/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Trading terminal dark theme
        terminal: {
          bg: '#0a0e14',
          surface: '#0d1117',
          card: '#161b22',
          border: '#21262d',
          hover: '#1c2128',
        },
        accent: {
          green: '#00ff88',
          red: '#ff3366',
          yellow: '#ffcc00',
          blue: '#00aaff',
          purple: '#aa66ff',
          cyan: '#00ffcc',
        },
        text: {
          primary: '#e6edf3',
          secondary: '#8b949e',
          muted: '#484f58',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Monaco', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.5s ease-out',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 255, 136, 0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 255, 136, 0.6)' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      boxShadow: {
        'neon-green': '0 0 10px rgba(0, 255, 136, 0.5)',
        'neon-red': '0 0 10px rgba(255, 51, 102, 0.5)',
        'neon-blue': '0 0 10px rgba(0, 170, 255, 0.5)',
      }
    },
  },
  plugins: [],
}
