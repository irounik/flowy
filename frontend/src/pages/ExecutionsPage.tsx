import { useEffect, useState } from 'react';
import { Panel } from '@/components/ui/Panel';
import { Badge } from '@/components/ui/Badge';
import { listExecutions, type ExecutionResponse } from '@/lib/api';

const statusColors: Record<string, string> = {
  RUNNING: '#22D3EE',
  WAITING: '#FBBF24',
  COMPLETED: '#34D399',
  FAILED: '#F87171',
  CANCELLED: '#64748B',
};

export function ExecutionsPage() {
  const [executions, setExecutions] = useState<ExecutionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await listExecutions();
      setExecutions(data);
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-full">
      <header className="px-6 py-4 border-b border-fds-border-subtle bg-fds-bg-raised">
        <h1 className="text-xl font-bold text-fds-text-primary">Executions</h1>
        <p className="text-sm text-fds-text-secondary mt-0.5">
          Live workflow runs — auto-refreshes every 2s
        </p>
      </header>

      <div className="flex-1 p-6 overflow-auto">
        <Panel title="Recent executions">
          {loading && executions.length === 0 && (
            <p className="p-4 text-sm text-fds-text-muted">Loading…</p>
          )}
          {error && (
            <p className="p-4 text-sm text-fds-status-failed">{error}</p>
          )}
          {!loading && executions.length === 0 && !error && (
            <p className="p-4 text-sm text-fds-text-muted">No executions yet. Run a workflow from the designer.</p>
          )}
          <div className="divide-y divide-fds-border-subtle">
            {executions.map((exec) => (
              <div
                key={exec.id}
                className="flex items-center gap-4 px-4 py-3 hover:bg-fds-bg-raised transition-colors"
              >
                <span className="text-xs font-mono text-fds-text-muted w-28 truncate">
                  {exec.id.slice(0, 8)}…
                </span>
                <span className="text-sm text-fds-text-primary flex-1">
                  {exec.trigger_type}
                </span>
                <span className="text-xs text-fds-text-secondary truncate max-w-[140px]">
                  {exec.current_node ?? '—'}
                </span>
                <Badge color={statusColors[exec.status] ?? '#64748B'}>{exec.status}</Badge>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
