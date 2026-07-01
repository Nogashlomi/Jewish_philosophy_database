import { useSearchParams } from 'react-router-dom';
import { SourceFilter } from '../components/SourceFilter';
import { useQuery } from '@tanstack/react-query'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline } from 'react-leaflet'
import { useState, useMemo } from 'react'
import Slider from 'rc-slider'
import 'rc-slider/assets/index.css'
import 'leaflet/dist/leaflet.css'
import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import api from '../services/api'
import L from 'leaflet'

// Fix for default marker icon (even though we use CircleMarker, good to have)
import iconManager from 'leaflet'
// @ts-ignore
delete iconManager.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
})

// Define types for our GeoJSON data
interface GeoJSONFeature {
    type: "Feature"
    geometry: {
        type: "Point"
        coordinates: [number, number] // [long, lat]
    }
    properties: {
        person_id: string
        person_label: string
        place_label: string
        type: string
        bucket: string | null
        source: string
    }
}

interface GeoJSONResponse {
    type: "FeatureCollection"
    features: GeoJSONFeature[]
}


const fetchGeoJSON = async (source?: string | null) => {
    const params = source ? { source } : {}
    const { data } = await api.get<GeoJSONResponse>('/geojson', { params })
    return data
}

interface TranslationFlow {
    translator_id: string;
    translator_label: string;
    author_id: string;
    author_label: string;
    path: [number, number][];
}

const fetchTranslationFlows = async () => {
    const { data } = await api.get<TranslationFlow[]>('/places/translations/flows')
    return data
}

