import { useSearchParams } from 'react-router-dom';
import { SourceFilter } from '../components/SourceFilter';
import { useQuery } from '@tanstack/react-query'
import { entityService } from '../services/entityService'
import ForceGraph2D from 'react-force-graph-2d'
import { Loader2, Search } from 'lucide-react'
import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate, } from 'react-router-dom'

// Color mapping from original app
const COLORS = {
    HistoricalPerson: '#e74c3c', // Red
    HistoricalWork: '#3498db',   // Blue
    Place: '#2ecc71',            // Green
    Subject: '#f1c40f',          // Yellow
    Language: '#95a5a6' // Grey
}

const LEGEND_ITEMS = [
    { label: 'Person', color: COLORS.HistoricalPerson, type: 'HistoricalPerson' },
    { label: 'Work', color: COLORS.HistoricalWork, type: 'HistoricalWork' },
    
    { label: 'Place', color: COLORS.Place, type: 'Place' },
    { label: 'Subject', color: COLORS.Subject, type: 'Subject' },
    { label: 'Language', color: COLORS.Language, type: 'Language' },
]

export default function Network() {

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

    const navigate = useNavigate()
    const fgRef = useRef<any>(null)

    const { data, isLoading, error } = useQuery({
        queryKey: ['network'],
        queryFn: () => entityService.getNetworkData(source || undefined),
    })

    const [graphData, setGraphData] = useState<{ nodes: any[], links: any[] } | null>(null)
    const [searchTerm, setSearchTerm] = useState('')

    // Filters State
    const [selectedTypes, setSelectedTypes] = useState<Record<string, boolean>>({
        HistoricalPerson: true,
        HistoricalWork: true,
        
        Place: true,
        Subject: true,
        HistoricalLanguage: true
    })

    useEffect(() => {
        if (data) {
            const nodes = data.nodes.map((n: any) => ({ ...n }))
            const links = data.edges.map((e: any) => ({
                source: e.from,
                target: e.to
            }))
            setGraphData({ nodes, links })
        }
    }, [data])

    // Derived Filtering Logic
    const filteredData = useMemo(() => {
        if (!graphData) return { nodes: [], links: [] }

        // 1. Filter Nodes
        const nodes = graphData.nodes.filter(node => {
            // Type Filter
            if (!selectedTypes[node.group]) return false
            return true
        })

        const visibleNodeIds = new Set(nodes.map(n => n.id))

        // 2. Filter Links (both ends must be visible)
        let links = graphData.links.filter(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source
            const targetId = typeof l.target === 'object' ? l.target.id : l.target
            return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId)
        })

        return { nodes, links }
    }, [graphData, selectedTypes])

    // Sidebar List Filtering (Search)
    const sidebarNodes = useMemo(() => {
        return filteredData.nodes.filter(node =>
            node.label.toLowerCase().includes(searchTerm.toLowerCase())
        ).sort((a, b) => a.label.localeCompare(b.label))
    }, [filteredData, searchTerm])


    const handleSidebarNodeClick = (node: any) => {
        if (fgRef.current) {
            fgRef.current.centerAt(node.x, node.y, 1000)
            fgRef.current.zoom(8, 2000)
        }
    }

    const toggleType = (type: string) => {
        setSelectedTypes(prev => ({ ...prev, [type]: !prev[type] }))
    }

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading data</div>
    if (!graphData) return null

    return (
        <div className="space-y-4 h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold font-sans">Network Graph</h1>
                    <span className="text-sm text-gray-500 font-sans mt-1">
                        Nodes: {filteredData.nodes.length}, Edges: {filteredData.links.length}
                    </span>
                </div>
                <div className="ml-auto">
                    <SourceFilter selectedSource={source} onChange={handleSourceChange} />
                </div>
            </div>

            <div className="flex flex-1 border border-gray-200 rounded-lg overflow-hidden bg-slate-50 relative">

                {/* Sidebar Controls & Index */}
                <div className="w-80 bg-white border-r border-gray-200 flex flex-col z-10 shrink-0">

                    {/* Filters Section */}
                    <div className="p-4 border-b border-gray-200 bg-gray-50 flex-1">
                        <div className="mb-2">
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Show Types</label>
                            <div className="space-y-3">
                                {LEGEND_ITEMS.map(item => (
                                    <label key={item.type} className="flex items-center space-x-3 text-sm cursor-pointer p-2 rounded hover:bg-gray-100 transition-colors">
                                        <input
                                            type="checkbox"
                                            checked={selectedTypes[item.type]}
                                            onChange={() => toggleType(item.type)}
                                            className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                                        />
                                        <span className="w-4 h-4 rounded-sm shadow-sm inline-block" style={{ backgroundColor: item.color }}></span>
                                        <span className="text-gray-700 font-medium">{item.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Graph Container */}
                <div className="flex-1 relative">
                    <ForceGraph2D
                        ref={fgRef}
                        graphData={filteredData}
                        nodeLabel="label"
                        nodeColor={(node: any) => COLORS[node.group as keyof typeof COLORS] || '#ccc'}
                        linkDirectionalArrowLength={3.5}
                        linkDirectionalArrowRelPos={1}
                        onNodeClick={(node: any) => {
                            if (node.group === 'HistoricalPerson') navigate(`/persons/${node.id}`)
                            else if (node.group === 'HistoricalWork') navigate(`/works/${node.id}`)
                            else if (node.group === 'Place') navigate(`/places/${node.id}`)
                            else if (node.group === 'Subject') navigate(`/subjects/${node.id}`)
                            else if (node.group === 'Language') navigate(`/languages/${node.id}`)
                            
                        }}
                        width={800} // Dynamic sizing is tricky in wrappers, but flexbox helps
                        height={600}
                        cooldownTicks={100}
                        onEngineStop={() => fgRef.current?.zoomToFit(400)}
                    />


                </div>
            </div>
        </div>
    )
}
