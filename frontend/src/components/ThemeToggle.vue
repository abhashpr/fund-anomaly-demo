<template>
  <button 
    @click="toggleTheme"
    class="theme-toggle p-2 rounded-lg transition-all duration-300"
    :class="isDark ? 'bg-terminal-surface hover:bg-terminal-hover' : 'bg-gray-200 hover:bg-gray-300'"
    :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
  >
    <Transition name="theme-icon" mode="out-in">
      <span v-if="isDark" key="dark" class="text-lg">🌙</span>
      <span v-else key="light" class="text-lg">☀️</span>
    </Transition>
  </button>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const isDark = ref(true)

function toggleTheme() {
  isDark.value = !isDark.value
  applyTheme()
}

function applyTheme() {
  const html = document.documentElement
  if (isDark.value) {
    html.classList.add('dark')
    html.classList.remove('light')
  } else {
    html.classList.remove('dark')
    html.classList.add('light')
  }
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

onMounted(() => {
  // Check localStorage or system preference
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme) {
    isDark.value = savedTheme === 'dark'
  } else {
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  applyTheme()
})
</script>

<style scoped>
.theme-icon-enter-active,
.theme-icon-leave-active {
  transition: all 0.2s ease;
}

.theme-icon-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.5);
}

.theme-icon-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.5);
}
</style>
