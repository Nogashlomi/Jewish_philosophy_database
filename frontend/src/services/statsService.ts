import api from './api';

export interface GlobalStats {
    persons: number;
    works: number;
    scholarly: number;
    places: number;
    subjects: number;
    languages: number;
    sources: number;
}

export const StatsService = {
    getStats: async (): Promise<GlobalStats> => {
        const response = await api.get<GlobalStats>('/stats');
        return response.data;
    }
};
