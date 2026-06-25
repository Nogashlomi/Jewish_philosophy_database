import { useState, useEffect } from 'react';
import { entityService } from '../services/entityService';

interface Source {
    id: string;
    label: string;
}

interface Props {
    selectedSource: string | null;
    onChange: (sourceId: string | null) => void;
}

export function SourceFilter({ selectedSource, onChange }: Props) {
    const [sources, setSources] = useState<Source[]>([]);
    
    useEffect(() => {
        entityService.getSources().then(setSources).catch(console.error);
    }, []);

    return (
        <div className="flex items-center space-x-2">
            <label htmlFor="source-filter" className="text-sm font-medium text-gray-700">Data Source:</label>
            <select 
                id="source-filter"
                value={selectedSource || ""}
                onChange={(e) => onChange(e.target.value || null)}
                className="border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm p-1.5 border"
            >
                <option value="">All Sources</option>
                {sources.map(s => (
                    <option key={s.id} value={s.id}>{s.label}</option>
                ))}
            </select>
        </div>
    );
}
