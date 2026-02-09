<template>
  <div class="card h-full flex flex-col">
    <div class="card-header flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button @click="$emit('close')" class="text-text-muted hover:text-text-primary">
          ← Back
        </button>
        <span class="text-text-primary font-medium">{{ fund?.fund_name || 'Fund Details' }}</span>
        <span v-if="fund?.anomaly_flag" class="badge badge-danger">ANOMALY</span>
      </div>
      <div class="flex items-center gap-4 text-sm">
        <div>
          <span class="text-text-muted">NAV:</span>
          <span class="font-mono text-text-primary ml-1">{{ fund?.latest_nav?.toFixed(2) }}</span>
        </div>
        <div>
          <span class="text-text-muted">Return:</span>
          <span class="font-mono ml-1" :class="(fund?.total_return || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'">
            {{ (fund?.total_return || 0) >= 0 ? '+' : '' }}{{ (fund?.total_return || 0).toFixed(2) }}%
          </span>
        </div>
        <div>
          <span class="text-text-muted">Volatility:</span>
          <span class="font-mono text-accent-yellow ml-1">{{ (fund?.volatility || 0).toFixed(1) }}%</span>
        </div>
      </div>
    </div>
    
    <div class="flex-1 min-h-0">
      <div ref="chartRef" class="w-full h-64 md:h-72"></div>
    </div>
    
    <!-- Risk metrics -->
    <div v-if="fund?.risk_metrics" class="border-t border-terminal-border pt-3 mt-2">
      <div class="grid grid-cols-5 gap-4 text-center">
        <div>
          <div class="text-lg font-mono text-accent-yellow">{{ fund.risk_metrics.volatility }}%</div>
          <div class="text-xs text-text-muted">Volatility</div>
        </div>
        <div>
          <div class="text-lg font-mono text-accent-red">{{ fund.risk_metrics.max_drawdown }}%</div>
          <div class="text-xs text-text-muted">Max Drawdown</div>
        </div>
        <div>
          <div class="text-lg font-mono text-accent-blue">{{ fund.risk_metrics.sharpe_estimate }}</div>
          <div class="text-xs text-text-muted">Sharpe Est.</div>
        </div>
        <div>
          <div class="text-lg font-mono text-text-primary">{{ fund.risk_metrics.anomaly_frequency }}%</div>
          <div class="text-xs text-text-muted">Anomaly Freq</div>
        </div>
        <div>
          <div class="text-lg font-mono" 
               :class="getRiskColor(fund.risk_metrics.risk_score)">
            {{ fund.risk_metrics.risk_score }}
          </div>
          <div class="text-xs text-text-muted">Risk Score</div>
        </div>
      </div>
    </div>
    
    <!-- Anomaly list -->
    <div v-if="fund?.anomalies?.length" class="border-t border-terminal-border pt-3 mt-2">
      <div class="text-xs text-text-muted mb-2">Recent Anomalies ({{ fund.anomaly_count }})</div>
      <div class="flex flex-wrap gap-2">
        <div 
          v-for="(anomaly, idx) in fund.anomalies.slice(0, 5)" 
          :key="idx"
          class="px-2 py-1 rounded text-xs"
          :class="anomaly.severity === 'high' ? 'bg-accent-red/20 text-accent-red' : 'bg-accent-yellow/20 text-accent-yellow'"
        >
          {{ anomaly.date }} 
          <span :class="anomaly.direction === 'up' ? 'text-accent-green' : 'text-accent-red'">
            {{ anomaly.direction === 'up' ? '↑' : '↓' }}
          </span>
          z={{ anomaly.zscore }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  fund: {
    type: Object,
    default: null
  }
})

defineEmits(['close'])

const chartRef = ref(null)
let chart = null

function initChart() {
  if (!chartRef.value || !props.fund?.history) return
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value, 'dark')
  
  const history = props.fund.history
  const dates = history.map(h => h.date)
  const navData = history.map(h => h.nav)
  const returns = history.map(h => h.daily_return)
  const anomalies = props.fund.anomalies || []
  
  // Mark anomaly points
  const markPoints = anomalies.map(a => ({
    name: a.date,
    xAxis: a.date,
    yAxis: a.nav,
    symbol: 'circle',
    symbolSize: 10,
    itemStyle: {
      color: a.severity === 'high' ? '#ff3366' : '#ffcc00',
    }
  }))
  
  const option = {
    backgroundColor: 'transparent',
    grid: {
      top: 40,
      right: 60,
      bottom: 40,
      left: 60,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#161b22',
      borderColor: '#21262d',
      textStyle: { color: '#e6edf3' },
      formatter: (params) => {
        const date = params[0].axisValue
        let html = `<div class="font-medium">${date}</div>`
        params.forEach(p => {
          const color = p.seriesName === 'NAV' ? '#00aaff' : (p.value >= 0 ? '#00ff88' : '#ff3366')
          html += `<div style="color:${color}">${p.seriesName}: ${p.value.toFixed(2)}</div>`
        })
        return html
      }
    },
    legend: {
      data: ['NAV', 'Daily Return'],
      top: 10,
      textStyle: { color: '#8b949e' }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#21262d' } },
      axisLabel: { color: '#8b949e', fontSize: 10 },
      splitLine: { show: false }
    },
    yAxis: [
      {
        type: 'value',
        name: 'NAV',
        position: 'left',
        axisLine: { lineStyle: { color: '#00aaff' } },
        axisLabel: { color: '#8b949e' },
        splitLine: { lineStyle: { color: '#21262d', type: 'dashed' } }
      },
      {
        type: 'value',
        name: 'Return %',
        position: 'right',
        axisLine: { lineStyle: { color: '#00ff88' } },
        axisLabel: { color: '#8b949e', formatter: '{value}%' },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: 'NAV',
        type: 'line',
        data: navData,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#00aaff', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 170, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 170, 255, 0)' }
          ])
        },
        markPoint: {
          data: markPoints,
          label: { show: false }
        }
      },
      {
        name: 'Daily Return',
        type: 'bar',
        yAxisIndex: 1,
        data: returns,
        itemStyle: {
          color: (params) => params.value >= 0 ? '#00ff88' : '#ff3366'
        },
        barWidth: '60%',
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 80,
        end: 100,
      }
    ]
  }
  
  chart.setOption(option)
}

function getRiskColor(score) {
  switch(score) {
    case 'High': return 'text-accent-red'
    case 'Medium': return 'text-accent-yellow'
    default: return 'text-accent-green'
  }
}

watch(() => props.fund, () => {
  if (props.fund) {
    setTimeout(initChart, 100)
  }
}, { deep: true })

onMounted(() => {
  window.addEventListener('resize', () => chart?.resize())
  if (props.fund) {
    setTimeout(initChart, 100)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', () => chart?.resize())
  if (chart) {
    chart.dispose()
  }
})
</script>
