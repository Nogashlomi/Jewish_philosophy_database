import re

with open('frontend/src/pages/Persons.tsx', 'r') as f:
    c = f.read()

imports = """import { useSearchParams } from 'react-router-dom';
import { SourceFilter } from '../components/SourceFilter';
"""
c = re.sub(r"import \{ Link \} from 'react-router-dom';", "import { Link } from 'react-router-dom';\n" + imports, c)

# Inside Persons component
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
        setPage(1); // Reset page on source change
    };
"""
c = re.sub(r'const \[page, setPage\] = useState\(1\);', 'const [page, setPage] = useState(1);\n' + setup, c)

# update fetchPersons
c = re.sub(r'entityService\.getPersons\(page, PAGE_SIZE\)', 'entityService.getPersons(page, PAGE_SIZE, source || undefined)', c)
c = re.sub(r'\}, \[page\]\)', '}, [page, source])', c)

# UI placement
ui_target = """                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <ArrowUpDown className="h-6 w-6 text-blue-600" />
                    Persons
                </h1>"""
ui_replacement = ui_target + """
                <div className="ml-auto flex items-center gap-4">
                    <SourceFilter selectedSource={source} onChange={handleSourceChange} />
                </div>"""
c = c.replace(ui_target, ui_replacement)

with open('frontend/src/pages/Persons.tsx', 'w') as f:
    f.write(c)
