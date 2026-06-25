import re

def rewrite(filepath, fn):
    with open(filepath, 'r') as f:
        c = f.read()
    c = fn(c)
    with open(filepath, 'w') as f:
        f.write(c)

def fix_person(c):
    c = re.sub(r'\{\s*/\*\s*Authority Links\s*\*/\s*\}(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?External Authorities(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?</div>\s*</div>\s*</div>', '</div>\n</div>', c, flags=re.DOTALL)
    # Actually just remove anything from {/* Authority Links */} to the end of the block.
    c = re.sub(r'\{\s*/\*\s*Authority Links\s*\*/\s*\}.*?External Authorities.*?</div>\s*</div>\s*</div>\s*\}', '', c, flags=re.DOTALL)
    return c

rewrite('frontend/src/pages/PersonDetail.tsx', fix_person)

def fix_service(c):
    c = re.sub(r'if \(source\) params\.source = source\n', '', c)
    c = re.sub(r'const params = source \? \{\} : \{\}\n', '', c)
    c = re.sub(r'\{ params \}', '{}', c)
    c = re.sub(r', \{\s*\}', '', c)
    return c

rewrite('frontend/src/services/entityService.ts', fix_service)
