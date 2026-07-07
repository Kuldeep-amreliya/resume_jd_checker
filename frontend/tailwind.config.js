/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0F1512',
        paper: '#F7F5EF',
        'paper-raised': '#FFFFFF',
        pine: '#2B6E5C',
        'pine-dim': '#E2EDE9',
        rust: '#B5482A',
        'rust-dim': '#F5E3DD',
        stone: '#8A8577',
        'stone-dim': '#EEECE5',
        hair: '#DED8C4',
        'hair-strong': '#C9C2A8',
        amber: '#C98A2C',
        'amber-dim': '#FDF1DE',
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
