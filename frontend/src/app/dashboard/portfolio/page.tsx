"use client"

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface PortfolioSummary {
    total_equity: number
    cash_balance: number
    positions_value: number
    daily_pnl: number
    daily_return_pct: number
    total_pnl: number
    total_return_pct: number
    num_positions: number
    num_long_positions: number
    num_short_positions: number
    last_updated: string
}

interface PerformanceMetrics {
    period: string
    total_return_pct: number
    annualized_return: number | null
    sharpe_ratio: number | null
    sortino_ratio: number | null
    max_drawdown_pct: number | null
    win_rate: number | null
    profit_factor: number | null
}

export default function PortfolioPage() {
    const [summary, setSummary] = useState<PortfolioSummary | null>(null)
    const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null)
    const [period, setPeriod] = useState('monthly')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchPortfolioData()
    }, [period])

    const fetchPortfolioData = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')

            // Fetch summary
            const summaryRes = await fetch('/api/v1/portfolio/summary', {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            const summaryData = await summaryRes.json()
            setSummary(summaryData)

            // Fetch performance metrics
            const metricsRes = await fetch(`/api/v1/portfolio/performance?period=${period}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            const metricsData = await metricsRes.json()
            setMetrics(metricsData)
        } catch (error) {
            console.error('Error fetching portfolio data:', error)
        } finally {
            setLoading(false)
        }
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value)
    }

    const formatPercent = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value / 100)
    }

    if (loading || !summary || !metrics) {
        return (
            <div className="flex items-center justify-center h-screen" data-testid="portfolio-loading-container">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" data-testid="portfolio-loading-spinner"></div>
                    <p className="mt-4 text-gray-600">Loading portfolio analytics...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="container mx-auto p-6 space-y-6" data-testid="portfolio-page-container">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Portfolio Analytics</h1>
            </div>

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4" data-testid="portfolio-summary-cards">
                <Card data-testid="portfolio-total-equity-card">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Equity</CardTitle>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            className="h-4 w-4 text-muted-foreground"
                        >
                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                        </svg>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold" data-testid="portfolio-total-equity-value">{formatCurrency(summary.total_equity)}</div>
                        <p className="text-xs text-muted-foreground">
                            Cash: {formatCurrency(summary.cash_balance)}
                        </p>
                    </CardContent>
                </Card>

                <Card data-testid="portfolio-daily-pnl-card">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Daily P&L</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${summary.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`} data-testid="portfolio-daily-pnl-value">
                            {formatCurrency(summary.daily_pnl)}
                        </div>
                        <p className={`text-xs ${summary.daily_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`} data-testid="portfolio-daily-return-pct">
                            {formatPercent(summary.daily_return_pct)}
                        </p>
                    </CardContent>
                </Card>

                <Card data-testid="portfolio-total-return-card">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Return</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`} data-testid="portfolio-total-return-value">
                            {formatCurrency(summary.total_pnl)}
                        </div>
                        <p className={`text-xs ${summary.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`} data-testid="portfolio-total-return-pct">
                            {formatPercent(summary.total_return_pct)}
                        </p>
                    </CardContent>
                </Card>

                <Card data-testid="portfolio-positions-card">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Positions</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold" data-testid="portfolio-positions-count">{summary.num_positions}</div>
                        <p className="text-xs text-muted-foreground" data-testid="portfolio-positions-breakdown">
                            {summary.num_long_positions} long, {summary.num_short_positions} short
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Performance Metrics */}
            <Tabs value={period} onValueChange={setPeriod} className="w-full" data-testid="portfolio-period-tabs">
                <TabsList className="grid w-full grid-cols-5" data-testid="portfolio-tabs-list">
                    <TabsTrigger value="daily" data-testid="portfolio-tab-daily">Daily</TabsTrigger>
                    <TabsTrigger value="weekly" data-testid="portfolio-tab-weekly">Weekly</TabsTrigger>
                    <TabsTrigger value="monthly" data-testid="portfolio-tab-monthly">Monthly</TabsTrigger>
                    <TabsTrigger value="yearly" data-testid="portfolio-tab-yearly">Yearly</TabsTrigger>
                    <TabsTrigger value="all_time" data-testid="portfolio-tab-all-time">All Time</TabsTrigger>
                </TabsList>

                <TabsContent value={period} className="space-y-4" data-testid="portfolio-metrics-content">
                    <div className="grid gap-4 md:grid-cols-3" data-testid="portfolio-metrics-grid">
                        <Card data-testid="portfolio-returns-card">
                            <CardHeader>
                                <CardTitle>Returns</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                <div data-testid="portfolio-total-return-metric">
                                    <p className="text-sm text-muted-foreground">Total Return</p>
                                    <p className={`text-xl font-bold ${metrics.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`} data-testid="portfolio-total-return-metric-value">
                                        {formatPercent(metrics.total_return_pct)}
                                    </p>
                                </div>
                                {metrics.annualized_return !== null && (
                                    <div data-testid="portfolio-annualized-return-metric">
                                        <p className="text-sm text-muted-foreground">Annualized Return</p>
                                        <p className="text-xl font-bold" data-testid="portfolio-annualized-return-metric-value">
                                            {formatPercent(metrics.annualized_return * 100)}
                                        </p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        <Card data-testid="portfolio-risk-metrics-card">
                            <CardHeader>
                                <CardTitle>Risk Metrics</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {metrics.sharpe_ratio !== null && (
                                    <div data-testid="portfolio-sharpe-ratio-metric">
                                        <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                                        <p className="text-xl font-bold" data-testid="portfolio-sharpe-ratio-value">{metrics.sharpe_ratio.toFixed(2)}</p>
                                    </div>
                                )}
                                {metrics.sortino_ratio !== null && (
                                    <div data-testid="portfolio-sortino-ratio-metric">
                                        <p className="text-sm text-muted-foreground">Sortino Ratio</p>
                                        <p className="text-xl font-bold" data-testid="portfolio-sortino-ratio-value">{metrics.sortino_ratio.toFixed(2)}</p>
                                    </div>
                                )}
                                {metrics.max_drawdown_pct !== null && (
                                    <div data-testid="portfolio-max-drawdown-metric">
                                        <p className="text-sm text-muted-foreground">Max Drawdown</p>
                                        <p className="text-xl font-bold text-red-600" data-testid="portfolio-max-drawdown-value">
                                            {formatPercent(metrics.max_drawdown_pct)}
                                        </p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        <Card data-testid="portfolio-trading-stats-card">
                            <CardHeader>
                                <CardTitle>Trading Stats</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {metrics.win_rate !== null && (
                                    <div data-testid="portfolio-win-rate-metric">
                                        <p className="text-sm text-muted-foreground">Win Rate</p>
                                        <p className="text-xl font-bold" data-testid="portfolio-win-rate-value">{formatPercent(metrics.win_rate)}</p>
                                    </div>
                                )}
                                {metrics.profit_factor !== null && (
                                    <div data-testid="portfolio-profit-factor-metric">
                                        <p className="text-sm text-muted-foreground">Profit Factor</p>
                                        <p className="text-xl font-bold" data-testid="portfolio-profit-factor-value">{metrics.profit_factor.toFixed(2)}</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    <Card data-testid="portfolio-equity-curve-card">
                        <CardHeader>
                            <CardTitle>Equity Curve</CardTitle>
                            <CardDescription>Portfolio value over time</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="h-64 flex items-center justify-center text-muted-foreground" data-testid="portfolio-equity-curve-placeholder">
                                Chart Component (integrate with lightweight-charts or recharts)
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
