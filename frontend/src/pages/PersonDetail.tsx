import { useQuery } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { entityService } from '../services/entityService'
import { Loader2, ArrowLeft, BookOpen, MapPin, Calendar, ExternalLink, GraduationCap } from 'lucide-react'

export default function PersonDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()

    const { data: person, isLoading, error } = useQuery({
        queryKey: ['person', id],
        queryFn: () => entityService.getPersonDetail(id!),
        enabled: !!id,
    })

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading person details</div>
    if (!person) return <div className="p-8">Person not found</div>

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <button
                onClick={() => navigate(-1)}
                className="flex items-center text-sm text-gray-500 hover:text-indigo-600 transition-colors"
            >
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
            </button>

            <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
                <div className="bg-indigo-50 px-6 py-4 border-b border-indigo-100">
                    <h1 className="text-2xl font-bold text-gray-900">{person.label}</h1>
                    <div className="text-sm text-gray-500 mt-1 font-mono">{person.id}</div>
                </div>

                <div className="p-6 space-y-8">
                    {/* Basic Info / Times */}
                    {person.times && person.times.length > 0 && (
                        <div className="flex items-start gap-3">
                            <Calendar className="h-5 w-5 text-indigo-500 mt-0.5" />
                            <div>
                                <h3 className="font-medium text-gray-900">Time Period</h3>
                                <div className="mt-1 space-y-1">
                                    {person.times.map((time, idx) => (
                                        <div key={idx} className="text-gray-600">
                                            {time.start} - {time.end} {time.type && <span className="text-xs text-gray-400">({time.type})</span>}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Places */}
                    {person.places && person.places.length > 0 && (
                        <div className="flex items-start gap-3">
                            <MapPin className="h-5 w-5 text-indigo-500 mt-0.5" />
                            <div>
                                <h3 className="font-medium text-gray-900">Related Places</h3>
                                <div className="mt-2 flex flex-wrap gap-2">
                                    {person.places.map((place, idx) => (
                                        <Link
                                            key={idx}
                                            to={`/places/${place.place_id}`}
                                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 hover:bg-blue-100"
                                        >
                                            {place.label}
                                            {place.type && <span className="ml-1 opacity-60">({place.type})</span>}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Works */}
                    {person.works && person.works.length > 0 && (
                        <div className="flex items-start gap-3">
                            <BookOpen className="h-5 w-5 text-indigo-500 mt-0.5" />
                            <div className="w-full">
                                <h3 className="font-medium text-gray-900 mb-2">Authored Works ({person.works.length})</h3>
                                <div className="grid gap-2 sm:grid-cols-2">
                                    {person.works.map((work) => (
                                        <Link
                                            key={work.id}
                                            to={`/works/${work.id}`}
                                            className="block p-3 rounded border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-all"
                                        >
                                            <div className="font-medium text-indigo-700 truncate" title={work.title}>{work.title}</div>
                                            <div className="text-xs text-gray-400 mt-1">{work.id}</div>
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Scholarly Mentions */}
                    {person.scholarly && person.scholarly.length > 0 && (
                        <div className="flex items-start gap-3">
                            <GraduationCap className="h-5 w-5 text-indigo-500 mt-0.5" />
                            <div className="w-full">
                                <h3 className="font-medium text-gray-900 mb-2">Scholarly Mentions ({person.scholarly.length})</h3>
                                <div className="space-y-2">
                                    {person.scholarly.map((mention) => (
                                        <div key={mention.id} className="p-3 bg-gray-50 rounded text-sm text-gray-700">
                                            <div className="font-medium">{mention.title}</div>
                                            {mention.year && <div className="text-xs text-gray-500 mt-1">{mention.year}</div>}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Authority Links */}
                    {person.authorities && person.authorities.length > 0 && (
                        <div className="flex items-start gap-3 border-t border-gray-100 pt-6">
                            <ExternalLink className="h-5 w-5 text-gray-400 mt-0.5" />
                            <div>
                                <h3 className="font-medium text-gray-900">External Authorities</h3>
                                <div className="mt-1 space-y-1">
                                    {person.authorities.map((auth, idx) => (
                                        <a
                                            key={idx}
                                            href={auth}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="block text-sm text-blue-600 hover:underline truncate max-w-md"
                                        >
                                            {auth}
                                        </a>
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
