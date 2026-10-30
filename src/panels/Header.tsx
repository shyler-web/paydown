import { Network, Database, Terminal, BrainCircuit, Wand2, LayoutDashboard } from 'lucide-react';

const TABS = [
  { id: 'analyze', label: 'Analyze', icon: LayoutDashboard },
  { id: 'refactor', label: 'Refactor', icon: Wand2 },
  { id: 'memory', label: 'Memory', icon: BrainCircuit },
  { id: 'status', label: 'Status', icon: Terminal }
];

export default function Header(props: any) {
  const { tenants, activeTenantKey, setActiveTenantKey, activeTab, setActiveTab } = props;
  const keys = Object.keys(tenants || {});

  return (
    <header className="border-b border-slate-800/80 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30 px-4 py-3">
      <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Network className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">Paydown</h1>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Cognitive-debt cockpit
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Analyze any Python repo · propose a safe refactor · remember what the agents did
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <Database className="w-3.5 h-3.5 text-pink-400" />
            <select
              value={activeTenantKey}
              onChange={(e) => setActiveTenantKey(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs font-mono text-white focus:outline-none cursor-pointer max-w-[280px]"
            >
              {keys.length === 0 && <option value="">no workspaces yet</option>}
              {keys.map((key) => (
                <option key={key} value={key} className="bg-slate-900 text-white">
                  {(tenants[key]?.name as string) || key} ({key})
                </option>
              ))}
            </select>
          </div>

          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center gap-1.5 ${
                  activeTab === id
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}
