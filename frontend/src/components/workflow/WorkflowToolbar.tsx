import {
  Download,
  Play,
  Redo2,
  Save,
  Undo2,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface WorkflowToolbarProps {
  workflowName: string;
  workflowDescription: string;
  onNameChange: (name: string) => void;
  onDescriptionChange: (desc: string) => void;
  onSave: () => void;
  onExport: () => void;
  onRun: () => void;
  isRunning?: boolean;
  statusMessage?: string;
}

export function WorkflowToolbar({
  workflowName,
  workflowDescription,
  onNameChange,
  onDescriptionChange,
  onSave,
  onExport,
  onRun,
  isRunning,
  statusMessage,
}: WorkflowToolbarProps) {
  return (
    <div className="flex items-center gap-4 px-4 h-14 border-b border-fds-border-subtle bg-fds-bg-raised shrink-0">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <Input
          value={workflowName}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Workflow name"
          className="max-w-[200px] font-semibold"
        />
        <Input
          value={workflowDescription}
          onChange={(e) => onDescriptionChange(e.target.value)}
          placeholder="Description"
          className="flex-1 max-w-md"
        />
      </div>

      {statusMessage && (
        <span className="text-xs text-fds-text-muted font-mono hidden lg:block">{statusMessage}</span>
      )}

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" title="Undo (coming soon)" disabled>
          <Undo2 size={15} />
        </Button>
        <Button variant="ghost" size="sm" title="Redo (coming soon)" disabled>
          <Redo2 size={15} />
        </Button>
        <div className="w-px h-5 bg-fds-border-subtle mx-1" />
        <Button variant="secondary" size="sm" onClick={onSave}>
          <Save size={15} />
          Save
        </Button>
        <Button variant="secondary" size="sm" onClick={onExport}>
          <Download size={15} />
          Export
        </Button>
        <Button variant="primary" size="sm" onClick={onRun} disabled={isRunning}>
          <Play size={15} />
          {isRunning ? 'Running…' : 'Run'}
        </Button>
      </div>
    </div>
  );
}
