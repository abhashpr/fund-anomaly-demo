<template>
  <div class="card h-full flex flex-col">
    <div class="card-header flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span><i class="pi pi-bell mr-2"></i>Signal Feed</span>
        <div v-if="signals.length > 0" class="flex items-center gap-1">
          <div class="w-2 h-2 rounded-full bg-accent-green animate-pulse"></div>
          <span class="text-xs text-accent-green">LIVE</span>
        </div>
      </div>
      <span class="text-xs text-text-muted">{{ signals.length }} events</span>
    </div>
    
    <div class="flex-1 overflow-y-auto space-y-2 signal-feed-scroll max-h-[400px]">
      <TransitionGroup name="slide">
        <div 
          v-for="signal in signals" 
          :key="signal.id"
          class="signal-item"
          :class="getSignalBorderClass(signal)"
          @click="$emit('selectFund', signal.scheme_code)"
        >
          <!-- Icon -->
          <div class="flex-shrink-0">
            <i 
              v-if="signal.icon && signal.icon.startsWith('pi')" 
              :class="[signal.icon, getIconColorClass(signal)]"
              class="text-sm font-bold"
            ></i>
            <span v-else class="text-xl">{{ signal.icon || getDefaultIcon(signal) }}</span>
          </div>
          
          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-text-primary truncate">
                {{ signal.title || signal.fund_name }}
              </span>
              <span 
                class="badge text-[10px]"
                :class="getSeverityClass(signal.severity)"
              >
                {{ signal.severity?.toUpperCase() || 'INFO' }}
              </span>
            </div>
            
            <div class="text-xs text-text-secondary mt-0.5 truncate">
              {{ signal.message }}
            </div>
            
            <div class="flex items-center gap-3 mt-1.5 text-xs">
              <span class="text-text-muted">{{ signal.category }}</span>
              <span class="font-mono" :class="getChangeClass(signal.metrics?.change)">
                {{ formatChange(signal.metrics?.change) }}
              </span>
              <span class="text-text-muted font-mono">
                z={{ signal.metrics?.zscore || signal.zscore }}
              </span>
              <span v-if="signal.confidence" class="text-accent-purple">
                {{ (signal.confidence * 100).toFixed(0) }}% conf
              </span>
            </div>
          </div>
          
          <!-- Timestamp -->
          <div class="flex-shrink-0 text-xs text-text-muted font-mono">
            {{ formatTime(signal.timestamp) }}
          </div>
        </div>
      </TransitionGroup>
      
      <!-- Empty state -->
      <div v-if="signals.length === 0" 
           class="flex flex-col items-center justify-center h-full text-text-muted py-8">
        <div class="text-4xl mb-2"><i class="pi pi-info-circle"></i></div>
        <div>No signals yet</div>
        <div class="text-xs mt-1">Waiting for market activity...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  signals: {
    type: Array,
    default: () => []
  }
})

defineEmits(['selectFund'])

function getDefaultIcon(signal) {
  if (signal.type === 'critical' || signal.severity === 'high') return '🚨'
  if (signal.direction === 'up') return '📈'
  if (signal.direction === 'down') return '📉'
  return '⚡'
}

function getIconColorClass(signal) {
  // Check if it's an up or down arrow icon
  if (signal.icon?.includes('arrow-up')) return 'text-accent-green'
  if (signal.icon?.includes('arrow-down')) return 'text-accent-red'
  // Fallback based on severity
  if (signal.severity === 'high') return 'text-accent-red'
  return 'text-accent-yellow'
}

function getSignalBorderClass(signal) {
  if (signal.severity === 'high' || signal.type === 'critical') {
    return 'border-l-2 border-l-accent-red'
  }
  if (signal.severity === 'medium' || signal.type === 'warning') {
    return 'border-l-2 border-l-accent-yellow'
  }
  return 'border-l-2 border-l-accent-blue'
}

function getSeverityClass(severity) {
  switch(severity) {
    case 'high': return 'badge-danger'
    case 'medium': return 'badge-warning'
    default: return 'badge-info'
  }
}

function getChangeClass(change) {
  if (!change && change !== 0) return 'text-text-muted'
  return change >= 0 ? 'text-accent-green' : 'text-accent-red'
}

function formatChange(change) {
  if (!change && change !== 0) return '--'
  return (change >= 0 ? '+' : '') + change.toFixed(2) + '%'
}

function formatTime(timestamp) {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}
</script>

<style scoped>
.slide-enter-active {
  transition: all 0.3s ease-out;
}

.slide-leave-active {
  transition: all 0.2s ease-in;
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* Custom scrollbar for signal feed */
.signal-feed-scroll {
  scrollbar-width: thin;
  scrollbar-color: #3a3a4a #1a1a2e;
}

.signal-feed-scroll::-webkit-scrollbar {
  width: 8px;
}

.signal-feed-scroll::-webkit-scrollbar-track {
  background: #1a1a2e;
  border-radius: 4px;
}

.signal-feed-scroll::-webkit-scrollbar-thumb {
  background: #3a3a4a;
  border-radius: 4px;
}

.signal-feed-scroll::-webkit-scrollbar-thumb:hover {
  background: #4a4a5a;
}
</style>
