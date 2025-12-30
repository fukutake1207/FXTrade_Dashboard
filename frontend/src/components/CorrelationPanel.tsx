import { useEffect, useState } from 'react';
import { getCorrelationOverview, CorrelationOverview } from '../lib/api';
import { RefreshCcw, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';

const CorrelationPanel = () => {
    const [data, setData] = useState<CorrelationOverview | null>(null);
    const [loading, setLoading] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const result = await getCorrelationOverview();
            setData(result);
        } catch (error) {
            console.error("Failed to fetch correlations", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 600000); // 10 minutes
        return () => clearInterval(interval);
    }, []);

    if (!data && !loading) return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full max-w-md flex justify-center items-center h-48">
            <button onClick={fetchData} className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
                <RefreshCcw className="w-4 h-4" /> Reload
            </button>
        </div>
    );

    return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full max-w-md">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <ExternalLink className="w-5 h-5" /> Correlation Monitor
                </h2>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Updated: {new Date().toLocaleTimeString()}</span>
                    <button onClick={fetchData} className="p-1.5 hover:bg-muted rounded-md transition-colors" disabled={loading}>
                        <RefreshCcw className={cn("w-4 h-4 text-muted-foreground", loading && "animate-spin")} />
                    </button>
                </div>
            </div>

            {/* Asset Grid */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                {['Gold', 'Nikkei', 'S&P500'].map(asset => {
                    const priceInfo = data?.market_status[asset];
                    const corrInfo = data?.correlations[asset];
                    const isUp = (priceInfo?.change_pct || 0) >= 0;

                    return (
                        <div key={asset} className="flex flex-col p-3 bg-secondary/50 rounded-lg">
                            <span className="text-xs text-muted-foreground font-medium">{asset}</span>
                            <span className={cn("text-sm font-bold", isUp ? "text-green-500" : "text-red-500")}>
                                {priceInfo?.price.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                            </span>
                            <span className={cn("text-xs", isUp ? "text-green-600" : "text-red-600")}>
                                {isUp ? '+' : ''}{priceInfo?.change_pct.toFixed(2)}%
                            </span>

                            {corrInfo && (
                                <div className="mt-2 pt-2 border-t border-border/50">
                                    <span className="text-[10px] text-muted-foreground block">Corr (20d)</span>
                                    <span className={cn(
                                        "text-xs font-medium",
                                        Math.abs(corrInfo.coefficient) > 0.5 ? "text-primary" : "text-muted-foreground"
                                    )}>
                                        {corrInfo.coefficient > 0 ? '+' : ''}{corrInfo.coefficient.toFixed(2)}
                                    </span>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Insights */}
            {data?.insights && data.insights.length > 0 && (
                <div className="mt-4 p-3 bg-muted/30 rounded-lg border border-border/50">
                    <h3 className="text-sm font-medium mb-2 text-foreground">Correlation Insights</h3>
                    <ul className="space-y-1">
                        {data.insights.map((insight, idx) => (
                            <li key={idx} className="text-xs text-muted-foreground flex items-start gap-1.5">
                                <span className="mt-0.5 w-1 h-1 rounded-full bg-accent-foreground shrink-0" />
                                {insight}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default CorrelationPanel;
