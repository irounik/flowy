import { nodePaletteItems, nodeColors } from '@/design-system/tokens';
import { DND_NODE_TYPE } from '@/lib/workflow-types';
import {
  Bell,
  Bot,
  Play,
  Plug,
  UserCheck,
  Wrench,
} from 'lucide-react';
import type { WorkflowNodeType } from '@/design-system/tokens';

const icons: Record<WorkflowNodeType, React.ElementType> = {
  trigger: Play,
  llm: Bot,
  tool: Wrench,
  mcp: Plug,
  approval: UserCheck,
  notification: Bell,
};

interface NodePaletteProps {
  onAddNode: (type: WorkflowNodeType) => void;
}

export function NodePalette({ onAddNode }: NodePaletteProps) {
  const onDragStart = (event: React.DragEvent, type: WorkflowNodeType) => {
    event.dataTransfer.setData(DND_NODE_TYPE, type);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="flex flex-col gap-1 p-3">
      <p className="text-[11px] font-medium text-fds-text-muted uppercase tracking-wider px-2 mb-2">
        Drag to canvas
      </p>
      {nodePaletteItems.map((item) => {
        const colors = nodeColors[item.type];
        const Icon = icons[item.type];
        return (
          <div
            key={item.type}
            draggable
            onDragStart={(e) => onDragStart(e, item.type)}
            onClick={() => onAddNode(item.type)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-fds-md cursor-grab active:cursor-grabbing
              border border-transparent hover:border-fds-border-subtle hover:bg-fds-bg-raised
              transition-all duration-[var(--fds-duration-fast)] group"
          >
            <div
              className="flex items-center justify-center w-8 h-8 rounded-fds-sm shrink-0
                transition-transform duration-[var(--fds-duration-fast)] group-hover:scale-105"
              style={{ backgroundColor: colors.bg, color: colors.color }}
            >
              <Icon size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-fds-text-primary">{item.defaultLabel}</p>
              <p className="text-xs text-fds-text-muted truncate">{item.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
