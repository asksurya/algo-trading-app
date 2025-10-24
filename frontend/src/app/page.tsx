import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, BarChart3, TrendingUp, Shield } from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between px-4">
          <h1 className="text-xl font-bold">Algo Trading Platform</h1>
          <div className="flex gap-4">
            <Link href="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="container px-4 py-24">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-4xl font-bold tracking-tight sm:text-6xl">
              Advanced Algorithmic Trading Platform
            </h2>
            <p className="mt-6 text-lg text-muted-foreground">
              Build, backtest, and deploy sophisticated trading strategies with our powerful platform.
              Real-time analytics, risk management, and automated execution.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg">
                  Get Started <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline">
                  Login
                </Button>
              </Link>
            </div>
          </div>
        </section>

        <section className="border-t bg-gray-50/50 py-24">
          <div className="container px-4">
            <div className="grid gap-8 md:grid-cols-3">
              <div className="flex flex-col items-center text-center">
                <div className="rounded-full bg-primary p-3 text-primary-foreground">
                  <TrendingUp className="h-6 w-6" />
                </div>
                <h3 className="mt-4 text-xl font-semibold">Multiple Strategies</h3>
                <p className="mt-2 text-muted-foreground">
                  Choose from a variety of pre-built strategies or create your own custom algorithms.
                </p>
              </div>
              <div className="flex flex-col items-center text-center">
                <div className="rounded-full bg-primary p-3 text-primary-foreground">
                  <BarChart3 className="h-6 w-6" />
                </div>
                <h3 className="mt-4 text-xl font-semibold">Real-time Analytics</h3>
                <p className="mt-2 text-muted-foreground">
                  Monitor your portfolio performance with detailed analytics and live updates.
                </p>
              </div>
              <div className="flex flex-col items-center text-center">
                <div className="rounded-full bg-primary p-3 text-primary-foreground">
                  <Shield className="h-6 w-6" />
                </div>
                <h3 className="mt-4 text-xl font-semibold">Risk Management</h3>
                <p className="mt-2 text-muted-foreground">
                  Built-in risk controls to protect your capital with stop-loss and position sizing.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-6">
        <div className="container px-4 text-center text-sm text-muted-foreground">
          © 2025 Algo Trading Platform. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
