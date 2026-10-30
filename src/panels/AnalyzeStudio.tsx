import { useEffect, useState } from 'react';
import { BarChart3, Network, Radar, Building2 } from 'lucide-react';
import { fetchClarifyAnalyze, type ClarifyAnalysis } from '../data/remote';
import RepoGraphCanvas from './RepoGraphCanvas';
import Track01Studio from './Track01Studio';
import Track03Brain from './Track03Brain';

/**
 * Analyze — the repo overview: cognitive-debt summary, AST repo map, dependency
 * hotspots (Track 01) and ownership/docs (Track 03), all over the loaded repo.
 */
export default function AnalyzeStudio({ repo }: { repo: string }) {
  const [analysis, setAnalysis] = useState<ClarifyAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!repo) {
      setAnalysis(null);
      return;
    }
    let alive = true;
    setError(null);
    fetchClarifyAnalyze(repo, 5)
      .then((data) => {
        if (alive) setAnalysis(data);
      })
      .catch((err) => {
        if (alive) setError((err as Error).message || String(err));
      });
    return () => {
      alive = false;
    };
  }, [repo]);

  if (!repo) {
    return (
      <div className="text-sm text-slate-400 border border-slate-800 rounded-2xl p-6">
        Load a repository first: paste a public GitHub URL above and press “Load repo”.
      </div>
    );
  }

  const worst = analysis?.files?.[0];

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-cyan-400" />
          Repository overview
        </h2>
        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <div className="text-slate-500">Repo</div>
            <div className="text-white font-mono truncate">{repo}</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <div className="text-slate-500">Debt index</div>
            <div className="text-white font-semibold">
              {analysis ? `${analysis.debt_index}/100` : '—'}
            </div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <div className="text-slate-500">Python files ranked</div>
            <div className="text-white font-semibold">{analysis?.total_ranked ?? '—'}</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <div className="text-slate-500">Worst file</div>
            <div className="text-white font-mono truncate" title={worst?.path}>
              {worst ? `${worst.path} (${worst.score})` : '—'}
            </div>
          </div>
        </div>
        {error && (
          <div className="mt-3 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
      </section>

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
          <Network className="w-3.5 h-3.5 text-cyan-400" /> Repo map (AST)
        </h3>
        <RepoGraphCanvas repo={repo} />
      </section>

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
          <Radar className="w-3.5 h-3.5 text-indigo-400" /> Dependency hotspots &amp; blast radius
        </h3>
        <Track01Studio repo={repo} />
      </section>

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
          <Building2 className="w-3.5 h-3.5 text-emerald-400" /> Ownership &amp; docs
        </h3>
        <Track03Brain repo={repo} />
      </section>
    </div>
  );
}
