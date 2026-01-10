import { useEffect, useState } from 'react';
import { getLatestNarrative, generateMarketNarrative, NarrativeResponse, getNarrativeProvider, setNarrativeProvider, getNarrativeHistory, NarrativeHistoryItem, getScenarios, MarketScenario } from '../lib/api';
import { Bot, Sparkles, RefreshCw, Info, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../lib/utils';

const NarrativePanel = () => {
    const [narrative, setNarrative] = useState<NarrativeResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [provider, setProvider] = useState<'gemini' | 'claude'>('gemini');
    const [switching, setSwitching] = useState(false);

    // History state
    const [history, setHistory] = useState<NarrativeHistoryItem[]>([]);
    const [selectedSession, setSelectedSession] = useState<string | null>(null);
    const [selectedNarrativeId, setSelectedNarrativeId] = useState<string | null>(null);

    // Scenarios state
    const [scenarios, setScenarios] = useState<MarketScenario[]>([]);

    const fetchLatest = async () => {
        setLoading(true);
        try {
            const data = await getLatestNarrative();
            setNarrative(data);
        } catch (error) {
            console.error("Failed to fetch narrative", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchProvider = async () => {
        try {
            const data = await getNarrativeProvider();
            setProvider(data.provider);
        } catch (error) {
            console.error("Failed to fetch provider", error);
        }
    };

    const fetchScenarios = async () => {
        try {
            const data = await getScenarios();
            setScenarios(data);
        } catch (error) {
            console.error("Failed to fetch scenarios", error);
        }
    };

    const handleSwitch = async (next: 'gemini' | 'claude') => {
        if (next === provider) return;
        setSwitching(true);
        try {
            const data = await setNarrativeProvider(next);
            setProvider(data.provider);
        } catch (error) {
            console.error("Failed to switch provider", error);
        } finally {
            setSwitching(false);
        }
    };

    const fetchHistory = async () => {
        try {
            const data = await getNarrativeHistory(selectedSession || undefined, 10);
            setHistory(data);
        } catch (error) {
            console.error("Failed to fetch narrative history", error);
        }
    };

    const handleGenerate = async () => {
        setGenerating(true);
        try {
            const data = await generateMarketNarrative();
            setNarrative(data);
            // Refresh history and select the newly generated narrative
            await fetchHistory();
            setSelectedNarrativeId(data.id);
        } catch (error) {
            console.error("Failed to generate narrative", error);
        } finally {
            setGenerating(false);
        }
    };

    useEffect(() => {
        fetchLatest();
        fetchProvider();
        fetchHistory();
        fetchScenarios();

        const scenarioInterval = setInterval(fetchScenarios, 300000); // 5分ごと
        return () => clearInterval(scenarioInterval);
    }, []);

    useEffect(() => {
        fetchHistory();
    }, [selectedSession]);

    // Determine which narrative to display
    const displayedNarrative = selectedNarrativeId
        ? history.find(h => h.id === selectedNarrativeId)
        : narrative;

    return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <div className="flex flex-col gap-1 flex-1">
                    <div className="flex items-center gap-3">
                        <h2 className="text-lg font-semibold flex items-center gap-2">
                            <Bot className="w-5 h-5 text-indigo-500" /> AI Market Narrative
                            <div className="group relative">
                                <Info className="w-3.5 h-3.5 text-muted-foreground hover:text-indigo-500 transition-colors cursor-help" />
                                {/* AI Narrative Info Tooltip */}
                                <div className="invisible group-hover:visible absolute left-0 top-6 z-50 w-[440px] p-4 bg-popover border border-border rounded-lg shadow-lg">
                                    <div className="space-y-3 text-xs">
                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">AI Market Narrative とは</h4>
                                            <p className="text-muted-foreground leading-relaxed">
                                                現在の市場データをAI（Gemini/Claude）が分析し、動的に生成する市場解説
                                            </p>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">分析に使用するデータ</h4>
                                            <ul className="space-y-1 text-muted-foreground leading-relaxed text-[10px]">
                                                <li>✓ USDJPY現在価格（MT5からリアルタイム取得）</li>
                                                <li>✓ 相関資産の価格変動（Gold/Nikkei/S&P500）</li>
                                                <li>✓ 市場セッションの状態（東京/ロンドン/NY）</li>
                                                <li>✓ 過去の価格データとトレンド</li>
                                            </ul>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">Key Scenarios との違い</h4>
                                            <div className="grid grid-cols-2 gap-2 text-[10px]">
                                                <div className="p-2 bg-orange-50 dark:bg-orange-950/30 rounded border border-orange-200 dark:border-orange-800">
                                                    <div className="font-semibold text-orange-700 dark:text-orange-400 mb-1">Key Scenarios</div>
                                                    <div className="text-muted-foreground">前日データから数学的に計算した固定レベル</div>
                                                </div>
                                                <div className="p-2 bg-indigo-50 dark:bg-indigo-950/30 rounded border border-indigo-200 dark:border-indigo-800">
                                                    <div className="font-semibold text-indigo-700 dark:text-indigo-400 mb-1">AI Narrative</div>
                                                    <div className="text-muted-foreground">現在の市場環境からAIが推論した動的レベル</div>
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">活用方法</h4>
                                            <ul className="space-y-1 text-muted-foreground leading-relaxed text-[10px]">
                                                <li><strong className="text-foreground">✓ トレンド把握:</strong> 現在の市場の方向性とその理由を理解</li>
                                                <li><strong className="text-foreground">✓ 重要レベル:</strong> AIが推定したサポート/レジスタンスを参考</li>
                                                <li><strong className="text-foreground">✓ シナリオ検討:</strong> 複数のシナリオで戦略を立案</li>
                                                <li><strong className="text-foreground">✓ 相関分析:</strong> 他資産との関係性から市場心理を読む</li>
                                            </ul>
                                        </div>

                                        <div className="pt-2 border-t border-border">
                                            <p className="text-[10px] text-muted-foreground italic">
                                                💡 "Analyze"ボタンで最新データに基づいた解説を生成。Gemini/Claude切替可能
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </h2>
                        <span className="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 border border-indigo-300 dark:border-indigo-700 rounded-md text-[10px] font-semibold text-indigo-700 dark:text-indigo-400 uppercase tracking-wide flex items-center gap-1">
                            <Sparkles className="w-3 h-3" /> AI-Powered
                        </span>
                    </div>
                    <p className="text-xs text-muted-foreground ml-7">
                        現在の価格と相関性から推定された重要レベルとシナリオ
                    </p>
                </div>
                <div className="flex items-center gap-4 shrink-0">
                    {/* Pivot Levels表示 - 枠で囲む */}
                    <div className="flex items-center gap-3 px-3 py-2 bg-card rounded-lg border shadow-sm">
                        {/* ALGORITHMICラベルと説明 */}
                        <div className="flex flex-col gap-0.5">
                            <span className="px-2 py-0.5 bg-orange-100 dark:bg-orange-900/30 border border-orange-300 dark:border-orange-700 rounded-md text-[10px] font-semibold text-orange-700 dark:text-orange-400 uppercase tracking-wide">
                                Algorithmic
                            </span>
                            <span className="text-[9px] text-muted-foreground text-center leading-tight">
                                前日D1足からの計算値
                            </span>
                        </div>

                        {/* 区切り線 */}
                        <div className="border-l border-border/50 h-8" />

                        {/* シナリオ表示 */}
                        <div className="flex items-center gap-3">
                            {scenarios.length === 0 ? (
                                <span className="text-xs text-muted-foreground">Loading...</span>
                            ) : (
                                scenarios.map((scenario, idx) => (
                                    <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-secondary/30 rounded border border-border/50">
                                        {scenario.direction === 'bullish' && <TrendingUp className="w-4 h-4 text-green-500 shrink-0" />}
                                        {scenario.direction === 'bearish' && <TrendingDown className="w-4 h-4 text-red-500 shrink-0" />}
                                        {scenario.direction === 'neutral' && <Minus className="w-4 h-4 text-yellow-500 shrink-0" />}
                                        <div className="flex flex-col">
                                            <span className={cn(
                                                "text-xs font-bold uppercase leading-tight",
                                                scenario.direction === 'bullish' ? "text-green-500" :
                                                    scenario.direction === 'bearish' ? "text-red-500" : "text-yellow-500"
                                            )}>
                                                {scenario.direction === 'bullish' ? '強気' :
                                                    scenario.direction === 'bearish' ? '弱気' : '中立'}
                                            </span>
                                            {scenario.active_levels.length > 0 && (
                                                <div className="flex gap-1 mt-0.5">
                                                    {scenario.active_levels.map((level, lIdx) => (
                                                        <span key={lIdx} className="text-xs font-mono text-orange-700 dark:text-orange-400 font-semibold">
                                                            {level.price.toFixed(2)}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* 区切り線 */}
                    <div className="border-l border-border/50 h-6" />

                    {/* 既存のボタン群 */}
                    <div className="flex items-center gap-1 bg-muted/50 border border-border/60 rounded-md p-1">
                        <button
                            onClick={() => handleSwitch('gemini')}
                            disabled={switching}
                            className={cn(
                                "px-2 py-0.5 text-[10px] font-semibold rounded",
                                provider === 'gemini' ? "bg-indigo-600 text-white" : "text-muted-foreground hover:text-foreground"
                            )}
                        >
                            Gemini
                        </button>
                        <button
                            onClick={() => handleSwitch('claude')}
                            disabled={switching}
                            className={cn(
                                "px-2 py-0.5 text-[10px] font-semibold rounded",
                                provider === 'claude' ? "bg-indigo-600 text-white" : "text-muted-foreground hover:text-foreground"
                            )}
                        >
                            Claude
                        </button>
                    </div>
                    {narrative && (
                        <span className="text-xs text-muted-foreground">
                            {new Date(narrative.timestamp).toLocaleString()}
                        </span>
                    )}
                    <button
                        onClick={handleGenerate}
                        disabled={generating}
                        className={cn(
                            "flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md transition-all",
                            generating
                                ? "bg-muted text-muted-foreground cursor-not-allowed"
                                : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm"
                        )}
                    >
                        {generating ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                            <Sparkles className="w-3.5 h-3.5" />
                        )}
                        {generating ? 'Generating...' : 'Analyze'}
                    </button>
                </div>
            </div>

            <div className="flex-1 flex gap-4 overflow-hidden">
                {/* Sidebar: History List */}
                <div className="w-[180px] flex flex-col gap-2 border-r pr-4">
                    {/* Session Filter Buttons */}
                    <div className="flex gap-1 mb-2 flex-wrap">
                        <button
                            onClick={() => setSelectedSession(null)}
                            className={cn(
                                "px-2 py-1 text-[10px] font-semibold rounded transition-colors",
                                !selectedSession ? "bg-indigo-600 text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
                            )}
                        >
                            All
                        </button>
                        <button
                            onClick={() => setSelectedSession('tokyo')}
                            className={cn(
                                "px-2 py-1 text-[10px] font-semibold rounded transition-colors",
                                selectedSession === 'tokyo' ? "bg-indigo-600 text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
                            )}
                        >
                            Tokyo
                        </button>
                        <button
                            onClick={() => setSelectedSession('london')}
                            className={cn(
                                "px-2 py-1 text-[10px] font-semibold rounded transition-colors",
                                selectedSession === 'london' ? "bg-indigo-600 text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
                            )}
                        >
                            London
                        </button>
                        <button
                            onClick={() => setSelectedSession('newyork')}
                            className={cn(
                                "px-2 py-1 text-[10px] font-semibold rounded transition-colors",
                                selectedSession === 'newyork' ? "bg-indigo-600 text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
                            )}
                        >
                            NY
                        </button>
                    </div>

                    {/* History List */}
                    <div className="flex-1 overflow-y-auto space-y-2">
                        {history.length === 0 ? (
                            <div className="text-center text-muted-foreground text-xs py-4">
                                {selectedSession ? `No narratives for ${selectedSession} session` : 'No narrative history yet'}
                            </div>
                        ) : (
                            history.map(item => (
                                <button
                                    key={item.id}
                                    onClick={() => setSelectedNarrativeId(item.id)}
                                    className={cn(
                                        "w-full text-left p-2 rounded-lg border transition-colors",
                                        selectedNarrativeId === item.id
                                            ? "bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500"
                                            : "bg-muted/30 hover:bg-muted/50 border-border"
                                    )}
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <span className={cn(
                                            "text-[10px] px-1.5 py-0.5 rounded font-medium uppercase shrink-0",
                                            item.session === 'tokyo' ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" :
                                            item.session === 'london' ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                                            "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                        )}>
                                            {item.session === 'newyork' ? 'NY' : item.session}
                                        </span>
                                        <span className="text-[10px] text-muted-foreground">
                                            {new Date(item.timestamp).toLocaleString('ja-JP', {
                                                month: 'numeric',
                                                day: 'numeric',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </span>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Main Content: Selected Narrative */}
                <div className="flex-1 overflow-y-auto p-4 bg-muted/30 rounded-lg border border-border/50">
                    {loading ? (
                        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                            Loading narrative...
                        </div>
                    ) : displayedNarrative ? (
                        <div
                            className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed"
                            dangerouslySetInnerHTML={{ __html: displayedNarrative.content }}
                        />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-sm gap-2">
                            <Bot className="w-8 h-8 opacity-20" />
                            <span>No narrative generated yet.</span>
                            <span className="text-xs opacity-70">Click 'Analyze' to generate insights with AI.</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NarrativePanel;
