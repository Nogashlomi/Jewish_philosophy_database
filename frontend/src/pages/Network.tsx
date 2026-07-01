import { useSearchParams } from 'react-router-dom';
import { SourceFilter } from '../components/SourceFilter';
import { useQuery } from '@tanstack/react-query'
import { entityService } from '../services/entityService'
import ForceGraph2D from 'react-force-graph-2d'
import { Loader2 } from 'lucide-react'
import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate, } from 'react-router-dom'
import Slider from 'rc-slider'
import 'rc-slider/assets/index.css'

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

// Generate buckets list
const bucketsList: number[] = [];
for (let y = -200; y <= 2050; y += 50) {
    bucketsList.push(y);
}

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

    const [timeRange, setTimeRange] = useState<[number, number]>([-200, 2050]);

    const { data, isLoading, error } = useQuery({
        queryKey: ['network', source],
        queryFn: () => entityService.getNetworkData(source || undefined),
    })

    const [graphData, setGraphData] = useState<{ nodes: any[], links: any[] } | null>(null)
    
    // Keep a ref to preserve node objects (and their x, y coordinates) across renders/fetches
    const nodeCache = useRef<Map<string, any>>(new Map())

    // Filters State
    const [selectedTypes, setSelectedTypes] = useState<Record<string, boolean>>({
        HistoricalPerson: true,
        HistoricalWork: true,
        Place: true,
        Subject: true,
        Language: true,
        HistoricalLanguage: true // For backward compatibility
    })

    useEffect(() => {
        if (data) {
            const currentCache = nodeCache.current
            const nodes = data.nodes.map((n: any) => {
                if (currentCache.has(n.id)) {
                    const existingNode = currentCache.get(n.id)
                    Object.assign(existingNode, n)
                    return existingNode
                } else {
                    const newNode = { ...n }
                    currentCache.set(n.id, newNode)
                    return newNode
                }
            })
            const links = data.edges.map((e: any) => ({
                source: e.from,
                target: e.to,
                dashes: e.dashes
            }))
            setGraphData({ nodes, links })
        }
    }, [data])

    // Derived Filtering Logic
    const filteredData = useMemo(() => {
        if (!graphData) return { nodes: [], links: [] }

        const isTimeFilterActive = timeRange[0] > -200 || timeRange[1] < 2050;
        let keptNodes = new Set<string>();

        if (isTimeFilterActive) {
            const validPersons = new Set<string>();
            graphData.nodes.forEach(n => {
                if (n.group === 'HistoricalPerson') {
                    if (n.buckets && n.buckets.length > 0) {
                        const inRange = n.buckets.some((b: string) => {
                            let isBCE = b.includes('BCE');
                            let yearStr = b.split('-')[0].replace('BCE', '');
                            let year = parseInt(yearStr);
                            if (isBCE) year = -year;
                            return year >= timeRange[0] && year <= timeRange[1];
                        });
                        if (inRange) validPersons.add(n.id);
                    }
                }
            });

            validPersons.forEach(id => keptNodes.add(id));

            graphData.links.forEach(l => {
                const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                if (validPersons.has(sourceId)) keptNodes.add(targetId);
                if (validPersons.has(targetId)) keptNodes.add(sourceId);
            });
        }

        // 1. Filter Nodes
        const nodes = graphData.nodes.filter(node => {
            // Type Filter
            if (!selectedTypes[node.group]) return false;
            
            // Time Filter
            if (isTimeFilterActive && !keptNodes.has(node.id)) return false;

            return true;
        })

        const visibleNodeIds = new Set(nodes.map(n => n.id))

        // 2. Filter Links (both ends must be visible)
        let links = graphData.links.filter(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source
            const targetId = typeof l.target === 'object' ? l.target.id : l.target
            return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId)
        })

        return { nodes, links }
    }, [graphData, selectedTypes, timeRange])


    const toggleType = (type: string) => {
        setSelectedTypes(prev => ({ ...prev, [type]: !prev[type] }))
    }

    if (error) return <div className="p-8 text-red-500">Error loading data</div>

    return (
        <div className="space-y-4 h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold font-sans">Network Graph</h1>
                    {filteredData && (
                        <span className="text-sm text-gray-500 font-sans mt-1">
                            Nodes: {filteredData.nodes.length}, Edges: {filteredData.links.length}
                        </span>
                    )}
                </div>
                <div className="ml-auto flex items-center gap-4">
                    {isLoading && <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />}
                    <SourceFilter selectedSource={source} onChange={handleSourceChange} />
                </div>
            </div>

            <div className="flex flex-1 border border-gray-200 rounded-lg overflow-hidden bg-slate-50 relative">

                {/* Sidebar Controls & Index */}
                <div className="w-80 bg-white border-r border-gray-200 flex flex-col z-10 shrink-0">

                    {/* Time Filter Section */}
                    <div className="p-4 border-b border-gray-200 bg-gray-50">
                        <div className="mb-4">
                            <label className="text-sm font-bold text-gray-700 uppercase tracking-wider">Time Range</label>
                        </div>
                        
                        <div className="px-2 pt-2 pb-6">
                            <div className="text-center text-sm font-medium text-indigo-600 mb-4">
                                {timeRange[0] < 0 ? `${-timeRange[0]} BCE` : timeRange[0]} - {timeRange[1] < 0 ? `${-timeRange[1]} BCE` : timeRange[1]}
                            </div>
                            <Slider
                                range
                                min={-200}
                                max={2050}
                                step={50}
                                marks={bucketsList.reduce((acc, curr) => {
                                    if (curr % 500 === 0) acc[curr] = curr < 0 ? `${-curr}BCE` : curr.toString();
                                    return acc;
                                }, {} as Record<number, string>)}
                                value={timeRange}
                                onChange={(value) => setTimeRange(value as [number, number])}
                                railStyle={{ backgroundColor: '#e2e8f0', height: 6 }}
                                trackStyle={[{ backgroundColor: '#4f46e5' }]}
                                handleStyle={[
                                    { borderColor: '#4f46e5', height: 16, width: 16, marginTop: -5, backgroundColor: '#fff', opacity: 1 },
                                    { borderColor: '#4f46e5', height: 16, width: 16, marginTop: -5, backgroundColor: '#fff', opacity: 1 }
                                ]}
                            />
                        </div>
                    </div>

                    {/* Filters Section */}
                    <div className="p-4 border-b border-gray-200 bg-white flex-1 overflow-y-auto">
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
                    {filteredData && (
                        <ForceGraph2D
                            ref={fgRef}
                            graphData={filteredData}
                            nodeLabel="label"
                            nodeColor={(node: any) => COLORS[node.group as keyof typeof COLORS] || '#ccc'}
                            linkDirectionalArrowLength={3.5}
                            linkDirectionalArrowRelPos={1}
                            linkLineDash={(link: any) => link.dashes ? [5, 5] : null}
                            onNodeClick={(node: any) => {
                                if (node.group === 'HistoricalPerson') navigate(`/persons/${node.id}`)
                                else if (node.group === 'HistoricalWork') navigate(`/works/${node.id}`)
                                else if (node.group === 'Place') navigate(`/places/${node.id}`)
                                else if (node.group === 'Subject') navigate(`/subjects/${node.id}`)
                                else if (node.group === 'Language') navigate(`/languages/${node.id}`)
                            }}
                            width={1000} // Dynamic sizing is tricky in wrappers, but flexbox helps
                            height={800}
                            cooldownTicks={100}
                            onEngineStop={() => fgRef.current?.zoomToFit(400)}
                        />
                    )}
                </div>
            </div>
        </div>
    )
}
