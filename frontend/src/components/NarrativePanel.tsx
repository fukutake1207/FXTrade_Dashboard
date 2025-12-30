import { useEffect, useState } from 'react';
import { getLatestNarrative, generateMarketNarrative, NarrativeResponse, getNarrativeProvider, setNarrativeProvider } from '../lib/api';
import { Bot, Sparkles, RefreshCw } from 'lucide-react';
import { cn } from '../lib/utils';

const NarrativePanel = () => {
    const [narrative, setNarrative] = useState<NarrativeResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [provider, setProvider] = useState<'gemini' | 'claude'>('gemini');
    const [switching, setSwitching] = useState(false);

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

    const handleGenerate = async () => {
        setGenerating(true);
        try {
            const data = await generateMarketNarrative();
            setNarrative(data);
        } catch (error) {
            console.error("Failed to generate narrative", error);
        } finally {
            setGenerating(false);
        }
    };

    useEffect(() => {
        fetchLatest();
        fetchProvider();
    }, []);

    return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Bot className="w-5 h-5 text-indigo-500" /> AI Market Narrative
                </h2>
                <div className="flex items-center gap-2">
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

            <div className="flex-1 overflow-y-auto min-h-[200px] p-4 bg-muted/30 rounded-lg border border-border/50">
                {loading ? (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                        Loading narrative...
                    </div>
                ) : narrative ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed whitespace-pre-line">
                        {narrative.content}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-sm gap-2">
                        <Bot className="w-8 h-8 opacity-20" />
                        <span>No narrative generated yet.</span>
                        <span className="text-xs opacity-70">Click 'Analyze' to generate insights with AI.</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default NarrativePanel;
