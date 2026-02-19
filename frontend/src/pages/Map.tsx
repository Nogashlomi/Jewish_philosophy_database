import { useQuery } from '@tanstack/react-query'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import { useState } from 'react'
import Slider from 'rc-slider'
import 'rc-slider/assets/index.css'
import 'leaflet/dist/leaflet.css'
import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import axios from 'axios'
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
        start: number | null
        end: number | null
    }
}

interface GeoJSONResponse {
    type: "FeatureCollection"
    features: GeoJSONFeature[]
}

import { useSearchParams } from 'react-router-dom'
import SourceFilter from '../components/SourceFilter'

const fetchGeoJSON = async (source?: string | null) => {
    const params = source ? { source } : {}
    const { data } = await axios.get<GeoJSONResponse>('/api/geojson', { params })
    return data
}

export default function MapView() {
    // Default time range from original app
    // Using simple array state for slider
    const [timeRange, setTimeRange] = useState<number[] | number>([1000, 1400])
    const [searchParams, setSearchParams] = useSearchParams();

    const selectedSource = searchParams.get('source');

    const handleSourceChange = (source: string | null) => {
        if (source) {
            setSearchParams({ source });
        } else {
            setSearchParams({});
        }
    };

    const { data, isLoading, error } = useQuery({
        queryKey: ['map-geojson', selectedSource],
        queryFn: () => fetchGeoJSON(selectedSource),
    })

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading map data</div>

    // Helper to get range values safely
    const range = Array.isArray(timeRange) ? timeRange : [1000, 1400]
    const minTime = range[0]
    const maxTime = range[1]

    // Filter logic based on original app
    const filteredFeatures = data?.features.filter(f => {
        const props = f.properties
        const hasDates = props.start !== null || props.end !== null

        if (!hasDates) return false // Hide undated entities (backend normally filters these anyway)

        // If only one date is present, treat it as a point-in-time by setting both start and end to that date.
        // This prevents entities with only a birth year from appearing for all time up to 9999.
        const entityStart = props.start !== null ? props.start : props.end!
        const entityEnd = props.end !== null ? props.end : props.start!

        // Check overlap: entityEnd >= filterStart && entityStart <= filterEnd
        return entityEnd >= minTime && entityStart <= maxTime
    }) || []

    return (
        <div className="space-y-4">
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <div className="mb-4">
                    <div className="flex justify-between items-start mb-4">
                        <label className="font-bold text-gray-700 block mb-2 font-sans">
                            Time Range: <span className="text-indigo-600 tabular-nums">{minTime} - {maxTime}</span>
                        </label>
                        <SourceFilter
                            selectedSource={selectedSource}
                            onSourceChange={handleSourceChange}
                        />
                    </div>
                    <div className="px-2">
                        <Slider
                            range
                            min={0}
                            max={2000}
                            defaultValue={[1000, 1400]}
                            value={range}
                            onChange={(value) => setTimeRange(value)}
                            railStyle={{ backgroundColor: '#e2e8f0', height: 10 }}
                            trackStyle={[{ backgroundColor: '#2980b9', height: 10 }]}
                            handleStyle={[
                                { borderColor: '#2980b9', height: 20, width: 20, marginTop: -5, backgroundColor: '#fff', opacity: 1 },
                                { borderColor: '#2980b9', height: 20, width: 20, marginTop: -5, backgroundColor: '#fff', opacity: 1 }
                            ]}
                        />
                    </div>
                    <p className="text-xs text-gray-500 mt-2 font-serif italic">
                        Showing entities active within the selected range. (Entities with unknown dates are grey).
                    </p>
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

                    {filteredFeatures.map((f, idx) => {
                        const props = f.properties
                        const hasDates = props.start !== null || props.end !== null
                        const color = hasDates ? '#e74c3c' : '#95a5a6'

                        return (
                            <CircleMarker
                                key={idx}
                                center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
                                radius={8}
                                pathOptions={{
                                    fillColor: color,
                                    color: "#fff",
                                    weight: 1,
                                    opacity: 1,
                                    fillOpacity: 0.8
                                }}
                            >
                                <Popup>
                                    <div className="font-serif text-sm">
                                        <div className="font-bold mb-1">
                                            <Link to={`/persons/${props.person_id}`} className="text-indigo-600 hover:underline">
                                                {props.person_label}
                                            </Link>
                                        </div>
                                        <div className="mb-1">{props.place_label}</div>
                                        <div className="italic text-gray-500 mb-1">{props.type}</div>
                                        <div className="text-gray-700">
                                            {props.start || '?'} - {props.end || '?'}
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
