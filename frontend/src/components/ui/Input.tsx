import { cn } from '@/lib/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function Input({ label, className, id, ...props }: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-fds-text-secondary">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          'h-9 px-3 rounded-fds-md bg-fds-bg-raised border border-fds-border-subtle',
          'text-sm text-fds-text-primary placeholder:text-fds-text-muted',
          'focus:outline-none focus:border-fds-brand focus:ring-1 focus:ring-fds-brand/40',
          'transition-colors duration-[var(--fds-duration-fast)]',
          className,
        )}
        {...props}
      />
    </div>
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export function Textarea({ label, className, id, ...props }: TextareaProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-fds-text-secondary">
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        className={cn(
          'min-h-[80px] px-3 py-2 rounded-fds-md bg-fds-bg-raised border border-fds-border-subtle',
          'text-sm text-fds-text-primary placeholder:text-fds-text-muted resize-y',
          'focus:outline-none focus:border-fds-brand focus:ring-1 focus:ring-fds-brand/40',
          'transition-colors duration-[var(--fds-duration-fast)]',
          className,
        )}
        {...props}
      />
    </div>
  );
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: Array<{ value: string; label: string }>;
}

export function Select({ label, options, className, id, ...props }: SelectProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-fds-text-secondary">
          {label}
        </label>
      )}
      <select
        id={inputId}
        className={cn(
          'h-9 px-3 rounded-fds-md bg-fds-bg-raised border border-fds-border-subtle',
          'text-sm text-fds-text-primary',
          'focus:outline-none focus:border-fds-brand focus:ring-1 focus:ring-fds-brand/40',
          className,
        )}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
