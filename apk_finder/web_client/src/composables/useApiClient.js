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

  const downloadFile = async (path, server, onProgress = null) => {
    try {
      const apiClient = createApiClient()
      
      const params = { path, server }
      
      const response = await apiClient.get('/download', {
        params,
        responseType: 'blob',
        timeout: 300000, // 5 minutes for large files
        onDownloadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        }
      })

      // Check if response is successful
      if (response.status !== 200) {
        throw new Error(`Download failed with status: ${response.status}`)
      }

      // Check if response is actually a blob (file content)
      if (response.data.type === 'application/json') {
        // If server returned JSON error instead of file
        const text = await response.data.text()
        const errorData = JSON.parse(text)
        throw new Error(errorData.detail || 'Download failed')
      }

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Extract filename from path
      let filename = path.split('/').pop() || path.split('\\').pop() || 'download.apk'
      
      // Try to get filename from response headers
      const contentDisposition = response.headers['content-disposition']
      if (contentDisposition) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '')
        }
      }
      
      // Ensure .apk extension
      if (!filename.toLowerCase().endsWith('.apk')) {
        filename += '.apk'
      }
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      return true
    } catch (error) {
      console.error('Download API error:', error)
      
      // Provide more detailed error messages
      if (error.response) {
        if (error.response.status === 500) {
          throw new Error('Server error - possibly due to file path encoding issues')
        } else if (error.response.status === 404) {
          throw new Error('File not found on server')
        } else {
          throw new Error(`Download failed: ${error.response.status} ${error.response.statusText}`)
        }
      } else if (error.request) {
        throw new Error('Network error - unable to reach server')
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
    getServers,
    getSystemStatus,
    healthCheck
  }
}