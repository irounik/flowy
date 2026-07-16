import { Panel } from '@/components/ui/Panel';
import { Badge } from '@/components/ui/Badge';

const MOCK_EXECUTIONS = [
  { id: 'exec-1', workflow: 'invoice-approval', status: 'WAITING', node: 'human_approval' },
  { id: 'exec-2', workflow: 'research', status: 'COMPLETED', node: 'slack_notification' },
  { id: 'exec-3', workflow: 'research', status: 'RUNNING', node: 'llm_summary' },
];

const statusColors: Record<string, string> = {
  RUNNING: '#22D3EE',
  WAITING: '#FBBF24',
  COMPLETED: '#34D399',
  FAILED: '#F87171',
};

export function ExecutionsPage() {
  return (
    <div className="flex flex-col h-full">
      <header className="px-6 py-4 border-b border-fds-border-subtle bg-fds-bg-raised">
        <h1 className="text-xl font-bold text-fds-text-primary">Executions</h1>
        <p className="text-sm text-fds-text-secondary mt-0.5">
          Monitor workflow runs — connect to backend for live data
        </p>
      </header>

      <div className="flex-1 p-6 overflow-auto">
        <Panel title="Recent executions">
          <div className="divide-y divide-fds-border-subtle">
            {MOCK_EXECUTIONS.map((exec) => (
              <div
                key={exec.id}
                className="flex items-center gap-4 px-4 py-3 hover:bg-fds-bg-raised transition-colors"
              >
                <span className="text-xs font-mono text-fds-text-muted w-24">{exec.id}</span>
                <span className="text-sm text-fds-text-primary flex-1">{exec.workflow}</span>
                <span className="text-xs text-fds-text-secondary">{exec.node}</span>
                <Badge color={statusColors[exec.status]}>{exec.status}</Badge>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
