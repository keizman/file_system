<template>
  <div v-if="isVisible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex justify-between items-center p-6 border-b border-gray-200">
        <h2 class="text-xl font-semibold text-gray-900">Settings</h2>
        <button 
          @click="closeDialog"
          class="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-6">
        <!-- Server Configuration -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-4">Server Configuration</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Server URL
              </label>
              <input
                v-model="formData.server_url"
                type="text"
                class="input-field"
                placeholder="http://localhost:9301"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                API Token
              </label>
              <input
                v-model="formData.api_token"
                type="text"
                class="input-field"
                placeholder="cs"
              />
            </div>
          </div>
        </div>

        <!-- Search Configuration -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-4">Search Configuration</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Max Search Results
              </label>
              <input
                v-model.number="formData.max_search_results"
                type="number"
                min="10"
                max="1000"
                class="input-field"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Default Results Per Page
              </label>
              <input
                v-model.number="formData.default_results_per_page"
                type="number"
                min="5"
                max="100"
                class="input-field"
              />
            </div>
          </div>
        </div>

        <!-- UI Configuration -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-4">UI Configuration</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Theme
              </label>
              <select v-model="formData.theme" class="input-field">
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Download Configuration -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-4">Download Configuration</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Download Timeout (ms)
              </label>
              <input
                v-model.number="formData.download_timeout"
                type="number"
                min="30000"
                max="600000"
                step="30000"
                class="input-field"
              />
              <p class="text-xs text-gray-500 mt-1">
                Timeout for large file downloads (30s - 10min)
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-between items-center p-6 border-t border-gray-200 bg-gray-50">
        <button
          @click="resetToDefaults"
          class="btn text-gray-600 bg-gray-200 hover:bg-gray-300"
        >
          Reset to Defaults
        </button>
        
        <div class="flex space-x-3">
          <button
            @click="closeDialog"
            class="btn btn-outline"
          >
            Cancel
          </button>
          <button
            @click="saveSettings"
            class="btn btn-primary"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, watch } from 'vue'
import config from '../config.js'

export default {
  name: 'SettingsDialog',
  props: {
    isVisible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'settings-updated'],
  setup(props, { emit }) {
    // Form data reactive object
    const formData = reactive({
      server_url: '',
      api_token: '',
      max_search_results: 50,
      default_results_per_page: 10,
      theme: 'light',
      download_timeout: 300000
    })
    
    // Load current settings when dialog opens
    watch(() => props.isVisible, (newValue) => {
      if (newValue) {
        loadCurrentSettings()
      }
    })
    
    const loadCurrentSettings = () => {
      formData.server_url = config.SERVER_URL
      formData.api_token = config.API_TOKEN
      formData.max_search_results = config.MAX_SEARCH_RESULTS
      formData.default_results_per_page = config.DEFAULT_RESULTS_PER_PAGE
      formData.theme = config.THEME
      formData.download_timeout = config.DOWNLOAD_TIMEOUT
    }
    
    const saveSettings = () => {
      // Validate inputs
      if (!formData.server_url.trim()) {
        alert('Server URL is required')
        return
      }
      
      if (!formData.api_token.trim()) {
        alert('API Token is required')
        return
      }
      
      if (formData.max_search_results < 10 || formData.max_search_results > 1000) {
        alert('Max Search Results must be between 10 and 1000')
        return
      }
      
      if (formData.default_results_per_page < 5 || formData.default_results_per_page > 100) {
        alert('Default Results Per Page must be between 5 and 100')
        return
      }
      
      if (formData.download_timeout < 30000 || formData.download_timeout > 600000) {
        alert('Download Timeout must be between 30 seconds and 10 minutes')
        return
      }
      
      // Update config
      config.updateSettings({
        SERVER_URL: formData.server_url.trim(),
        API_TOKEN: formData.api_token.trim(),
        MAX_SEARCH_RESULTS: formData.max_search_results,
        DEFAULT_RESULTS_PER_PAGE: formData.default_results_per_page,
        THEME: formData.theme,
        DOWNLOAD_TIMEOUT: formData.download_timeout
      })
      
      // Emit settings updated event
      emit('settings-updated', {
        server_url: formData.server_url.trim(),
        api_token: formData.api_token.trim(),
        max_search_results: formData.max_search_results,
        default_results_per_page: formData.default_results_per_page,
        theme: formData.theme,
        download_timeout: formData.download_timeout
      })
      
      closeDialog()
    }
    
    const resetToDefaults = () => {
      if (confirm('Are you sure you want to reset all settings to default values?')) {
        config.resetSettings()
        loadCurrentSettings()
      }
    }
    
    const closeDialog = () => {
      emit('close')
    }
    
    // Load settings on component mount
    loadCurrentSettings()
    
    return {
      formData,
      saveSettings,
      resetToDefaults,
      closeDialog
    }
  }
}
</script>