import { useQuery } from '@tanstack/react-query'
import { entityService } from '../services/entityService'
import ForceGraph2D from 'react-force-graph-2d'
import { Loader2, Search } from 'lucide-react'
import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import SourceFilter from '../components/SourceFilter'

// Color mapping from original app
const COLORS = {
    HistoricalPerson: '#e74c3c', // Red
    HistoricalWork: '#3498db',   // Blue
    ScholarlyWork: '#9b59b6',    // Purple
    Place: '#2ecc71',            // Green
    Subject: '#f1c40f',          // Yellow
    HistoricalLanguage: '#95a5a6' // Grey
}

const LEGEND_ITEMS = [
    { label: 'Person', color: COLORS.HistoricalPerson, type: 'HistoricalPerson' },
    { label: 'Work', color: COLORS.HistoricalWork, type: 'HistoricalWork' },
    { label: 'Scholarly', color: COLORS.ScholarlyWork, type: 'ScholarlyWork' },
    { label: 'Place', color: COLORS.Place, type: 'Place' },
    { label: 'Subject', color: COLORS.Subject, type: 'Subject' },
    { label: 'Language', color: COLORS.HistoricalLanguage, type: 'HistoricalLanguage' },
]

export default function Network() {
    const navigate = useNavigate()
    const fgRef = useRef<any>(null)
    const [searchParams, setSearchParams] = useSearchParams();
    const selectedSource = searchParams.get('source');

    const { data, isLoading, error } = useQuery({
        queryKey: ['network', selectedSource],
        queryFn: () => entityService.getNetworkData(selectedSource || undefined),
    })

    const [graphData, setGraphData] = useState<{ nodes: any[], links: any[] } | null>(null)
    const [searchTerm, setSearchTerm] = useState('')

    // Filters State
    const [selectedTypes, setSelectedTypes] = useState<Record<string, boolean>>({
        HistoricalPerson: true,
        HistoricalWork: true,
        ScholarlyWork: true,
        Place: true,
        Subject: true,
        HistoricalLanguage: true
    })

    const handleSourceChange = (source: string | null) => {
        if (source) {
            setSearchParams({ source });
        } else {
            setSearchParams({});
        }
    };

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
                <h1 className="text-2xl font-bold font-sans">Network Graph</h1>
                <span className="text-sm text-gray-500 font-sans">
                    Nodes: {filteredData.nodes.length}, Edges: {filteredData.links.length}
                </span>
            </div>

            <div className="flex flex-1 border border-gray-200 rounded-lg overflow-hidden bg-slate-50 relative">

                {/* Sidebar Controls & Index */}
                <div className="w-80 bg-white border-r border-gray-200 flex flex-col z-10 shrink-0">

                    {/* Filters Section */}
                    <div className="p-4 border-b border-gray-200 bg-gray-50">
                        <div className="mb-4">
                            <SourceFilter
                                selectedSource={selectedSource}
                                onSourceChange={handleSourceChange}
                            />
                        </div>

                        <div className="mb-2">
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Show Types</label>
                            <div className="space-y-1">
                                {LEGEND_ITEMS.map(item => (
                                    <label key={item.type} className="flex items-center space-x-2 text-sm cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={selectedTypes[item.type]}
                                            onChange={() => toggleType(item.type)}
                                            className="rounded text-indigo-600 focus:ring-indigo-500"
                                        />
                                        <span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: item.color }}></span>
                                        <span className="text-gray-700">{item.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Search Section */}
                    <div className="p-4 border-b border-gray-100">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search filtered nodes..."
                                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                            <Search className="h-4 w-4 text-gray-400 absolute left-3 top-2.5" />
                        </div>
                    </div>

                    {/* Node List */}
                    <div className="flex-1 overflow-y-auto">
                        {sidebarNodes.length > 0 ? (
                            <div className="divide-y divide-gray-100">
                                {sidebarNodes.map((node) => (
                                    <button
                                        key={node.id}
                                        onClick={() => handleSidebarNodeClick(node)}
                                        className="w-full text-left px-4 py-2 hover:bg-indigo-50 transition-colors group"
                                    >
                                        <div className="text-sm font-medium text-gray-900 group-hover:text-indigo-700 truncate">
                                            {node.label}
                                        </div>
                                        <div className="text-xs text-gray-500 mt-0.5 capitalize flex items-center gap-1">
                                            <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: COLORS[node.group as keyof typeof COLORS] }}></span>
                                            {node.group?.replace('Historical', '')}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <div className="p-4 text-sm text-gray-500 text-center">
                                No nodes found
                            </div>
                        )}
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
                            else if (node.group === 'HistoricalLanguage') navigate(`/languages/${node.id}`)
                            else if (node.group === 'ScholarlyWork') navigate(`/scholarly/${node.id}`)
                        }}
                        width={800} // Dynamic sizing is tricky in wrappers, but flexbox helps
                        height={600}
                        cooldownTicks={100}
                        onEngineStop={() => fgRef.current?.zoomToFit(400)}
                    />

                    {/* Legend Overlay */}
                    <div className="absolute top-4 right-4 bg-white/90 p-3 rounded shadow text-xs border border-gray-200">
                        <h4 className="font-bold mb-2">Legend</h4>
                        <div className="space-y-1">
                            {LEGEND_ITEMS.map(item => (
                                <div key={item.type} className="flex items-center space-x-2">
                                    <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: item.color }}></span>
                                    <span>{item.label}</span>
                                </div>
                            ))}
                        </div>
                        <div className="mt-3 pt-2 border-t border-gray-200 text-gray-500">
                            <p>Scroll to Zoom</p>
                            <p>Drag to Pan</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
