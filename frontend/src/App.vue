<template>
  <div class="min-h-screen bg-terminal-bg transition-colors duration-300">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

// Initialize theme on app load
onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  const html = document.documentElement
  
  if (savedTheme === 'light') {
    html.classList.add('light')
    html.classList.remove('dark')
  } else {
    html.classList.add('dark')
    html.classList.remove('light')
  }
})
</script>

<style>
/* Global scrollbar styling for trading terminal look */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #0d1117;
}

::-webkit-scrollbar-thumb {
  background: #21262d;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #30363d;
}
</style>
