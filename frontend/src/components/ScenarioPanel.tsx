import { useEffect, useState } from 'react';
import { getScenarios, MarketScenario } from '../lib/api';
import { Target, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
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
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-3">
                        <h2 className="text-lg font-semibold flex items-center gap-2">
                            <Target className="w-5 h-5 text-orange-500" /> Key Scenarios
                            <div className="group relative">
                                <Info className="w-3.5 h-3.5 text-muted-foreground hover:text-orange-500 transition-colors cursor-help" />
                                {/* Key Scenarios Info Tooltip */}
                                <div className="invisible group-hover:visible absolute left-0 top-6 z-50 w-[440px] p-4 bg-popover border border-border rounded-lg shadow-lg">
                                    <div className="space-y-3 text-xs">
                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">Key Scenarios とは</h4>
                                            <p className="text-muted-foreground leading-relaxed">
                                                前日D1足データから数学的に計算される固定的なピボットポイントと重要価格レベル
                                            </p>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">計算方法</h4>
                                            <div className="space-y-1 text-[10px] text-muted-foreground font-mono bg-secondary/30 p-2 rounded">
                                                <div>Pivot = (High + Low + Close) / 3</div>
                                                <div>R1 = (2 × Pivot) - Low</div>
                                                <div>S1 = (2 × Pivot) - High</div>
                                                <div>キリ番 = 整数価格（157.00など）</div>
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">価格レベルの意味</h4>
                                            <div className="space-y-2 text-[10px]">
                                                <div className="flex items-start gap-2">
                                                    <span className="text-orange-700 dark:text-orange-400 font-semibold shrink-0">P</span>
                                                    <div>
                                                        <div className="font-medium text-foreground">Pivot（ピボット）</div>
                                                        <div className="text-muted-foreground">均衡点。上なら強気、下なら弱気</div>
                                                    </div>
                                                </div>
                                                <div className="flex items-start gap-2">
                                                    <span className="text-orange-700 dark:text-orange-400 font-semibold shrink-0">R</span>
                                                    <div>
                                                        <div className="font-medium text-foreground">Resistance（レジスタンス）</div>
                                                        <div className="text-muted-foreground">上昇を止める壁。利確・ショート検討</div>
                                                    </div>
                                                </div>
                                                <div className="flex items-start gap-2">
                                                    <span className="text-orange-700 dark:text-orange-400 font-semibold shrink-0">S</span>
                                                    <div>
                                                        <div className="font-medium text-foreground">Support（サポート）</div>
                                                        <div className="text-muted-foreground">下落を支える床。利確・ロング検討</div>
                                                    </div>
                                                </div>
                                                <div className="flex items-start gap-2">
                                                    <span className="text-orange-700 dark:text-orange-400 font-semibold shrink-0">#</span>
                                                    <div>
                                                        <div className="font-medium text-foreground">Round Number（キリ番）</div>
                                                        <div className="text-muted-foreground">心理的節目。大口注文が集中しやすい</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">トレード戦略</h4>
                                            <ul className="space-y-1 text-muted-foreground leading-relaxed text-[10px]">
                                                <li><strong className="text-foreground">✓ ブレイクアウト:</strong> R/S突破で順張りエントリー</li>
                                                <li><strong className="text-foreground">✓ レンジ取引:</strong> R/S間の往復を狙う逆張り</li>
                                                <li><strong className="text-foreground">✓ 利確目標:</strong> 次のR/Sレベルで部分利確</li>
                                                <li><strong className="text-foreground">✓ ストップ配置:</strong> R/Sの少し外にストップロス設定</li>
                                            </ul>
                                        </div>

                                        <div className="pt-2 border-t border-border">
                                            <p className="text-[10px] text-muted-foreground italic">
                                                📊 多くのトレーダーが同じレベルを見るため、自己実現的に機能しやすい
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </h2>
                        <span className="px-2 py-0.5 bg-orange-100 dark:bg-orange-900/30 border border-orange-300 dark:border-orange-700 rounded-md text-[10px] font-semibold text-orange-700 dark:text-orange-400 uppercase tracking-wide">
                            Algorithmic
                        </span>
                    </div>
                    <p className="text-xs text-muted-foreground ml-7">
                        前日D1足から計算されたピボットポイントとキリ番
                    </p>
                </div>
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
                                    {scenario.direction === 'bullish' ? '強気' :
                                        scenario.direction === 'bearish' ? '弱気' : '中立'}
                                </span>
                            </div>
                            <p className="text-sm text-foreground mb-2">{scenario.description}</p>

                            {scenario.active_levels.length > 0 && (
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {scenario.active_levels.map((level, lIdx) => (
                                        <span key={lIdx} className="px-2 py-0.5 bg-orange-50 dark:bg-orange-950 border border-orange-200 dark:border-orange-800 rounded text-[10px] items-center flex gap-1 text-muted-foreground font-mono">
                                            {level.type === 'pivot' && 'P'}
                                            {level.type === 'resistance' && 'R'}
                                            {level.type === 'support' && 'S'}
                                            {level.type === 'round' && '#'}
                                            <span className="font-semibold text-orange-700 dark:text-orange-400">{level.price.toFixed(2)}</span>
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
