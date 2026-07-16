const API_BASE = '/api/v1';

export interface WorkflowResponse {
  id: string;
  name: string;
  description: string | null;
  version: string;
  status: string;
}

export interface ExecutionStartResponse {
  execution_id: string;
}

export async function listWorkflows(): Promise<WorkflowResponse[]> {
  const res = await fetch(`${API_BASE}/workflows`);
  if (!res.ok) throw new Error('Failed to fetch workflows');
  return res.json();
}

export async function registerWorkflow(name: string, description: string): Promise<WorkflowResponse> {
  const res = await fetch(`${API_BASE}/workflows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description, version: '0.1.0' }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Failed to register workflow');
  }
  return res.json();
}

export async function runDynamicWorkflow(
  definition: Record<string, unknown>,
): Promise<ExecutionStartResponse & { workflow_name: string; status: string }> {
  const res = await fetch(`${API_BASE}/workflows/dynamic/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(definition),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Failed to run dynamic workflow');
  }
  return res.json();
}

export interface ExecutionResponse {
  id: string;
  workflow_id: string;
  status: string;
  trigger_type: string;
  current_node: string | null;
  context: Record<string, unknown>;
  metrics: Record<string, unknown>;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export async function listExecutions(): Promise<ExecutionResponse[]> {
  const res = await fetch(`${API_BASE}/executions`);
  if (!res.ok) throw new Error('Failed to fetch executions');
  return res.json();
}

export async function getExecution(id: string): Promise<ExecutionResponse> {
  const res = await fetch(`${API_BASE}/executions/${id}`);
  if (!res.ok) throw new Error('Failed to fetch execution');
  return res.json();
}

export async function runWorkflow(
  workflowName: string,
  input: Record<string, unknown> = {},
): Promise<ExecutionStartResponse> {
  const res = await fetch(`${API_BASE}/workflows/${workflowName}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Failed to run workflow');
  }
  return res.json();
}

export function saveWorkflowLocal(definition: unknown): void {
  const key = 'flowy-workflows';
  const existing = JSON.parse(localStorage.getItem(key) ?? '[]');
  const workflows = Array.isArray(existing) ? existing : [];
  const def = definition as { id: string };
  const idx = workflows.findIndex((w: { id: string }) => w.id === def.id);
  if (idx >= 0) workflows[idx] = definition;
  else workflows.push(definition);
  localStorage.setItem(key, JSON.stringify(workflows));
}

export function loadWorkflowsLocal(): unknown[] {
  return JSON.parse(localStorage.getItem('flowy-workflows') ?? '[]');
}
