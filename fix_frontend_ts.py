import re

def add_imports(c):
    if 'useSearchParams' not in c:
        c = re.sub(r"import (.*?) from 'react';", r"import \1 from 'react';\nimport { useSearchParams } from 'react-router-dom';\nimport { SourceFilter } from '../components/SourceFilter';", c)
    return c

def fix_map():
    with open('frontend/src/pages/Map.tsx', 'r') as f:
        c = f.read()
    c = add_imports(c)
    # The UI replacement probably failed to find the title match.
    ui_target = """                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <MapPin className="h-6 w-6 text-blue-600" />
                    Geographic Map
                </h1>"""
    ui_replacement = ui_target + """
                <div className="ml-auto flex items-center gap-4">
                    <SourceFilter selectedSource={source} onChange={handleSourceChange} />
                </div>"""
    c = c.replace(ui_target, ui_replacement)
    # useSearchParams could be missing if it wasn't imported.
    with open('frontend/src/pages/Map.tsx', 'w') as f:
        f.write(c)

def fix_network():
    with open('frontend/src/pages/Network.tsx', 'r') as f:
        c = f.read()
    c = add_imports(c)
    ui_target = """                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <Share2 className="h-6 w-6 text-blue-600" />
                    Network Graph
                </h1>"""
    ui_replacement = ui_target + """
                <div className="ml-auto flex items-center gap-4">
                    <SourceFilter selectedSource={source} onChange={handleSourceChange} />
                </div>"""
    c = c.replace(ui_target, ui_replacement)
    with open('frontend/src/pages/Network.tsx', 'w') as f:
        f.write(c)

def fix_persons():
    with open('frontend/src/pages/Persons.tsx', 'r') as f:
        c = f.read()
    ui_target = """                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <ArrowUpDown className="h-6 w-6 text-blue-600" />
                    Persons
                </h1>"""
    ui_replacement = ui_target + """
                <div className="ml-auto flex items-center gap-4">
                    <SourceFilter selectedSource={source} onChange={handleSourceChange} />
                </div>"""
    if '<SourceFilter' not in c:
        c = c.replace(ui_target, ui_replacement)
    with open('frontend/src/pages/Persons.tsx', 'w') as f:
        f.write(c)

def fix_entity():
    with open('frontend/src/services/entityService.ts', 'r') as f:
        c = f.read()
    # getNetworkData source
    c = re.sub(r'const response = await api\.get<any>\(\'/network/\', source \? \{ params: \{ source \} \} : \{\}\)', 'const response = await api.get<any>(\'/network/\', { params: source ? { source } : {} })', c)
    with open('frontend/src/services/entityService.ts', 'w') as f:
        f.write(c)

fix_map()
fix_network()
fix_persons()
fix_entity()
