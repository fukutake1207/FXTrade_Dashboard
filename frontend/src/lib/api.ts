import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    timeout: 30000, // 30秒
    headers: {
        'Content-Type': 'application/json',
    },
});

// グローバルエラーハンドリング
api.interceptors.response.use(
    response => response,
    error => {
        if (error.code === 'ECONNABORTED') {
            console.error('API request timed out:', error.config.url);
        } else if (error.response) {
            console.error('API error:', error.response.status, error.response.data);
        } else if (error.request) {
            console.error('No response from API:', error.request);
        } else {
            console.error('API request error:', error.message);
        }
        return Promise.reject(error);
    }
);

export interface PriceStat {
    date: string;
    session: string;
    open_price: number;
    high_price: number;
    low_price: number;
    close_price: number;
    range_pips: number;
    volatility: number;
    last_updated?: string;
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
    id: string;
    timestamp: string;
    content: string;
}

export interface NarrativeHistoryItem {
    id: string;
    timestamp: string;
    session: string;
    content: string;
}

export interface NarrativeProviderResponse {
    provider: 'gemini' | 'claude';
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
    trade_id: string;
    position_id?: string;
    entry_ticket?: string;
    exit_ticket?: string;
    timestamp: string;
    symbol: string;
    direction: 'LONG' | 'SHORT';
    entry_price: number;
    position_size: number;
    exit_price?: number;
    profit_loss_pips?: number;
    profit_loss_amount?: number;
    trade_duration_minutes?: number;
    pre_trade_confidence?: number;
    post_trade_evaluation?: string;
    lessons_learned?: string;
    entry_context?: {
        context_type: 'entry';
        session?: string;
        market_condition?: string;
        ai_narrative_summary?: string;
        active_scenarios: string[];
        key_levels_nearby: number[];
        correlation_status: Record<string, number>;
        economic_events_upcoming: string[];
    };
    exit_context?: {
        context_type: 'exit';
        session?: string;
        market_condition?: string;
        ai_narrative_summary?: string;
        active_scenarios: string[];
        key_levels_nearby: number[];
        correlation_status: Record<string, number>;
        economic_events_upcoming: string[];
    };
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

export const getNarrativeHistory = async (
    session?: string,
    limit: number = 10
): Promise<NarrativeHistoryItem[]> => {
    const params = new URLSearchParams();
    if (session) params.append('session', session);
    params.append('limit', limit.toString());

    const response = await api.get<NarrativeHistoryItem[]>(
        `/narratives/history?${params.toString()}`
    );
    return response.data;
};

export const getNarrativeProvider = async (): Promise<NarrativeProviderResponse> => {
    const response = await api.get<NarrativeProviderResponse>('/settings/narrative-provider');
    return response.data;
};

export const setNarrativeProvider = async (provider: 'gemini' | 'claude'): Promise<NarrativeProviderResponse> => {
    const response = await api.put<NarrativeProviderResponse>('/settings/narrative-provider', { provider });
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

export const syncTrades = async (): Promise<TradeLog[]> => {
    const response = await api.post<TradeLog[]>('/trades/sync');
    return response.data;
};

export const updateTrade = async (tradeId: string, trade: Partial<TradeLog>): Promise<TradeLog> => {
    const response = await api.put<TradeLog>(`/trades/${tradeId}`, trade);
    return response.data;
};

export const deleteTrade = async (tradeId: string): Promise<void> => {
    await api.delete(`/trades/${tradeId}`);
};

export const triggerDataCollection = async () => {
    const response = await api.post('/prices/collect');
    return response.data;
}

export default api;
