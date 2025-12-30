import PricePanel from './components/PricePanel'
import CorrelationPanel from './components/CorrelationPanel'
import SessionPanel from './components/SessionPanel'
import NarrativePanel from './components/NarrativePanel'
import ScenarioPanel from './components/ScenarioPanel'
import AlertPanel from './components/AlertPanel'
import TradePanel from './components/TradePanel'

function App() {
    return (
        <div className="min-h-screen bg-background p-8">
            <header className="mb-8">
                <h1 className="text-3xl font-bold tracking-tight text-foreground">
                    FX Discretionary Trading Cockpit
                </h1>
                <p className="text-muted-foreground mt-2">
                    USDJPY Market Analysis & Context
                </p>
            </header>

            <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Category 1: Price Data */}
                <div className="col-span-1">
                    <PricePanel />
                </div>

                {/* Placeholders for other categories */}
                <div className="col-span-1">
                    <CorrelationPanel />
                </div>

                {/* Category 3: Session Info */}
                <div className="col-span-1">
                    <SessionPanel />
                </div>
                <div className="col-span-1">
                    <NarrativePanel />
                </div>

                {/* Category 5: Scenarios */}
                <div className="col-span-1">
                    <ScenarioPanel />
                </div>

                {/* Category 6: Alerts */}
                <div className="col-span-1">
                    <AlertPanel />
                </div>

                {/* Category 7: Trade Logs */}
                <div className="col-span-1 md:col-span-2 lg:col-span-1">
                    <TradePanel />
                </div>
            </main>
        </div>
    )
}

export default App
