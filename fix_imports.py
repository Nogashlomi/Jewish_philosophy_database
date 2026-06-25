import re

for filepath in ['frontend/src/pages/Map.tsx', 'frontend/src/pages/Network.tsx']:
    with open(filepath, 'r') as f:
        c = f.read()
    
    # Add imports at the beginning
    if 'useSearchParams' not in c[:1000]: # check if imported at top
        c = "import { useSearchParams } from 'react-router-dom';\nimport { SourceFilter } from '../components/SourceFilter';\n" + c
    
    with open(filepath, 'w') as f:
        f.write(c)

with open('frontend/src/pages/Persons.tsx', 'r') as f:
    c = f.read()
if "import { SourceFilter } from '../components/SourceFilter';" not in c:
    c = "import { SourceFilter } from '../components/SourceFilter';\n" + c
with open('frontend/src/pages/Persons.tsx', 'w') as f:
    f.write(c)

# Fix entityService unused source in getNetworkData
with open('frontend/src/services/entityService.ts', 'r') as f:
    c = f.read()
c = re.sub(r'getNetworkData: async \(source\?: string\) => \{', 'getNetworkData: async (source?: string) => {', c)
# If it's unused, let's remove it entirely for now to fix compile error? No, I need it to pass to the backend!
# In entityService.ts: const response = await api.get<any>('/network/', { params: source ? { source } : {} })
# Oh, it's unused if I didn't successfully do that replacement. Let's force it.
c = re.sub(r'const response = await api\.get<any>\(\'/network/\', \{ params: source \? \{ source \} : \{\} \}\)', 'const response = await api.get<any>(\'/network/\', { params: source ? { source } : {} })', c)
with open('frontend/src/services/entityService.ts', 'w') as f:
    f.write(c)

