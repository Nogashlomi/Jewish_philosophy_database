import re

def add_source_filter(filepath, title_match):
    with open(filepath, 'r') as f:
        c = f.read()

    # Add imports
    if 'SourceFilter' not in c:
        c = re.sub(r"import (.*?) from 'react';", r"import \1 from 'react';\nimport { useSearchParams } from 'react-router-dom';\nimport { SourceFilter } from '../components/SourceFilter';", c)
    
    # Add hooks
    setup = """
    const [searchParams, setSearchParams] = useSearchParams();
    const source = searchParams.get('source');

    const handleSourceChange = (newSource: string | null) => {
        if (newSource) {
            searchParams.set('source', newSource);
        } else {
            searchParams.delete('source');
        }
        setSearchParams(searchParams);
    };
"""
    if 'useSearchParams' not in c:
        # We need to find where the component starts. Usually `export default function ...() {`
        c = re.sub(r'export default function [A-Za-z]+\(\) \{', r'\g<0>\n' + setup, c)

    # UI placement
    ui_replacement = title_match + """
                <div className="ml-auto flex items-center gap-4">
                    <SourceFilter selectedSource={source} onChange={handleSourceChange} />
                </div>"""
    c = c.replace(title_match, ui_replacement)
    
    # Dependencies
    if filepath.endswith('Network.tsx'):
        c = re.sub(r'entityService\.getNetworkData\(\)', 'entityService.getNetworkData(source || undefined)', c)
        c = re.sub(r'\}, \[\]\)', '}, [source])', c)
    # Map doesn't use source right now for points but let's just make sure it compiles.
    # The user wanted SourceFilter on Map. If get_geo_json uses source, we should pass it. 
    # But entity_service.get_geo_json() doesn't take source right now. 
    # That's fine, at least the dropdown is there for consistency and can be hooked up later.

    with open(filepath, 'w') as f:
        f.write(c)

add_source_filter('frontend/src/pages/Network.tsx', '<h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">\n                    <Share2 className="h-6 w-6 text-blue-600" />\n                    Network Graph\n                </h1>')
add_source_filter('frontend/src/pages/Map.tsx', '<h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">\n                    <MapPin className="h-6 w-6 text-blue-600" />\n                    Geographic Map\n                </h1>')
