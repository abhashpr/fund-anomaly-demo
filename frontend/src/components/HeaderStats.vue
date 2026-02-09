<template>
  <div class="p-4 border-b border-terminal-border bg-terminal-surface">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full bg-accent-green animate-pulse"></div>
          <h1 class="text-xl font-bold">
            <span class="text-accent-green">FUND</span>
            <span class="text-text-primary">MONITOR</span>
          </h1>
        </div>
        <span class="text-xs text-text-muted font-mono">AI-Powered Anomaly Detection</span>
      </div>
      
      <div class="flex items-center gap-6">
        <!-- Stats -->
        <div class="flex items-center gap-6">
          <div class="text-center">
            <div class="stat-value text-accent-blue">{{ stats.totalFunds }}</div>
            <div class="stat-label">FUNDS</div>
          </div>
          
          <div class="text-center">
            <div class="stat-value" :class="stats.anomalyCount > 0 ? 'text-accent-red' : 'text-accent-green'">
              {{ stats.anomalyCount }}
            </div>
            <div class="stat-label">ANOMALIES</div>
          </div>
          
          <div class="text-center">
            <div class="stat-value" :class="stats.avgChange >= 0 ? 'text-accent-green' : 'text-accent-red'">
              {{ stats.avgChange >= 0 ? '+' : '' }}{{ stats.avgChange.toFixed(2) }}%
            </div>
            <div class="stat-label">AVG 30D</div>
          </div>
          
          <div class="text-center">
            <div class="stat-value text-accent-yellow">{{ stats.avgVolatility.toFixed(1) }}%</div>
            <div class="stat-label">VOL 30D</div>
          </div>
        </div>
        
        <!-- Connection status -->
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full" 
             :class="wsConnected ? 'bg-accent-green/10' : 'bg-accent-red/10'">
          <div class="w-2 h-2 rounded-full" 
               :class="wsConnected ? 'bg-accent-green animate-pulse' : 'bg-accent-red'"></div>
          <span class="text-xs font-mono" :class="wsConnected ? 'text-accent-green' : 'text-accent-red'">
            {{ wsConnected ? 'LIVE' : 'OFFLINE' }}
          </span>
        </div>
        
        <!-- Last update -->
        <div class="text-xs text-text-muted font-mono">
          {{ formattedTime }}
        </div>
        
        <!-- Theme toggle -->
        <ThemeToggle />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import ThemeToggle from './ThemeToggle.vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({
      totalFunds: 0,
      anomalyCount: 0,
      avgChange: 0,
      avgVolatility: 0,
    })
  },
  wsConnected: {
    type: Boolean,
    default: false
  },
  lastUpdate: {
    type: String,
    default: null
  }
})

const currentTime = ref(new Date())
let timeInterval = null

const formattedTime = computed(() => {
  return currentTime.value.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
})

onMounted(() => {
  timeInterval = setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>
