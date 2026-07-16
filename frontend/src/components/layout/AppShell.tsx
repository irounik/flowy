import { NavLink, Outlet } from 'react-router-dom';
import { GitBranch, LayoutDashboard, Settings } from 'lucide-react';
import { Logo } from '@/components/ui/Logo';
import { cn } from '@/lib/cn';

const navItems = [
  { to: '/', label: 'Designer', icon: GitBranch, end: true },
  { to: '/executions', label: 'Executions', icon: LayoutDashboard },
];

export function AppShell() {
  return (
    <div className="flex h-full">
      {/* Primary nav rail */}
      <nav className="w-14 shrink-0 flex flex-col items-center py-4 gap-2 bg-fds-bg-base border-r border-fds-border-subtle">
        <Logo size="sm" className="mb-4" />

        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={label}
            className={({ isActive }) =>
              cn(
                'flex items-center justify-center w-10 h-10 rounded-fds-md transition-all duration-[var(--fds-duration-fast)]',
                isActive
                  ? 'bg-fds-brand/15 text-fds-brand shadow-[0_0_16px_var(--fds-brand-glow)]'
                  : 'text-fds-text-muted hover:text-fds-text-secondary hover:bg-fds-bg-raised',
              )
            }
          >
            <Icon size={18} />
          </NavLink>
        ))}

        <div className="flex-1" />

        <button
          title="Settings"
          className="flex items-center justify-center w-10 h-10 rounded-fds-md text-fds-text-muted hover:text-fds-text-secondary hover:bg-fds-bg-raised transition-colors"
        >
          <Settings size={18} />
        </button>
      </nav>

      <div className="flex-1 min-w-0 flex flex-col">
        <Outlet />
      </div>
    </div>
  );
}
