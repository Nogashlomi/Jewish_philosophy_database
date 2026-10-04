import axios from 'axios'

// Determine API base URL based on environment
function getApiBaseUrl(): string {
  // 1. Try environment variable from build time
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (envUrl) {
    return envUrl
  }

  // 2. Default to relative URL for local development
  return '/api/v1'
}

const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
})

export default api
