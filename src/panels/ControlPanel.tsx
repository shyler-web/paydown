import { useState } from 'react';
import { Github, Play, RefreshCw } from 'lucide-react';

/** Repo bar: pick an already-loaded repo or paste a GitHub URL to load a new one. */
export default function ControlPanel(props: any) {
  const {
    repos = [],
    activeRepoId,
    setActiveRepoId,
    repoLoading,
    repoError,
    repoNote,
    onLoadRepo
  } = props;
  const [repoUrl, setRepoUrl] = useState('');

  return (
    <section className="bg-slate-900/50 border-b border-slate-800/80 px-4 py-3">
      <div className="max-w-[1600px] mx-auto flex flex-wrap items-center gap-2">
        <Github className="w-4 h-4 text-cyan-400" />
        <span className="text-xs text-slate-400">Repository:</span>
        <select
          value={activeRepoId}
          onChange={(e) => setActiveRepoId(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs font-mono text-white focus:outline-none cursor-pointer"
        >
          {repos.length === 0 && <option value="">no repos loaded</option>}
          {repos.map((r: any) => (
            <option key={r.id} value={r.id} className="bg-slate-900 text-white">
              {r.name} ({r.id})
            </option>
          ))}
        </select>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            const url = repoUrl.trim();
            if (url) onLoadRepo(url);
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="Paste a public GitHub URL…"
            className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-72"
          />
          <button
            type="submit"
            disabled={repoLoading || !repoUrl.trim()}
            className="px-3 py-1 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5"
          >
            {repoLoading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
            Load repo
          </button>
        </form>

        {repoError && (
          <span className="text-[11px] text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-2 py-1">
            {repoError}
          </span>
        )}
        {repoNote && (
          <span className="text-[11px] text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-2 py-1">
            {repoNote}
          </span>
        )}
      </div>
    </section>
  );
}
