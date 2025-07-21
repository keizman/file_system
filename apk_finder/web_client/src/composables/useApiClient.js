import axios from 'axios'
import config from '../config.js'

// Create axios instance with dynamic config
const createApiClient = () => {
  return axios.create({
    baseURL: '/api',
    headers: {
      'Authorization': `Bearer ${config.API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    timeout: 30000
  })
}

export function useApiClient() {
  const searchApkFiles = async ({ keyword = '', server = null, build_type = 'release', limit = 10, offset = 0 }) => {
    try {
      const apiClient = createApiClient()
      const response = await apiClient.post('/search', {
        keyword,
        server,
        build_type,
        limit,
        offset
      })
      
      return response.data.data
    } catch (error) {
      console.error('Search API error:', error)
      throw new Error(error.response?.data?.message || 'Search failed')
    }
  }

  const refreshScan = async (server = null) => {
    try {
      const apiClient = createApiClient()
      const params = server ? { server } : {}
      const response = await apiClient.post('/refresh', null, { params })
      return response.status === 200
    } catch (error) {
      console.error('Refresh API error:', error)
      throw new Error(error.response?.data?.message || 'Refresh failed')
    }
  }

  const checkDownloadCapability = async (path, server) => {
    try {
      const apiClient = createApiClient()
      const response = await apiClient.get('/download/check', {
        params: { path, server }
      })
      return response.data
    } catch (error) {
      console.error('Download capability check error:', error)
      return { downloadable: false, error: error.message }
    }
  }

  const downloadFile = async (path, server, onProgress = null) => {
    try {
      // Detect Android browser
      const isAndroid = /Android/i.test(navigator.userAgent)
      const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
      
      console.log(`Download request - Path: ${path}, Server: ${server}, IsAndroid: ${isAndroid}, IsMobile: ${isMobile}`)
      
      // For Android, first check download capability
      if (isAndroid) {
        const capability = await checkDownloadCapability(path, server)
        console.log('Download capability check:', capability)
        
        if (!capability.downloadable) {
          throw new Error(capability.error || 'File not downloadable')
        }
      }
      
      const apiClient = createApiClient()
      const params = { path, server }
      
      // Android-specific optimizations
      const requestConfig = {
        params,
        responseType: 'blob',
        timeout: isAndroid ? 600000 : 300000, // Longer timeout for Android (10 minutes)
        onDownloadProgress: (progressEvent) => {
          if (onProgress) {
            // For Android, handle cases where total might be undefined
            if (progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              onProgress(progress, progressEvent.loaded, progressEvent.total)
            } else {
              // Progress without total (chunked transfer)
              onProgress(null, progressEvent.loaded, null)
            }
          }
        }
      }
      
      // Add headers for Android compatibility
      if (isAndroid) {
        requestConfig.headers = {
          'Accept': 'application/vnd.android.package-archive, application/octet-stream, */*',
          'Accept-Encoding': 'identity', // Disable compression for Android
          'Cache-Control': 'no-cache'
        }
      }
      
      const response = await apiClient.get('/download', requestConfig)

      // Check if response is successful
      if (response.status !== 200 && response.status !== 206) {
        throw new Error(`Download failed with status: ${response.status}`)
      }

      // Check if response is actually a blob (file content)
      if (response.data.type === 'application/json') {
        // If server returned JSON error instead of file
        const text = await response.data.text()
        const errorData = JSON.parse(text)
        throw new Error(errorData.detail || 'Download failed')
      }

      // Extract filename from path and clean it
      let filename = path.split('/').pop() || path.split('\\').pop() || 'download.apk'
      
      // Try to get filename from response headers
      const contentDisposition = response.headers['content-disposition']
      if (contentDisposition) {
        // Handle both standard and RFC 2231 encoding
        let matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
        if (!matches) {
          // Try RFC 2231 encoding
          matches = /filename\*=UTF-8''([^;\n]*)/.exec(contentDisposition)
          if (matches) {
            filename = decodeURIComponent(matches[1])
          }
        } else if (matches[1]) {
          filename = matches[1].replace(/['"]/g, '')
        }
      }
      
      // Clean filename for Android compatibility
      filename = filename.replace(/[\\\/\:*?"<>|]/g, '_').trim()
      
      // Ensure .apk extension
      if (!filename.toLowerCase().endsWith('.apk')) {
        filename += '.apk'
      }
      
      console.log(`Downloading file: ${filename} (${response.data.size} bytes)`)
      
      // For Android browsers, use a more compatible download method
      if (isAndroid) {
        // Create a more robust download for Android
        const blob = new Blob([response.data], { 
          type: 'application/vnd.android.package-archive' 
        })
        
        // Try multiple download methods for Android compatibility
        if (window.navigator && window.navigator.msSaveOrOpenBlob) {
          // IE/Edge
          window.navigator.msSaveOrOpenBlob(blob, filename)
        } else {
          // Modern browsers with Android-specific handling
          const url = window.URL.createObjectURL(blob)
          
          // For Android, create a more explicit download
          const link = document.createElement('a')
          link.href = url
          link.download = filename
          link.style.display = 'none'
          
          // Add additional attributes for Android
          link.setAttribute('type', 'application/vnd.android.package-archive')
          link.setAttribute('target', '_blank')
          
          document.body.appendChild(link)
          
          // For Android, trigger with user gesture simulation
          const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
          })
          
          link.dispatchEvent(clickEvent)
          
          // Clean up after a delay to ensure download starts
          setTimeout(() => {
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
          }, 1000)
        }
      } else {
        // Standard download method for desktop browsers
        const url = window.URL.createObjectURL(new Blob([response.data], {
          type: 'application/vnd.android.package-archive'
        }))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      }
      
      return true
    } catch (error) {
      console.error('Download API error:', error)
      
      // Provide more detailed error messages
      if (error.response) {
        if (error.response.status === 500) {
          throw new Error('Server error - file might be corrupted or inaccessible')
        } else if (error.response.status === 404) {
          throw new Error('File not found on server')
        } else if (error.response.status === 416) {
          throw new Error('Range request error - file might be corrupted')
        } else {
          throw new Error(`Download failed: ${error.response.status} ${error.response.statusText}`)
        }
      } else if (error.request) {
        throw new Error('Network error - check your connection and try again')
      } else {
        throw new Error(error.message || 'Download failed')
      }
    }
  }

  const getServers = async () => {
    try {
      const apiClient = createApiClient()
      const response = await apiClient.get('/servers')
      return response.data.data
    } catch (error) {
      console.error('Get servers API error:', error)
      return []
    }
  }

  const getSystemStatus = async () => {
    try {
      const apiClient = createApiClient()
      const response = await apiClient.get('/status')
      return response.data
    } catch (error) {
      console.error('Get status API error:', error)
      throw new Error(error.response?.data?.message || 'Status check failed')
    }
  }

  const healthCheck = async () => {
    try {
      const response = await axios.get('/health', { timeout: 10000 })
      return response.status === 200
    } catch (error) {
      console.error('Health check error:', error)
      return false
    }
  }

  return {
    searchApkFiles,
    refreshScan,
    downloadFile,
    checkDownloadCapability,
    getServers,
    getSystemStatus,
    healthCheck
  }
}