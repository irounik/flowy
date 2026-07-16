import { cn } from '@/lib/cn';

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

export function IconButton({ className, active, children, ...props }: IconButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center w-8 h-8 rounded-fds-md',
        'text-fds-text-secondary hover:text-fds-brand hover:bg-fds-bg-panel',
        'transition-colors duration-[var(--fds-duration-fast)] cursor-pointer',
        'disabled:opacity-40 disabled:pointer-events-none',
        active && 'text-fds-brand bg-fds-brand/10',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
