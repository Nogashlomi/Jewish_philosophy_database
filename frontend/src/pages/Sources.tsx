import { useState, useEffect } from 'react';
import { entityService } from '../services/entityService';
import { Database, Loader2 } from 'lucide-react';

export default function Sources() {
    const [sources, setSources] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSources = async () => {
            try {
                const data = await entityService.getSources();
                setSources(data);
            } catch (error) {
                console.error("Failed to fetch sources", error);
            } finally {
                setLoading(false);
            }
        };
        fetchSources();
    }, []);

    if (loading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 font-sans">Data Sources</h1>
                <p className="text-gray-500 text-sm mt-1">
                    Projects and datasets integrated into the platform
                </p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {sources.map(source => (
                    <div key={source.id} className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden flex flex-col transition-all hover:shadow-md">
                        <div className="p-5 flex-grow">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                                    <Database className="h-5 w-5" />
                                </div>
                                <h3 className="font-semibold text-gray-900">{source.label}</h3>
                            </div>
                            <p className="text-sm text-gray-600">{source.description}</p>
                            
                            <div className="mt-4 pt-4 border-t border-gray-50 flex justify-between items-center text-sm">
                                <span className="text-gray-500">Entities</span>
                                <span className="font-medium text-gray-900 bg-gray-100 px-2 py-1 rounded">{source.count}</span>
                            </div>
                        </div>
                    </div>
                ))}
                
                {sources.length === 0 && (
                    <div className="col-span-full py-12 text-center text-gray-500 bg-white rounded-lg border border-dashed border-gray-300">
                        No data sources found.
                    </div>
                )}
            </div>
        </div>
    )
}
