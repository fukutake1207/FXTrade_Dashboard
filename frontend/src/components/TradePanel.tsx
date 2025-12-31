import { useEffect, useState } from 'react';
import { getTrades, getTradeStats, createTrade, TradeLog, TradeStats } from '../lib/api';
import { ClipboardList, Plus } from 'lucide-react';
import { cn } from '../lib/utils';
import { syncTrades } from '../lib/api';

const TradePanel = () => {
    const [trades, setTrades] = useState<TradeLog[]>([]);
    const [stats, setStats] = useState<TradeStats | null>(null);
    const [loading, setLoading] = useState(false);

    // Form State
    const [symbol, setSymbol] = useState('USDJPY');
    const [direction, setDirection] = useState<'LONG' | 'SHORT'>('LONG');
    const [entryPrice, setEntryPrice] = useState('');
    const [positionSize, setPositionSize] = useState('0.1');

    const fetchData = async () => {
        setLoading(true);
        try {
            const [tradesData, statsData] = await Promise.all([
                getTrades(),
                getTradeStats()
            ]);
            setTrades(tradesData);
            setStats(statsData);
        } catch (error) {
            console.error("Failed to fetch trade data", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createTrade({
                symbol,
                direction,
                entry_price: parseFloat(entryPrice),
                position_size: parseFloat(positionSize)
            });
            await fetchData();
            setEntryPrice('');
        } catch (error) {
            console.error("Failed to create trade", error);
        }
    };

    const handleSync = async () => {
        setLoading(true);
        try {
            await syncTrades();
            await fetchData();
        } catch (error: any) {
            console.error("Failed to sync trades", error);
            // Show alert or toast
            if (error.response?.status === 503) {
                alert("MT5との同期に失敗しました。\nMT5が起動しているか確認してください。");
            } else {
                alert("同期中にエラーが発生しました。");
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <ClipboardList className="w-5 h-5 text-emerald-500" /> Trade Log
                    <button
                        onClick={handleSync}
                        className="text-xs bg-muted hover:bg-muted/80 text-muted-foreground px-2 py-1 rounded ml-2 border flex items-center gap-1"
                        disabled={loading}
                    >
                        {loading ? "Syncing..." : "Sync MT5"}
                    </button>
                </h2>
                {stats && (
                    <div className="flex gap-4 text-xs font-mono">
                        <div className="flex flex-col items-end">
                            <span className="text-muted-foreground">Win Rate</span>
                            <span className="font-bold">{stats.win_rate}%</span>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className="text-muted-foreground">PF</span>
                            <span className="font-bold">{stats.profit_factor}</span>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className="text-muted-foreground">Total PnL</span>
                            <span className={cn("font-bold", stats.total_pnl >= 0 ? "text-green-500" : "text-red-500")}>
                                {stats.total_pnl}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* Simple Add Form */}
            <form onSubmit={handleCreate} className="flex gap-2 mb-4 bg-muted/40 p-2 rounded-lg">
                <select value={symbol} onChange={e => setSymbol(e.target.value)} className="bg-background border rounded px-2 py-1 text-sm w-20">
                    <option value="USDJPY">USDJPY</option>
                    <option value="GOLD">Gold</option>
                </select>
                <select value={direction} onChange={e => setDirection(e.target.value as any)} className="bg-background border rounded px-2 py-1 text-sm">
                    <option value="LONG">Long</option>
                    <option value="SHORT">Short</option>
                </select>
                <input
                    type="number" step="0.01" value={entryPrice} onChange={e => setEntryPrice(e.target.value)}
                    placeholder="Entry" className="bg-background border rounded px-2 py-1 text-sm w-20" required
                />
                <input
                    type="number" step="0.01" value={positionSize} onChange={e => setPositionSize(e.target.value)}
                    placeholder="Size" className="bg-background border rounded px-2 py-1 text-sm w-16" required
                />
                <button type="submit" className="bg-emerald-600 text-white p-1.5 rounded hover:bg-emerald-700">
                    <Plus className="w-4 h-4" />
                </button>
            </form>

            <div className="flex-1 overflow-y-auto space-y-2">
                {trades.length === 0 ? (
                    <div className="text-center text-muted-foreground text-sm py-4">No logged trades</div>
                ) : (
                    trades.slice().reverse().map(trade => (
                        <div key={trade.trade_id} className="flex justify-between items-center p-2 border rounded bg-card hover:bg-muted/50 transition-colors">
                            <div className="flex items-center gap-2">
                                <span className={cn(
                                    "px-1.5 py-0.5 text-[10px] font-bold rounded",
                                    trade.direction === 'LONG' ? "bg-blue-500/10 text-blue-500" : "bg-red-500/10 text-red-500"
                                )}>
                                    {trade.direction}
                                </span>
                                <span className="text-sm font-medium">{trade.symbol}</span>
                                <span className="text-xs text-muted-foreground">@ {trade.entry_price}</span>
                            </div>
                            <div className="text-right">
                                <span className={cn(
                                    "text-sm font-bold block",
                                    ((trade.profit_loss_amount || 0) >= 0) ? "text-green-500" : "text-red-500"
                                )}>
                                    {trade.profit_loss_amount != null ? trade.profit_loss_amount : "OPEN"}
                                </span>
                                <span className="text-[10px] text-muted-foreground">
                                    {new Date(trade.timestamp).toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default TradePanel;
