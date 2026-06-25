import re

def rewrite(filepath, fn):
    with open(filepath, 'r') as f:
        c = f.read()
    c = fn(c)
    with open(filepath, 'w') as f:
        f.write(c)

def fix_unused(c):
    c = re.sub(r'\s*const \[searchParams, setSearchParams\] = useSearchParams\(\);?', '', c)
    c = re.sub(r'\s*const handleSourceChange = \(.*?\) => \{.*?\};', '', c, flags=re.DOTALL)
    c = re.sub(r'Legend,?\s*', '', c)
    return c

for p in ['frontend/src/pages/Languages.tsx', 'frontend/src/pages/Map.tsx', 'frontend/src/pages/Network.tsx', 'frontend/src/pages/Persons.tsx', 'frontend/src/pages/Places.tsx', 'frontend/src/pages/Subjects.tsx', 'frontend/src/pages/Works.tsx']:
    rewrite(p, fix_unused)

# PersonDetail
def fix_person_detail(c):
    # The previous regex might have missed them if there was extra whitespace or different formatting.
    # Let's just remove the lines referencing them.
    # We need to remove the whole blocks for Scholarly, Sources, Authorities.
    c = re.sub(r'\{\s*/\*\s*Scholarly Mentions\s*\*/\s*\}(?:[^{}]|\{[^{}]*\})*?person\.scholarly(?:[^{}]|\{[^{}]*\})*?</div>\s*</div>\s*</div>', '', c, flags=re.DOTALL)
    # Actually it's easier to just strip out everything after "Works" section if I can, or use specific regex for the JSX.
    c = re.sub(r'\{\s*/\*\s*Scholarly Mentions\s*\*/\s*\}.*?(?=\{\s*/\*|$)', '', c, flags=re.DOTALL)
    c = re.sub(r'\{\s*/\*\s*Data Sources\s*\*/\s*\}.*?(?=\{\s*/\*|$)', '', c, flags=re.DOTALL)
    c = re.sub(r'\{\s*/\*\s*Sources\s*\*/\s*\}.*?(?=\{\s*/\*|$)', '', c, flags=re.DOTALL)
    c = re.sub(r'\{\s*/\*\s*External Authorities\s*\*/\s*\}.*?(?=\{\s*/\*|$)', '', c, flags=re.DOTALL)
    return c

rewrite('frontend/src/pages/PersonDetail.tsx', fix_person_detail)

def fix_entity_service(c):
    # entityService.ts has params: { source } remaining
    c = re.sub(r'params:\s*\{\s*source\s*\},?', '', c)
    c = re.sub(r'params:\s*\{\s*\},?', '', c)
    c = re.sub(r',\s*\}', '}', c)
    return c

rewrite('frontend/src/services/entityService.ts', fix_entity_service)

