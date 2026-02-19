import api from './api'
import type { PersonList, WorkList, PlaceList, SubjectList, LanguageList, ScholarlyList, PersonDetail } from '../types/entity'

export const entityService = {
    getPersons: async (source?: string) => {
        const params = source ? { source } : {}
        const response = await api.get<PersonList[]>('/persons/', { params })
        return response.data
    },
    getWorks: async (source?: string) => {
        const params = source ? { source } : {}
        const response = await api.get<WorkList[]>('/works/', { params })
        return response.data
    },
    getPlaces: async (source?: string) => {
        const params = source ? { source } : {}
        const response = await api.get<PlaceList[]>('/places/', { params })
        return response.data
    },
    getSubjects: async (source?: string) => {
        const params = source ? { source } : {}
        const response = await api.get<SubjectList[]>('/subjects/', { params })
        return response.data
    },
    getLanguages: async (source?: string) => {
        const params = source ? { source } : {}
        const response = await api.get<LanguageList[]>('/languages/', { params })
        return response.data
    },
    getScholarlyWorks: async (source?: string) => {
        const params = source ? { source } : {}
        const response = await api.get<ScholarlyList[]>('/scholarly/', { params })
        return response.data
    },
    getPersonDetail: async (id: string) => {
        const response = await api.get<PersonDetail>(`/persons/${id}`)
        return response.data
    },
    getWorkDetail: async (id: string) => {
        const response = await api.get<any>(`/works/${id}`)
        return response.data
    },
    getPlaceDetail: async (id: string) => {
        const response = await api.get<any>(`/places/${id}`)
        return response.data
    },
    getSubjectDetail: async (id: string) => {
        const response = await api.get<any>(`/subjects/${id}`)
        return response.data
    },
    getLanguageDetail: async (id: string) => {
        const response = await api.get<any>(`/languages/${id}`)
        return response.data
    },
    getScholarlyDetail: async (id: string) => {
        const response = await api.get<any>(`/scholarly/${id}`)
        return response.data
    },
    getNetworkData: async (source?: string) => {
        const params = source ? { source } : {}
        const response = await api.get<any>('/network/', { params })
        return response.data
    },
    getSources: async () => {
        const response = await api.get<any[]>('/sources/')
        return response.data
    },
    getOntologyGraph: async () => {
        const response = await api.get<any>('/ontology/')
        return response.data
    }
}
