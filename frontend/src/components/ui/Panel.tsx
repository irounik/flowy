import { cn } from '@/lib/cn';

interface PanelProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  action?: React.ReactNode;
}

export function Panel({ children, className, title, action }: PanelProps) {
  return (
    <div
      className={cn(
        'flex flex-col bg-fds-bg-panel border border-fds-border-subtle rounded-fds-lg shadow-[var(--fds-shadow-md)]',
        className,
      )}
    >
      {title && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-fds-border-subtle">
          <h3 className="text-sm font-semibold text-fds-text-primary">{title}</h3>
          {action}
        </div>
      )}
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
