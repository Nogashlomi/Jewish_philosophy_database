import { useQuery } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { entityService } from '../services/entityService'
import { Loader2, ArrowLeft, Languages as LanguagesIcon, BookOpen } from 'lucide-react'

export default function LanguageDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()

    const { data: language, isLoading, error } = useQuery({
        queryKey: ['language', id],
        queryFn: () => entityService.getLanguageDetail(id!),
        enabled: !!id,
    })

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading language details</div>
    if (!language) return <div className="p-8">Language not found</div>

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <button
                onClick={() => navigate(-1)}
                className="flex items-center text-sm text-gray-500 hover:text-indigo-600 transition-colors"
            >
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
            </button>

            <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
                <div className="bg-pink-50 px-6 py-4 border-b border-pink-100">
                    <h1 className="text-2xl font-bold text-gray-900">{language.label}</h1>
                    <div className="text-sm text-gray-500 mt-1 font-mono">{id}</div>
                </div>

                <div className="p-6">
                    {/* Works linked to this language */}
                    {language.works && language.works.length > 0 ? (
                        <div className="flex items-start gap-3">
                            <BookOpen className="h-5 w-5 text-pink-500 mt-0.5" />
                            <div className="w-full">
                                <h3 className="font-medium text-gray-900 mb-3">Works in this Language ({language.works.length})</h3>
                                <div className="grid gap-2 sm:grid-cols-2">
                                    {language.works.map((work: any) => (
                                        <Link
                                            key={work.id}
                                            to={`/works/${work.id}`}
                                            className="block p-3 rounded border border-gray-100 hover:bg-pink-50 hover:border-pink-200 transition-all"
                                        >
                                            <div className="font-medium text-indigo-700 truncate" title={work.title}>{work.title}</div>
                                            <div className="text-xs text-gray-400 mt-1">{work.id}</div>
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-gray-500 italic">No works found for this language.</div>
                    )}
                </div>
            </div>
        </div>
    )
}
