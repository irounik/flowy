import { useCallback, useState } from 'react';
import type { Edge, Node } from '@xyflow/react';
import { GitBranch, LayoutTemplate, Plus } from 'lucide-react';
import { WorkflowCanvas } from '@/components/workflow/WorkflowCanvas';
import { NodePalette } from '@/components/workflow/NodePalette';
import { PropertiesPanel } from '@/components/workflow/PropertiesPanel';
import { WorkflowToolbar } from '@/components/workflow/WorkflowToolbar';
import { Panel } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import {
  INVOICE_TEMPLATE,
  RESEARCH_TEMPLATE,
  serializeWorkflow,
  type WorkflowDefinition,
  type WorkflowNodeData,
} from '@/lib/workflow-types';
import { runDynamicWorkflow, saveWorkflowLocal } from '@/lib/api';
import type { WorkflowNodeType } from '@/design-system/tokens';

export function DesignerPage() {
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [selectedNode, setSelectedNode] = useState<Node<WorkflowNodeData> | null>(null);
  const [nodes, setNodes] = useState<Node<WorkflowNodeData>[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [template, setTemplate] = useState<WorkflowDefinition | undefined>(undefined);
  const [statusMessage, setStatusMessage] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [addNodeRequest, setAddNodeRequest] = useState<{ type: WorkflowNodeType; key: number } | null>(null);

  const handleGraphChange = useCallback((n: Node<WorkflowNodeData>[], e: Edge[]) => {
    setNodes(n);
    setEdges(e);
  }, []);

  const handleAddNode = useCallback((type: WorkflowNodeType) => {
    setAddNodeRequest({ type, key: Date.now() });
  }, []);

  const handleUpdateNode = useCallback((nodeId: string, data: Partial<WorkflowNodeData>) => {
    setNodes((prev) =>
      prev.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n)),
    );
    setSelectedNode((prev) =>
      prev?.id === nodeId ? { ...prev, data: { ...prev.data, ...data } } : prev,
    );
  }, []);

  const handleDeleteNode = useCallback((nodeId: string) => {
    setNodes((prev) => prev.filter((n) => n.id !== nodeId));
    setEdges((prev) => prev.filter((e) => e.source !== nodeId && e.target !== nodeId));
    setSelectedNode(null);
  }, []);

  const getDefinition = useCallback(
    () => serializeWorkflow(workflowName, workflowDescription, nodes, edges),
    [workflowName, workflowDescription, nodes, edges],
  );

  const handleSave = useCallback(() => {
    const def = getDefinition();
    saveWorkflowLocal(def);
    setStatusMessage(`Saved locally at ${new Date().toLocaleTimeString()}`);
  }, [getDefinition]);

  const handleExport = useCallback(() => {
    const def = getDefinition();
    const blob = new Blob([JSON.stringify(def, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflowName.toLowerCase().replace(/\s+/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setStatusMessage('Exported JSON');
  }, [getDefinition, workflowName]);

  const handleRun = useCallback(async () => {
    if (nodes.length === 0) {
      setStatusMessage('Add at least one node before running');
      return;
    }
    setIsRunning(true);
    setStatusMessage('Starting execution…');
    try {
      const def = getDefinition();
      const result = await runDynamicWorkflow({ ...def, input: { source: 'designer' } });
      setStatusMessage(`Execution started: ${result.execution_id.slice(0, 8)}…`);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : 'Run failed — is the backend running?');
    } finally {
      setIsRunning(false);
    }
  }, [getDefinition, nodes.length]);

  const loadTemplate = useCallback((def: WorkflowDefinition) => {
    setWorkflowName(def.name);
    setWorkflowDescription(def.description);
    setTemplate(def);
    setSelectedNode(null);
    setStatusMessage(`Loaded template: ${def.name}`);
  }, []);

  return (
    <div className="flex flex-col h-full">
      <WorkflowToolbar
        workflowName={workflowName}
        workflowDescription={workflowDescription}
        onNameChange={setWorkflowName}
        onDescriptionChange={setWorkflowDescription}
        onSave={handleSave}
        onExport={handleExport}
        onRun={handleRun}
        isRunning={isRunning}
        statusMessage={statusMessage}
      />

      <div className="flex flex-1 min-h-0">
        {/* Left sidebar — palette */}
        <aside className="w-60 shrink-0 border-r border-fds-border-subtle bg-fds-bg-raised flex flex-col">
          <Panel title="Nodes" className="flex-1 border-0 rounded-none shadow-none bg-transparent">
            <NodePalette onAddNode={handleAddNode} />
          </Panel>

          <div className="border-t border-fds-border-subtle p-3">
            <p className="text-[11px] font-medium text-fds-text-muted uppercase tracking-wider px-2 mb-2">
              Templates
            </p>
            <div className="flex flex-col gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="justify-start w-full"
                onClick={() => loadTemplate(INVOICE_TEMPLATE)}
              >
                <LayoutTemplate size={14} />
                Invoice Approval
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="justify-start w-full"
                onClick={() => loadTemplate(RESEARCH_TEMPLATE)}
              >
                <GitBranch size={14} />
                Research
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="justify-start w-full"
                onClick={() => {
                  setTemplate(undefined);
                  setWorkflowName('Untitled Workflow');
                  setWorkflowDescription('');
                  setNodes([]);
                  setEdges([]);
                  setSelectedNode(null);
                  setStatusMessage('New blank workflow');
                }}
              >
                <Plus size={14} />
                Blank workflow
              </Button>
            </div>
          </div>
        </aside>

        {/* Canvas */}
        <main className="flex-1 min-w-0 bg-fds-bg-canvas">
          <WorkflowCanvas
            key={template?.id ?? 'blank'}
            initialDefinition={template}
            onSelectionChange={setSelectedNode}
            onGraphChange={handleGraphChange}
            addNodeRequest={addNodeRequest}
            onDeleteNode={handleDeleteNode}
            externalNodes={nodes}
            externalEdges={edges}
            onUpdateNode={handleUpdateNode}
          />
        </main>

        {/* Right sidebar — properties */}
        <aside className="w-72 shrink-0 border-l border-fds-border-subtle bg-fds-bg-raised p-3">
          <PropertiesPanel
            selectedNode={selectedNode}
            onUpdate={handleUpdateNode}
            onDelete={handleDeleteNode}
          />
        </aside>
      </div>
    </div>
  );
}
