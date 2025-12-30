import { useEffect, useState } from 'react';
import { getPriceStats, PriceStat, triggerDataCollection } from '../lib/api';
import { ArrowUp, ArrowDown, RefreshCcw } from 'lucide-react';
import { cn } from '../lib/utils'; // Assuming generic card utils are available or inline styles

const PricePanel = () => {
    const [stats, setStats] = useState<PriceStat[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const data = await getPriceStats();
            setStats(data);
        } catch (error) {
            console.error("Failed to fetch stats", error);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async () => {
        setLoading(true);
        try {
            await triggerDataCollection();
            await fetchStats();
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchStats();
        // Refresh every 60 seconds
        const interval = setInterval(fetchStats, 60000);
        return () => clearInterval(interval);
    }, []);

    if (stats.length === 0 && !loading) {
        return (
            <div className="p-4 bg-card rounded-lg border shadow-sm">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold">Price Statistics</h2>
                    <button onClick={handleRefresh} className="p-2 hover:bg-secondary rounded-full" disabled={loading}>
                        <RefreshCcw className={cn("w-4 h-4", loading && "animate-spin")} />
                    </button>
                </div>
                <p className="text-muted-foreground">No data available.</p>
            </div>
        )
    }

    // Use the latest stat for display
    const latest = stats[0] || {};
    const isUp = latest.close_price >= latest.open_price;

    return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full max-w-md">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold text-card-foreground">USDJPY Summary</h2>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{latest.date}</span>
                    <button onClick={handleRefresh} className="p-1.5 hover:bg-muted rounded-md transition-colors" disabled={loading}>
                        <RefreshCcw className={cn("w-4 h-4 text-muted-foreground", loading && "animate-spin")} />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 flex items-baseline gap-2 mb-2">
                    <span className={cn("text-4xl font-bold tracking-tight", isUp ? "text-green-500" : "text-red-500")}>
                        {latest.close_price?.toFixed(2)}
                    </span>
                    <span className="text-sm font-medium text-muted-foreground">
                        Last
                    </span>
                </div>

                <StatBox label="Open" value={latest.open_price?.toFixed(2)} />
                <StatBox label="High" value={latest.high_price?.toFixed(2)} />
                <StatBox label="Low" value={latest.low_price?.toFixed(2)} />
                <StatBox label="Range" value={`${latest.range_pips?.toFixed(1)} pips`} />
            </div>

            <div className="mt-6 pt-4 border-t">
                <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Volatility (Avg Range)</span>
                    <span className="text-sm font-medium">{latest.volatility?.toFixed(1)} pips</span>
                </div>
            </div>
        </div>
    );
};

const StatBox = ({ label, value }: { label: string, value: string }) => (
    <div className="flex flex-col">
        <span className="text-xs text-muted-foreground uppercase">{label}</span>
        <span className="text-lg font-mono font-medium">{value}</span>
    </div>
)

export default PricePanel;
