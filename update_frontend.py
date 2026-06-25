import re
import os

def rewrite_file(filepath, callback):
    with open(filepath, 'r') as f:
        content = f.read()
    new_content = callback(content)
    with open(filepath, 'w') as f:
        f.write(new_content)

def fix_app(c):
    c = re.sub(r'import Scholarly from \'\./pages/Scholarly\'\n', '', c)
    c = re.sub(r'import ScholarlyDetail from \'\./pages/ScholarlyDetail\'\n', '', c)
    c = re.sub(r'\s*<Route path="scholarly" element=\{<Scholarly />\} />\n', '\n', c)
    c = re.sub(r'\s*<Route path="scholarly/:id" element=\{<ScholarlyDetail />\} />\n', '\n', c)
    return c

def fix_layout(c):
    # Remove the Scholarly Works NavLink block
    pattern = r'<NavLink\s+to="/scholarly"\s+className=\{.*?\}\s*>\s*Scholarly Works\s*</NavLink>'
    c = re.sub(pattern, '', c, flags=re.DOTALL)
    return c

def fix_home(c):
    # Remove scholarly from stats grid
    pattern = r'\{ label: "Scholarly Works".*?\},'
    c = re.sub(pattern, '', c)
    # Also remove "scholarly: number" from GlobalStats interface if it exists
    c = re.sub(r'scholarly\??:\s*number\s*;?', '', c)
    # Also remove the "Sources" card
    c = re.sub(r'\{ label: "Data Sources".*?\},', '', c)
    c = re.sub(r'sources\??:\s*number\s*;?', '', c)
    return c

def fix_source_detail(c):
    # Delete the whole SourceDetail file or just ignore it since it's being deleted anyway?
    pass

def fix_person_detail(c):
    # Remove Scholarly Mentions block
    c = re.sub(r'\{\s*/\* Scholarly Mentions \*/\s*\}(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?Scholarly Mentions(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?</div>\s*</div>', '', c, flags=re.DOTALL)
    # Remove authorities
    c = re.sub(r'\{\s*/\* External Authorities \*/\s*\}(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?External Authorities(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?</div>\s*</div>', '', c, flags=re.DOTALL)
    return c

def fix_work_detail(c):
    # Remove Scholarly Mentions block
    c = re.sub(r'\{\s*/\* Scholarly Mentions \*/\s*\}(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?Scholarly Mentions(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?</div>\s*</div>', '', c, flags=re.DOTALL)
    return c

def fix_network(c):
    c = re.sub(r'ScholarlyWork: \'#9b59b6\',\s*// Purple\n', '', c)
    c = re.sub(r'\{\s*label:\s*\'Scholarly\',\s*color:\s*COLORS\.ScholarlyWork,\s*type:\s*\'ScholarlyWork\'\s*\},', '', c)
    c = re.sub(r'ScholarlyWork:\s*true,', '', c)
    c = re.sub(r'else if \(node\.group === \'ScholarlyWork\'\) navigate\(`/scholarly/\$\{node\.id\}`\)', '', c)
    return c

def fix_entity_service(c):
    c = re.sub(r'ScholarlyList, ', '', c)
    c = re.sub(r'ScholarlyList', '', c)
    # Remove getScholarlyWorks
    c = re.sub(r'getScholarlyWorks: async \(.*?\) => \{\n(?:[^{}]|\{[^{}]*\})*?\},\n', '', c, flags=re.DOTALL)
    c = re.sub(r'getScholarlyDetail: async \(.*?\) => \{\n(?:[^{}]|\{[^{}]*\})*?\},?\n', '', c, flags=re.DOTALL)
    # Remove source parameter from all other methods
    c = re.sub(r'\(source\?: string\) => \{', '() => {', c)
    c = re.sub(r'\(source\?: string, ', '(', c)
    c = re.sub(r'params:\s*\{\s*source\s*\},?', '', c)
    c = re.sub(r'params:\s*\{\s*source,\s*', 'params: { ', c)
    return c

rewrite_file('frontend/src/App.tsx', fix_app)
rewrite_file('frontend/src/components/Layout.tsx', fix_layout)
rewrite_file('frontend/src/pages/Home.tsx', fix_home)
rewrite_file('frontend/src/pages/PersonDetail.tsx', fix_person_detail)
rewrite_file('frontend/src/pages/WorkDetail.tsx', fix_work_detail)
rewrite_file('frontend/src/pages/Network.tsx', fix_network)
rewrite_file('frontend/src/services/entityService.ts', fix_entity_service)

