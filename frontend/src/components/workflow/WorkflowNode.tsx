import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import {
  Bell,
  Bot,
  Play,
  Plug,
  UserCheck,
  Wrench,
} from 'lucide-react';
import { nodeColors, type WorkflowNodeType } from '@/design-system/tokens';
import type { WorkflowNodeData } from '@/lib/workflow-types';
import { cn } from '@/lib/cn';

const icons: Record<WorkflowNodeType, React.ElementType> = {
  trigger: Play,
  llm: Bot,
  tool: Wrench,
  mcp: Plug,
  approval: UserCheck,
  notification: Bell,
};

function WorkflowNodeComponent({ data, selected }: NodeProps) {
  const nodeData = data as WorkflowNodeData;
  const { nodeType, label, description } = nodeData;
  const colors = nodeColors[nodeType];
  const Icon = icons[nodeType];

  return (
    <div
      className={cn(
        'min-w-[220px] rounded-fds-lg border bg-fds-bg-panel shadow-[var(--fds-shadow-md)]',
        'transition-all duration-[var(--fds-duration-normal)]',
        selected
          ? 'border-fds-brand shadow-[0_0_24px_var(--fds-brand-glow)]'
          : 'border-fds-border-subtle hover:border-fds-border-strong',
      )}
      style={{ borderLeftWidth: 4, borderLeftColor: colors.color }}
    >
      {nodeType !== 'trigger' && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-2.5 !h-2.5 !bg-fds-brand !border-2 !border-fds-bg-base"
        />
      )}

      <div className="p-3.5">
        <div className="flex items-start gap-3">
          <div
            className="flex items-center justify-center w-9 h-9 rounded-fds-md shrink-0"
            style={{ backgroundColor: colors.bg, color: colors.color }}
          >
            <Icon size={18} strokeWidth={2} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-fds-text-primary truncate">
                {label}
              </span>
            </div>
            <span
              className="text-[11px] font-mono uppercase tracking-wider mt-0.5 block"
              style={{ color: colors.color }}
            >
              {colors.label}
            </span>
            {description && (
              <p className="text-xs text-fds-text-muted mt-1.5 line-clamp-2">{description}</p>
            )}
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="!w-2.5 !h-2.5 !bg-fds-brand !border-2 !border-fds-bg-base"
      />
    </div>
  );
}

export const WorkflowNode = memo(WorkflowNodeComponent);

export const nodeTypes = {
  workflowNode: WorkflowNode,
};
