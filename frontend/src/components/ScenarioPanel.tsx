import { useEffect, useState } from 'react';
import { getScenarios, MarketScenario } from '../lib/api';
import { Target, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../lib/utils';

const ScenarioPanel = () => {
    const [scenarios, setScenarios] = useState<MarketScenario[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchScenarios = async () => {
        setLoading(true);
        try {
            const data = await getScenarios();
            setScenarios(data);
        } catch (error) {
            console.error("Failed to fetch scenarios", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchScenarios();
        const interval = setInterval(fetchScenarios, 300000); // 5 minutes
        return () => clearInterval(interval);
    }, []);

    if (loading && scenarios.length === 0) return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full h-full flex items-center justify-center">
            <span className="text-muted-foreground text-sm">Analyzing scenarios...</span>
        </div>
    );

    return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Target className="w-5 h-5 text-orange-500" /> Key Scenarios
                </h2>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3">
                {scenarios.length === 0 ? (
                    <div className="text-sm text-muted-foreground text-center py-4">No scenarios generated</div>
                ) : (
                    scenarios.map((scenario, idx) => (
                        <div key={idx} className="p-3 bg-secondary/30 rounded-lg border border-border/50">
                            <div className="flex items-center gap-2 mb-2">
                                {scenario.direction === 'bullish' && <TrendingUp className="w-4 h-4 text-green-500" />}
                                {scenario.direction === 'bearish' && <TrendingDown className="w-4 h-4 text-red-500" />}
                                {scenario.direction === 'neutral' && <Minus className="w-4 h-4 text-yellow-500" />}
                                <span className={cn(
                                    "text-sm font-bold uppercase",
                                    scenario.direction === 'bullish' ? "text-green-500" :
                                        scenario.direction === 'bearish' ? "text-red-500" : "text-yellow-500"
                                )}>
                                    {scenario.direction}
                                </span>
                            </div>
                            <p className="text-sm text-foreground mb-2">{scenario.description}</p>

                            {scenario.active_levels.length > 0 && (
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {scenario.active_levels.map((level, lIdx) => (
                                        <span key={lIdx} className="px-2 py-0.5 bg-background border rounded text-[10px] items-center flex gap-1 text-muted-foreground font-mono">
                                            {level.type === 'pivot' && 'P'}
                                            {level.type === 'resistance' && 'R'}
                                            {level.type === 'support' && 'S'}
                                            {level.type === 'round' && '#'}
                                            <span className="font-semibold text-foreground">{level.price.toFixed(2)}</span>
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ScenarioPanel;
