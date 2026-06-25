import re

with open('frontend/src/pages/PersonDetail.tsx', 'r') as f:
    c = f.read()

c = re.sub(r'ExternalLink,?\s*', '', c)

with open('frontend/src/pages/PersonDetail.tsx', 'w') as f:
    f.write(c)

with open('frontend/src/services/entityService.ts', 'r') as f:
    c = f.read()

# getPersons
c = re.sub(r'const params: Record<string, any> = \{ page, page_size \}\n\s*if \(source\) params\.source = source\n\s*const response = await api\.get<PaginatedResponse<PersonList>>\(\'/persons/\', \{ params \}\)', 'const response = await api.get<PaginatedResponse<PersonList>>(`/persons/?page=${page}&page_size=${page_size}`)', c)
# I already replaced the if (source) part. The code probably just has:
c = re.sub(r'\s*const params: Record<string, any> = \{ page, page_size \}', '', c)

with open('frontend/src/services/entityService.ts', 'w') as f:
    f.write(c)
