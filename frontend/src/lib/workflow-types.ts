import type { WorkflowNodeType } from '@/design-system/tokens';

export interface WorkflowNodeData {
  label: string;
  description?: string;
  nodeType: WorkflowNodeType;
  config: Record<string, string>;
  [key: string]: unknown;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  nodes: Array<{
    id: string;
    type: WorkflowNodeType;
    label: string;
    description?: string;
    position: { x: number; y: number };
    config: Record<string, string>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
  }>;
}

export const DND_NODE_TYPE = 'application/flowy-node';

export function createDefaultConfig(type: WorkflowNodeType): Record<string, string> {
  switch (type) {
    case 'trigger':
      return { triggerType: 'manual' };
    case 'llm':
      return { model: 'gemini-2.5-flash', prompt: '' };
    case 'tool':
      return { function: 'calculator', params: '{}' };
    case 'mcp':
      return { server: 'filesystem', tool: 'read_file' };
    case 'approval':
      return { message: 'Please review and approve.' };
    case 'notification':
      return { channel: 'email', template: '' };
    default:
      return {};
  }
}

export function serializeWorkflow(
  name: string,
  description: string,
  nodes: Array<{
    id: string;
    type?: string;
    position: { x: number; y: number };
    data: WorkflowNodeData;
  }>,
  edges: Array<{ id: string; source: string; target: string }>,
): WorkflowDefinition {
  return {
    id: crypto.randomUUID(),
    name,
    description,
    version: '0.1.0',
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.data.nodeType,
      label: n.data.label,
      description: n.data.description,
      position: n.position,
      config: n.data.config,
    })),
    edges: edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
    })),
  };
}

export const INVOICE_TEMPLATE: WorkflowDefinition = {
  id: 'template-invoice',
  name: 'Invoice Approval',
  description: 'Extract, summarize, approve, and email',
  version: '0.1.0',
  nodes: [
    { id: 't1', type: 'trigger', label: 'Manual Trigger', position: { x: 80, y: 200 }, config: { triggerType: 'manual' } },
    { id: 'n1', type: 'tool', label: 'Invoice Extraction', position: { x: 340, y: 200 }, config: { function: 'extract_invoice_data' } },
    { id: 'n2', type: 'llm', label: 'Summary', position: { x: 600, y: 200 }, config: { model: 'gemini-2.5-flash', prompt: 'Summarize invoice' } },
    { id: 'n3', type: 'approval', label: 'Human Approval', position: { x: 860, y: 200 }, config: { message: 'Approve this invoice?' } },
    { id: 'n4', type: 'notification', label: 'Email', position: { x: 1120, y: 200 }, config: { channel: 'email' } },
  ],
  edges: [
    { id: 'e1', source: 't1', target: 'n1' },
    { id: 'e2', source: 'n1', target: 'n2' },
    { id: 'e3', source: 'n2', target: 'n3' },
    { id: 'e4', source: 'n3', target: 'n4' },
  ],
};

export const RESEARCH_TEMPLATE: WorkflowDefinition = {
  id: 'template-research',
  name: 'Research Workflow',
  description: 'Search, summarize, and notify',
  version: '0.1.0',
  nodes: [
    { id: 't1', type: 'trigger', label: 'Webhook', position: { x: 80, y: 200 }, config: { triggerType: 'webhook' } },
    { id: 'n1', type: 'tool', label: 'Search Tool', position: { x: 340, y: 200 }, config: { function: 'web_search' } },
    { id: 'n2', type: 'llm', label: 'LLM Summary', position: { x: 600, y: 200 }, config: { model: 'gemini-2.5-flash', prompt: 'Summarize results' } },
    { id: 'n3', type: 'notification', label: 'Slack', position: { x: 860, y: 200 }, config: { channel: 'slack' } },
  ],
  edges: [
    { id: 'e1', source: 't1', target: 'n1' },
    { id: 'e2', source: 'n1', target: 'n2' },
    { id: 'e3', source: 'n2', target: 'n3' },
  ],
};
