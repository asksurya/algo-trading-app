"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  TrendingUp,
  BarChart3,
  Settings,
  Shield,
  Bell,
  Activity,
  Zap,
  Rocket,
} from "lucide-react";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    testId: "nav-dashboard",
  },
  {
    name: "Strategies",
    href: "/dashboard/strategies",
    icon: TrendingUp,
    testId: "nav-strategies",
  },
  {
    name: "Backtests",
    href: "/dashboard/backtests",
    icon: Activity,
    testId: "nav-backtests",
  },
  {
    name: "Strategy Optimizer",
    href: "/dashboard/optimizer",
    icon: Zap,
    testId: "nav-optimizer",
  },
  {
    name: "Live Trading",
    href: "/dashboard/live-trading",
    icon: Rocket,
    testId: "nav-live-trading",
  },
  {
    name: "Risk Rules",
    href: "/dashboard/risk-rules",
    icon: Shield,
    testId: "nav-risk-rules",
  },
  {
    name: "Notifications",
    href: "/dashboard/notifications",
    icon: Bell,
    testId: "nav-notifications",
  },
  {
    name: "Trades",
    href: "/dashboard/trades",
    icon: BarChart3,
    testId: "nav-trades",
  },
  {
    name: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
    testId: "nav-settings",
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-gray-50/50">
      <nav className="flex flex-col gap-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              data-testid={item.testId}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
