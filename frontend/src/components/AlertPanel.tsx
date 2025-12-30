import { useEffect, useState } from 'react';
import { getAlerts, createAlert, deleteAlert, AlertRule } from '../lib/api';
import { Bell, Trash2, Plus, AlertCircle, CheckCircle2 } from 'lucide-react';
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
