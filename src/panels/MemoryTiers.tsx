import { ShieldAlert, Layers, MessageSquare, GitBranch } from 'lucide-react';

/**
 * Repo-scoped agent memory. The tiers are written by real agent runs on the
 * active repo (`tenant:repo-<slug>`): analyses, proposals, validations and
 * handoffs — not the old demo narrative.
 */
export default function MemoryTiers(props: any) {
  const { currentTenant } = props;
  if (!currentTenant) {
    return (
      <div className="text-sm text-slate-400 border border-slate-800 rounded-2xl p-6">
        No memory yet. Load a repo to bootstrap episodic, semantic, procedural and
        coordination memory for it.
      </div>
    );
  }

  const episodes = currentTenant.episodes ?? [];
  const nodes = currentTenant.nodes ?? [];
  const playbooks = currentTenant.playbooks ?? [];
  const handoffs = currentTenant.handoffs ?? [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {/* Tier 1: Episodic */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-pink-400" />
            1. Episodic
          </h3>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-pink-500/20 text-pink-300">
            {episodes.length} events
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          What the agents did on this repo: loads, rankings, proposals, validations.
        </p>
        <div className="space-y-3 flex-1 max-h-[460px] overflow-y-auto pr-1">
          {episodes.map((ep: any) => (
            <div key={ep.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                <span className="truncate">{ep.session}</span>
                <span className="shrink-0">{ep.timestamp}</span>
              </div>
              <div className="text-xs text-slate-300 leading-relaxed">{ep.summary || ep.prompt}</div>
            </div>
          ))}
          {episodes.length === 0 && <div className="text-xs text-slate-500">No events yet.</div>}
        </div>
      </div>

      {/* Tier 2: Semantic */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            2. Semantic
          </h3>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
            {nodes.length} files
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          Ranked files with their A/B/E comprehension-risk evidence.
        </p>
        <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
          {nodes.map((n: any) => (
            <div key={n.id} className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <div className="flex items-center justify-between text-[11px] font-mono mb-0.5">
                <span className="text-indigo-400">
                  L{n.persona_level} · {n.domain}
                </span>
                <span
                  className={
                    n.status === 'ALERT' || n.status === 'CRITICAL'
                      ? 'text-rose-400 font-bold'
                      : 'text-slate-400'
                  }
                >
                  {n.status}
                </span>
              </div>
              <div className="text-xs font-semibold text-white truncate">{n.title}</div>
              <div className="text-[11px] text-slate-400 line-clamp-2">{n.summary}</div>
            </div>
          ))}
          {nodes.length === 0 && <div className="text-xs text-slate-500">No files scored yet.</div>}
        </div>
      </div>

      {/* Tier 3: Procedural */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-emerald-400" />
            3. Procedural
          </h3>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
            {playbooks.length} playbooks
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          Reusable refactor playbooks the agent can replay on future files.
        </p>
        <div className="space-y-3 flex-1">
          {playbooks.map((pb: any) => (
            <div key={pb.id} className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/40">
              <div className="text-xs font-bold text-emerald-300 mb-1">{pb.rule_name}</div>
              <div className="text-[11px] font-mono text-slate-400 mb-1">
                Trigger: {pb.trigger_domain}
              </div>
              <div className="text-xs text-slate-200 mb-1.5">{pb.enforced_action}</div>
              <div className="text-[10px] font-mono text-emerald-400">Source: {pb.learned_from}</div>
            </div>
          ))}
          {playbooks.length === 0 && <div className="text-xs text-slate-500">No playbooks yet.</div>}
        </div>
      </div>

      {/* Tier 4: Coordination */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-violet-400" />
            4. Coordination
          </h3>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-violet-500/20 text-violet-300">
            {handoffs.length} handoffs
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          Agent-to-agent handoffs: analyzer → refactorer → validator → reviewer.
        </p>
        <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
          {handoffs.map((h: any) => (
            <div key={h.id} className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <div className="flex items-center justify-between text-[11px] font-mono mb-0.5">
                <span className="text-slate-300">
                  {h.from || '?'} → {h.to || '?'}
                </span>
                <span
                  className={
                    h.status === 'COMPLETED'
                      ? 'text-emerald-400'
                      : h.status === 'ALERT_RAISED'
                      ? 'text-rose-400'
                      : 'text-amber-400'
                  }
                >
                  {h.status}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 truncate">{h.target}</div>
            </div>
          ))}
          {handoffs.length === 0 && <div className="text-xs text-slate-500">No handoffs yet.</div>}
        </div>
      </div>
    </div>
  );
}
