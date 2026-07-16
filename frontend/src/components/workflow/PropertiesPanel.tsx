import type { Node } from '@xyflow/react';
import { Trash2 } from 'lucide-react';
import { Panel } from '@/components/ui/Panel';
import { Input, Textarea, Select } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { nodeColors } from '@/design-system/tokens';
import type { WorkflowNodeData } from '@/lib/workflow-types';

interface PropertiesPanelProps {
  selectedNode: Node<WorkflowNodeData> | null;
  onUpdate: (nodeId: string, data: Partial<WorkflowNodeData>) => void;
  onDelete: (nodeId: string) => void;
}

export function PropertiesPanel({ selectedNode, onUpdate, onDelete }: PropertiesPanelProps) {
  if (!selectedNode) {
    return (
      <Panel title="Properties" className="h-full">
        <div className="flex flex-col items-center justify-center h-full p-6 text-center">
          <div className="w-12 h-12 rounded-fds-lg bg-fds-bg-raised border border-fds-border-subtle flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-fds-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5" />
            </svg>
          </div>
          <p className="text-sm text-fds-text-secondary">Select a node to edit its properties</p>
          <p className="text-xs text-fds-text-muted mt-1">Or drag a new node from the palette</p>
        </div>
      </Panel>
    );
  }

  const { nodeType, label, description, config } = selectedNode.data;
  const colors = nodeColors[nodeType];

  const updateConfig = (key: string, value: string) => {
    onUpdate(selectedNode.id, {
      config: { ...config, [key]: value },
    });
  };

  return (
    <Panel
      title="Properties"
      className="h-full"
      action={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(selectedNode.id)}
          className="text-fds-status-failed hover:text-fds-status-failed"
        >
          <Trash2 size={14} />
        </Button>
      }
    >
      <div className="p-4 flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Badge color={colors.color}>{colors.label}</Badge>
          <span className="text-xs text-fds-text-muted font-mono">{selectedNode.id}</span>
        </div>

        <Input
          label="Label"
          value={label}
          onChange={(e) => onUpdate(selectedNode.id, { label: e.target.value })}
        />

        <Textarea
          label="Description"
          value={description ?? ''}
          onChange={(e) => onUpdate(selectedNode.id, { description: e.target.value })}
          placeholder="Optional description"
        />

        <div className="border-t border-fds-border-subtle pt-4 flex flex-col gap-3">
          <p className="text-xs font-medium text-fds-text-muted uppercase tracking-wider">Configuration</p>

          {nodeType === 'trigger' && (
            <Select
              label="Trigger type"
              value={config.triggerType ?? 'manual'}
              onChange={(e) => updateConfig('triggerType', e.target.value)}
              options={[
                { value: 'manual', label: 'Manual' },
                { value: 'webhook', label: 'Webhook' },
              ]}
            />
          )}

          {nodeType === 'llm' && (
            <>
              <Select
                label="Model"
                value={config.model ?? 'gemini-2.5-flash'}
                onChange={(e) => updateConfig('model', e.target.value)}
                options={[
                  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
                  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
                ]}
              />
              <Textarea
                label="Prompt template"
                value={config.prompt ?? ''}
                onChange={(e) => updateConfig('prompt', e.target.value)}
                placeholder="Enter prompt template…"
              />
            </>
          )}

          {nodeType === 'tool' && (
            <>
              <Select
                label="Function"
                value={config.function ?? 'calculator'}
                onChange={(e) => updateConfig('function', e.target.value)}
                options={[
                  { value: 'calculator', label: 'Calculator' },
                  { value: 'web_search', label: 'Web Search' },
                  { value: 'send_email', label: 'Send Email' },
                  { value: 'extract_invoice_data', label: 'Extract Invoice' },
                ]}
              />
              <Textarea
                label="Parameters (JSON)"
                value={config.params ?? '{}'}
                onChange={(e) => updateConfig('params', e.target.value)}
                className="font-mono text-xs"
              />
            </>
          )}

          {nodeType === 'mcp' && (
            <>
              <Select
                label="MCP Server"
                value={config.server ?? 'filesystem'}
                onChange={(e) => updateConfig('server', e.target.value)}
                options={[
                  { value: 'filesystem', label: 'Filesystem' },
                  { value: 'github', label: 'GitHub' },
                ]}
              />
              <Input
                label="Tool name"
                value={config.tool ?? 'read_file'}
                onChange={(e) => updateConfig('tool', e.target.value)}
              />
            </>
          )}

          {nodeType === 'approval' && (
            <Textarea
              label="Approval message"
              value={config.message ?? ''}
              onChange={(e) => updateConfig('message', e.target.value)}
              placeholder="Message shown to approver"
            />
          )}

          {nodeType === 'notification' && (
            <>
              <Select
                label="Channel"
                value={config.channel ?? 'email'}
                onChange={(e) => updateConfig('channel', e.target.value)}
                options={[
                  { value: 'email', label: 'Email' },
                  { value: 'slack', label: 'Slack' },
                ]}
              />
              <Textarea
                label="Template"
                value={config.template ?? ''}
                onChange={(e) => updateConfig('template', e.target.value)}
                placeholder="Notification body template"
              />
            </>
          )}
        </div>
      </div>
    </Panel>
  );
}
