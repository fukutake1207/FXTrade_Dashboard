import { useEffect, useState } from 'react';
import { getTrades, getTradeStats, createTrade, TradeLog, TradeStats, updateTrade, deleteTrade } from '../lib/api';
import { ClipboardList, Plus, Info, Link, Edit3, Pencil, Trash2, X } from 'lucide-react';
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

    // Edit Modal State
    const [editingTrade, setEditingTrade] = useState<TradeLog | null>(null);
    const [editSymbol, setEditSymbol] = useState('');
    const [editDirection, setEditDirection] = useState<'LONG' | 'SHORT'>('LONG');
    const [editEntryPrice, setEditEntryPrice] = useState('');
    const [editPositionSize, setEditPositionSize] = useState('');
    const [editExitPrice, setEditExitPrice] = useState('');
    const [editProfitLoss, setEditProfitLoss] = useState('');

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

    const handleEditClick = (trade: TradeLog) => {
        setEditingTrade(trade);
        setEditSymbol(trade.symbol);
        setEditDirection(trade.direction);
        setEditEntryPrice(trade.entry_price.toString());
        setEditPositionSize(trade.position_size.toString());
        setEditExitPrice(trade.exit_price?.toString() || '');
        setEditProfitLoss(trade.profit_loss_amount?.toString() || '');
    };

    const handleEditSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingTrade) return;

        try {
            await updateTrade(editingTrade.trade_id, {
                symbol: editSymbol,
                direction: editDirection,
                entry_price: parseFloat(editEntryPrice),
                position_size: parseFloat(editPositionSize),
                exit_price: editExitPrice ? parseFloat(editExitPrice) : undefined,
                profit_loss_amount: editProfitLoss ? parseFloat(editProfitLoss) : undefined,
            });
            await fetchData();
            setEditingTrade(null);
        } catch (error: any) {
            console.error("Failed to update trade", error);
            if (error.response?.status === 403) {
                alert("MT5同期されたトレードは編集できません。");
            } else {
                alert("トレードの更新に失敗しました。");
            }
        }
    };

    const handleDelete = async (tradeId: string) => {
        if (!confirm("このトレードを削除しますか？")) return;

        try {
            await deleteTrade(tradeId);
            await fetchData();
        } catch (error: any) {
            console.error("Failed to delete trade", error);
            if (error.response?.status === 403) {
                alert("MT5同期されたトレードは削除できません。");
            } else {
                alert("トレードの削除に失敗しました。");
            }
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
                    <div className="group relative">
                        <Info className="w-3.5 h-3.5 text-muted-foreground hover:text-emerald-500 transition-colors cursor-help" />
                        {/* Trade Log Info Tooltip */}
                        <div className="invisible group-hover:visible absolute left-0 top-6 z-50 w-[400px] p-4 bg-popover border border-border rounded-lg shadow-lg">
                            <div className="space-y-3 text-xs">
                                <div>
                                    <h4 className="font-semibold text-foreground mb-1">Trade Log とは</h4>
                                    <p className="text-muted-foreground leading-relaxed">
                                        トレード履歴の記録と統計表示。MT5と同期してパフォーマンスを追跡
                                    </p>
                                </div>

                                <div>
                                    <h4 className="font-semibold text-foreground mb-1">表示される統計</h4>
                                    <div className="space-y-2 text-[10px]">
                                        <div>
                                            <div className="font-medium text-foreground">Win Rate（勝率）</div>
                                            <div className="text-muted-foreground">勝ちトレード数 ÷ 全トレード数 × 100%</div>
                                        </div>
                                        <div>
                                            <div className="font-medium text-foreground">PF（Profit Factor）</div>
                                            <div className="text-muted-foreground">総利益 ÷ 総損失。1.0以上で利益、2.0以上で優秀</div>
                                        </div>
                                        <div>
                                            <div className="font-medium text-foreground">Total PnL（総損益）</div>
                                            <div className="text-muted-foreground">すべてのトレードの損益合計</div>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-semibold text-foreground mb-1">使い方</h4>
                                    <ul className="space-y-1 text-muted-foreground leading-relaxed text-[10px]">
                                        <li><strong className="text-foreground">✓ MT5同期:</strong> "Sync MT5"ボタンでMT5の履歴を自動取得</li>
                                        <li><strong className="text-foreground">✓ 手動追加:</strong> フォームからトレードを手動登録</li>
                                        <li><strong className="text-foreground">✓ 傾向分析:</strong> 勝率・PFから戦略の有効性を評価</li>
                                        <li><strong className="text-foreground">✓ 改善点:</strong> 負けトレードのパターンを分析</li>
                                    </ul>
                                </div>

                                <div className="pt-2 border-t border-border">
                                    <p className="text-[10px] text-muted-foreground italic">
                                        💡 PF 2.0以上、勝率60%以上が一般的な目標値
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
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
                    trades.map(trade => {
                        // MT5同期か手動入力かを判定
                        const isMT5Synced = Boolean(trade.position_id || trade.entry_ticket);

                        return (
                            <div key={trade.trade_id} className="flex justify-between items-center p-2 border rounded bg-card hover:bg-muted/50 transition-colors">
                                <div className="flex items-center gap-2">
                                    {/* MT5同期/手動入力アイコン + ツールチップ */}
                                    <div className="group relative">
                                        {isMT5Synced ? (
                                            <Link className="w-3.5 h-3.5 text-blue-500" />
                                        ) : (
                                            <Edit3 className="w-3.5 h-3.5 text-amber-500" />
                                        )}
                                        {/* ツールチップ */}
                                        <div className="invisible group-hover:visible absolute left-0 top-5 z-50 w-[280px] p-3 bg-popover border border-border rounded-lg shadow-lg">
                                            <div className="space-y-2 text-xs">
                                                <div>
                                                    <div className="font-semibold text-foreground mb-1">
                                                        {isMT5Synced ? "🔗 MT5同期" : "✏️ 手動入力"}
                                                    </div>
                                                    <div className="text-[10px] text-muted-foreground">
                                                        {isMT5Synced ? "MT5から自動同期されたトレード" : "手動で登録されたトレード"}
                                                    </div>
                                                </div>
                                                {isMT5Synced && (
                                                    <div className="pt-2 border-t border-border space-y-1 text-[10px]">
                                                        {trade.position_id && (
                                                            <div>
                                                                <span className="font-medium text-foreground">Position ID: </span>
                                                                <span className="text-muted-foreground font-mono">{trade.position_id}</span>
                                                            </div>
                                                        )}
                                                        {trade.entry_ticket && (
                                                            <div>
                                                                <span className="font-medium text-foreground">Entry Ticket: </span>
                                                                <span className="text-muted-foreground font-mono">{trade.entry_ticket}</span>
                                                            </div>
                                                        )}
                                                        {trade.exit_ticket && (
                                                            <div>
                                                                <span className="font-medium text-foreground">Exit Ticket: </span>
                                                                <span className="text-muted-foreground font-mono">{trade.exit_ticket}</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <span className={cn(
                                        "px-1.5 py-0.5 text-[10px] font-bold rounded",
                                        trade.direction === 'LONG' ? "bg-blue-500/10 text-blue-500" : "bg-red-500/10 text-red-500"
                                    )}>
                                        {trade.direction}
                                    </span>
                                    <span className="text-sm font-medium">{trade.symbol}</span>
                                    <span className="text-xs text-muted-foreground">@ {trade.entry_price}</span>
                                </div>
                                <div className="text-right flex items-center gap-2">
                                    <div>
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
                                    {/* Edit/Delete buttons for manual trades only */}
                                    {!isMT5Synced && (
                                        <div className="flex gap-1">
                                            <button
                                                onClick={() => handleEditClick(trade)}
                                                className="p-1 hover:bg-muted rounded transition-colors"
                                                title="編集"
                                            >
                                                <Pencil className="w-3.5 h-3.5 text-blue-500" />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(trade.trade_id)}
                                                className="p-1 hover:bg-muted rounded transition-colors"
                                                title="削除"
                                            >
                                                <Trash2 className="w-3.5 h-3.5 text-red-500" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Edit Modal */}
            {editingTrade && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setEditingTrade(null)}>
                    <div className="bg-card border rounded-xl p-6 w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold">トレードを編集</h3>
                            <button onClick={() => setEditingTrade(null)} className="p-1 hover:bg-muted rounded">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <form onSubmit={handleEditSave} className="space-y-4">
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">通貨ペア</label>
                                    <select
                                        value={editSymbol}
                                        onChange={e => setEditSymbol(e.target.value)}
                                        className="bg-background border rounded px-3 py-2 text-sm w-full"
                                    >
                                        <option value="USDJPY">USDJPY</option>
                                        <option value="GOLD">Gold</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">方向</label>
                                    <select
                                        value={editDirection}
                                        onChange={e => setEditDirection(e.target.value as 'LONG' | 'SHORT')}
                                        className="bg-background border rounded px-3 py-2 text-sm w-full"
                                    >
                                        <option value="LONG">Long</option>
                                        <option value="SHORT">Short</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">エントリー価格</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={editEntryPrice}
                                        onChange={e => setEditEntryPrice(e.target.value)}
                                        className="bg-background border rounded px-3 py-2 text-sm w-full"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">ポジションサイズ</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={editPositionSize}
                                        onChange={e => setEditPositionSize(e.target.value)}
                                        className="bg-background border rounded px-3 py-2 text-sm w-full"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">決済価格（任意）</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={editExitPrice}
                                        onChange={e => setEditExitPrice(e.target.value)}
                                        className="bg-background border rounded px-3 py-2 text-sm w-full"
                                        placeholder="未決済の場合は空欄"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">損益（任意）</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={editProfitLoss}
                                        onChange={e => setEditProfitLoss(e.target.value)}
                                        className="bg-background border rounded px-3 py-2 text-sm w-full"
                                        placeholder="損益額"
                                    />
                                </div>
                            </div>

                            <div className="flex gap-2 pt-2">
                                <button
                                    type="submit"
                                    className="flex-1 bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700 font-medium"
                                >
                                    保存
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setEditingTrade(null)}
                                    className="flex-1 bg-muted text-foreground px-4 py-2 rounded hover:bg-muted/80 font-medium"
                                >
                                    キャンセル
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TradePanel;
