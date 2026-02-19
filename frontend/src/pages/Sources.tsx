import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { Database, Loader2 } from 'lucide-react'

interface Source {
    id: string
    label: string
    description?: string
    count: number
}

const Sources: React.FC = () => {
    const { data: sources, isLoading, error } = useQuery<Source[]>({
        queryKey: ['sources'],
        queryFn: async () => {
            const res = await api.get('/sources/')
            return res.data
        }
    })

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-gray-900 font-serif">Data Sources</h1>
                <div className="text-sm text-gray-500">
                    Total: {sources?.length || 0} sources
                </div>
            </div>
            <p className="text-gray-500 mt-2 max-w-2xl text-lg font-light">
                The research data is aggregated from the following scholarly sources.
            </p>

            {isLoading ? (
                <div className="flex justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
                </div>
            ) : error ? (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg">
                    Error loading sources.
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {sources?.map((source) => (
                        <div key={source.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="p-2 bg-primary-50 rounded-lg text-primary-600">
                                            <Database className="h-5 w-5" />
                                        </div>
                                        <h3 className="text-xl font-semibold text-gray-900">
                                            {source.label}
                                        </h3>
                                    </div>

                                    <p className="text-gray-600 mt-3 leading-relaxed">
                                        {source.description || "A primary source collection for the Research Explorer."}
                                    </p>

                                    <div className="mt-5 flex items-center gap-4 text-sm">
                                        <div className="bg-gray-50 px-3 py-1 rounded-full border border-gray-100 text-gray-600 font-medium">
                                            {source.count} Scholarly Works
                                        </div>
                                        <Link
                                            to={`/scholarly?source=${encodeURIComponent(source.id)}`}
                                            className="text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 group"
                                        >
                                            View Works
                                            <span className="group-hover:translate-x-0.5 transition-transform">→</span>
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default Sources
