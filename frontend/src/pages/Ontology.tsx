import { useQuery } from '@tanstack/react-query'
import { entityService } from '../services/entityService'
import ForceGraph2D from 'react-force-graph-2d'
import { Loader2 } from 'lucide-react'
import { useState, useRef, useEffect, useMemo } from 'react'

export default function Ontology() {
    const fgRef = useRef<any>(null)
    const { data, isLoading, error } = useQuery({
        queryKey: ['ontology'],
        queryFn: entityService.getOntologyGraph,
    })

    const [graphData, setGraphData] = useState<{ nodes: any[], links: any[] } | null>(null)

    useEffect(() => {
        if (data) {
            const nodes = data.nodes.map((n: any) => ({ ...n }))
            const links = data.edges.map((e: any) => ({
                source: e.from,
                target: e.to,
                label: e.label
            }))
            setGraphData({ nodes, links })
        }
    }, [data])

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading ontology data</div>
    if (!graphData) return null

    return (
        <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex justify-between items-center flex-shrink-0">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 font-serif">Ontology Graph</h1>
                    <p className="text-gray-500 mt-2 font-light">
                        Visualizing classes and properties from <span className="font-mono text-sm bg-gray-100 p-1 rounded">vocabulary.ttl</span>
                    </p>
                </div>
                <div className="text-sm text-gray-500">
                    Classes: {graphData.nodes.length}, Properties: {graphData.links.length}
                </div>
            </div>

            <div className="flex-1 border border-gray-200 rounded-lg overflow-hidden bg-white relative shadow-sm">
                <ForceGraph2D
                    ref={fgRef}
                    graphData={graphData}
                    nodeLabel={(node: any) => `${node.label} \n ${node.title || ''}`}
                    nodeColor={() => '#4f46e5'} // Indigo 600
                    nodeRelSize={6}
                    linkColor={() => '#94a3b8'}
                    linkDirectionalArrowLength={3.5}
                    linkDirectionalArrowRelPos={1}
                    linkLabel="label"
                    linkCurvature={0.2}
                    width={1000} // Wrapper handles visual size, but this helps init
                    onEngineStop={() => fgRef.current?.zoomToFit(400, 50)}
                    cooldownTicks={100}
                />
                <div className="absolute top-4 right-4 bg-white/90 p-3 rounded shadow text-xs border border-gray-200 pointer-events-none">
                    <p className="font-bold text-indigo-800">Nodes = Classes</p>
                    <p className="font-bold text-gray-500">Edges = Object Properties</p>
                </div>
            </div>
        </div>
    )
}
