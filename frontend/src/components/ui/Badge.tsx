import { cn } from '@/lib/cn';

interface BadgeProps {
  children: React.ReactNode;
  color?: string;
  className?: string;
}

export function Badge({ children, color, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-fds-sm px-2 py-0.5 text-[11px] font-medium font-mono uppercase tracking-wide',
        className,
      )}
      style={
        color
          ? { color, backgroundColor: `${color}20`, border: `1px solid ${color}40` }
          : undefined
      }
    >
      {children}
    </span>
  );
}
