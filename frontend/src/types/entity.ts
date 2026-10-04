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
  time_buckets?: string
  subjects?: string
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
}

export interface LanguageList {
  id: string
  label: string
  count: number
  works?: number
}

// Minimal Detail interfaces for now, extend as needed
export interface PersonDetail {
  id: string
  uri: string
  label: string
  works: RelatedWork[]
  places: PlaceRelation[]
  times: TimeRelation[]
  time_buckets: string[]
  subjects?: string[]
  languages?: string[]
}

export interface RelatedWork {
  id: string
  uri: string
  title: string
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
  label?: string
}

export interface WorkAuthor {
  id: string
  uri: string
  label: string
}

export interface ScholarlyMention {
  id: string
  title: string
  year?: string
}

export interface WorkDetail {
  id: string
  uri: string
  title: string
  authors: WorkAuthor[]
  subjects: string[]
  languages: string[]
  places: PlaceRelation[]
  times: TimeRelation[]
  sources?: string[]
  scholarly_mentions?: ScholarlyMention[]
}

export interface PersonAtPlace {
  id: string
  label: string
  type?: string
}

export interface PlaceDetail {
  id: string
  uri: string
  label: string
  lat?: string
  long?: string
  people: PersonAtPlace[]
}

export interface SubjectWorkInfo {
  id: string
  title: string
}

export interface SubjectDetail {
  label: string
  works: SubjectWorkInfo[]
}

export interface LanguagePersonInfo {
  id: string
  name: string
}

export interface LanguageDetail {
  label: string
  persons: LanguagePersonInfo[]
}

export interface Source {
  id: string
  label: string
  description: string
  count: number
}

export interface NetworkNode {
  id: string
  label: string
  group: string
  buckets: string[]
}

export interface NetworkEdge {
  from: string
  to: string
  relation?: string
  dashes?: boolean
}

export interface NetworkData {
  nodes: NetworkNode[]
  edges: NetworkEdge[]
}

export interface OntologyNode {
  id: string
  label: string
  title?: string | null
  group: string
}

export interface OntologyEdge {
  from: string
  to: string
  label: string
}

export interface OntologyGraph {
  nodes: OntologyNode[]
  edges: OntologyEdge[]
}

export interface OntologyAuditSection {
  defined_count: number
  actual_count: number
  unused: string[]
  undefined: string[]
}

export interface OntologyAudit {
  classes: OntologyAuditSection
  properties: OntologyAuditSection
}
