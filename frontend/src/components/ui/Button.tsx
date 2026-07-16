import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const variants: Record<ButtonVariant, string> = {
  primary:
    'bg-fds-brand text-fds-bg-base hover:brightness-110 shadow-[0_0_20px_var(--fds-brand-glow)] font-semibold',
  secondary:
    'bg-fds-bg-panel border border-fds-border-subtle text-fds-text-primary hover:border-fds-border-strong hover:bg-fds-bg-raised',
  ghost: 'text-fds-text-secondary hover:text-fds-brand hover:bg-fds-bg-panel',
  danger: 'bg-fds-status-failed/15 text-fds-status-failed border border-fds-status-failed/30 hover:bg-fds-status-failed/25',
};

const sizes: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs gap-1.5',
  md: 'h-9 px-4 text-sm gap-2',
  lg: 'h-11 px-5 text-sm gap-2',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'secondary', size = 'md', disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center rounded-fds-md font-sans transition-all duration-[var(--fds-duration-fast)] ease-[var(--fds-ease)]',
        'disabled:opacity-40 disabled:pointer-events-none cursor-pointer',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  ),
);

Button.displayName = 'Button';
