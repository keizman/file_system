// Web Client Configuration
// Mirrors the PyQt5 client configuration structure

import tokenEncryption from './utils/encryption.js'

class WebClientConfig {
  constructor() {
    // Server Configuration - using Vite environment variables
    this.SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:9301'
    this.API_TOKEN = import.meta.env.VITE_API_TOKEN || 'cs'
    
    // Client Configuration
    this.MAX_SEARCH_RESULTS = parseInt(import.meta.env.VITE_MAX_SEARCH_RESULTS) || 50
    this.DEFAULT_RESULTS_PER_PAGE = parseInt(import.meta.env.VITE_DEFAULT_RESULTS_PER_PAGE) || 10
    this.THEME = import.meta.env.VITE_THEME || 'light'
    
    // Download Configuration
    this.DOWNLOAD_TIMEOUT = parseInt(import.meta.env.VITE_DOWNLOAD_TIMEOUT) || 300000
    
    // Load saved settings from localStorage
    this.loadSettings()
  }
  
  // Load settings from localStorage (equivalent to config file in desktop client)
  loadSettings() {
    try {
      const savedSettings = localStorage.getItem('apk_finder_settings')
      if (savedSettings) {
        const settings = JSON.parse(savedSettings)
        
        // Override with saved settings
        this.SERVER_URL = settings.server_url || this.SERVER_URL
        // Decrypt API token if it was stored encrypted
        if (settings.api_token) {
          this.API_TOKEN = tokenEncryption.isEncrypted(settings.api_token) 
            ? tokenEncryption.decrypt(settings.api_token)
            : settings.api_token
        }
        this.MAX_SEARCH_RESULTS = settings.max_search_results || this.MAX_SEARCH_RESULTS
        this.DEFAULT_RESULTS_PER_PAGE = settings.default_results_per_page || this.DEFAULT_RESULTS_PER_PAGE
        this.THEME = settings.theme || this.THEME
        this.DOWNLOAD_TIMEOUT = settings.download_timeout || this.DOWNLOAD_TIMEOUT
      }
    } catch (error) {
      console.warn('Failed to load settings from localStorage:', error)
    }
  }
  
  // Save settings to localStorage
  saveSettings() {
    try {
      const settings = {
        server_url: this.SERVER_URL,
        api_token: tokenEncryption.encrypt(this.API_TOKEN),
        max_search_results: this.MAX_SEARCH_RESULTS,
        default_results_per_page: this.DEFAULT_RESULTS_PER_PAGE,
        theme: this.THEME,
        download_timeout: this.DOWNLOAD_TIMEOUT
      }
      
      localStorage.setItem('apk_finder_settings', JSON.stringify(settings))
    } catch (error) {
      console.error('Failed to save settings to localStorage:', error)
    }
  }
  
  // Get a specific setting
  getSetting(key, defaultValue = null) {
    return this[key] !== undefined ? this[key] : defaultValue
  }
  
  // Set a specific setting and save
  setSetting(key, value) {
    if (this.hasOwnProperty(key) || this[key] !== undefined) {
      this[key] = value
      this.saveSettings()
    }
  }
  
  // Update multiple settings at once
  updateSettings(newSettings) {
    Object.keys(newSettings).forEach(key => {
      if (this.hasOwnProperty(key) || this[key] !== undefined) {
        this[key] = newSettings[key]
      }
    })
    this.saveSettings()
  }
  
  // Reset to default settings
  resetSettings() {
    this.SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:9301'
    this.API_TOKEN = import.meta.env.VITE_API_TOKEN || 'cs'
    this.MAX_SEARCH_RESULTS = parseInt(import.meta.env.VITE_MAX_SEARCH_RESULTS) || 50
    this.DEFAULT_RESULTS_PER_PAGE = parseInt(import.meta.env.VITE_DEFAULT_RESULTS_PER_PAGE) || 10
    this.THEME = import.meta.env.VITE_THEME || 'light'
    this.DOWNLOAD_TIMEOUT = parseInt(import.meta.env.VITE_DOWNLOAD_TIMEOUT) || 300000
    
    this.saveSettings()
  }
}

// Create and export singleton instance
export const config = new WebClientConfig()
export default config