import axios from 'axios'

// Determine API base URL based on environment
function getApiBaseUrl(): string {
    // 1. Try environment variable from build time
    const envUrl = import.meta.env.VITE_API_BASE_URL
    if (envUrl) {
        return envUrl
    }

    // 2. On Render production (pjh-frontend.onrender.com), use backend service
    if (typeof window !== 'undefined' && window.location.hostname === 'pjh-frontend.onrender.com') {
        return 'https://pjh-backend-i8oj.onrender.com/api/v1'
    }

    // 3. Default to relative URL for local development
    return '/api/v1'
}

const api = axios.create({
    baseURL: getApiBaseUrl(),
    headers: {
        'Content-Type': 'application/json',
    },
})

export default api
