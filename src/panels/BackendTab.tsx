import { Server } from 'lucide-react';

export default function BackendTab(_props: any) {
  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 max-w-3xl mx-auto space-y-5">
      <div>
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Server className="w-5 h-5 text-indigo-400" />
          Paydown — Status &amp; setup
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          One command runs the whole stack. AI features need a Nebius key; everything
          else works without one.
        </p>
      </div>

      <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4 space-y-2">
        <div className="text-xs font-semibold text-emerald-300">
          Run everything (one command)
        </div>
        <pre className="text-xs font-mono bg-slate-950 text-emerald-300 p-3 rounded-lg border border-slate-800 overflow-x-auto">
{`docker compose up --build`}
        </pre>
        <p className="text-xs text-slate-300">
          Open <span className="font-mono text-white">http://localhost:5173</span> →
          paste a public GitHub URL → press <strong>Load repo</strong>.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-xs font-semibold text-cyan-300 mb-1">Works without a key</div>
          <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
            <li>Analyze: debt score, repo map, dependencies, ownership</li>
            <li>Memory: the repo's 4-tier agent memory</li>
          </ul>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-xs font-semibold text-amber-300 mb-1">
            Needs <span className="font-mono">NEBIUS_API_KEY</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
            <li>Refactor → Propose refactor</li>
            <li>Refactor → Explain file</li>
            <li>Analyze → graph-grounded guidance</li>
          </ul>
        </div>
      </div>

      <details className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
        <summary className="text-xs font-semibold text-slate-300 cursor-pointer">
          Optional environment (backend only)
        </summary>
        <pre className="mt-2 text-[11px] font-mono bg-slate-950 text-slate-300 p-3 rounded-lg border border-slate-800 overflow-x-auto">
{`NEBIUS_API_KEY=...                 # AI calls (server-side only)
NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
TAVILY_API_KEY=...                 # optional: research
DEMO_ACCESS_CODE=...               # optional: gate AI + repo load
DEMO_MAX_CALLS_PER_DAY=100         # budget guard
CLARIFY_PUBLISH_ENABLED=false      # keep PR publishing off`}
        </pre>
      </details>

      <details className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
        <summary className="text-xs font-semibold text-slate-300 cursor-pointer">
          Health checks (optional)
        </summary>
        <pre className="mt-2 text-[11px] font-mono bg-slate-950 text-slate-300 p-3 rounded-lg border border-slate-800 overflow-x-auto">
{`GET /api/health          # FalkorDB node count (503 if down)
GET /api/llm/info        # provider + model + configured
GET /api/clarify/usage   # today's AI calls/tokens vs limits`}
        </pre>
      </details>
    </div>
  );
}
