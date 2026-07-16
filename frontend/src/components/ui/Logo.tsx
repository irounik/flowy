import { cn } from '@/lib/cn';

interface LogoProps {
  size?: 'sm' | 'md';
  className?: string;
}

export function Logo({ size = 'md', className }: LogoProps) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div
        className={cn(
          'flex items-center justify-center rounded-fds-md bg-fds-brand/15 border border-fds-brand/30',
          size === 'sm' ? 'w-7 h-7' : 'w-8 h-8',
        )}
      >
        <svg viewBox="0 0 24 24" className={size === 'sm' ? 'w-4 h-4' : 'w-5 h-5'} fill="none">
          <path
            d="M4 12c0-1.5 2-4 8-4s8 2.5 8 4-2 4-8 4-8-2.5-8-4z"
            stroke="#22D3EE"
            strokeWidth="1.5"
          />
          <path
            d="M12 4v16M4 12h16"
            stroke="#22D3EE"
            strokeWidth="1.5"
            strokeLinecap="round"
            opacity="0.4"
          />
        </svg>
      </div>
      <span
        className={cn(
          'font-bold tracking-tight text-fds-text-primary',
          size === 'sm' ? 'text-sm' : 'text-base',
        )}
      >
        Flowy
      </span>
    </div>
  );
}
