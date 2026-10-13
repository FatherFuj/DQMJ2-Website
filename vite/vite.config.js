import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
  build: {
    rolldownOptions: {
      input: {
        home: resolve(import.meta.dirname, 'index.html'),
        monsters: resolve(import.meta.dirname, 'pages/monsters.html'),
        monsterDetail: resolve(import.meta.dirname, 'pages/monster-detail.html'),
        favorites: resolve(import.meta.dirname, 'pages/favorites.html'),
        synthesis: resolve(import.meta.dirname, 'pages/synthesis.html'),
        skills: resolve(import.meta.dirname, 'pages/skills.html'),
      }
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './tests/setup.js',
    include: ['tests/**/*.test.js']
  }
})
