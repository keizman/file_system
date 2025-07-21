import axios from 'axios'

const API_BASE_URL = '/api'
const API_TOKEN = 'cs' // Same as client config

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_TOKEN}`,
    'Content-Type': 'application/json'
  },
  timeout: 30000
})

export function useApiClient() {
  const searchApkFiles = async ({ keyword = '', server = null, build_type = 'release', limit = 10, offset = 0 }) => {
    try {
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

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Try to get filename from response headers or use path
      const contentDisposition = response.headers['content-disposition']
      let filename = path.split('/').pop() || path.split('\\').pop() || 'download'
      
      if (contentDisposition) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '')
        }
      }
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      return true
    } catch (error) {
      console.error('Download API error:', error)
      throw new Error(error.response?.data?.message || 'Download failed')
    }
  }

  const getServers = async () => {
    try {
      const response = await apiClient.get('/servers')
      return response.data.data
    } catch (error) {
      console.error('Get servers API error:', error)
      return []
    }
  }

  const getSystemStatus = async () => {
    try {
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