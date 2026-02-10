<template>
  <div class="min-h-screen bg-terminal-bg flex flex-col items-center justify-center p-8 relative">
    <!-- Theme Toggle (top right) -->
    <div class="absolute top-4 right-4">
      <ThemeToggle />
    </div>
    
    <!-- Header -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-text-primary mb-2">
        📊 Fund Anomaly Monitor
      </h1>
      <p class="text-text-secondary">Upload NAV data to begin analysis</p>
    </div>

    <!-- Upload Card -->
    <div class="card w-full max-w-2xl">
      <div class="card-header">Data Upload</div>
      
      <div class="p-6">
        <!-- Drop Zone -->
        <div 
          class="border-2 border-dashed border-terminal-border rounded-lg p-8 text-center transition-colors"
          :class="isDragging ? 'border-accent-blue bg-accent-blue/10' : 'hover:border-accent-blue/50'"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <!-- <div class="text-4xl mb-4">📁</div> -->
          <i class="pi pi-folder text-4xl mb-4 text-text-muted "></i>
          <p class="text-text-primary mb-2">
            Drag & drop your NAV file here
          </p>
          <p class="text-text-muted text-sm mb-4">
            Supports CSV or Parquet files
          </p>
          <label class="btn-primary cursor-pointer">
            Browse Files
            <input 
              type="file" 
              class="hidden" 
              accept=".csv,.parquet"
              @change="handleFileSelect"
            />
          </label>
        </div>

        <!-- File Info -->
        <div v-if="selectedFile" class="mt-4 p-3 bg-terminal-surface rounded-lg flex items-center gap-3">
          <span class="text-2xl">📄</span>
          <div class="flex-1 min-w-0">
            <div class="text-text-primary truncate">{{ selectedFile.name }}</div>
            <div class="text-text-muted text-xs">{{ formatFileSize(selectedFile.size) }}</div>
          </div>
          <button @click="clearFile" class="text-text-muted hover:text-accent-red">✕</button>
        </div>

        <!-- Upload Button -->
        <button 
          v-if="selectedFile && !isUploading && !previewData"
          @click="uploadFile"
          class="btn-primary w-full mt-4"
        >
          Upload & Preview
        </button>

        <!-- Loading State -->
        <div v-if="isUploading" class="mt-4 text-center">
          <div class="animate-spin text-2xl mb-2"><i class="pi pi-refresh"></i></div>
          <p class="text-text-secondary">Processing file...</p>
        </div>

        <!-- Error -->
        <div v-if="error" class="mt-4 p-3 bg-accent-red/20 border border-accent-red rounded-lg text-accent-red text-sm">
          {{ error }}
        </div>
      </div>
    </div>

    <!-- Preview Card -->
    <div v-if="previewData" class="card w-full max-w-4xl mt-6">
      <div class="card-header flex items-center justify-between">
        <span>Data Preview</span>
        <span class="text-xs text-text-muted">
          Showing {{ previewData.preview.length }} of {{ previewData.total_rows.toLocaleString() }} rows
        </span>
      </div>
      
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-terminal-surface">
              <th v-for="col in previewData.columns" :key="col" 
                  class="px-4 py-2 text-left text-text-muted font-medium">
                {{ col }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in previewData.preview" :key="idx"
                class="border-t border-terminal-border hover:bg-terminal-hover">
              <td v-for="col in previewData.columns" :key="col"
                  class="px-4 py-2 text-text-primary font-mono">
                {{ row[col] }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Summary Stats -->
      <div class="p-4 border-t border-terminal-border grid grid-cols-3 gap-4 text-center">
        <div>
          <div class="text-2xl font-bold text-accent-blue">{{ previewData.total_rows.toLocaleString() }}</div>
          <div class="text-xs text-text-muted">Total Rows</div>
        </div>
        <div>
          <div class="text-2xl font-bold text-accent-green">{{ previewData.unique_funds.toLocaleString() }}</div>
          <div class="text-xs text-text-muted">Unique Funds</div>
        </div>
        <div>
          <div class="text-2xl font-bold text-accent-purple">{{ previewData.columns.length }}</div>
          <div class="text-xs text-text-muted">Columns</div>
        </div>
      </div>

      <!-- Proceed Button -->
      <div class="p-4 border-t border-terminal-border">
        <button @click="proceedToDashboard" class="btn-primary w-full text-lg py-3">
          <i class="pi pi-external-link text-lg mr-2 "></i> Launch Dashboard
        </button>
      </div>
    </div>

    <!-- Use Demo Data Link -->
    <div class="mt-6 text-center">
      <button @click="useDemoData" class="text-accent-blue hover:underline text-sm">
        <i class="pi pi-database text-sm mr-1"></i> Or use demo data →
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8020'

const isDragging = ref(false)
const selectedFile = ref(null)
const isUploading = ref(false)
const error = ref(null)
const previewData = ref(null)

function handleDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file && (file.name.endsWith('.csv') || file.name.endsWith('.parquet'))) {
    selectedFile.value = file
    error.value = null
    previewData.value = null
  } else {
    error.value = 'Please upload a CSV or Parquet file'
  }
}

function handleFileSelect(e) {
  const file = e.target.files[0]
  if (file) {
    selectedFile.value = file
    error.value = null
    previewData.value = null
  }
}

function clearFile() {
  selectedFile.value = null
  previewData.value = null
  error.value = null
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function uploadFile() {
  if (!selectedFile.value) return
  
  isUploading.value = true
  error.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const response = await axios.post(`${API_BASE}/api/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    previewData.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to upload file'
  } finally {
    isUploading.value = false
  }
}

function proceedToDashboard() {
  router.push('/dashboard')
}

function useDemoData() {
  router.push('/dashboard')
}
</script>

<style scoped>
.btn-primary {
  @apply bg-accent-blue text-white px-6 py-2 rounded-lg font-medium 
         hover:bg-accent-blue/80 transition-colors inline-block;
}
</style>
