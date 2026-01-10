import { useEffect, useState } from 'react';
import { getAlerts, createAlert, deleteAlert, AlertRule } from '../lib/api';
import { Bell, Trash2, Plus, AlertCircle, CheckCircle2, Info } from 'lucide-react';
import { cn } from '../lib/utils';

const AlertPanel = () => {
    const [alerts, setAlerts] = useState<AlertRule[]>([]);
    const [loading, setLoading] = useState(false);

    // Form State
    const [symbol, setSymbol] = useState('USDJPY');
    const [condition, setCondition] = useState<'above' | 'below'>('above');
    const [price, setPrice] = useState('150.00');
    const [creating, setCreating] = useState(false);

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const data = await getAlerts();
            setAlerts(data);
        } catch (error) {
            console.error("Failed to fetch alerts", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        try {
            await createAlert(symbol, condition, parseFloat(price));
            await fetchAlerts();
            setPrice(''); // Reset price field only
        } catch (error) {
            console.error("Failed to create alert", error);
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Delete this alert?")) return;
        try {
            await deleteAlert(id);
            // Optimistic update or refetch
            setAlerts(prev => prev.filter(a => a.id !== id));
        } catch (error) {
            console.error("Failed to delete alert", error);
        }
    };

    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 10000); // Poll frequently for alerts
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Bell className="w-5 h-5 text-yellow-500" /> Price Alerts
                    <div className="group relative">
                        <Info className="w-3.5 h-3.5 text-muted-foreground hover:text-yellow-500 transition-colors cursor-help" />
                        {/* Price Alerts Info Tooltip */}
                        <div className="invisible group-hover:visible absolute left-0 top-6 z-50 w-[400px] p-4 bg-popover border border-border rounded-lg shadow-lg">
                            <div className="space-y-3 text-xs">
                                <div>
                                    <h4 className="font-semibold text-foreground mb-1">Price Alerts とは</h4>
                                    <p className="text-muted-foreground leading-relaxed">
                                        指定した価格に到達したら通知するアラート機能。重要レベルの監視に活用
                                    </p>
                                </div>

                                <div>
                                    <h4 className="font-semibold text-foreground mb-1">アラートの種類</h4>
                                    <div className="space-y-2 text-[10px]">
                                        <div className="flex items-start gap-2">
                                            <span className="text-yellow-700 dark:text-yellow-400 font-semibold shrink-0">▲</span>
                                            <div>
                                                <div className="font-medium text-foreground">Above（上抜け）</div>
                                                <div className="text-muted-foreground">指定価格を上回ったら通知（レジスタンスブレイク監視）</div>
                                            </div>
                                        </div>
                                        <div className="flex items-start gap-2">
                                            <span className="text-yellow-700 dark:text-yellow-400 font-semibold shrink-0">▼</span>
                                            <div>
                                                <div className="font-medium text-foreground">Below（下抜け）</div>
                                                <div className="text-muted-foreground">指定価格を下回ったら通知（サポートブレイク監視）</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-semibold text-foreground mb-1">効果的な使い方</h4>
                                    <ul className="space-y-1 text-muted-foreground leading-relaxed text-[10px]">
                                        <li><strong className="text-foreground">✓ 重要レベル監視:</strong> ピボット、S/R、キリ番にアラート設定</li>
                                        <li><strong className="text-foreground">✓ ブレイクアウト:</strong> レジスタンス上抜けで買いエントリー準備</li>
                                        <li><strong className="text-foreground">✓ 損切り監視:</strong> ストップロス価格にアラート設定</li>
                                        <li><strong className="text-foreground">✓ 利確タイミング:</strong> 目標価格到達を通知</li>
                                    </ul>
                                </div>

                                <div>
                                    <h4 className="font-semibold text-foreground mb-1">ステータス表示</h4>
                                    <div className="flex gap-4 text-[10px]">
                                        <div className="flex items-center gap-1">
                                            <AlertCircle className="w-3 h-3 text-yellow-500" />
                                            <span className="text-muted-foreground">待機中</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <CheckCircle2 className="w-3 h-3 text-green-500" />
                                            <span className="text-muted-foreground">発火済み</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-2 border-t border-border">
                                    <p className="text-[10px] text-muted-foreground italic">
                                        🔔 10秒ごとに価格をチェック。発火後も自動削除されないので手動で削除
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </h2>
            </div>

            {/* Create Form */}
            <form onSubmit={handleCreate} className="flex gap-2 mb-4 bg-muted/40 p-2 rounded-lg">
                <select
                    value={symbol} onChange={e => setSymbol(e.target.value)}
                    className="bg-background border rounded px-2 py-1 text-sm w-20"
                >
                    <option value="USDJPY">USDJPY</option>
                    <option value="GOLD">Gold</option>
                    <option value="Nikkei">Nikkei</option>
                </select>
                <select
                    value={condition} onChange={e => setCondition(e.target.value as 'above' | 'below')}
                    className="bg-background border rounded px-2 py-1 text-sm flex-1"
                >
                    <option value="above">Above</option>
                    <option value="below">Below</option>
                </select>
                <input
                    type="number"
                    step="0.01"
                    value={price}
                    onChange={e => setPrice(e.target.value)}
                    placeholder="Price"
                    className="bg-background border rounded px-2 py-1 text-sm w-20"
                    required
                />
                <button
                    type="submit"
                    disabled={creating}
                    className="bg-primary text-primary-foreground p-1.5 rounded hover:bg-primary/90 disabled:opacity-50"
                >
                    <Plus className="w-4 h-4" />
                </button>
            </form>

            {/* Alert List */}
            <div className="flex-1 overflow-y-auto space-y-2 max-h-[200px]">
                {loading && alerts.length === 0 ? (
                    <div className="text-xs text-muted-foreground text-center">Loading...</div>
                ) : alerts.length === 0 ? (
                    <div className="text-xs text-muted-foreground text-center py-4">No active alerts</div>
                ) : (
                    alerts.map(alert => (
                        <div key={alert.id} className={cn(
                            "flex items-center justify-between p-2 rounded border",
                            alert.triggered ? "bg-red-500/10 border-red-500/50" : "bg-card border-border"
                        )}>
                            <div className="flex flex-col">
                                <span className={cn(
                                    "text-sm font-medium flex items-center gap-1",
                                    alert.triggered && "text-red-500"
                                )}>
                                    {alert.triggered ? <AlertCircle className="w-3 h-3" /> : null}
                                    {alert.symbol} {alert.condition} {alert.price.toFixed(2)}
                                </span>
                                {alert.triggered && (
                                    <span className="text-[10px] text-muted-foreground">
                                        Triggered: {new Date(alert.triggered_at || '').toLocaleTimeString()}
                                    </span>
                                )}
                            </div>
                            <button
                                onClick={() => handleDelete(alert.id)}
                                className="text-muted-foreground hover:text-red-500"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default AlertPanel;
