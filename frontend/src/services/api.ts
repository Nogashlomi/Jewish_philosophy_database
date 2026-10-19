import axios from 'axios'
import { auth } from './firebase'

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

api.interceptors.request.use(async (config) => {
  const token = await auth.currentUser?.getIdToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
