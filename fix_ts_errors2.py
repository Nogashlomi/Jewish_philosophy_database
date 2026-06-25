import re

def rewrite(filepath, fn):
    with open(filepath, 'r') as f:
        c = f.read()
    c = fn(c)
    with open(filepath, 'w') as f:
        f.write(c)

def fix_imports(c):
    c = re.sub(r'useSearchParams,?\s*', '', c)
    c = re.sub(r'GraduationCap,?\s*', '', c)
    # clean up empty import braces
    c = re.sub(r'import\s*\{\s*\}\s*from\s*[\'"].*?[\'"];?\n', '', c)
    return c

for p in ['frontend/src/pages/Languages.tsx', 'frontend/src/pages/Map.tsx', 'frontend/src/pages/Network.tsx', 'frontend/src/pages/Persons.tsx', 'frontend/src/pages/Places.tsx', 'frontend/src/pages/Subjects.tsx', 'frontend/src/pages/Works.tsx', 'frontend/src/pages/PersonDetail.tsx']:
    rewrite(p, fix_imports)

# PersonDetail remaining authorities
def fix_person_detail(c):
    c = re.sub(r'\{\s*/\*\s*External Authorities\s*\*/\s*\}.*?(?=\{\s*/\*|$)', '', c, flags=re.DOTALL)
    # Also if it's the last element before closing tags:
    c = re.sub(r'\{\s*/\*\s*External Authorities\s*\*/\s*\}.*?</div>\s*</div>\s*</div>', '</div>\n</div>', c, flags=re.DOTALL)
    return c
rewrite('frontend/src/pages/PersonDetail.tsx', fix_person_detail)

# entityService.ts
def fix_entity_service(c):
    c = re.sub(r'params:\s*\{\s*source\s*\}', 'params: {}', c)
    c = re.sub(r'const\s*params\s*=\s*\{\s*source\s*\}', 'const params = {}', c)
    # let's just remove the `source` reference entirely inside the methods
    c = re.sub(r'source,?', '', c)
    # Actually `source` was removed from function arguments so any reference to `source` inside the function is an error.
    # Let's replace any `{ source }` with `{}`
    return c

# Wait, `source` is used as `import { Source } from '...'`? I deleted it.
with open('frontend/src/services/entityService.ts', 'r') as f:
    c = f.read()
    c = re.sub(r'\{\s*source\s*\}', '{}', c)
    c = re.sub(r',\s*source\s*\}', '}', c)
    c = re.sub(r'\{\s*source\s*,', '{', c)
with open('frontend/src/services/entityService.ts', 'w') as f:
    f.write(c)

