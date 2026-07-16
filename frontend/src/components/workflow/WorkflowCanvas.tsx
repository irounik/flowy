import { useCallback, useEffect, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Edge,
  type Node,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { nodeTypes } from './WorkflowNode';
import {
  createDefaultConfig,
  DND_NODE_TYPE,
  type WorkflowDefinition,
  type WorkflowNodeData,
} from '@/lib/workflow-types';
import { nodeColors, type WorkflowNodeType } from '@/design-system/tokens';

let nodeId = 0;
const getId = () => `node_${++nodeId}`;

interface WorkflowCanvasProps {
  initialDefinition?: WorkflowDefinition;
  onSelectionChange: (node: Node<WorkflowNodeData> | null) => void;
  onGraphChange: (nodes: Node<WorkflowNodeData>[], edges: Edge[]) => void;
  addNodeRequest?: { type: WorkflowNodeType; key: number } | null;
  onDeleteNode?: (nodeId: string) => void;
  externalNodes?: Node<WorkflowNodeData>[];
  externalEdges?: Edge[];
  onUpdateNode?: (nodeId: string, data: Partial<WorkflowNodeData>) => void;
}

function definitionToGraph(def?: WorkflowDefinition): {
  nodes: Node<WorkflowNodeData>[];
  edges: Edge[];
} {
  if (!def) return { nodes: [], edges: [] };
  nodeId = def.nodes.length;
  return {
    nodes: def.nodes.map((n) => ({
      id: n.id,
      type: 'workflowNode',
      position: n.position,
      data: {
        label: n.label,
        description: n.description,
        nodeType: n.type,
        config: n.config,
      },
    })),
    edges: def.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      animated: true,
    })),
  };
}

function CanvasInner({
  initialDefinition,
  onSelectionChange,
  onGraphChange,
  addNodeRequest,
}: WorkflowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();
  const initial = definitionToGraph(initialDefinition);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);

  useEffect(() => {
    onGraphChange(nodes, edges);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!addNodeRequest) return;
    const newNode: Node<WorkflowNodeData> = {
      id: getId(),
      type: 'workflowNode',
      position: { x: 200 + Math.random() * 120, y: 120 + Math.random() * 120 },
      data: {
        label: nodeColors[addNodeRequest.type].label,
        nodeType: addNodeRequest.type,
        config: createDefaultConfig(addNodeRequest.type),
      },
    };
    setNodes((nds) => {
      const next = [...nds, newNode];
      onGraphChange(next, edges);
      return next;
    });
  }, [addNodeRequest]); // eslint-disable-line react-hooks/exhaustive-deps

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => {
        const next = addEdge({ ...connection, animated: true }, eds);
        onGraphChange(nodes, next);
        return next;
      });
    },
    [nodes, setEdges, onGraphChange],
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData(DND_NODE_TYPE) as WorkflowNodeType;
      if (!type) return;

      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      const newNode: Node<WorkflowNodeData> = {
        id: getId(),
        type: 'workflowNode',
        position,
        data: {
          label: nodeColors[type].label,
          nodeType: type,
          config: createDefaultConfig(type),
        },
      };
      setNodes((nds) => {
        const next = [...nds, newNode];
        onGraphChange(next, edges);
        return next;
      });
    },
    [screenToFlowPosition, edges, setNodes, onGraphChange],
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onSelectionChange(node as Node<WorkflowNodeData>);
    },
    [onSelectionChange],
  );

  const onPaneClick = useCallback(() => {
    onSelectionChange(null);
  }, [onSelectionChange]);

  const handleNodesChange = useCallback(
    (changes: Parameters<typeof onNodesChange>[0]) => {
      onNodesChange(changes);
      setNodes((nds) => {
        onGraphChange(nds, edges);
        return nds;
      });
    },
    [onNodesChange, edges, onGraphChange, setNodes],
  );

  const handleEdgesChange = useCallback(
    (changes: Parameters<typeof onEdgesChange>[0]) => {
      onEdgesChange(changes);
      setEdges((eds) => {
        onGraphChange(nodes, eds);
        return eds;
      });
    },
    [onEdgesChange, nodes, onGraphChange, setEdges],
  );

  return (
    <div ref={reactFlowWrapper} className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[16, 16]}
        defaultEdgeOptions={{ animated: true }}
        proOptions={{ hideAttribution: true }}
        deleteKeyCode={['Backspace', 'Delete']}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1E2733" />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) => {
            const data = n.data as WorkflowNodeData;
            return nodeColors[data?.nodeType]?.color ?? '#64748B';
          }}
          maskColor="rgba(8, 11, 16, 0.75)"
        />
      </ReactFlow>
    </div>
  );
}

export function WorkflowCanvas(props: WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  );
}
