<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <h1 class="text-2xl font-bold text-gray-900">APK Finder</h1>
          <div class="flex space-x-3">
            <button @click="refreshScan" :disabled="isRefreshing" class="btn btn-primary">
              <span v-if="isRefreshing">Refreshing...</span>
              <span v-else>🔄 Refresh</span>
            </button>
            <button @click="showSettings" class="btn btn-outline">
              ⚙️ Settings
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <!-- Server and Build Type Controls -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <!-- Server Selection -->
        <div class="card p-4">
          <h3 class="text-lg font-semibold mb-3">Server</h3>
          <div class="flex flex-wrap gap-2">
            <button
              @click="selectServer('')"
              :class="['btn', selectedServer === '' ? 'btn-primary' : 'btn-outline']"
            >
              All Servers
            </button>
            <button
              v-for="server in servers"
              :key="server.name"
              @click="selectServer(server.name)"
              :class="['btn', selectedServer === server.name ? 'btn-primary' : 'btn-outline']"
            >
              {{ server.display_name }}
            </button>
          </div>
        </div>

        <!-- Build Type Selection -->
        <div class="card p-4">
          <h3 class="text-lg font-semibold mb-3">Build Type</h3>
          <div class="flex flex-wrap gap-2">
            <button
              @click="selectBuildType('release')"
              :class="['btn', buildType === 'release' ? 'btn-secondary' : 'btn-outline']"
            >
              Release
            </button>
            <button
              @click="selectBuildType('debug')"
              :class="['btn', buildType === 'debug' ? 'btn-secondary' : 'btn-outline']"
            >
              Debug
            </button>
            <button
              @click="selectBuildType('combine')"
              :class="['btn', buildType === 'combine' ? 'btn-secondary' : 'btn-outline']"
            >
              Combine
            </button>
          </div>
        </div>
      </div>

      <!-- Search Section -->
      <div class="card p-6 mb-6">
        <div class="flex gap-4">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="🔍 Search APK files... (use | to separate multiple keywords)"
            class="input-field flex-1"
            @keypress.enter="searchFiles"
          />
          <button @click="searchFiles" :disabled="isSearching" class="btn btn-primary">
            <span v-if="isSearching">Searching...</span>
            <span v-else">🔍 Search</span>
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- File List -->
        <div class="lg:col-span-2">
          <div class="card">
            <div class="p-4 border-b border-gray-200">
              <h3 class="text-lg font-semibold">File List</h3>
              <p class="text-sm text-gray-600">Found {{ totalFiles }} files</p>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      File Name
                    </th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Build Type
                    </th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created Time
                    </th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr 
                    v-for="file in files" 
                    :key="file.relative_path"
                    :class="['hover:bg-gray-50 cursor-pointer', selectedFile?.relative_path === file.relative_path ? 'bg-blue-50' : '']"
                    @click="selectFile(file)"
                  >
                    <td class="px-4 py-3 text-sm font-medium text-gray-900 truncate max-w-xs">
                      {{ file.file_name }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500">
                      {{ formatFileSize(file.file_size) }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500">
                      <span :class="getBuildTypeClass(file.build_type)">
                        {{ file.build_type }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500">
                      {{ formatDateTime(file.created_time) }}
                    </td>
                    <td class="px-4 py-3 text-sm font-medium">
                      <div class="flex space-x-2">
                        <button 
                          @click.stop="downloadFile(file)"
                          :disabled="isDownloading[file.relative_path]"
                          class="text-primary hover:text-primary-hover"
                        >
                          <span v-if="isDownloading[file.relative_path]">⏳</span>
                          <span v-else>📥</span>
                        </button>
                        <button 
                          @click.stop="copyToClipboard(file, 'smb')"
                          class="text-gray-600 hover:text-gray-800"
                          title="Copy SMB Path"
                        >
                          📋
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              
              <div v-if="files.length === 0 && !isSearching" class="p-8 text-center text-gray-500">
                No files found. Try adjusting your search criteria.
              </div>
              
              <div v-if="isSearching" class="p-8 text-center text-gray-500">
                Searching for files...
              </div>
            </div>
          </div>
        </div>

        <!-- Download Panel -->
        <div class="space-y-6">
          <!-- Download Actions -->
          <div class="card p-4">
            <h3 class="text-lg font-semibold mb-3">Download</h3>
            
            <!-- Selected File Info -->
            <div v-if="selectedFile" class="mb-4 p-3 bg-gray-50 rounded-lg">
              <p class="text-sm font-medium text-gray-900 truncate">{{ selectedFile.file_name }}</p>
              <p class="text-xs text-gray-500">{{ formatFileSize(selectedFile.file_size) }}</p>
            </div>
            
            <!-- Download Progress -->
            <div v-if="currentDownload" class="mb-4">
              <div class="flex justify-between text-sm text-gray-600 mb-1">
                <span>{{ currentDownload.fileName }}</span>
                <span>{{ currentDownload.progress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div 
                  class="bg-primary h-2 rounded-full transition-all duration-300"
                  :style="{ width: currentDownload.progress + '%' }"
                ></div>
              </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="space-y-2">
              <button 
                @click="downloadSelectedFile"
                :disabled="!selectedFile || currentDownload"
                class="w-full btn btn-primary"
              >
                📥 Download
              </button>
              
              <!-- Auto Install button (disabled) -->
              <button 
                disabled
                class="w-full btn bg-gray-300 text-gray-500 cursor-not-allowed"
                title="Auto install not available in web version"
              >
                📱 Auto Install (Disabled)
              </button>
            </div>
          </div>

          <!-- Recent Downloads -->
          <div class="card p-4">
            <div class="flex justify-between items-center mb-3">
              <h3 class="text-lg font-semibold">Recent Downloads</h3>
              <button 
                @click="clearRecentDownloads"
                class="text-sm text-red-600 hover:text-red-800"
              >
                Clear
              </button>
            </div>
            
            <div v-if="recentDownloads.length === 0" class="text-sm text-gray-500">
              No recent downloads...
            </div>
            
            <div v-else class="space-y-2 max-h-60 overflow-y-auto">
              <div 
                v-for="download in recentDownloads" 
                :key="download.name"
                class="p-2 bg-gray-50 rounded text-sm"
              >
                <p class="font-medium truncate">📁 {{ download.name }}</p>
                <p class="text-xs text-gray-500">{{ download.time }}</p>
              </div>
            </div>
          </div>

          <!-- Connection Status -->
          <div class="card p-4">
            <h3 class="text-lg font-semibold mb-3">Status</h3>
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Connection:</span>
                <span :class="['text-sm font-medium', connectionStatus ? 'text-green-600' : 'text-red-600']">
                  {{ connectionStatus ? '🟢 Connected' : '🔴 Disconnected' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notifications -->
    <div class="fixed bottom-4 right-4 space-y-2">
      <div 
        v-for="toast in toasts" 
        :key="toast.id"
        :class="[
          'px-4 py-3 rounded-lg shadow-lg text-white max-w-sm',
          toast.type === 'success' ? 'bg-green-500' :
          toast.type === 'error' ? 'bg-red-500' :
          'bg-blue-500'
        ]"
      >
        {{ toast.message }}
      </div>
    </div>

    <!-- Settings Dialog -->
    <SettingsDialog 
      :is-visible="isSettingsVisible" 
      @close="closeSettings"
      @settings-updated="onSettingsUpdated"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue'
import { useApiClient } from './composables/useApiClient'
import { formatFileSize, formatDateTime } from './utils/formatters'
import SettingsDialog from './components/SettingsDialog.vue'
import config from './config.js'

export default {
  name: 'App',
  components: {
    SettingsDialog
  },
  setup() {
    // Reactive state
    const isDarkMode = ref(config.THEME === 'dark')
    const searchKeyword = ref('')
    const selectedServer = ref('')
    const buildType = ref('release')
    const selectedFile = ref(null)
    const isSearching = ref(false)
    const isRefreshing = ref(false)
    const isDownloading = reactive({})
    const currentDownload = ref(null)
    const isSettingsVisible = ref(false)
    
    // Data
    const servers = ref([])
    const files = ref([])
    const totalFiles = ref(0)
    const recentDownloads = ref([])
    const connectionStatus = ref(false)
    const toasts = ref([])
    
    // API client
    const { searchApkFiles, refreshScan, downloadFile, getServers, healthCheck } = useApiClient()
    
    // Methods
    const selectServer = (serverName) => {
      selectedServer.value = serverName
      searchFiles()
    }
    
    const selectBuildType = (type) => {
      buildType.value = type
      searchFiles()
    }
    
    const selectFile = (file) => {
      selectedFile.value = file
    }
    
    const searchFiles = async () => {
      if (isSearching.value) return
      
      isSearching.value = true
      try {
        const result = await searchApkFiles({
          keyword: searchKeyword.value,
          server: selectedServer.value || null,
          build_type: buildType.value,
          limit: config.MAX_SEARCH_RESULTS,
          offset: 0
        })
        
        files.value = result.items
        totalFiles.value = result.total
      } catch (error) {
        showToast('Search failed: ' + error.message, 'error')
      } finally {
        isSearching.value = false
      }
    }
    
    const downloadSelectedFile = async () => {
      if (!selectedFile.value) return
      await downloadFileAction(selectedFile.value)
    }
    
    const downloadFileAction = async (file) => {
      if (isDownloading[file.relative_path]) return
      
      isDownloading[file.relative_path] = true
      currentDownload.value = {
        fileName: file.file_name,
        progress: 0
      }
      
      try {
        // Find server name from file data
        const serverName = findServerNameFromPrefix(file.server_prefix)
        
        await downloadFile(file.relative_path, serverName, (progress) => {
          if (currentDownload.value) {
            currentDownload.value.progress = progress
          }
        })
        
        // Add to recent downloads
        addRecentDownload(file.file_name)
        showToast('Download completed successfully', 'success')
        
      } catch (error) {
        showToast('Download failed: ' + error.message, 'error')
      } finally {
        isDownloading[file.relative_path] = false
        currentDownload.value = null
      }
    }
    
    const findServerNameFromPrefix = (prefix) => {
      const server = servers.value.find(s => s.path === prefix)
      return server ? server.name : 'server_1'
    }
    
    const refreshScanAction = async () => {
      if (isRefreshing.value) return
      
      isRefreshing.value = true
      try {
        await refreshScan()
        showToast('Refresh triggered successfully', 'success')
        setTimeout(() => searchFiles(), 2000)
      } catch (error) {
        showToast('Refresh failed: ' + error.message, 'error')
      } finally {
        isRefreshing.value = false
      }
    }
    
    const copyToClipboard = async (file, type) => {
      let path = ''
      if (type === 'smb') {
        path = `${file.server_prefix}${file.relative_path}`
      } else {
        // Convert to HTTP path
        const serverPrefix = file.server_prefix
        if (serverPrefix.startsWith('\\\\')) {
          const parts = serverPrefix.split('\\')
          if (parts.length >= 4) {
            const serverIp = parts[2]
            const sharePath = parts.slice(3).join('/')
            path = `http://${serverIp}/${sharePath}${file.relative_path.replace(/\\/g, '/')}`
          }
        }
      }
      
      try {
        await navigator.clipboard.writeText(path)
        showToast(`${type.toUpperCase()} path copied to clipboard`, 'success')
      } catch (error) {
        showToast('Failed to copy to clipboard', 'error')
      }
    }
    
    const addRecentDownload = (fileName) => {
      const download = {
        name: fileName,
        time: new Date().toLocaleString()
      }
      
      // Remove if already exists
      recentDownloads.value = recentDownloads.value.filter(d => d.name !== fileName)
      
      // Add to beginning
      recentDownloads.value.unshift(download)
      
      // Keep only last 10
      recentDownloads.value = recentDownloads.value.slice(0, 10)
    }
    
    const clearRecentDownloads = () => {
      recentDownloads.value = []
    }
    
    const showSettings = () => {
      isSettingsVisible.value = true
    }
    
    const closeSettings = () => {
      isSettingsVisible.value = false
    }
    
    const onSettingsUpdated = (newSettings) => {
      // Update theme if changed
      if (newSettings.theme !== config.THEME) {
        isDarkMode.value = newSettings.theme === 'dark'
        // Apply theme changes to UI
        document.documentElement.setAttribute('data-theme', newSettings.theme)
      }
      
      showToast('Settings saved successfully', 'success')
      
      // Reload API clients with new configuration
      // Note: This may require page refresh for full effect in some cases
    }
    
    const checkConnection = async () => {
      try {
        connectionStatus.value = await healthCheck()
      } catch (error) {
        connectionStatus.value = false
      }
    }
    
    const showToast = (message, type = 'info') => {
      const toast = {
        id: Date.now(),
        message,
        type
      }
      toasts.value.push(toast)
      
      setTimeout(() => {
        const index = toasts.value.findIndex(t => t.id === toast.id)
        if (index > -1) {
          toasts.value.splice(index, 1)
        }
      }, 3000)
    }
    
    const getBuildTypeClass = (buildType) => {
      switch (buildType.toLowerCase()) {
        case 'release':
          return 'px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full'
        case 'debug':
          return 'px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full'
        default:
          return 'px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full'
      }
    }
    
    // Load initial data
    onMounted(async () => {
      try {
        servers.value = await getServers()
        await searchFiles()
        await checkConnection()
      } catch (error) {
        showToast('Failed to load initial data', 'error')
      }
      
      // Check connection periodically
      setInterval(checkConnection, 30000)
    })
    
    return {
      // State
      isDarkMode,
      searchKeyword,
      selectedServer,
      buildType,
      selectedFile,
      isSearching,
      isRefreshing,
      isDownloading,
      currentDownload,
      isSettingsVisible,
      
      // Data
      servers,
      files,
      totalFiles,
      recentDownloads,
      connectionStatus,
      toasts,
      
      // Methods
      selectServer,
      selectBuildType,
      selectFile,
      searchFiles,
      downloadSelectedFile,
      downloadFile: downloadFileAction,
      refreshScan: refreshScanAction,
      copyToClipboard,
      clearRecentDownloads,
      showSettings,
      closeSettings,
      onSettingsUpdated,
      showToast,
      getBuildTypeClass,
      
      // Utils
      formatFileSize,
      formatDateTime
    }
  }
}
</script>