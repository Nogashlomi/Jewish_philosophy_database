import { useState, useEffect } from 'react';
import { entityService } from '../services/entityService';

interface Source {
    id: string;
    label: string;
    count: number;
}

interface SourceFilterProps {
    selectedSource: string | null;
    onSourceChange: (sourceId: string | null) => void;
}

export default function SourceFilter({ selectedSource, onSourceChange }: SourceFilterProps) {
    const [sources, setSources] = useState<Source[]>([]);
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

    if (loading) return null;

    return (
        <div className="flex items-center space-x-2 mb-4">
            <span className="text-sm font-medium text-gray-700">Filter by Data Source:</span>
            <select
                value={selectedSource || ''}
                onChange={(e) => onSourceChange(e.target.value || null)}
                className="block w-64 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pl-3 pr-10 py-2 border"
            >
                <option value="">All Sources</option>
                {sources.map((source) => (
                    <option key={source.id} value={source.id}>
                        {source.label} ({source.count})
                    </option>
                ))}
            </select>
        </div>
    );
}
