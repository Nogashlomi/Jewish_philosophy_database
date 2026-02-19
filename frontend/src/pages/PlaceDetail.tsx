import { useQuery } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { entityService } from '../services/entityService'
import { Loader2, ArrowLeft, MapPin, Users } from 'lucide-react'

export default function PlaceDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()

    const { data: place, isLoading, error } = useQuery({
        queryKey: ['place', id],
        queryFn: () => entityService.getPlaceDetail(id!),
        enabled: !!id,
    })

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading place details</div>
    if (!place) return <div className="p-8">Place not found</div>

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <button
                onClick={() => navigate(-1)}
                className="flex items-center text-sm text-gray-500 hover:text-indigo-600 transition-colors"
            >
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
            </button>

            <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
                <div className="bg-orange-50 px-6 py-4 border-b border-orange-100">
                    <h1 className="text-2xl font-bold text-gray-900">{place.label}</h1>
                    <div className="flex items-center gap-4 mt-1">
                        <div className="text-sm text-gray-500 font-mono">{place.id}</div>
                        {place.lat && place.long && (
                            <div className="text-xs px-2 py-0.5 bg-orange-100 text-orange-800 rounded">
                                {place.lat}, {place.long}
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-6 space-y-8">
                    {/* People linked to this place */}
                    {place.people && place.people.length > 0 && (
                        <div className="flex items-start gap-3">
                            <Users className="h-5 w-5 text-orange-500 mt-0.5" />
                            <div>
                                <h3 className="font-medium text-gray-900">People Associated</h3>
                                <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                                    {place.people.map((person: any) => (
                                        <Link
                                            key={person.id}
                                            to={`/persons/${person.id}`}
                                            className="flex items-center p-2 rounded-md border border-gray-100 hover:bg-orange-50 hover:border-orange-200 transition-colors"
                                        >
                                            <div className="text-sm font-medium text-gray-700">{person.label}</div>
                                            {person.type && <div className="text-xs text-gray-400 ml-2">({person.type})</div>}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
