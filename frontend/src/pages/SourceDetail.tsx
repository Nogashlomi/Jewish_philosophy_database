import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { Database, Loader2, Users, BookOpen, MapPin, Glasses } from 'lucide-react'

// Note: Reusing definitions or fetching custom SourceDetail model
interface SourceDetailData {
    id: string
    label: string
    description?: string
    count: number
}

// We will fetch counts per category for the source separately or from a new endpoint.
// For now, we provide links to the list views filtered by this source.
interface SourceSpecificStats {
    persons: number
    works: number
    places: number
    scholarly: number
}

const SourceDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>()

    const { data: source, isLoading: isLoadingSource } = useQuery<SourceDetailData>({
        queryKey: ['source', id],
        queryFn: async () => {
            // In a real app we'd have a GET /sources/:id endpoint
            // For now we can fetch all and filter, or we will need to add that endpoint.
            const res = await api.get('/sources/')
            return res.data.find((s: any) => s.id === id)
        }
    })

    const { data: stats, isLoading: isLoadingStats } = useQuery<SourceSpecificStats>({
        queryKey: ['source-stats', id],
        queryFn: async () => {
            const res = await api.get(`/stats?source=${id}`)
            return res.data
        },
        enabled: !!id
    })

    if (isLoadingSource || isLoadingStats) {
        return (
            <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
            </div>
        )
    }

    if (!source) {
        return (
            <div className="bg-red-50 text-red-600 p-4 rounded-lg">
                Source not found.
            </div>
        )
    }

    const statCards = [
        {
            title: "Historical Persons",
            count: stats?.persons || 0,
            icon: Users,
            color: "text-blue-600",
            bg: "bg-blue-50",
            link: `/persons?source=${id}`
        },
        {
            title: "Historical Works",
            count: stats?.works || 0,
            icon: BookOpen,
            color: "text-amber-600",
            bg: "bg-amber-50",
            link: `/works?source=${id}`
        },
        {
            title: "Scholarly Literature",
            count: stats?.scholarly || 0,
            icon: Glasses,
            color: "text-purple-600",
            bg: "bg-purple-50",
            link: `/scholarly?source=${id}`
        },
        {
            title: "Places",
            count: stats?.places || 0,
            icon: MapPin,
            color: "text-emerald-600",
            bg: "bg-emerald-50",
            link: `/places?source=${id}`
        }
    ]

    return (
        <div className="space-y-8 max-w-5xl mx-auto">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
                <div className="flex items-center gap-4 mb-4">
                    <div className="p-3 bg-primary-50 rounded-xl text-primary-600">
                        <Database className="h-8 w-8" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 font-serif">
                            {source.label}
                        </h1>
                        <p className="text-gray-500 font-medium mt-1">Data Source Profile</p>
                    </div>
                </div>

                <p className="text-gray-600 text-lg leading-relaxed max-w-3xl mt-6">
                    {source.description || "A primary source collection for the Research Explorer."}
                </p>
            </div>

            <div>
                <h2 className="text-2xl font-bold text-gray-900 font-serif mb-6">Connected Entities</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {statCards.map((stat, idx) => (
                        <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col items-center text-center">
                            <div className={`p-3 rounded-xl ${stat.bg} ${stat.color} mb-4`}>
                                <stat.icon className="h-6 w-6" />
                            </div>
                            <h3 className="text-gray-500 font-medium mb-1">{stat.title}</h3>
                            <p className="text-3xl font-bold text-gray-900 mb-4">{stat.count}</p>
                            <Link
                                to={stat.link}
                                className="mt-auto px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 hover:text-primary-600 transition-colors w-full"
                            >
                                View List
                            </Link>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default SourceDetail
