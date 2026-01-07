"use client"

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Plus, Trash2, Bell } from 'lucide-react'

interface Watchlist {
    id: string
    name: string
    description: string | null
    items: WatchlistItem[]
}

interface WatchlistItem {
    id: string
    symbol: string
    notes: string | null
    current_price: number | null
    change_percent: number | null
}

export default function WatchlistPage() {
    const [watchlists, setWatchlists] = useState<Watchlist[]>([])
    const [selectedWatchlist, setSelectedWatchlist] = useState<string | null>(null)
    const [newWatchlistName, setNewWatchlistName] = useState('')
    const [newSymbol, setNewSymbol] = useState('')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchWatchlists()
    }, [])

    const fetchWatchlists = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const response = await fetch('/api/v1/watchlist', {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            const data = await response.json()
            setWatchlists(data.watchlists || [])
        } catch (error) {
            console.error('Error fetching watchlists:', error)
        } finally {
            setLoading(false)
        }
    }

    const createWatchlist = async () => {
        if (!newWatchlistName.trim()) return

        try {
            const token = localStorage.getItem('token')
            await fetch('/api/v1/watchlist', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: newWatchlistName })
            })
            setNewWatchlistName('')
            fetchWatchlists()
        } catch (error) {
            console.error('Error creating watchlist:', error)
        }
    }

    const addSymbol = async (watchlistId: string) => {
        if (!newSymbol.trim()) return

        try {
            const token = localStorage.getItem('token')
            await fetch(`/api/v1/watchlist/${watchlistId}/items`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbol: newSymbol.toUpperCase() })
            })
            setNewSymbol('')
            fetchWatchlists()
        } catch (error) {
            console.error('Error adding symbol:', error)
        }
    }

    const formatPercent = (value: number | null) => {
        if (value === null) return 'N/A'
        const formatted = value.toFixed(2)
        return value >= 0 ? `+${formatted}%` : `${formatted}%`
    }

    const formatPrice = (value: number | null) => {
        if (value === null) return 'N/A'
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value)
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen" data-testid="watchlist-loading-container">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" data-testid="watchlist-spinner"></div>
                    <p className="mt-4 text-gray-600">Loading watchlists...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="container mx-auto p-6 space-y-6" data-testid="watchlist-page">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Watchlists</h1>
                <div className="flex gap-2">
                    <Input
                        placeholder="New watchlist name"
                        value={newWatchlistName}
                        onChange={(e) => setNewWatchlistName(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && createWatchlist()}
                        className="w-64"
                        data-testid="watchlist-create-input"
                    />
                    <Button onClick={createWatchlist} data-testid="watchlist-create-button">
                        <Plus className="h-4 w-4 mr-2" />
                        Create Watchlist
                    </Button>
                </div>
            </div>

            {watchlists.length === 0 ? (
                <Card data-testid="watchlist-empty-state">
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <p className="text-muted-foreground mb-4">No watchlists yet</p>
                        <p className="text-sm text-muted-foreground">Create your first watchlist to track symbols</p>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3" data-testid="watchlist-grid">
                    {watchlists.map((watchlist) => (
                        <Card key={watchlist.id} className="hover:shadow-lg transition-shadow" data-testid={`watchlist-card-${watchlist.id}`}>
                            <CardHeader>
                                <CardTitle className="flex justify-between items-center">
                                    <span>{watchlist.name}</span>
                                    <Badge variant="secondary">{watchlist.items.length} symbols</Badge>
                                </CardTitle>
                                {watchlist.description && (
                                    <CardDescription>{watchlist.description}</CardDescription>
                                )}
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Add Symbol */}
                                <div className="flex gap-2">
                                    <Input
                                        placeholder="Symbol (e.g., AAPL)"
                                        value={newSymbol}
                                        onChange={(e) => setNewSymbol(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && addSymbol(watchlist.id)}
                                        className="flex-1"
                                        data-testid={`watchlist-add-symbol-input-${watchlist.id}`}
                                    />
                                    <Button size="sm" onClick={() => addSymbol(watchlist.id)} data-testid={`watchlist-add-symbol-button-${watchlist.id}`}>
                                        <Plus className="h-4 w-4" />
                                    </Button>
                                </div>

                                {/* Watchlist Items */}
                                <div className="space-y-2" data-testid={`watchlist-items-${watchlist.id}`}>
                                    {watchlist.items.length === 0 ? (
                                        <p className="text-sm text-muted-foreground text-center py-4" data-testid={`watchlist-empty-items-${watchlist.id}`}>
                                            No symbols added yet
                                        </p>
                                    ) : (
                                        watchlist.items.map((item) => (
                                            <div
                                                key={item.id}
                                                className="flex justify-between items-center p-3 bg-secondary/50 rounded-lg hover:bg-secondary transition-colors"
                                                data-testid={`watchlist-item-row-${item.id}`}
                                            >
                                                <div className="flex-1">
                                                    <p className="font-semibold" data-testid={`watchlist-item-symbol-${item.id}`}>{item.symbol}</p>
                                                    <p className="text-sm text-muted-foreground" data-testid={`watchlist-item-price-${item.id}`}>
                                                        {formatPrice(item.current_price)}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className={`text-sm font-medium ${item.change_percent && item.change_percent >= 0
                                                            ? 'text-green-600'
                                                            : 'text-red-600'
                                                        }`} data-testid={`watchlist-item-change-${item.id}`}>
                                                        {formatPercent(item.change_percent)}
                                                    </span>
                                                    <Button size="sm" variant="ghost" data-testid={`watchlist-item-alert-button-${item.id}`}>
                                                        <Bell className="h-4 w-4" />
                                                    </Button>
                                                    <Button size="sm" variant="ghost" data-testid={`watchlist-item-delete-button-${item.id}`}>
                                                        <Trash2 className="h-4 w-4 text-red-600" />
                                                    </Button>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
}
