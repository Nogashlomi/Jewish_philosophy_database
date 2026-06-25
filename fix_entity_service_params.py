import re

with open('frontend/src/services/entityService.ts', 'r') as f:
    c = f.read()

c = re.sub(r'\s*const params: Record<string, any> = \{ page, page_size \}\n\s*const response = await api\.get<PaginatedResponse<PersonList>>\(\'/persons/\', \{ params \}\)', '\n        const response = await api.get<PaginatedResponse<PersonList>>(`/persons/?page=${page}&page_size=${page_size}`)', c)
c = re.sub(r'\s*const params: Record<string, any> = \{ page, page_size \}\n\s*const response = await api\.get<PaginatedResponse<WorkList>>\(\'/works/\', \{ params \}\)', '\n        const response = await api.get<PaginatedResponse<WorkList>>(`/works/?page=${page}&page_size=${page_size}`)', c)

with open('frontend/src/services/entityService.ts', 'w') as f:
    f.write(c)

