import api from './api'
import type { PersonList, WorkList, PlaceList, SubjectList, LanguageList, PersonDetail, PaginatedResponse } from '../types/entity'

export const entityService = {
    getPersons: async (page: number = 1, page_size: number = 100, source?: string, search?: string) => {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: page_size.toString()
        });
        if (source) params.append('source', source);
        if (search) params.append('search', search);
        
        const response = await api.get<PaginatedResponse<PersonList>>(`/persons/?${params.toString()}`)
        return response.data
    },
    getWorks: async (page: number = 1, page_size: number = 100) => {
        const response = await api.get<PaginatedResponse<WorkList>>(`/works/?page=${page}&page_size=${page_size}`)
        return response.data
    },
    getPlaces: async () => {
                const response = await api.get<PlaceList[]>('/places/')
        return response.data
    },
    getSubjects: async () => {
                const response = await api.get<SubjectList[]>('/subjects/')
        return response.data
    },
    getLanguages: async () => {
                const response = await api.get<LanguageList[]>('/languages/')
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
    getNetworkData: async (source?: string, bucket?: string): Promise<any> => {
        const params: Record<string, string> = {};
        if (source) params.source = source;
        if (bucket) params.bucket = bucket;
        const response = await api.get('/network/', { params });
        return response.data;
    },
    getSources: async () => {
        const response = await api.get<any[]>('/sources/')
        return response.data
    },
    getOntologyGraph: async () => {
        const response = await api.get<any>('/ontology/')
        return response.data
    },

    getOntologyAudit: async () => {
        const response = await api.get<any>('/ontology/audit')
        return response.data
    }
}
