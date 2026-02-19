import { useQuery } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { entityService } from '../services/entityService'
import { Loader2, ArrowLeft, User, BookOpen, Hash, Languages as LanguagesIcon, GraduationCap } from 'lucide-react'

export default function WorkDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()

    const { data: work, isLoading, error } = useQuery({
        queryKey: ['work', id],
        queryFn: () => entityService.getWorkDetail(id!),
        enabled: !!id,
    })

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>
    if (error) return <div className="p-8 text-red-500">Error loading work details</div>
    if (!work) return <div className="p-8">Work not found</div>

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <button
                onClick={() => navigate(-1)}
                className="flex items-center text-sm text-gray-500 hover:text-indigo-600 transition-colors"
            >
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
            </button>

            <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
                <div className="bg-teal-50 px-6 py-4 border-b border-teal-100">
                    <h1 className="text-2xl font-bold text-gray-900">{work.title}</h1>
                    <div className="text-sm text-gray-500 mt-1 font-mono">{work.id}</div>
                </div>

                <div className="p-6 space-y-8">
                    {/* Authors */}
                    {work.authors && work.authors.length > 0 && (
                        <div className="flex items-start gap-3">
                            <User className="h-5 w-5 text-teal-500 mt-0.5" />
                            <div>
                                <h3 className="font-medium text-gray-900">Authors</h3>
                                <div className="mt-2 flex flex-wrap gap-2">
                                    {work.authors.map((author: any) => (
                                        <Link
                                            key={author.id}
                                            to={`/persons/${author.id}`}
                                            className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
                                        >
                                            {author.label}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Subjects */}
                    {work.subjects && work.subjects.length > 0 && (
                        <div className="flex items-start gap-3">
                            <Hash className="h-5 w-5 text-teal-500 mt-0.5" />
                            <div>
                                <h3 className="font-medium text-gray-900">Subjects</h3>
                                <div className="mt-2 flex flex-wrap gap-2">
                                    {work.subjects.map((subject: string, idx: number) => (
                                        <span
                                            key={idx}
                                            className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                                        >
                                            {subject}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Languages */}
                    {work.languages && work.languages.length > 0 && (
                        <div className="flex items-start gap-3">
                            <LanguagesIcon className="h-5 w-5 text-teal-500 mt-0.5" />
                            <div>
                                <h3 className="font-medium text-gray-900">Languages</h3>
                                <div className="mt-2 flex flex-wrap gap-2">
                                    {work.languages.map((lang: string, idx: number) => (
                                        <span
                                            key={idx}
                                            className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                                        >
                                            {lang}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Scholarly Mentions */}
                    {work.scholarly_mentions && work.scholarly_mentions.length > 0 && (
                        <div className="flex items-start gap-3">
                            <GraduationCap className="h-5 w-5 text-teal-500 mt-0.5" />
                            <div className="w-full">
                                <h3 className="font-medium text-gray-900 mb-2">Scholarly Mentions ({work.scholarly_mentions.length})</h3>
                                <div className="space-y-2">
                                    {work.scholarly_mentions.map((mention: any) => (
                                        <div key={mention.id} className="p-3 bg-gray-50 rounded text-sm text-gray-700">
                                            <div className="font-medium">{mention.title}</div>
                                            {mention.year && <div className="text-xs text-gray-500 mt-1">{mention.year}</div>}
                                        </div>
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
