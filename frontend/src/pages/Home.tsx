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

        { label: "Subjects", count: stats?.subjects, path: "/subjects" },
        { label: "Languages", count: stats?.languages, path: "/languages" },
        { label: "Data Sources / Research Projects", count: stats?.sources, path: "/sources" }
    ]

    return (
        <div className="h-full flex flex-col justify-center items-center font-serif text-gray-900 max-w-5xl mx-auto px-4 py-8">
            <div className="flex flex-col md:flex-row items-center gap-12 mb-16">
                <div className="flex-1 space-y-6">
                    <h2 className="text-2xl font-bold font-sans text-gray-800">About the Project</h2>
                    <p className="text-gray-600 leading-relaxed text-lg">
                        Welcome to the Jewish Philosophy Knowledge Graph. This project maps the rich history of Jewish philosophical thought, tracking the movement of historical figures, the works they authored, and the subjects they engaged with across different regions and time periods.
                    </p>
                    <p className="text-gray-600 leading-relaxed text-lg">
                        Explore the interactive map, delve into the network of connections, and discover the diverse data sources that power this platform.
                    </p>
                </div>
                <div className="flex-1 flex flex-col justify-center items-center">
                    <img 
                        src="/hero.png" 
                        alt="Historical Jewish Philosophy Manuscript Tree" 
                        className="rounded-xl shadow-lg border border-gray-200 max-h-80 object-cover"
                    />
                    <div className="mt-4 text-[10px] text-gray-400 text-center max-w-sm font-sans leading-tight">
                        <p>A fifteenth-century diagram of the three faculties of the soul from Italy, inscribed in the Cambridge Hebrew manuscript. Cambridge, University Library, MS Dd.10.68, fol. 239v.</p>
                        <p className="mt-1">Reproduced by kind permission of the Syndics of Cambridge University Library.</p>
                        <p className="mt-1">Citation: The Journal of Jewish Thought and Philosophy 33, 1 (2025) ; 10.1163/1477285x-12341366.</p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-x-8 gap-y-12 text-center w-full border-t border-gray-200 pt-12">
                {items.map((item) => (
                    <Link
                        key={item.label}
                        to={item.path}
                        className="group flex flex-col items-center hover:opacity-60 transition-opacity duration-300"
                    >
                        <span className="text-2xl font-bold mb-2 tracking-tight text-indigo-700">
                            {isLoading ? "-" : item.count || 0}
                        </span>
                        <span className="text-xs uppercase tracking-wider opacity-80 group-hover:opacity-100 font-sans font-medium text-gray-500">
                            {item.label}
                        </span>
                    </Link>
                ))}
            </div>
        </div>
    )
}
