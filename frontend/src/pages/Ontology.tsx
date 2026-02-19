import { useQuery } from '@tanstack/react-query'
import { entityService } from '../services/entityService'
import ForceGraph2D from 'react-force-graph-2d'
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

export default function Ontology() {
    const fgRef = useRef<any>(null)
    const [view, setView] = useState<'graph' | 'audit'>('graph')

    const { data, isLoading, error } = useQuery({
        queryKey: ['ontology'],
        queryFn: entityService.getOntologyGraph,
    })

    const { data: audit, isLoading: isAuditLoading } = useQuery({
        queryKey: ['ontology-audit'],
        queryFn: entityService.getOntologyAudit,
        enabled: view === 'audit'
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

    // Adjust force sim after data loads to spread things out
    useEffect(() => {
        if (fgRef.current && graphData) {
            fgRef.current.d3Force('charge').strength(-600)
            fgRef.current.d3Force('link').distance(180)
        }
    }, [graphData])

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading ontology data</div>
    if (!graphData) return null

    return (
        <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex justify-between items-center flex-shrink-0">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 font-serif">Ontology explorer</h1>
                    <p className="text-gray-500 mt-2 font-light">
                        Structure defined in <span className="font-mono text-sm bg-gray-100 p-1 rounded">vocabulary.ttl</span>
                    </p>
                </div>
                <div className="flex bg-gray-100 p-1 rounded-lg">
                    <button
                        onClick={() => setView('graph')}
                        className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${view === 'graph' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Visual Graph
                    </button>
                    <button
                        onClick={() => setView('audit')}
                        className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${view === 'audit' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Structure Audit
                    </button>
                </div>
            </div>

            {view === 'graph' ? (
                <div className="flex-1 border border-gray-200 rounded-lg overflow-hidden bg-[#f8fafc] relative shadow-sm">
                    <ForceGraph2D
                        ref={fgRef}
                        graphData={graphData}
                        nodeLabel={(node: any) => `${node.label}`}

                        // Performance and Visual Tuning
                        cooldownTicks={100}

                        // Permanent Labels for Nodes (Compact Pill style)
                        nodeCanvasObject={(node: any, ctx, globalScale) => {
                            const label = node.label;
                            const fontSize = 12 / globalScale;
                            ctx.font = `500 ${fontSize}px Inter, sans-serif`;

                            const textWidth = ctx.measureText(label).width;
                            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.8);

                            // Draw Pill Background
                            ctx.fillStyle = '#4f46e5';
                            ctx.beginPath();
                            const x = node.x - bckgDimensions[0] / 2;
                            const y = node.y - bckgDimensions[1] / 2;
                            const w = bckgDimensions[0];
                            const h = bckgDimensions[1];
                            const r = h / 2; // Full rounded ends

                            ctx.moveTo(x + r, y);
                            ctx.lineTo(x + w - r, y);
                            ctx.arcTo(x + w, y, x + w, y + r, r);
                            ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
                            ctx.lineTo(x + r, y + h);
                            ctx.arcTo(x, y + h, x, y + h - r, r);
                            ctx.arcTo(x, y, x + r, y, r);
                            ctx.closePath();
                            ctx.fill();

                            // Label text
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillStyle = '#ffffff';
                            ctx.fillText(label, node.x, node.y);
                        }}

                        // Permanent Labels for Links with backgrounds
                        linkCanvasObjectMode={() => 'after'}
                        linkCanvasObject={(link: any, ctx, globalScale) => {
                            const MAX_FONT_SIZE = 4;
                            const start = link.source;
                            const end = link.target;

                            if (typeof start !== 'object' || typeof end !== 'object') return;

                            const textPos = {
                                x: start.x + (end.x - start.x) / 2,
                                y: start.y + (end.y - start.y) / 2
                            };

                            const label = link.label;
                            const fontSize = Math.min(MAX_FONT_SIZE, 12 / globalScale);
                            ctx.font = `${fontSize}px Sans-Serif`;
                            const textWidth = ctx.measureText(label).width;

                            // Draw background for link label
                            ctx.save();
                            ctx.translate(textPos.x, textPos.y);

                            ctx.fillStyle = 'rgba(248, 250, 252, 0.9)'; // Match page background
                            ctx.fillRect(-textWidth / 2 - 1, -fontSize / 2 - 1, textWidth + 2, fontSize + 2);

                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillStyle = '#64748b'; // Slate 500
                            ctx.fillText(label, 0, 0);
                            ctx.restore();
                        }}

                        linkColor={() => '#cbd5e1'}
                        linkDirectionalArrowLength={3}
                        linkDirectionalArrowRelPos={1}
                        linkCurvature={0.25}
                        onEngineStop={() => fgRef.current?.zoomToFit(400, 100)}
                    />
                    <div className="absolute top-4 right-4 bg-white/90 p-3 rounded shadow text-xs border border-gray-200 pointer-events-none">
                        <p className="font-bold text-indigo-800">Nodes = Classes</p>
                        <p className="font-bold text-gray-500">Edges = Object Properties</p>
                    </div>
                </div>
            ) : (
                <div className="flex-1 bg-white border border-gray-200 rounded-lg shadow-sm overflow-y-auto p-6">
                    {isAuditLoading ? (
                        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Classes Section */}
                            <section className="space-y-4">
                                <h2 className="text-xl font-bold text-gray-900 border-b pb-2">Classes Usage</h2>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-indigo-50 p-4 rounded-lg">
                                        <div className="text-sm text-indigo-600 font-medium">Defined</div>
                                        <div className="text-2xl font-bold">{audit?.classes.defined_count}</div>
                                    </div>
                                    <div className="bg-emerald-50 p-4 rounded-lg">
                                        <div className="text-sm text-emerald-600 font-medium">Actually Used</div>
                                        <div className="text-2xl font-bold">{audit?.classes.actual_count}</div>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-gray-500 uppercase flex items-center gap-2">
                                        <AlertCircle className="h-4 w-4 text-orange-500" />
                                        Unused in Data ({audit?.classes.unused.length})
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {audit?.classes.unused.map((uri: string) => (
                                            <span key={uri} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded font-mono">
                                                {uri.split('#').pop()}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-gray-500 uppercase flex items-center gap-2">
                                        <AlertCircle className="h-4 w-4 text-red-500" />
                                        Undefined in Ontology ({audit?.classes.undefined.length})
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {audit?.classes.undefined.map((uri: string) => (
                                            <span key={uri} className="px-2 py-1 bg-red-50 text-red-600 text-xs rounded font-mono border border-red-100">
                                                {uri.split('#').pop() || uri}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </section>

                            {/* Properties Section */}
                            <section className="space-y-4">
                                <h2 className="text-xl font-bold text-gray-900 border-b pb-2">Properties Usage</h2>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-indigo-50 p-4 rounded-lg">
                                        <div className="text-sm text-indigo-600 font-medium">Defined</div>
                                        <div className="text-2xl font-bold">{audit?.properties.defined_count}</div>
                                    </div>
                                    <div className="bg-emerald-50 p-4 rounded-lg">
                                        <div className="text-sm text-emerald-600 font-medium">Actually Used</div>
                                        <div className="text-2xl font-bold">{audit?.properties.actual_count}</div>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-gray-500 uppercase flex items-center gap-2">
                                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                                        Unused ({audit?.properties.unused.length})
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {audit?.properties.unused.map((uri: string) => (
                                            <span key={uri} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded font-mono">
                                                {uri.split('#').pop()}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-gray-500 uppercase flex items-center gap-2">
                                        <AlertCircle className="h-4 w-4 text-red-500" />
                                        Undefined ({audit?.properties.undefined.length})
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {audit?.properties.undefined.map((uri: string) => (
                                            <span key={uri} className="px-2 py-1 bg-red-50 text-red-600 text-xs rounded font-mono border border-red-100">
                                                {uri.split('#').pop() || uri}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </section>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
