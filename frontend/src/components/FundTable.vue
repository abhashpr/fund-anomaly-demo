<template>
  <div class="card flex flex-col overflow-y-auto space-y-2 max-h-[750px]">
    <div class="card-header flex items-center justify-between">
      <span>Fund Performance</span>
      <div class="flex items-center gap-2">
        <button 
          v-for="filter in filters" 
          :key="filter.value"
          @click="activeFilter = filter.value"
          class="px-2 py-0.5 text-xs rounded transition-colors"
          :class="activeFilter === filter.value 
            ? 'bg-accent-blue text-white' 
            : 'text-text-secondary hover:text-text-primary'"
        >
          {{ filter.label }}
        </button>
      </div>
    </div>
    
    <div class="flex-1 overflow-auto">
      <table class="data-table">
        <thead class="sticky top-0 bg-terminal-card z-10">
          <tr>
            <th @click="sortBy('scheme_code')" class="cursor-pointer hover:text-accent-blue">
              Scheme Code {{ sortIcon('scheme_code') }}
            </th>
            <th @click="sortBy('category')" class="cursor-pointer hover:text-accent-blue">
              Category {{ sortIcon('category') }}
            </th>
            <th @click="sortBy('latest_nav')" class="cursor-pointer hover:text-accent-blue text-right">
              NAV {{ sortIcon('latest_nav') }}
            </th>
            <th @click="sortBy('daily_return')" class="cursor-pointer hover:text-accent-blue text-right">
              Change {{ sortIcon('daily_return') }}
            </th>
            <th @click="sortBy('volatility')" class="cursor-pointer hover:text-accent-blue text-right">
              Vol {{ sortIcon('volatility') }}
            </th>
            <th class="text-center">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="fund in filteredFunds" 
            :key="fund.scheme_code"
            @click="$emit('selectFund', fund.scheme_code)"
            :class="{ 'bg-accent-red/5': fund.anomaly_flag }"
          >
            <td>
              <div class="flex items-center gap-2">
                <div v-if="fund.anomaly_flag" 
                     class="w-2 h-2 rounded-full bg-accent-red animate-pulse"></div>
                <span class="font-medium text-text-primary truncate max-w-[180px]">
                  {{ fund.scheme_code }}
                </span>
              </div>
            </td>
            <td>
              <span class="badge badge-info">{{ fund.category }}</span>
            </td>
            <td class="text-right font-mono">
              {{ fund.latest_nav.toFixed(2) }}
            </td>
            <td class="text-right font-mono">
              <span :class="fund.daily_return >= 0 ? 'text-accent-green' : 'text-accent-red'">
                {{ fund.daily_return >= 0 ? '+' : '' }}{{ fund.daily_return.toFixed(2) }}%
              </span>
            </td>
            <td class="text-right font-mono text-text-secondary">
              {{ fund.volatility.toFixed(1) }}%
            </td>
            <td class="text-center">
              <span v-if="fund.anomaly_flag" class="badge badge-danger">
                ALERT
              </span>
              <span v-else class="badge badge-success">
                OK
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- Empty state -->
      <div v-if="filteredFunds.length === 0" 
           class="flex items-center justify-center h-32 text-text-muted">
        No funds found
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  funds: {
    type: Array,
    default: () => []
  }
})

defineEmits(['selectFund'])

const activeFilter = ref('all')
const sortField = ref('scheme_code')
const sortAsc = ref(true)

const filters = [
  { label: 'All', value: 'all' },
  { label: 'Anomalies', value: 'anomaly' },
  { label: 'Equity', value: 'equity' },
  { label: 'Debt', value: 'debt' },
]

const filteredFunds = computed(() => {
  let result = [...props.funds]
  
  // Apply filter
  if (activeFilter.value === 'anomaly') {
    result = result.filter(f => f.anomaly_flag)
  } else if (activeFilter.value === 'equity') {
    result = result.filter(f => 
      ['Large Cap', 'Small Cap', 'Mid Cap', 'Sectoral', 'International', 'Thematic'].includes(f.category)
    )
  } else if (activeFilter.value === 'debt') {
    result = result.filter(f => ['Debt', 'Gilt', 'Hybrid'].includes(f.category))
  }
  
  // Apply sorting
  result.sort((a, b) => {
    const aVal = a[sortField.value]
    const bVal = b[sortField.value]
    
    if (typeof aVal === 'string') {
      return sortAsc.value 
        ? aVal.localeCompare(bVal) 
        : bVal.localeCompare(aVal)
    }
    
    return sortAsc.value ? aVal - bVal : bVal - aVal
  })
  
  return result
})

function sortBy(field) {
  if (sortField.value === field) {
    sortAsc.value = !sortAsc.value
  } else {
    sortField.value = field
    sortAsc.value = true
  }
}

function sortIcon(field) {
  if (sortField.value !== field) return ''
  return sortAsc.value ? '↑' : '↓'
}
</script>
