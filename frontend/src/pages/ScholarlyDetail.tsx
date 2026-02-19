import { useQuery } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { entityService } from '../services/entityService'
import { Loader2, ArrowLeft, GraduationCap, Link as LinkIcon, User, BookOpen } from 'lucide-react'

export default function ScholarlyDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()

    const { data: work, isLoading, error } = useQuery({
        queryKey: ['scholarly', id],
        queryFn: () => entityService.getScholarlyDetail(id!),
        enabled: !!id,
    })

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading scholarly work details</div>
    if (!work) return <div className="p-8">Scholarly work not found</div>

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <button
                onClick={() => navigate(-1)}
                className="flex items-center text-sm text-gray-500 hover:text-indigo-600 transition-colors"
            >
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
            </button>

            <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
                <div className="bg-blue-50 px-6 py-4 border-b border-blue-100">
                    <h1 className="text-xl font-bold text-gray-900">{work.title}</h1>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                        {work.year && (
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded">{work.year}</span>
                        )}
                        {work.authors && work.authors.length > 0 && (
                            <span>{work.authors.map((a: any) => a.name).join(", ")}</span>
                        )}
                    </div>
                </div>

                <div className="p-6 space-y-6">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                        <LinkIcon className="h-4 w-4" />
                        <a href={work.uri} target="_blank" rel="noopener noreferrer" className="hover:underline hover:text-blue-600 truncate">
                            {work.uri}
                        </a>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8">
                        {/* Mentioned Persons */}
                        {work.mentions_person && work.mentions_person.length > 0 && (
                            <div>
                                <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                    <User className="h-4 w-4 text-blue-500" />
                                    Mentioned Persons
                                </h3>
                                <div className="space-y-2">
                                    {work.mentions_person.map((person: any) => (
                                        <Link
                                            key={person.id}
                                            to={`/persons/${person.id}`}
                                            className="block p-2 rounded bg-gray-50 hover:bg-blue-50 transition-colors text-sm text-indigo-700"
                                        >
                                            {person.label}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Mentioned Works */}
                        {work.mentions_work && work.mentions_work.length > 0 && (
                            <div>
                                <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                    <BookOpen className="h-4 w-4 text-blue-500" />
                                    Mentioned Works
                                </h3>
                                <div className="space-y-2">
                                    {work.mentions_work.map((mentionedWork: any) => (
                                        <Link
                                            key={mentionedWork.id}
                                            to={`/works/${mentionedWork.id}`}
                                            className="block p-2 rounded bg-gray-50 hover:bg-blue-50 transition-colors text-sm text-indigo-700"
                                        >
                                            {mentionedWork.title}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
