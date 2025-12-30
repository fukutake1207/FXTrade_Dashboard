import { useEffect, useState } from 'react';
import { getSessionStatus, SessionResponse } from '../lib/api';
import { Clock } from 'lucide-react';
import { cn } from '../lib/utils';

const SessionPanel = () => {
    const [data, setData] = useState<SessionResponse | null>(null);

    const toMinutes = (timeStr: string) => {
        const [h, m] = timeStr.split(':').map(Number);
        return (h * 60) + (m || 0);
    };

    const buildSessionBlocks = () => {
        if (!data) return [];
        return Object.values(data.sessions).flatMap(session => {
            const start = toMinutes(session.start_time_str);
            const end = toMinutes(session.end_time_str);
            const color =
                session.id === 'tokyo' ? "bg-blue-500/30" :
                session.id === 'london' ? "bg-yellow-500/30" :
                "bg-green-500/30";

            if (start < end) {
                return [{
                    id: session.id,
                    title: `${session.name} (${session.start_time_str}-${session.end_time_str})`,
                    leftPct: (start / 1440) * 100,
                    widthPct: ((end - start) / 1440) * 100,
                    color
                }];
            }

            return [
                {
                    id: `${session.id}-late`,
                    title: `${session.name} (${session.start_time_str}-24:00)`,
                    leftPct: (start / 1440) * 100,
                    widthPct: ((1440 - start) / 1440) * 100,
                    color
                },
                {
                    id: `${session.id}-early`,
                    title: `${session.name} (00:00-${session.end_time_str})`,
                    leftPct: 0,
                    widthPct: (end / 1440) * 100,
                    color
                }
            ];
        });
    };

    const sessionBlocks = buildSessionBlocks();

    const fetchData = async () => {
        try {
            const result = await getSessionStatus();
            setData(result);
        } catch (error) {
            console.error("Failed to fetch session status", error);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000); // 1 minute
        return () => clearInterval(interval);
    }, []);

    if (!data) return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full max-w-md h-48 flex items-center justify-center">
            <span className="text-muted-foreground">Loading sessions...</span>
        </div>
    );

    return (
        <div className="p-6 bg-card rounded-xl border shadow-sm w-full max-w-md">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Clock className="w-5 h-5" /> Market Sessions
                </h2>
                <div className="flex items-center gap-2">
                    <span className="text-xl font-mono font-medium">{data.current_time}</span>
                    <span className="text-xs text-muted-foreground">JST</span>
                </div>
            </div>

            {/* Active/Upcoming Sessions List */}
            <div className="space-y-4 mb-6">
                {Object.values(data.sessions).map(session => (
                    <div key={session.id} className={cn(
                        "flex items-center justify-between p-3 rounded-lg border",
                        session.is_active ? "bg-accent/50 border-accent" : "bg-card border-border"
                    )}>
                        <div className="flex items-center gap-3">
                            <span className={cn(
                                "w-2.5 h-2.5 rounded-full shrink-0",
                                session.id === 'tokyo' ? "bg-blue-500" :
                                    session.id === 'london' ? "bg-yellow-500" :
                                        "bg-green-500",
                                !session.is_active && "opacity-30"
                            )} />
                            <div className="flex flex-col">
                                <span className={cn("text-sm font-medium", !session.is_active && "text-muted-foreground")}>
                                    {session.name}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                    {session.start_time_str} - {session.end_time_str}
                                </span>
                            </div>
                        </div>

                        <div className="text-right">
                            {session.is_active ? (
                                <>
                                    <span className="text-xs font-bold text-primary block">ACTIVE</span>
                                    <span className="text-xs text-muted-foreground">closes in {session.remaining_duration}</span>
                                </>
                            ) : (
                                <>
                                    <span className="text-xs text-muted-foreground block">{session.status.toUpperCase()}</span>
                                    {session.status === 'upcoming' && (
                                        <span className="text-xs text-muted-foreground">starts in {session.remaining_duration}</span>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Timeline Visualization (JST 24h) */}
            <div className="relative h-2 bg-secondary rounded-full overflow-hidden mb-2">
                {/* Current Time Indicator */}
                <div
                    className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
                    style={{ left: `${data.timeline_progress}%` }}
                />

                {sessionBlocks.map(block => (
                    <div
                        key={block.id}
                        className={`absolute top-0 bottom-0 ${block.color}`}
                        style={{ left: `${block.leftPct}%`, width: `${block.widthPct}%` }}
                        title={block.title}
                    />
                ))}
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                <span>00:00</span>
                <span>06:00</span>
                <span>12:00</span>
                <span>18:00</span>
                <span>24:00</span>
            </div>
        </div>
    );
};

export default SessionPanel;
