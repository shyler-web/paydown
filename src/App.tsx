import { useCallback, useEffect, useState } from 'react';
import { loadTenants } from './data';
import type { TenantMap } from './data';
import { deleteRepo, fetchRepos, loadRepo, type RepoSummary } from './data/remote';
import Header from './panels/Header';
import ControlPanel from './panels/ControlPanel';
import AnalyzeStudio from './panels/AnalyzeStudio';
import RefactorStudio from './panels/RefactorStudio';
import MemoryTiers from './panels/MemoryTiers';
import BackendTab from './panels/BackendTab';
import { LoadingScreen, ErrorScreen } from './panels/DataStates';

type LoadState = 'loading' | 'ready' | 'error';

/**
 * Paydown shell — four tabs over one repo:
 *   Analyze  · debt summary + repo map + dependency/ownership context
 *   Refactor · Clarify analyze/propose/explain
 *   Memory   · repo-scoped 4-tier agent memory
 *   Status   · backend health + setup
 */
export default function App() {
  const [tenants, setTenants] = useState<TenantMap>({});
  const [activeTenantKey, setActiveTenantKey] = useState('');
  const [activeRepoId, setActiveRepoId] = useState('');
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('analyze');
  const [repoLoading, setRepoLoading] = useState(false);
  const [repoError, setRepoError] = useState<string | null>(null);
  const [repoNote, setRepoNote] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoadState('loading');
    setLoadError(null);
    try {
      const map = await loadTenants();
      setTenants(map);
      setActiveTenantKey((prev) =>
        prev && map[prev] ? prev : Object.keys(map)[0] ?? ''
      );
      setLoadState('ready');
    } catch (err) {
      setLoadError((err as Error).message || String(err));
      setLoadState('error');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Repo registry: pick the first loaded repo instead of a hardcoded demo slug.
  useEffect(() => {
    fetchRepos()
      .then((list) => {
        setRepos(list);
        setActiveRepoId((prev) => prev || list[0]?.id || '');
      })
      .catch((err) => setRepoError((err as Error).message || String(err)));
  }, []);

  // Keep the workspace selector pointed at the active repo's memory tenant.
  useEffect(() => {
    if (!activeRepoId) return;
    const key = `repo-${activeRepoId}`;
    if (tenants[key]) setActiveTenantKey(key);
  }, [activeRepoId, tenants]);

  const handleLoadRepo = useCallback(async (url: string) => {
    setRepoLoading(true);
    setRepoError(null);
    setRepoNote(null);
    try {
      const result = await loadRepo(url);
      setActiveRepoId(result.repo_id);
      setRepoNote(
        `Loaded ${result.name}: ${result.files} files · ${result.symbols} symbols · ${result.commits} commits`
      );
      const [map, list] = await Promise.all([loadTenants(), fetchRepos()]);
      setTenants(map);
      setRepos(list);
      setActiveTenantKey(`repo-${result.repo_id}`);
      setActiveTab('analyze');
    } catch (err) {
      setRepoError((err as Error).message || String(err));
    } finally {
      setRepoLoading(false);
    }
  }, []);

  const handleDeleteRepo = useCallback(async () => {
    if (!activeRepoId) return;
    setRepoLoading(true);
    setRepoError(null);
    setRepoNote(null);
    const slug = activeRepoId;
    try {
      await deleteRepo(slug);
      const [map, list] = await Promise.all([loadTenants(), fetchRepos()]);
      setTenants(map);
      setRepos(list);
      const next = list[0]?.id ?? '';
      setActiveRepoId(next);
      const nextTenant = next ? `repo-${next}` : '';
      setActiveTenantKey(
        nextTenant && map[nextTenant] ? nextTenant : Object.keys(map)[0] ?? ''
      );
      setRepoNote(`Cleared ${slug}`);
    } catch (err) {
      setRepoError((err as Error).message || String(err));
    } finally {
      setRepoLoading(false);
    }
  }, [activeRepoId]);

  if (loadState === 'loading') {
    return <LoadingScreen />;
  }
  if (loadState === 'error') {
    return (
      <ErrorScreen
        message={loadError}
        onRetry={() => {
          void load();
        }}
      />
    );
  }

  const currentTenant = tenants[activeTenantKey];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      <Header
        tenants={tenants}
        activeTenantKey={activeTenantKey}
        setActiveTenantKey={setActiveTenantKey}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <ControlPanel
        repos={repos}
        activeRepoId={activeRepoId}
        setActiveRepoId={setActiveRepoId}
        repoLoading={repoLoading}
        repoError={repoError}
        repoNote={repoNote}
        onLoadRepo={handleLoadRepo}
        onDeleteRepo={handleDeleteRepo}
      />

      <main className="flex-1 max-w-[1600px] w-full mx-auto p-4">
        {activeTab === 'analyze' && <AnalyzeStudio repo={activeRepoId} />}
        {activeTab === 'refactor' && <RefactorStudio repo={activeRepoId} />}
        {activeTab === 'memory' && <MemoryTiers currentTenant={currentTenant} />}
        {activeTab === 'status' && <BackendTab />}
      </main>
    </div>
  );
}
