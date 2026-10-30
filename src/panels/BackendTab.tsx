import { Server } from 'lucide-react';

export default function BackendTab(_props: any) {
  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 max-w-4xl mx-auto space-y-4">
      <h2 className="text-lg font-bold text-white flex items-center gap-2">
        <Server className="w-5 h-5 text-indigo-400" />
        Paydown — Status &amp; setup
      </h2>
      <p className="text-xs text-slate-300 leading-relaxed">
        Paydown is a React cockpit over a FastAPI backend, a FalkorDB graph, and
        Nebius Token Factory (NVIDIA Nemotron) for AI calls. Keys live only in the
        backend environment — the browser never receives one.
      </p>

      <div className="space-y-2">
        <div className="text-xs font-mono text-indigo-300">1. Run the full stack:</div>
        <pre className="text-xs font-mono bg-slate-950 text-emerald-300 p-3 rounded-xl border border-slate-800 overflow-x-auto">
{`docker compose up --build
# open http://localhost:5173`}
        </pre>
      </div>

      <div className="space-y-2">
        <div className="text-xs font-mono text-indigo-300">2. Load a repo:</div>
        <pre className="text-xs font-mono bg-slate-950 text-cyan-300 p-3 rounded-xl border border-slate-800 overflow-x-auto">
{`Paste a public URL, e.g. https://github.com/psf/requests
Then press "Load repo".

Analyze + Memory work without an LLM key.
Refactor "Propose" / "Explain" need NEBIUS_API_KEY.`}
        </pre>
      </div>

      <div className="space-y-2">
        <div className="text-xs font-mono text-indigo-300">3. Environment (backend only):</div>
        <pre className="text-xs font-mono bg-slate-950 text-slate-300 p-3 rounded-xl border border-slate-800 overflow-x-auto">
{`NEBIUS_API_KEY=...                 # AI calls (server-side only)
NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
TAVILY_API_KEY=...                 # optional: research
DEMO_ACCESS_CODE=...               # optional: gate AI + repo load
DEMO_MAX_CALLS_PER_DAY=100         # budget guard
CLARIFY_PUBLISH_ENABLED=false      # keep PR publishing off`}
        </pre>
      </div>

      <div className="space-y-2">
        <div className="text-xs font-mono text-indigo-300">4. Status checks:</div>
        <pre className="text-xs font-mono bg-slate-950 text-slate-300 p-3 rounded-xl border border-slate-800 overflow-x-auto">
{`GET /api/health          # FalkorDB node count (503 if down)
GET /api/llm/info        # provider + model + configured
GET /api/clarify/usage   # today's AI calls/tokens vs limits`}
        </pre>
      </div>

      <p className="text-[11px] text-slate-500 leading-relaxed">
        Native dev: start FalkorDB with Docker, run{' '}
        <code className="text-indigo-300">uv run uvicorn app.main:app --port 8000</code>{' '}
        in <code className="text-indigo-300">backend/</code>, and{' '}
        <code className="text-indigo-300">npm run dev</code> at the repo root.
      </p>
    </div>
  );
}
