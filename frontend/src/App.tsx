import { useState, useEffect } from 'react'
import { X, Info, RefreshCcw, TrendingUp, TrendingDown } from 'lucide-react'
import { getPriceStats, PriceStat, triggerDataCollection, getCorrelationOverview, CorrelationOverview, getSessionStatus, SessionResponse } from './lib/api'
import { cn } from './lib/utils'
import NarrativePanel from './components/NarrativePanel'
import AlertPanel from './components/AlertPanel'
import TradePanel from './components/TradePanel'

function App() {
    const [showBanner, setShowBanner] = useState(
        !localStorage.getItem('dual-perspective-explained')
    );
    const [priceStats, setPriceStats] = useState<PriceStat[]>([]);
    const [priceLoading, setPriceLoading] = useState(false);
    const [correlations, setCorrelations] = useState<CorrelationOverview | null>(null);
    const [sessions, setSessions] = useState<SessionResponse | null>(null);

    const dismissBanner = () => {
        localStorage.setItem('dual-perspective-explained', 'true');
        setShowBanner(false);
    };

    const fetchPriceStats = async () => {
        setPriceLoading(true);
        try {
            const data = await getPriceStats();
            setPriceStats(data);
        } catch (error) {
            console.error("Failed to fetch price stats", error);
        } finally {
            setPriceLoading(false);
        }
    };

    const handlePriceRefresh = async () => {
        setPriceLoading(true);
        try {
            await triggerDataCollection();
            await fetchPriceStats();
        } catch (error) {
            console.error("Failed to refresh prices", error);
        } finally {
            setPriceLoading(false);
        }
    };

    const fetchCorrelations = async () => {
        try {
            const data = await getCorrelationOverview();
            setCorrelations(data);
        } catch (error) {
            console.error("Failed to fetch correlations", error);
        }
    };

    const fetchSessions = async () => {
        try {
            const data = await getSessionStatus();
            setSessions(data);
        } catch (error) {
            console.error("Failed to fetch sessions", error);
        }
    };

    useEffect(() => {
        fetchPriceStats();
        fetchCorrelations();
        fetchSessions();

        const priceInterval = setInterval(fetchPriceStats, 60000); // 60 seconds
        const corrInterval = setInterval(fetchCorrelations, 600000); // 10 minutes
        const sessionInterval = setInterval(fetchSessions, 60000); // 60 seconds

        return () => {
            clearInterval(priceInterval);
            clearInterval(corrInterval);
            clearInterval(sessionInterval);
        };
    }, []);

    const latestPrice = priceStats[0] || {};
    const isUp = latestPrice.close_price >= latestPrice.open_price;

    return (
        <div className="min-h-screen bg-background p-8">
            <header className="mb-6 flex items-start gap-4">
                {/* Title */}
                <div className="flex-shrink-0">
                    <h1 className="text-2xl font-bold tracking-tight text-foreground leading-tight">
                        FX Discretionary<br />Trading Cockpit
                    </h1>
                    <p className="text-xs text-muted-foreground mt-1">USDJPY Analysis</p>
                </div>

                {/* Enhanced USDJPY Price Display */}
                <div className="flex flex-col gap-3 px-4 py-3 pb-8 bg-card rounded-lg border shadow-sm">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">USDJPY</span>
                            <div className="group relative">
                                <Info className="w-3 h-3 text-muted-foreground hover:text-primary transition-colors cursor-help" />
                                {/* USDJPY Price Info Tooltip */}
                                <div className="invisible group-hover:visible absolute left-0 top-6 z-50 w-[400px] p-4 bg-popover border border-border rounded-lg shadow-lg">
                                    <div className="space-y-3 text-xs">
                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">OHLC価格データ</h4>
                                            <p className="text-muted-foreground leading-relaxed">
                                                現在の1時間足（H1）の価格情報を表示
                                            </p>
                                        </div>

                                        <div className="grid grid-cols-2 gap-2">
                                            <div>
                                                <div className="font-medium text-foreground text-[10px]">Open（始値）</div>
                                                <div className="text-[10px] text-muted-foreground">その時間足の最初の価格</div>
                                            </div>
                                            <div>
                                                <div className="font-medium text-foreground text-[10px]">High（高値）</div>
                                                <div className="text-[10px] text-muted-foreground">その時間足の最高価格</div>
                                            </div>
                                            <div>
                                                <div className="font-medium text-foreground text-[10px]">Low（安値）</div>
                                                <div className="text-[10px] text-muted-foreground">その時間足の最安価格</div>
                                            </div>
                                            <div>
                                                <div className="font-medium text-foreground text-[10px]">Last（現在値）</div>
                                                <div className="text-[10px] text-muted-foreground">最新の取引価格</div>
                                            </div>
                                        </div>

                                        <div>
                                            <div className="font-medium text-foreground mb-1">Range（値幅）- pipsとは</div>
                                            <p className="text-[10px] text-muted-foreground leading-relaxed">
                                                pips = 価格の最小変動単位。USDJPYでは0.01円=1pips。
                                                <br />例: 156.50→156.75 = 25pipsの上昇
                                            </p>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold text-foreground mb-1">価格アクションの読み方</h4>
                                            <ul className="space-y-1 text-muted-foreground leading-relaxed text-[10px]">
                                                <li><strong className="text-green-600 dark:text-green-400">↑ 緑色:</strong> Last ≥ Open（上昇トレンド/強気）</li>
                                                <li><strong className="text-red-600 dark:text-red-400">↓ 赤色:</strong> Last &lt; Open（下降トレンド/弱気）</li>
                                                <li><strong className="text-foreground">Range大:</strong> ボラティリティ高い（トレンド発生中）</li>
                                                <li><strong className="text-foreground">Range小:</strong> レンジ相場（ブレイクアウト待ち）</li>
                                            </ul>
                                        </div>

                                        <div className="pt-2 border-t border-border">
                                            <p className="text-[10px] text-muted-foreground italic">
                                                🔄 60秒ごとに自動更新。手動更新は右上のボタンから
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={handlePriceRefresh}
                            className="p-1 hover:bg-muted rounded transition-colors"
                            disabled={priceLoading}
                        >
                            <RefreshCcw className={cn("w-3.5 h-3.5 text-muted-foreground", priceLoading && "animate-spin")} />
                        </button>
                    </div>

                    <div className="flex items-center gap-6">
                        {/* Current Price */}
                        <div className="flex flex-col">
                            <div className="flex items-baseline gap-2">
                                <span className={cn("text-2xl font-bold tracking-tight tabular-nums", isUp ? "text-green-500" : "text-red-500")}>
                                    {latestPrice.close_price?.toFixed(2) || '---'}
                                </span>
                                {isUp ? <TrendingUp className="w-5 h-5 text-green-500" /> : <TrendingDown className="w-5 h-5 text-red-500" />}
                            </div>
                            <span className="text-[10px] text-red-500">
                                {latestPrice.last_updated
                                    ? new Date(latestPrice.last_updated + (latestPrice.last_updated.includes('Z') ? '' : 'Z')).toLocaleString('ja-JP')
                                    : 'No Data'}
                            </span>
                        </div>

                        {/* OHLR Details */}
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                            <div className="flex flex-col">
                                <span className="text-muted-foreground text-[10px]">Open</span>
                                <span className="font-mono font-medium tabular-nums">{latestPrice.open_price?.toFixed(2) || '--'}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-muted-foreground text-[10px]">High</span>
                                <span className="font-mono font-medium tabular-nums">{latestPrice.high_price?.toFixed(2) || '--'}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-muted-foreground text-[10px]">Low</span>
                                <span className="font-mono font-medium tabular-nums">{latestPrice.low_price?.toFixed(2) || '--'}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-muted-foreground text-[10px]">Range</span>
                                <span className="font-mono font-medium tabular-nums">{latestPrice.range_pips?.toFixed(0) || '--'} pips</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Market Sessions - Timeline View */}
                <div className="flex flex-col gap-2 px-4 py-2 bg-card rounded-lg border shadow-sm min-w-[420px]">
                    <div className="flex items-center gap-2">
                        <div className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Market Sessions</div>
                        <div className="group relative">
                            <Info className="w-3 h-3 text-muted-foreground hover:text-primary transition-colors cursor-help" />
                            {/* Market Sessions Info Tooltip */}
                            <div className="invisible group-hover:visible absolute left-0 top-6 z-50 w-[420px] p-4 bg-popover border border-border rounded-lg shadow-lg">
                                <div className="space-y-3 text-xs">
                                    <div>
                                        <h4 className="font-semibold text-foreground mb-1">主要市場セッション</h4>
                                        <p className="text-muted-foreground leading-relaxed">
                                            3つの主要FX市場の取引時間と特徴を表示
                                        </p>
                                    </div>

                                    <div className="space-y-2">
                                        <div className="flex items-start gap-2">
                                            <div className="w-2 h-2 rounded-full bg-blue-500 mt-1 shrink-0"></div>
                                            <div>
                                                <div className="font-medium text-foreground">東京市場 (9:00-18:00)</div>
                                                <div className="text-[10px] text-muted-foreground">アジア圏の取引。円関連の動きが活発。比較的ボラティリティは低め。</div>
                                            </div>
                                        </div>
                                        <div className="flex items-start gap-2">
                                            <div className="w-2 h-2 rounded-full bg-yellow-500 mt-1 shrink-0"></div>
                                            <div>
                                                <div className="font-medium text-foreground">ロンドン市場 (17:00-翌2:00)</div>
                                                <div className="text-[10px] text-muted-foreground">最大の取引量。欧州経済指標発表。ボラティリティ高い。</div>
                                            </div>
                                        </div>
                                        <div className="flex items-start gap-2">
                                            <div className="w-2 h-2 rounded-full bg-green-500 mt-1 shrink-0"></div>
                                            <div>
                                                <div className="font-medium text-foreground">NY市場 (22:00-翌7:00)</div>
                                                <div className="text-[10px] text-muted-foreground">米国経済指標発表。ロンドンと重複時間帯が最も活発。</div>
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-foreground mb-1">トレード戦略</h4>
                                        <ul className="space-y-1 text-muted-foreground leading-relaxed text-[10px]">
                                            <li><strong className="text-foreground">✓ 重複時間:</strong> ロンドン-NY重複（22:00-2:00）が最も流動性高く、スプレッド縮小</li>
                                            <li><strong className="text-foreground">✓ ブレイクアウト:</strong> 東京→ロンドン移行時にレンジブレイク多発</li>
                                            <li><strong className="text-foreground">✓ 経済指標:</strong> 各市場の主要指標発表時は急変動に注意</li>
                                        </ul>
                                    </div>

                                    <div className="pt-2 border-t border-border">
                                        <p className="text-[10px] text-muted-foreground italic">
                                            💡 タイムライン上の赤い線が現在時刻を示します
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">JST</span>
                            <span className="text-lg font-mono font-bold tabular-nums">{sessions?.current_time || '--:--'}</span>
                        </div>
                        <div className="flex gap-4">
                            {sessions && Object.values(sessions.sessions).map(session => (
                                <div key={session.id} className="flex flex-col gap-0.5 min-w-[70px]">
                                    <div className="flex items-center gap-1.5">
                                        <span className={cn(
                                            "w-2.5 h-2.5 rounded-full shrink-0",
                                            session.id === 'tokyo' ? "bg-blue-500" :
                                                session.id === 'london' ? "bg-yellow-500" :
                                                    "bg-green-500",
                                            !session.is_active && session.status !== 'closed' && "opacity-30",
                                            session.status === 'closed' && "opacity-50 grayscale"
                                        )} />
                                        <span className={cn("text-xs font-semibold", session.is_active ? "text-foreground" : "text-muted-foreground")}>
                                            {session.name}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-1 ml-3.5">
                                        <span className="text-[9px] font-mono text-muted-foreground">
                                            {session.start_time_str}-{session.end_time_str}
                                        </span>
                                    </div>
                                    {session.is_active ? (
                                        <div className="ml-3.5">
                                            <span className={cn(
                                                "text-[9px] font-semibold px-1.5 py-0.5 rounded",
                                                session.id === 'tokyo' ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400" :
                                                    session.id === 'london' ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400" :
                                                        "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                                            )}>
                                                ACTIVE
                                            </span>
                                        </div>
                                    ) : session.status === 'closed' && (
                                        <div className="ml-3.5">
                                            <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                                                CLOSE
                                            </span>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Timeline Visualization */}
                    <div className="relative h-3 bg-secondary/50 rounded-full overflow-hidden">
                        {/* Current Time Indicator */}
                        <div
                            className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
                            style={{ left: `${sessions?.timeline_progress || 0}%` }}
                        />

                        {/* Session Blocks */}
                        {sessions && (() => {
                            const toMinutes = (timeStr: string) => {
                                const [h, m] = timeStr.split(':').map(Number);
                                return (h * 60) + (m || 0);
                            };

                            return Object.values(sessions.sessions).flatMap(session => {
                                const start = toMinutes(session.start_time_str);
                                const end = toMinutes(session.end_time_str);
                                const color =
                                    session.id === 'tokyo' ? "bg-blue-500/40" :
                                        session.id === 'london' ? "bg-yellow-500/40" :
                                            "bg-green-500/40";

                                if (start < end) {
                                    return (
                                        <div
                                            key={session.id}
                                            className={`absolute top-0 bottom-0 ${color}`}
                                            style={{
                                                left: `${(start / 1440) * 100}%`,
                                                width: `${((end - start) / 1440) * 100}%`
                                            }}
                                            title={`${session.name} (${session.start_time_str}-${session.end_time_str})`}
                                        />
                                    );
                                }

                                // Handle sessions that cross midnight
                                return [
                                    <div
                                        key={`${session.id}-late`}
                                        className={`absolute top-0 bottom-0 ${color}`}
                                        style={{
                                            left: `${(start / 1440) * 100}%`,
                                            width: `${((1440 - start) / 1440) * 100}%`
                                        }}
                                        title={`${session.name} (${session.start_time_str}-24:00)`}
                                    />,
                                    <div
                                        key={`${session.id}-early`}
                                        className={`absolute top-0 bottom-0 ${color}`}
                                        style={{
                                            left: '0%',
                                            width: `${(end / 1440) * 100}%`
                                        }}
                                        title={`${session.name} (00:00-${session.end_time_str})`}
                                    />
                                ];
                            });
                        })()}
                    </div>

                    {/* Time Labels */}
                    <div className="flex justify-between text-[9px] text-muted-foreground font-mono -mt-1">
                        <span>00:00</span>
                        <span>06:00</span>
                        <span>12:00</span>
                        <span>18:00</span>
                        <span>24:00</span>
                    </div>
                </div>

                {/* Enhanced Correlation Monitor */}
                <div className="flex flex-col gap-3 px-4 py-3 pb-8 bg-card rounded-lg border shadow-sm">
                    <div className="flex items-center gap-2">
                        <div className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Correlations</div>
                        <div className="group relative">
                            <Info className="w-3 h-3 text-muted-foreground hover:text-primary transition-colors cursor-help" />
                            {/* Correlation Info Tooltip */}
                            <div className="invisible group-hover:visible absolute left-0 top-6 z-50 w-[420px] p-4 bg-popover border border-border rounded-lg shadow-lg">
                                <div className="space-y-3 text-xs">
                                    <div>
                                        <h4 className="font-semibold text-foreground mb-1">相関係数（Correlation）とは</h4>
                                        <p className="text-muted-foreground leading-relaxed">
                                            USDJPYと各資産の価格変動の連動性を示す指標（-1.0〜+1.0）
                                        </p>
                                    </div>

                                    <div className="grid grid-cols-2 gap-2 text-[10px]">
                                        <div className="space-y-0.5">
                                            <div className="text-green-600 dark:text-green-400 font-medium">+0.7〜+1.0 強い正相関</div>
                                            <div className="text-green-600/70 dark:text-green-400/70">+0.4〜+0.7 中程度</div>
                                            <div className="text-muted-foreground">+0.2〜+0.4 弱い</div>
                                        </div>
                                        <div className="space-y-0.5">
                                            <div className="text-red-600 dark:text-red-400 font-medium">-0.7〜-1.0 強い逆相関</div>
                                            <div className="text-red-600/70 dark:text-red-400/70">-0.4〜-0.7 中程度</div>
                                            <div className="text-muted-foreground">-0.2〜-0.4 弱い</div>
                                        </div>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-foreground mb-1">トレードでの活用法</h4>
                                        <ul className="space-y-1 text-muted-foreground leading-relaxed">
                                            <li><strong className="text-foreground">✓ シグナル確認:</strong> Nikkei↑+相関+0.6 → USDJPY上昇の信頼性UP</li>
                                            <li><strong className="text-foreground">✓ ダイバージェンス:</strong> 通常連動するのに逆行 → 反転の兆候</li>
                                            <li><strong className="text-foreground">✓ リスク判断:</strong> 複数資産の動きからリスクオン/オフを判定</li>
                                            <li><strong className="text-foreground">✓ 先行指標:</strong> S&P500が先に動く場合、USDJPYの動きを予測</li>
                                        </ul>
                                    </div>

                                    <div className="pt-2 border-t border-border">
                                        <p className="text-[10px] text-muted-foreground italic">
                                            ⚠️ 相関は市場環境で変動します。低相関時は他指標を重視してください。
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        {['Gold', 'Nikkei', 'S&P500'].map(asset => {
                            const priceInfo = correlations?.market_status[asset];
                            const corrInfo = correlations?.correlations[asset];
                            const isUp = (priceInfo?.change_pct || 0) >= 0;

                            return (
                                <div key={asset} className="flex flex-col min-w-[85px]">
                                    <span className="text-[10px] text-muted-foreground font-medium mb-1.5">{asset}</span>
                                    <div className="flex items-baseline gap-1.5">
                                        <span className={cn("text-xl font-bold tabular-nums", isUp ? "text-green-500" : "text-red-500")}>
                                            {priceInfo ? (asset === 'Gold' ? priceInfo.price.toFixed(0) : priceInfo.price.toFixed(0)) : '--'}
                                        </span>
                                        <span className={cn("text-xs tabular-nums", isUp ? "text-green-600" : "text-red-600")}>
                                            {priceInfo ? `${isUp ? '+' : ''}${priceInfo.change_pct.toFixed(2)}%` : '--'}
                                        </span>
                                    </div>
                                    {corrInfo && (
                                        <div className="flex items-center gap-1 mt-1.5">
                                            <span className="text-[9px] text-muted-foreground">Corr:</span>
                                            <span className={cn(
                                                "text-[10px] font-medium tabular-nums",
                                                Math.abs(corrInfo.coefficient) > 0.5 ? "text-primary" : "text-muted-foreground"
                                            )}>
                                                {corrInfo.coefficient > 0 ? '+' : ''}{corrInfo.coefficient.toFixed(2)}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            </header>

            {/* Dual Perspective Explanation Banner */}
            {showBanner && (
                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg flex items-start gap-3">
                    <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 shrink-0" />
                    <div className="flex-1">
                        <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
                            2つの分析視点
                        </h3>
                        <p className="text-xs text-blue-800 dark:text-blue-200 leading-relaxed">
                            このダッシュボードは2つの独立した分析視点を提供します：<br />
                            <strong className="text-orange-600 dark:text-orange-400">Pivot Levels</strong> - 前日D1足から計算された固定的なピボットポイント<br />
                            <strong className="text-indigo-600 dark:text-indigo-400">AI Market Narrative</strong> - AIが現在の市場環境から推定した動的なレベル<br />
                            価格レベルが異なる場合がありますが、これは意図的な設計です。
                        </p>
                    </div>
                    <button
                        onClick={dismissBanner}
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 shrink-0"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Row 1: AI Market Narrative (Full width) */}
                <div className="col-span-1 md:col-span-2 lg:col-span-3">
                    <NarrativePanel />
                </div>

                {/* Row 2: Trade Panel, Price Alerts */}
                <div className="col-span-1">
                    <TradePanel />
                </div>
                <div className="col-span-1">
                    <AlertPanel />
                </div>
            </main>
        </div>
    )
}

export default App
