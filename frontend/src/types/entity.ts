export interface PersonList {
    id: string
    uri: string
    label: string
    birth_year?: string
    death_year?: string
    workCount: number
    mentionCount: number
    places: string
    times: string
}

export interface PaginatedResponse<T> {
    items: T[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface WorkList {
    id: string
    uri: string
    title: string
    creation_year?: string
    authors?: string
    subjects?: string
    languages?: string
    mentionCount: number
}

export interface PlaceList {
    id: string
    uri: string
    label: string
    lat?: string
    long?: string
    personCount: number
}

export interface SubjectList {
    id: string
    label: string
    count: number
    authors?: number
    works?: number
}

export interface LanguageList {
    id: string
    label: string
    count: number
}

export interface Scholar {
    id: string
    name: string
}

export interface Source {
    id: string
    label: string
}

export interface ScholarlyList {
    uri: string
    id: string
    title: string
    year?: string
    authors: Scholar[]
    sources?: Source[]
    publisher?: string
    type?: string
    mentions_person_count: number
    mentions_work_count: number
}

// Minimal Detail interfaces for now, extend as needed
export interface PersonDetail {
    id: string
    uri: string
    label: string
    sources: string[]
    authorities: string[]
    works: RelatedWork[]
    scholarly: ScholarlyMention[]
    places: PlaceRelation[]
    times: TimeRelation[]
    subjects?: string[]
    languages?: string[]
}

export interface RelatedWork {
    id: string
    uri: string
    title: string
}

export interface ScholarlyMention {
    id: string
    uri: string
    title: string
    year?: string
}

export interface PlaceRelation {
    place_id: string
    place_uri: string
    label: string
    type?: string
}

export interface TimeRelation {
    type?: string
    start?: string
    end?: string
}
