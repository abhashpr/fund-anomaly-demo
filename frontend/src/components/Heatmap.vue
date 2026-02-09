<template>
  <div class="card h-full">
    <div class="card-header flex items-center justify-between">
      <span>Fund Heatmap</span>
      <div class="flex items-center gap-2">
        <span class="text-xs text-text-muted">Returns</span>
        <div class="flex gap-0.5">
          <div class="w-3 h-3 rounded-sm bg-red-600"></div>
          <div class="w-3 h-3 rounded-sm bg-red-400"></div>
          <div class="w-3 h-3 rounded-sm bg-gray-600"></div>
          <div class="w-3 h-3 rounded-sm bg-green-400"></div>
          <div class="w-3 h-3 rounded-sm bg-green-600"></div>
        </div>
      </div>
    </div>
    
    <div class="grid gap-2 max-h-48 overflow-auto pr-1">
      <div v-for="category in categories" :key="category" class="space-y-1">
        <div class="text-xs text-text-muted font-medium">{{ category }}</div>
        <div class="flex flex-wrap gap-1">
          <div
            v-for="fund in getFundsByCategory(category)"
            :key="fund.scheme_code"
            class="heatmap-cell relative group"
            :class="getCellClass(fund)"
            :style="{ width: '24px', height: '24px' }"
            @click="$emit('selectFund', fund.scheme_code)"
          >
            <!-- Anomaly indicator -->
            <div v-if="fund.anomaly" 
                 class="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-accent-red animate-pulse"></div>
            
            <!-- Tooltip -->
            <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 
                        bg-terminal-surface border border-terminal-border rounded text-xs 
                        opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap pointer-events-none">
              <div class="font-medium text-text-primary">{{ fund.name }}</div>
              <div class="flex items-center gap-2 text-text-secondary">
                <span :class="fund.value >= 0 ? 'text-accent-green' : 'text-accent-red'">
                  {{ fund.value >= 0 ? '+' : '' }}{{ fund.value.toFixed(2) }}%
                </span>
                <span>NAV: {{ fund.nav.toFixed(2) }}</span>
              </div>
              <div v-if="fund.anomaly" class="text-accent-red text-xs mt-1">
                ⚠️ Anomaly Detected
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Empty state -->
    <div v-if="!data || data.length === 0" class="flex items-center justify-center h-32 text-text-muted">
      Loading heatmap data...
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

defineEmits(['selectFund'])

const categories = computed(() => {
  const cats = new Set(props.data.map(f => f.category))
  return Array.from(cats).sort()
})

function getFundsByCategory(category) {
  return props.data.filter(f => f.category === category)
}

function getCellClass(fund) {
  const value = fund.value || 0
  const isAnomaly = fund.anomaly
  
  if (isAnomaly) {
    return value > 0 
      ? 'bg-amber-500/80 border-2 border-accent-yellow' 
      : 'bg-rose-500/80 border-2 border-accent-red'
  }
  
  if (value > 2) return 'bg-green-500'
  if (value > 0.5) return 'bg-green-600/70'
  if (value > -0.5) return 'bg-gray-600/50'
  if (value > -2) return 'bg-red-600/70'
  return 'bg-red-500'
}
</script>
