/**
 * API Service for Fund Anomaly Dashboard
 * Handles all REST API calls and WebSocket connections
 */

import axios from 'axios'

// API base URL - uses Vite env or defaults for development
const API_URL = import.meta.env.VITE_API_URL || ''
const API_BASE = API_URL ? `${API_URL}/api` : '/api'

// WebSocket URL - derive from API_URL or use relative path
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const WS_BASE = API_URL 
  ? `${WS_PROTOCOL}//${new URL(API_URL).host}/ws`
  : `${WS_PROTOCOL}//${window.location.host}/ws`

// Axios instance with defaults
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    throw error
  }
)

/**
 * Fetch all funds with optional filters
 */
export async function getFunds(options = {}) {
  const params = new URLSearchParams()
  if (options.category) params.append('category', options.category)
  if (options.anomalyOnly) params.append('anomaly_only', 'true')
  if (options.sortBy) params.append('sort_by', options.sortBy)
  if (options.limit) params.append('limit', options.limit)
  
  return api.get(`/funds?${params.toString()}`)
}

/**
 * Fetch detailed data for a specific fund
 */
export async function getFundDetails(schemeCode) {
  return api.get(`/fund/${schemeCode}`)
}

/**
 * Fetch dashboard overview statistics
 */
export async function getOverview() {
  return api.get('/overview')
}

/**
 * Fetch anomaly signals for signal feed
 */
export async function getSignals(options = {}) {
  const params = new URLSearchParams()
  if (options.limit) params.append('limit', options.limit)
  if (options.severity) params.append('severity', options.severity)
  
  return api.get(`/signals?${params.toString()}`)
}

/**
 * Fetch recent anomalies
 */
export async function getAnomalies(options = {}) {
  const params = new URLSearchParams()
  if (options.days) params.append('days', options.days)
  if (options.limit) params.append('limit', options.limit)
  
  return api.get(`/anomalies?${params.toString()}`)
}

/**
 * Fetch heatmap data
 */
export async function getHeatmapData() {
  return api.get('/heatmap')
}

/**
 * Fetch categories with stats
 */
export async function getCategories() {
  return api.get('/categories')
}

/**
 * WebSocket connection manager
 */
export class WebSocketManager {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 2000
    this.listeners = new Map()
    this.isConnecting = false
  }

  /**
   * Connect to WebSocket stream
   */
  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }

    this.isConnecting = true
    
    try {
      this.ws = new WebSocket(`${WS_BASE}/stream`)

      this.ws.onopen = () => {
        console.log('🔌 WebSocket connected')
        this.reconnectAttempts = 0
        this.isConnecting = false
        this.emit('connected', null)
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.emit('message', data)
          
          // Emit typed events
          if (data.type) {
            this.emit(data.type, data.data)
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected')
        this.isConnecting = false
        this.emit('disconnected', null)
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnecting = false
        this.emit('error', error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.isConnecting = false
    }
  }

  /**
   * Subscribe to events
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event).add(callback)
    
    return () => this.off(event, callback)
  }

  /**
   * Unsubscribe from events
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback)
    }
  }

  /**
   * Emit event to listeners
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data)
        } catch (e) {
          console.error('Error in WebSocket listener:', e)
        }
      })
    }
  }

  /**
   * Attempt to reconnect
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`)
    
    setTimeout(() => {
      this.connect()
    }, this.reconnectDelay * this.reconnectAttempts)
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * Check if connected
   */
  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// Singleton WebSocket manager
export const wsManager = new WebSocketManager()

export default {
  getFunds,
  getFundDetails,
  getOverview,
  getSignals,
  getAnomalies,
  getHeatmapData,
  getCategories,
  wsManager,
}
