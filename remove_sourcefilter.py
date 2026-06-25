import re
import os

def process_file(filepath):
    with open(filepath, 'r') as f:
        c = f.read()
    
    # Remove import SourceFilter
    c = re.sub(r'import SourceFilter from \'../components/SourceFilter\'\n', '', c)
    c = re.sub(r'import SourceFilter from \'../components/SourceFilter\';?\n', '', c)
    
    # Remove selectedSource state / searchParams
    c = re.sub(r'\s*const selectedSource = searchParams\.get\(\'source\'\);?\n', '\n', c)
    
    # Remove handleSourceChange
    c = re.sub(r'\s*const handleSourceChange = \(source: string \| null\) => \{\n(?:[^{}]|\{[^{}]*\})*?\};?\n', '\n', c, flags=re.DOTALL)
    
    # Remove <SourceFilter ... /> component block
    c = re.sub(r'\s*<SourceFilter[^>]*/>\n', '\n', c, flags=re.DOTALL)
    
    # Update entityService calls to remove selectedSource
    c = re.sub(r'\(selectedSource \|\| undefined, ', '(', c)
    c = re.sub(r'\(selectedSource \|\| undefined\)', '()', c)
    c = re.sub(r'fetchGeoJSON\(selectedSource\)', 'fetchGeoJSON()', c)
    c = re.sub(r'entityService\.getNetworkData\(selectedSource \|\| undefined\)', 'entityService.getNetworkData()', c)
    
    # queryKey: ['...', selectedSource]
    c = re.sub(r"queryKey: \['([^']+)', selectedSource\]", r"queryKey: ['\1']", c)
    
    # UseEffect dependencies
    c = re.sub(r'\[selectedSource\]', '[]', c)
    c = re.sub(r'\[selectedSource, ', '[', c)
    
    with open(filepath, 'w') as f:
        f.write(c)

pages = [
    'frontend/src/pages/Languages.tsx',
    'frontend/src/pages/Works.tsx',
    'frontend/src/pages/Persons.tsx',
    'frontend/src/pages/Map.tsx',
    'frontend/src/pages/Places.tsx',
    'frontend/src/pages/Subjects.tsx',
    'frontend/src/pages/Network.tsx'
]

for p in pages:
    process_file(p)

# Update App.tsx
with open('frontend/src/App.tsx', 'r') as f:
    app_c = f.read()
app_c = re.sub(r'import Sources from \'./pages/Sources\'\n', '', app_c)
app_c = re.sub(r'import SourceDetail from \'./pages/SourceDetail\'\n', '', app_c)
app_c = re.sub(r'\s*<Route path="sources" element=\{<Sources />\} />\n', '\n', app_c)
app_c = re.sub(r'\s*<Route path="sources/:id" element=\{<SourceDetail />\} />\n', '\n', app_c)
with open('frontend/src/App.tsx', 'w') as f:
    f.write(app_c)

# Update PersonDetail and WorkDetail
def remove_sources_block(filepath):
    with open(filepath, 'r') as f:
        c = f.read()
    c = re.sub(r'\{\s*/\* Sources \*/\s*\}(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?Data Sources(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?</div>\s*</div>', '', c, flags=re.DOTALL)
    with open(filepath, 'w') as f:
        f.write(c)

remove_sources_block('frontend/src/pages/PersonDetail.tsx')
remove_sources_block('frontend/src/pages/WorkDetail.tsx')

