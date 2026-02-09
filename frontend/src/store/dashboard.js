import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getFunds, getOverview, getSignals, getHeatmapData, getFundDetails, wsManager } from '@/services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const funds = ref([])
  const overview = ref(null)
  const signals = ref([])
  const heatmapData = ref(null)
  const selectedFund = ref(null)
  const selectedFundDetails = ref(null)
  const isLoading = ref(false)
  const wsConnected = ref(false)
  const lastUpdate = ref(null)

  // Getters
  const anomalyFunds = computed(() => 
    funds.value.filter(f => f.anomaly_flag)
  )

  const fundsByCategory = computed(() => {
    const grouped = {}
    funds.value.forEach(fund => {
      if (!grouped[fund.category]) {
        grouped[fund.category] = []
      }
      grouped[fund.category].push(fund)
    })
    return grouped
  })

  const recentSignals = computed(() => 
    signals.value.slice(0, 10)
  )

  const stats = computed(() => ({
    totalFunds: overview.value?.total_funds || 0,
    anomalyCount: overview.value?.funds_in_anomaly || 0,
    avgChange: overview.value?.avg_nav_change || 0,
    avgVolatility: overview.value?.avg_volatility || 0,
  }))

  // Actions
  async function fetchFunds() {
    try {
      funds.value = await getFunds({ limit: 50 })
    } catch (error) {
      console.error('Failed to fetch funds:', error)
    }
  }

  async function fetchOverview() {
    try {
      overview.value = await getOverview()
    } catch (error) {
      console.error('Failed to fetch overview:', error)
    }
  }

  async function fetchSignals() {
    try {
      signals.value = await getSignals({ limit: 20 })
    } catch (error) {
      console.error('Failed to fetch signals:', error)
    }
  }

  async function fetchHeatmapData() {
    try {
      if (funds.value.length > 0) {
        heatmapData.value = {
          data: funds.value.map(fund => ({
            scheme_code: fund.scheme_code,
            name: fund.fund_name,
            category: fund.category,
            value: fund.daily_return,
            nav: fund.latest_nav,
            anomaly: fund.anomaly_flag,
            zscore: fund.zscore,
          })),
          categories: [...new Set(funds.value.map(f => f.category))],
        }
        return
      }

      heatmapData.value = await getHeatmapData()
    } catch (error) {
      console.error('Failed to fetch heatmap data:', error)
    }
  }

  async function fetchFundDetails(schemeCode) {
    try {
      selectedFund.value = schemeCode
      selectedFundDetails.value = await getFundDetails(schemeCode)
    } catch (error) {
      console.error('Failed to fetch fund details:', error)
    }
  }

  async function loadAllData() {
    isLoading.value = true
    try {
      await fetchFunds()
      await fetchOverview()
      await fetchSignals()
      await fetchHeatmapData()
      lastUpdate.value = new Date().toISOString()
    } finally {
      isLoading.value = false
    }
  }

  function connectWebSocket() {
    wsManager.connect()

    wsManager.on('connected', () => {
      wsConnected.value = true
    })

    wsManager.on('disconnected', () => {
      wsConnected.value = false
    })

    wsManager.on('nav_update', (data) => {
      // Update fund in list
      const index = funds.value.findIndex(f => f.scheme_code === data.scheme_code)
      if (index !== -1) {
        funds.value[index] = {
          ...funds.value[index],
          latest_nav: data.nav,
          daily_return: data.change_pct,
          anomaly_flag: data.is_anomaly,
          zscore: data.zscore,
        }
      }
      lastUpdate.value = new Date().toISOString()
    })

    wsManager.on('anomaly', (data) => {
      // Add to signals feed
      signals.value.unshift({
        id: data.id,
        timestamp: data.timestamp || new Date().toISOString(),
        type: data.severity === 'high' ? 'critical' : 'warning',
        // icon: data.direction === 'up' ? '📈' : '📉',
        icon: data.direction === 'up' ? 'pi pi-arrow-up' : 'pi pi-arrow-down',
        color: data.severity === 'high' ? 'red' : 'yellow',
        title: data.signal,
        fund_name: data.fund_name,
        scheme_code: data.scheme_code,
        category: data.category,
        message: data.explanation,
        severity: data.severity,
        confidence: data.confidence,
        metrics: {
          nav: data.nav,
          zscore: data.zscore,
        }
      })

      // Keep only last 40 signals
      if (signals.value.length > 40) {
        signals.value = signals.value.slice(0, 40)
      }

      // Update anomaly count
      if (overview.value) {
        overview.value.funds_in_anomaly = anomalyFunds.value.length
      }
    })

    wsManager.on('market_summary', (data) => {
      if (overview.value) {
        overview.value.total_funds = data.total_funds
        overview.value.funds_in_anomaly = data.anomaly_count
      }
    })
  }

  function disconnectWebSocket() {
    wsManager.disconnect()
    wsConnected.value = false
  }

  function clearSelectedFund() {
    selectedFund.value = null
    selectedFundDetails.value = null
  }

  return {
    // State
    funds,
    overview,
    signals,
    heatmapData,
    selectedFund,
    selectedFundDetails,
    isLoading,
    wsConnected,
    lastUpdate,
    // Getters
    anomalyFunds,
    fundsByCategory,
    recentSignals,
    stats,
    // Actions
    fetchFunds,
    fetchOverview,
    fetchSignals,
    fetchHeatmapData,
    fetchFundDetails,
    loadAllData,
    connectWebSocket,
    disconnectWebSocket,
    clearSelectedFund,
  }
})