export default function MapView() {

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

    const { data, isLoading, error } = useQuery({
        queryKey: ['map-geojson', source],
        queryFn: () => fetchGeoJSON(source),
        staleTime: Infinity,
        gcTime: Infinity
    })

    const { data: translationFlows } = useQuery({
        queryKey: ['map-translation-flows'],
        queryFn: fetchTranslationFlows,
        staleTime: Infinity,
        gcTime: Infinity
    })

    // Parse available buckets and min/max
    const { minYear, maxYear, bucketsList } = useMemo(() => {
        if (!data) return { minYear: 1000, maxYear: 1400, bucketsList: [] };
        const buckets = new Set<number>();
        data.features.forEach(f => {
            if (f.properties.bucket) {
                const year = parseInt(f.properties.bucket.split('-')[0]);
                if (!isNaN(year)) buckets.add(year);
            }
        });
        const sorted = Array.from(buckets).sort((a, b) => a - b);
        if (sorted.length === 0) return { minYear: 1000, maxYear: 2050, bucketsList: [] };
        
        // Force the max year to be at least 2050
        const maxYear = Math.max(sorted[sorted.length - 1], 2050);
        
        // Fill in any missing buckets up to maxYear so the slider reaches it smoothly
        const fullBucketsList = [];
        for (let y = sorted[0]; y <= maxYear; y += 50) {
            fullBucketsList.push(y);
        }

        return {
            minYear: sorted[0],
            maxYear: maxYear,
            bucketsList: fullBucketsList
        };
    }, [data]);

    const [selectedYear, setSelectedYear] = useState<number>(1100);
    const [showConnections, setShowConnections] = useState(false);
    const [showTranslationFlows, setShowTranslationFlows] = useState(false);
    const [colorBySource, setColorBySource] = useState(false);

    // Make sure selectedYear is updated if it's out of bounds when data loads
    useMemo(() => {
        if (bucketsList.length > 0 && !bucketsList.includes(selectedYear)) {
            setSelectedYear(bucketsList[Math.floor(bucketsList.length / 2)]);
        }
    }, [bucketsList]);

    // Group features by place for the selected bucket
    const { groupedPlaces, connections, activePersonIds } = useMemo(() => {
        if (!data) return { groupedPlaces: [], connections: [], activePersonIds: [] };

        const bucketStrPrefix = `${selectedYear}-`;

        // 1. Filter features for current bucket
        const activeFeatures = data.features.filter(f => {
            return f.properties.bucket && f.properties.bucket.startsWith(bucketStrPrefix);
        });

        // 2. Group by Place
        const placeMap = new Map<string, {
            label: string,
            coords: [number, number],
            persons: Map<string, string>, // id -> label
            sources: Set<string>
        }>();

        // Also track which places a person is at for connections
        const personPlaces = new Map<string, [number, number][]>();

        activeFeatures.forEach(f => {
            const placeKey = `${f.geometry.coordinates[0]},${f.geometry.coordinates[1]}`;
            
            if (!placeMap.has(placeKey)) {
                placeMap.set(placeKey, {
                    label: f.properties.place_label,
                    coords: [f.geometry.coordinates[1], f.geometry.coordinates[0]], // Leaflet expects [lat, lng]
                    persons: new Map(),
                    sources: new Set()
                });
            }
            const p = placeMap.get(placeKey)!;
            p.persons.set(f.properties.person_id, f.properties.person_label);
            if (f.properties.source) {
                p.sources.add(f.properties.source);
            }

            // Add to person places
            if (!personPlaces.has(f.properties.person_id)) {
                personPlaces.set(f.properties.person_id, []);
            }
            // Avoid duplicate coords for the same person (e.g. birth and residence at same place)
            const coordsList = personPlaces.get(f.properties.person_id)!;
            const latlng = [f.geometry.coordinates[1], f.geometry.coordinates[0]] as [number, number];
            if (!coordsList.some(c => c[0] === latlng[0] && c[1] === latlng[1])) {
                coordsList.push(latlng);
            }
        });

        // 3. Generate connections (only if person is at >1 place in this bucket)
        const conns: [number, number][][] = [];
        personPlaces.forEach(coordsList => {
            if (coordsList.length > 1) {
                // Draw a simple path connecting their locations
                conns.push(coordsList);
            }
        });

        return {
            groupedPlaces: Array.from(placeMap.values()),
            connections: conns,
            activePersonIds: Array.from(personPlaces.keys())
        };
    }, [data, selectedYear]);

    const activeTranslationFlows = useMemo(() => {
        if (!translationFlows || !data) return [];
        const activePersons = new Set(activePersonIds);
        return translationFlows.filter(flow => 
            activePersons.has(flow.translator_id) || activePersons.has(flow.author_id)
        );
    }, [translationFlows, activePersonIds]);



    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading map data</div>

    // Helper to calculate marker radius based on number of persons
    const getRadius = (personCount: number) => {
        return Math.min(Math.max(personCount * 2 + 5, 8), 30);
    }

    return (
        <div className="space-y-4">
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <div className="mb-4">
                    <div className="flex justify-between items-start mb-4">
                        <label className="font-bold text-gray-700 block mb-2 font-sans flex items-center">
                            Time Bucket: <span className="text-indigo-600 tabular-nums ml-2">{selectedYear} - {selectedYear + 49}</span>
                        </label>
                        <div className="ml-auto flex items-center gap-4">
                            <button 
                                onClick={() => setColorBySource(!colorBySource)}
                                className={`text-sm px-3 py-1.5 rounded-md font-medium transition-colors ${colorBySource ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                            >
                                {colorBySource ? "Stop Coloring by Source" : "Color by Source"}
                            </button>
                            <button 
                                onClick={() => setShowTranslationFlows(!showTranslationFlows)}
                                className={`text-sm px-3 py-1.5 rounded-md font-medium transition-colors ${showTranslationFlows ? 'bg-orange-500 text-white' : 'bg-orange-100 text-orange-700 hover:bg-orange-200'}`}
                            >
                                {showTranslationFlows ? "Hide Translation Flows" : "Show Translation Flows"}
                            </button>
                            <button 
                                onClick={() => setShowConnections(!showConnections)}
                                className={`text-sm px-3 py-1.5 rounded-md font-medium transition-colors ${showConnections ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                            >
                                {showConnections ? "Hide Person Connections" : "Show Person Connections"}
                            </button>
                            <SourceFilter selectedSource={source} onChange={handleSourceChange} />
                        </div>
                    </div>
                    <div className="px-4 py-2">
                        <Slider
                            min={minYear}
                            max={maxYear}
                            step={50}
                            marks={bucketsList.reduce((acc, curr) => {
                                // Only show every 2nd or 3rd mark if there are too many
                                if (bucketsList.length < 15 || curr % 100 === 0) {
                                    acc[curr] = curr.toString();
                                }
                                return acc;
                            }, {} as Record<number, string>)}
                            value={selectedYear}
                            onChange={(value) => setSelectedYear(value as number)}
                            railStyle={{ backgroundColor: '#e2e8f0', height: 8 }}
                            trackStyle={{ backgroundColor: 'transparent' }}
                            handleStyle={{ borderColor: '#4f46e5', height: 20, width: 20, marginTop: -6, backgroundColor: '#fff', opacity: 1 }}
                        />
                    </div>
                    <p className="text-xs text-gray-500 mt-6 font-serif italic text-center">
                        Showing grouped places for people active between {selectedYear} and {selectedYear + 49}.
                    </p>

                    {/* Color Index Legend */}
                    {colorBySource && (
                        <div className="mt-6 flex flex-wrap justify-center gap-6 text-sm font-sans font-medium text-gray-700 bg-gray-50 py-3 rounded-lg border border-gray-100">
                            <div className="flex items-center gap-2">
                                <span className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: '#3498db' }}></span> 
                                General List
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: '#2ecc71' }}></span> 
                                Zonta Table
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: '#9b59b6' }}></span> 
                                Mixed Sources
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: '#f1c40f' }}></span> 
                                Other
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="h-[600px] w-full rounded-lg overflow-hidden border border-gray-200 shadow relative z-0">
                <MapContainer center={[32.0, 35.0]} zoom={4} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                        subdomains="abcd"
                        maxZoom={19}
                    />

                    {/* Render Connections */}
                    {showConnections && connections.map((coords, idx) => (
                        <Polyline 
                            key={`conn-${idx}`} 
                            positions={coords} 
                            pathOptions={{ color: '#6366f1', weight: 2, opacity: 0.6, dashArray: '5, 5' }} 
                        />
                    ))}

                    {/* Render Translation Flows */}
                    {showTranslationFlows && activeTranslationFlows.map((flow, idx) => (
                        <Polyline 
                            key={`tflow-${idx}`} 
                            positions={flow.path} 
                            pathOptions={{ color: '#f97316', weight: 3, opacity: 0.8, dashArray: '8, 8' }} 
                        >
                            <Popup>
                                <div className="font-serif text-sm">
                                    <Link to={`/persons/${flow.translator_id}`} className="font-bold text-indigo-600 hover:underline">{flow.translator_label}</Link> 
                                    {' '}translated{' '} 
                                    <Link to={`/persons/${flow.author_id}`} className="font-bold text-indigo-600 hover:underline">{flow.author_label}</Link>
                                </div>
                            </Popup>
                        </Polyline>
                    ))}

                    {/* Render Grouped Places */}
                    {groupedPlaces.map((place, idx) => {
                        const personCount = place.persons.size;
                        
                        let color = '#e74c3c'; // Default Red
                        if (colorBySource) {
                            if (place.sources.size > 1) {
                                color = '#9b59b6'; // Purple for mixed
                            } else if (place.sources.size === 1) {
                                const s = Array.from(place.sources)[0].toLowerCase();
                                if (s.includes('zonta')) color = '#2ecc71'; // Green
                                else if (s.includes('general')) color = '#3498db'; // Blue
                                else color = '#f1c40f'; // Yellow for other singular source
                            }
                        }

                        return (
                            <CircleMarker
                                key={idx}
                                center={place.coords}
                                radius={getRadius(personCount)}
                                pathOptions={{
                                    fillColor: color,
                                    color: "#fff",
                                    weight: 2,
                                    opacity: 1,
                                    fillOpacity: 0.7
                                }}
                            >
                                <Popup maxWidth={300}>
                                    <div className="font-serif text-sm">
                                        <div className="font-bold mb-2 text-base border-b pb-1">
                                            {place.label}
                                            <span className="text-gray-500 text-xs ml-2 font-normal">
                                                ({personCount} person{personCount !== 1 ? 's' : ''})
                                            </span>
                                        </div>
                                        <div className="max-h-48 overflow-y-auto pr-2 space-y-1">
                                            {Array.from(place.persons.entries()).map(([id, label]) => (
                                                <div key={id}>
                                                    <Link to={`/persons/${id}`} className="text-indigo-600 hover:underline">
                                                        {label}
                                                    </Link>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </Popup>
                            </CircleMarker>
                        )
                    })}
                </MapContainer>
            </div>
        </div>
    )
}
