import api from './api'
import type {
  PersonList,
  WorkList,
  PlaceList,
  SubjectList,
  LanguageList,
  PersonDetail,
  WorkDetail,
  PlaceDetail,
  SubjectDetail,
  LanguageDetail,
  Source,
  SourceInput,
  PersonConnectionInput,
  PlaceInput,
  NetworkData,
  OntologyGraph,
  OntologyAudit,
  PaginatedResponse,
  VerifyNameRequest,
} from '../types/entity'

export const entityService = {
  getPersons: async (
    page: number = 1,
    page_size: number = 100,
    source?: string,
    search?: string,
  ) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: page_size.toString(),
    })
    if (source) params.append('source', source)
    if (search) params.append('search', search)

    const response = await api.get<PaginatedResponse<PersonList>>(`/persons/?${params.toString()}`)
    return response.data
  },
  getWorks: async (page: number = 1, page_size: number = 100) => {
    const response = await api.get<PaginatedResponse<WorkList>>(
      `/works/?page=${page}&page_size=${page_size}`,
    )
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
  verifyPersonName: async (id: string, body: VerifyNameRequest) => {
    const response = await api.post<PersonDetail>(`/persons/${id}/name/verify`, body)
    return response.data
  },
  updatePersonConnections: async (id: string, connections: PersonConnectionInput[]) => {
    const response = await api.put<PersonDetail>(`/persons/${id}/connections`, { connections })
    return response.data
  },
  createPlace: async (body: PlaceInput) => {
    const response = await api.post<PlaceList>('/places/', body)
    return response.data
  },
  getWorkDetail: async (id: string) => {
    const response = await api.get<WorkDetail>(`/works/${id}`)
    return response.data
  },
  getPlaceDetail: async (id: string) => {
    const response = await api.get<PlaceDetail>(`/places/${id}`)
    return response.data
  },
  getSubjectDetail: async (id: string) => {
    const response = await api.get<SubjectDetail>(`/subjects/${id}`)
    return response.data
  },
  getLanguageDetail: async (id: string) => {
    const response = await api.get<LanguageDetail>(`/languages/${id}`)
    return response.data
  },
  getNetworkData: async (source?: string, bucket?: string) => {
    const params: Record<string, string> = {}
    if (source) params.source = source
    if (bucket) params.bucket = bucket
    const response = await api.get<NetworkData>('/network/', { params })
    return response.data
  },
  getSources: async () => {
    const response = await api.get<Source[]>('/sources/')
    return response.data
  },
  createSource: async (body: SourceInput) => {
    const response = await api.post<Source>('/sources/', body)
    return response.data
  },
  updateSource: async (id: string, body: SourceInput) => {
    const response = await api.put<Source>(`/sources/${id}`, body)
    return response.data
  },
  deleteSource: async (id: string) => {
    await api.delete(`/sources/${id}`)
  },
  getOntologyGraph: async () => {
    const response = await api.get<OntologyGraph>('/ontology/')
    return response.data
  },

  getOntologyAudit: async () => {
    const response = await api.get<OntologyAudit>('/ontology/audit')
    return response.data
  },
}
