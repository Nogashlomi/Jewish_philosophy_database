import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { StatsService } from '../services/statsService'

export default function Home() {
    const { data: stats, isLoading } = useQuery({
        queryKey: ['stats'],
        queryFn: StatsService.getStats
    })

    const items = [
        { label: "Historical Persons", count: stats?.persons, path: "/persons" },
        { label: "Historical Works", count: stats?.works, path: "/works" },
        { label: "Scholarly Works", count: stats?.scholarly, path: "/scholarly" },
        { label: "Places", count: stats?.places, path: "/places" },
        { label: "Subjects", count: stats?.subjects, path: "/subjects" },
        { label: "Languages", count: stats?.languages, path: "/languages" },
        { label: "Sources", count: stats?.sources, path: "/sources" }
    ]

    return (
        <div className="h-full flex flex-col justify-center items-center font-serif text-gray-900">
            <h1 className="text-3xl font-medium mb-16 tracking-wider font-serif">
                Philosophy in Jewish History
            </h1>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-x-20 gap-y-16 text-center">
                {items.map((item) => (
                    <Link
                        key={item.label}
                        to={item.path}
                        className="group flex flex-col items-center hover:opacity-60 transition-opacity duration-300"
                    >
                        <span className="text-4xl font-bold mb-3 tracking-tight">
                            {isLoading ? "-" : item.count || 0}
                        </span>
                        <span className="text-sm uppercase tracking-widest opacity-80 group-hover:opacity-100">
                            {item.label}
                        </span>
                    </Link>
                ))}
            </div>
        </div>
    )
}
