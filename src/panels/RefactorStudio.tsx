import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Sparkles,
  Wand2,
  XCircle
} from 'lucide-react';
import {
  explainClarifyFile,
  fetchClarifyAnalyze,
  proposeClarifyRefactor,
  type ClarifyAnalysis,
  type ClarifyExplanation,
  type ClarifyFile,
  type ClarifyProposal
} from '../data/remote';

const LEVELS = ['L0 Vibe', 'L1 PM', 'L2 Junior', 'L3 Full-Stack', 'L4 Senior', 'L5 Principal'];

/**
 * Refactor Studio — drives the real Clarify engine (`/api/clarify/*`).
 * Analyze ranks the repo's Python files by the A/B/E comprehension-risk proxy.
 * "Propose refactor" asks Nemotron (Nebius Token Factory) for a rewrite and
 * score-validates it. Behavior is verified only when a Docker runner is wired;
 * otherwise the proposal is explicitly labelled "not verified".
 */
export default function RefactorStudio(props: any) {
  const { repo = 'graphhacks' } = props;

  const [analysis, setAnalysis] = useState<ClarifyAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState<string>('');
  const [proposal, setProposal] = useState<ClarifyProposal | null>(null);
  const [proposing, setProposing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [level, setLevel] = useState(3);
  const [explanation, setExplanation] = useState<ClarifyExplanation | null>(null);
  const [explaining, setExplaining] = useState(false);

  const load = useCallback(async () => {
    if (!repo) {
      setAnalysis(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    setProposal(null);
    setExplanation(null);
    try {
      const data = await fetchClarifyAnalyze(repo, 50);
      setAnalysis(data);
      setSelectedPath((prev) =>
        prev && data.files.some((f) => f.path === prev) ? prev : data.files[0]?.path ?? ''
      );
    } catch (err) {
      setAnalysis(null);
      setError((err as Error).message || String(err));
    } finally {
      setLoading(false);
    }
  }, [repo]);

  useEffect(() => {
    void load();
  }, [load]);

  const selected: ClarifyFile | undefined =
    analysis?.files.find((f) => f.path === selectedPath) ?? analysis?.files[0];

  const propose = async () => {
    if (!selected) return;
    setProposing(true);
    setActionError(null);
    setProposal(null);
    try {
      setProposal(await proposeClarifyRefactor(repo, selected.path));
    } catch (err) {
      setActionError((err as Error).message || String(err));
    } finally {
      setProposing(false);
    }
  };

  const explain = async () => {
    if (!selected) return;
    setExplaining(true);
    setActionError(null);
    setExplanation(null);
    try {
      setExplanation(await explainClarifyFile(repo, selected.path, level));
    } catch (err) {
      setActionError((err as Error).message || String(err));
    } finally {
      setExplaining(false);
    }
  };

  if (!repo) {
    return (
      <div className="text-sm text-slate-400 border border-slate-800 rounded-2xl p-6">
        Load a repository first: paste a public GitHub URL above and press “Load repo”.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              Clarify · Cognitive-Debt Studio
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Rank a repo's Python files by an explainable A/B/E risk proxy, then propose a
              score-validated refactor with Nemotron on Nebius Token Factory.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono px-2 py-1 rounded-lg bg-slate-950 border border-slate-800 text-cyan-300">
              {repo}
            </span>
            <button
              onClick={() => void load()}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Analyze
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-3 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        {analysis && (
          <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-300">
            <span>
              Debt index: <strong className="text-white">{analysis.debt_index}</strong>/100
            </span>
            <span>
              Files ranked: <strong className="text-white">{analysis.total_ranked}</strong>
            </span>
            <span>
              Skipped: <strong className="text-white">{analysis.skipped}</strong>
            </span>
          </div>
        )}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* File ranking */}
        <section className="lg:col-span-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Worst files
          </h3>
          {loading && (
            <div className="text-xs text-slate-500 p-4 flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Ranking files…
            </div>
          )}
          <div className="space-y-1.5 max-h-[560px] overflow-auto">
            {analysis?.files.map((f) => {
              const active = f.path === selected?.path;
              return (
                <button
                  key={f.path}
                  onClick={() => {
                    setSelectedPath(f.path);
                    setProposal(null);
                    setExplanation(null);
                  }}
                  className={`w-full text-left rounded-lg border px-2.5 py-2 transition ${
                    active
                      ? 'border-cyan-500/60 bg-cyan-500/10'
                      : 'border-slate-800 bg-slate-950/60 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-[11px] text-white truncate">{f.path}</span>
                    <span className="text-[11px] font-semibold text-amber-300 shrink-0">
                      {f.score.toFixed(1)}
                    </span>
                  </div>
                  <div className="mt-1 flex gap-2 text-[10px] text-slate-400">
                    {(['A', 'B', 'E'] as const).map((k) => (
                      <span key={k}>
                        {k}{' '}
                        <span className="text-slate-200">
                          {(f.signals[k]?.contribution ?? 0).toFixed(1)}
                        </span>
                      </span>
                    ))}
                  </div>
                </button>
              );
            })}
            {!loading && analysis && analysis.files.length === 0 && (
              <div className="text-xs text-slate-500 p-4">No rankable Python files found.</div>
            )}
          </div>
        </section>

        {/* Detail + actions */}
        <section className="lg:col-span-7 space-y-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold text-white font-mono">
                {selected?.path ?? 'Select a file'}
              </h3>
              <div className="flex items-center gap-2">
                <select
                  value={level}
                  onChange={(e) => setLevel(Number(e.target.value))}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-white"
                >
                  {LEVELS.map((label, i) => (
                    <option key={label} value={i}>
                      {label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => void explain()}
                  disabled={!selected || explaining}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold"
                >
                  {explaining ? 'Explaining…' : 'Explain file'}
                </button>
                <button
                  onClick={() => void propose()}
                  disabled={!selected || proposing}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5"
                >
                  <Wand2 className="w-3.5 h-3.5" />
                  {proposing ? 'Proposing…' : 'Propose refactor'}
                </button>
              </div>
            </div>

            {selected && (
              <div className="mt-2 grid grid-cols-3 gap-2 text-[11px] text-slate-400">
                {(['A', 'B', 'E'] as const).map((k) => (
                  <div key={k} className="rounded-lg border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                    <div className="text-slate-500">{k} contribution</div>
                    <div className="text-white font-semibold">
                      {(selected.signals[k]?.contribution ?? 0).toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {actionError && (
              <div className="mt-3 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2">
                {actionError}
              </div>
            )}
          </div>

          {explanation && (
            <div className="rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-4">
              <div className="text-xs font-semibold text-indigo-300 mb-1">
                Explanation · {LEVELS[explanation.level]}
                {explanation.provider && (
                  <span className="ml-2 font-mono text-[10px] text-cyan-300">
                    {explanation.provider.name} · {explanation.provider.model} ·{' '}
                    {explanation.provider.elapsed_ms} ms
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-200 whitespace-pre-wrap">{explanation.answer}</p>
            </div>
          )}

          {proposal && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                    proposal.validation.accepted
                      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
                      : 'bg-rose-500/15 text-rose-300 border-rose-500/40'
                  }`}
                >
                  {proposal.status}
                </span>
                <span className="text-[11px] text-slate-400">
                  {proposal.before_score} → {proposal.after_score} ({proposal.validation.score_drop > 0 ? '−' : '+'}
                  {Math.abs(proposal.validation.score_drop)})
                </span>
                {!proposal.behavior_verified && (
                  <span className="text-[11px] text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-full px-2 py-0.5 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Behavior not verified
                  </span>
                )}
                {proposal.provider && (
                  <span className="text-[11px] text-cyan-300 bg-cyan-500/10 border border-cyan-500/30 rounded-full px-2 py-0.5 font-mono">
                    {proposal.provider.name} · {proposal.provider.model} ·{' '}
                    {proposal.provider.elapsed_ms} ms
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-1.5">
                {Object.entries(proposal.validation.checks).map(([name, ok]) => (
                  <div key={name} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                    {ok ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-rose-400" />
                    )}
                    {name.replace(/_/g, ' ')}
                  </div>
                ))}
              </div>

              <div className="text-xs text-slate-300">
                <strong className="text-white">Intent:</strong> {proposal.intent_note}
              </div>
              <div className="text-xs text-slate-300">
                <strong className="text-white">Reviewer question:</strong>{' '}
                {proposal.reviewer_question}
              </div>

              <div>
                <div className="text-[11px] font-semibold text-slate-400 mb-1">Proposed diff</div>
                <pre className="text-[11px] leading-relaxed text-slate-300 bg-slate-950 border border-slate-800 rounded-lg p-3 max-h-80 overflow-auto">
                  {proposal.diff || '(no changes)'}
                </pre>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
