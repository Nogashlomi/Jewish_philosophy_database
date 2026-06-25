import re

with open('frontend/src/services/entityService.ts', 'r') as f:
    c = f.read()

# getPersons: add source parameter
c = re.sub(r'getPersons: async \(page: number = 1, page_size: number = 100\) => \{', 'getPersons: async (page: number = 1, page_size: number = 100, source?: string) => {', c)
c = re.sub(r'const response = await api\.get<PaginatedResponse<PersonList>>\(`/persons/\?page=\$\{page\}&page_size=\$\{page_size\}`\)', 'const url = source ? `/persons/?page=${page}&page_size=${page_size}&source=${source}` : `/persons/?page=${page}&page_size=${page_size}`\n        const response = await api.get<PaginatedResponse<PersonList>>(url)', c)

# getNetworkData: add source parameter
c = re.sub(r'getNetworkData: async \(\) => \{', 'getNetworkData: async (source?: string) => {', c)
c = re.sub(r'const params = \{\}', 'const params = source ? { source } : {}', c)
# Actually `const params = {}` was replaced with empty earlier.
c = re.sub(r'const response = await api\.get<any>\(\'/network/\', \{ params \}\)', 'const response = await api.get<any>(\'/network/\', source ? { params: { source } } : {})', c)

if 'getSources' not in c:
    sources_fn = """
    getSources: async () => {
        const response = await api.get<any[]>('/sources/')
        return response.data
    },"""
    c = c.replace('getOntologyGraph: async', sources_fn + '\n    getOntologyGraph: async')

with open('frontend/src/services/entityService.ts', 'w') as f:
    f.write(c)

