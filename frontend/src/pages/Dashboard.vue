<template>
  <div class="min-h-screen bg-terminal-bg flex flex-col">
    <!-- Header -->
    <HeaderStats 
      :stats="store.stats" 
      :ws-connected="store.wsConnected"
      :last-update="store.lastUpdate"
    />
    
    <!-- Main content -->
    <div class="flex-1 p-4 overflow-hidden">
      <div class="h-full grid grid-cols-12 gap-4">
        
        <!-- Left column: Heatmap + Signal Feed -->
        <div class="col-span-3 flex flex-col gap-4 min-h-0">
          <!-- Heatmap -->
          <div class="flex-shrink-0 h-64">
            <Heatmap 
              :data="heatmapCells" 
              @select-fund="selectFund"
            />
          </div>
          
          <!-- Signal Feed -->
          <div class="flex-1 min-h-0">
            <SignalFeed 
              :signals="store.signals" 
              @select-fund="selectFund"
            />
          </div>
        </div>
        
        <!-- Center column: Table or Chart -->
        <div class="col-span-6 min-h-0">
          <Transition name="fade" mode="out-in">
            <FundChart 
              v-if="store.selectedFundDetails"
              :fund="store.selectedFundDetails"
              @close="store.clearSelectedFund()"
            />
            <FundTable 
              v-else
              :funds="store.funds"
              @select-fund="selectFund"
            />
          </Transition>
        </div>
        
        <!-- Right column: Stats panel -->
        <div class="col-span-3 flex flex-col gap-4 min-h-0">
          <!-- Quick stats -->
          <div class="card">
            <div class="card-header">Market Overview</div>
            <div class="grid grid-cols-2 gap-4">
              <div class="text-center p-3 bg-terminal-surface rounded-lg">
                <div class="text-2xl font-bold text-accent-green">
                  {{ gainersCount }}
                </div>
                <div class="text-xs text-text-muted">Gainers</div>
              </div>
              <div class="text-center p-3 bg-terminal-surface rounded-lg">
                <div class="text-2xl font-bold text-accent-red">
                  {{ losersCount }}
                </div>
                <div class="text-xs text-text-muted">Losers</div>
              </div>
            </div>
          </div>
          
          <!-- Category breakdown -->
          <div class="card flex-1 overflow-auto">
            <div class="card-header">Category Stats</div>
            <div class="space-y-3">
              <div 
                v-for="cat in categoryStats" 
                :key="cat.category"
                class="flex items-center justify-between p-2 bg-terminal-surface rounded"
              >
                <div>
                  <div class="text-sm font-medium text-text-primary">{{ cat.category }}</div>
                  <div class="text-xs text-text-muted">{{ cat.count }} funds</div>
                </div>
                <div class="text-right">
                  <div 
                    class="text-sm font-mono"
                    :class="(cat.avg_return || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'"
                  >
                    {{ ((cat.avg_return || 0) * 100).toFixed(2) }}%
                  </div>
                  <div class="text-xs text-text-muted">avg 30d return</div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Top movers -->
          <div class="card">
            <div class="card-header">Top Movers</div>
            <div class="space-y-2">
              <div 
                v-for="fund in topMovers" 
                :key="fund.scheme_code"
                class="flex items-center justify-between p-2 bg-terminal-surface rounded cursor-pointer hover:bg-terminal-hover transition-colors"
                @click="selectFund(fund.scheme_code)"
              >
                <div class="flex items-center gap-2">
                  <span class="text-lg">{{ fund.daily_return >= 0 ? '📈' : '📉' }}</span>
                  <span class="text-sm text-text-primary truncate max-w-[120px]">
                    {{ fund.fund_name }}
                  </span>
                </div>
                <span 
                  class="text-sm font-mono"
                  :class="fund.daily_return >= 0 ? 'text-accent-green' : 'text-accent-red'"
                >
                  {{ fund.daily_return >= 0 ? '+' : '' }}{{ fund.daily_return.toFixed(2) }}%
                </span>
              </div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
    
    <!-- Loading overlay -->
    <Transition name="fade">
      <div 
        v-if="store.isLoading" 
        class="fixed inset-0 bg-terminal-bg/80 flex items-center justify-center z-50"
      >
        <div class="text-center">
          <div class="w-12 h-12 border-4 border-accent-green border-t-transparent rounded-full animate-spin mx-auto"></div>
          <div class="text-text-secondary mt-4">Loading market data...</div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/store/dashboard'
import HeaderStats from '@/components/HeaderStats.vue'
import Heatmap from '@/components/Heatmap.vue'
import FundTable from '@/components/FundTable.vue'
import FundChart from '@/components/FundChart.vue'
import SignalFeed from '@/components/SignalFeed.vue'

const store = useDashboardStore()

// Computed properties
const heatmapCells = computed(() => {
  if (!store.heatmapData?.data) return []
  return store.heatmapData.data
})

const categoryStats = computed(() => {
  return store.overview?.category_stats || []
})

const gainersCount = computed(() => {
  return store.funds.filter(f => f.daily_return > 0).length
})

const losersCount = computed(() => {
  return store.funds.filter(f => f.daily_return < 0).length
})

const topMovers = computed(() => {
  return [...store.funds]
    .sort((a, b) => Math.abs(b.daily_return) - Math.abs(a.daily_return))
    .slice(0, 5)
})

// Methods
function selectFund(schemeCode) {
  store.fetchFundDetails(schemeCode)
}

// Lifecycle
let refreshInterval = null

onMounted(async () => {
  // Load initial data
  await store.loadAllData()
  
  // Connect WebSocket for live updates
  store.connectWebSocket()
  
  // Refresh data periodically
  refreshInterval = setInterval(() => {
    store.fetchFunds()
    store.fetchOverview()
  }, 60000) // Every minute
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  store.disconnectWebSocket()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
