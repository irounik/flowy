export const tokens = {
  color: {
    bg: {
      base: '#080B10',
      raised: '#0F1419',
      panel: '#151B23',
      canvas: '#0C1017',
    },
    border: {
      subtle: '#1E2733',
      strong: '#2D3A4D',
    },
    text: {
      primary: '#F1F5F9',
      secondary: '#94A3B8',
      muted: '#64748B',
      inverse: '#080B10',
    },
    brand: {
      DEFAULT: '#22D3EE',
      dim: '#0891B2',
      glow: 'rgba(34, 211, 238, 0.25)',
    },
    status: {
      running: '#22D3EE',
      waiting: '#FBBF24',
      completed: '#34D399',
      failed: '#F87171',
    },
  },
  font: {
    sans: '"Plus Jakarta Sans", system-ui, sans-serif',
    mono: '"IBM Plex Mono", ui-monospace, monospace',
  },
  radius: {
    sm: '6px',
    md: '10px',
    lg: '14px',
    xl: '20px',
  },
  space: {
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    5: '20px',
    6: '24px',
    8: '32px',
  },
  duration: {
    fast: '120ms',
    normal: '200ms',
    slow: '320ms',
  },
} as const;

export type WorkflowNodeType =
  | 'trigger'
  | 'llm'
  | 'tool'
  | 'mcp'
  | 'approval'
  | 'notification';

export const nodeColors: Record<
  WorkflowNodeType,
  { color: string; bg: string; label: string }
> = {
  trigger: { color: '#F43F5E', bg: 'rgba(244, 63, 94, 0.12)', label: 'Trigger' },
  llm: { color: '#A78BFA', bg: 'rgba(167, 139, 250, 0.12)', label: 'LLM' },
  tool: { color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.12)', label: 'Tool' },
  mcp: { color: '#2DD4BF', bg: 'rgba(45, 212, 191, 0.12)', label: 'MCP' },
  approval: { color: '#FBBF24', bg: 'rgba(251, 191, 36, 0.12)', label: 'Approval' },
  notification: { color: '#34D399', bg: 'rgba(52, 211, 153, 0.12)', label: 'Notify' },
};

export const nodePaletteItems: Array<{
  type: WorkflowNodeType;
  description: string;
  defaultLabel: string;
}> = [
  { type: 'trigger', description: 'Manual or webhook entry', defaultLabel: 'Trigger' },
  { type: 'llm', description: 'Gemini reasoning step', defaultLabel: 'LLM Agent' },
  { type: 'tool', description: 'Python function call', defaultLabel: 'Tool' },
  { type: 'mcp', description: 'MCP server tool', defaultLabel: 'MCP Tool' },
  { type: 'approval', description: 'Pause for human review', defaultLabel: 'Approval' },
  { type: 'notification', description: 'Email or Slack alert', defaultLabel: 'Notify' },
];
