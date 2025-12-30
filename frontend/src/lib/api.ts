import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface PriceStat {
    date: string;
    session: string;
    open_price: number;
    high_price: number;
    low_price: number;
    close_price: number;
    range_pips: number;
    volatility: number;
}

export interface CorrelationOverview {
    correlations: Record<string, {
        coefficient: number;
        strength: string;
        relationship: string;
    }>;
    market_status: Record<string, {
        price: number;
        change_pct: number;
    }>;
    insights: string[];
}

export interface SessionInfo {
    id: string;
    name: string;
    status: 'active' | 'upcoming' | 'closed';
    start_time_str: string;
    end_time_str: string;
    remaining_duration: string;
    is_active: boolean;
}

export interface SessionResponse {
    current_time: string;
    timeline_progress: number;
    sessions: Record<string, SessionInfo>;
}

export interface NarrativeResponse {
    id: number;
    timestamp: string;
    content: string;
}

export interface KeyLevel {
    price: number;
    type: string;
    description: string;
    strength: number;
}

export interface MarketScenario {
    direction: string;
    description: string;
    active_levels: KeyLevel[];
}

export interface AlertRule {
    id: string;
    symbol: string;
    condition: 'above' | 'below';
    price: number;
    active: boolean;
    triggered: boolean;
    triggered_at?: string;
    message: string;
}

export interface TradeLog {
    id: number;
    symbol: string;
    entry_time: string;
    entry_price: number;
    exit_time?: string;
    exit_price?: number;
    direction: 'LONG' | 'SHORT';
    volume: number;
    pnl?: number;
    status: 'OPEN' | 'CLOSED';
}

export interface TradeStats {
    total_trades: number;
    win_rate: number;
    profit_factor: number;
    total_pnl: number;
    win_count: number;
    loss_count: number;
}

export const getPriceStats = async (): Promise<PriceStat[]> => {
    const response = await api.get<PriceStat[]>('/prices/stats/today');
    return response.data;
};

export const getCorrelationOverview = async (): Promise<CorrelationOverview> => {
    const response = await api.get<CorrelationOverview>('/correlations/overview');
    return response.data;
};

export const getSessionStatus = async (): Promise<SessionResponse> => {
    const response = await api.get<SessionResponse>('/sessions/status');
    return response.data;
};

export const getLatestNarrative = async (): Promise<NarrativeResponse | null> => {
    const response = await api.get<NarrativeResponse | null>('/narratives/latest');
    return response.data;
};

export const generateMarketNarrative = async (): Promise<NarrativeResponse> => {
    const response = await api.post<NarrativeResponse>('/narratives/generate');
    return response.data;
};

export const getScenarios = async (): Promise<MarketScenario[]> => {
    const response = await api.get<MarketScenario[]>('/scenarios/current');
    return response.data;
};

export const getAlerts = async (): Promise<AlertRule[]> => {
    const response = await api.get<AlertRule[]>('/alerts/');
    return response.data;
};

export const createAlert = async (symbol: string, condition: 'above' | 'below', price: number): Promise<AlertRule> => {
    const response = await api.post<AlertRule>('/alerts/', {
        symbol, condition, price
    });
    return response.data;
};

export const deleteAlert = async (id: string): Promise<void> => {
    await api.delete(`/alerts/${id}`);
};

// Trades
export const getTrades = async (): Promise<TradeLog[]> => {
    const response = await api.get<TradeLog[]>('/trades/');
    return response.data;
};

export const getTradeStats = async (): Promise<TradeStats> => {
    const response = await api.get<TradeStats>('/trades/stats');
    return response.data;
};

export const createTrade = async (trade: Partial<TradeLog>): Promise<TradeLog> => {
    const response = await api.post<TradeLog>('/trades/', trade);
    return response.data;
};

export const triggerDataCollection = async () => {
    const response = await api.post('/prices/collect');
    return response.data;
}

export default api;
