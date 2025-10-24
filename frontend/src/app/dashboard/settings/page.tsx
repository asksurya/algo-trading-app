"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/stores/auth-store";
import { useToast } from "@/components/ui/use-toast";
import { useState } from "react";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
            <CardDescription>
              Your account details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Email</Label>
              <Input value={user?.email || ""} disabled />
            </div>
            <div className="space-y-2">
              <Label>Full Name</Label>
              <Input value={user?.full_name || ""} disabled />
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <Input value={user?.role || ""} disabled />
            </div>
            <div className="space-y-2">
              <Label>Account Status</Label>
              <Input 
                value={user?.is_active ? "Active" : "Inactive"} 
                disabled 
                className={user?.is_active ? "text-green-600" : "text-red-600"}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Trading Configuration</CardTitle>
            <CardDescription>
              Configure your trading preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="apiKey">Alpaca API Key</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="Enter your Alpaca API key"
                disabled
              />
              <p className="text-xs text-muted-foreground">
                API integration coming soon
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="apiSecret">Alpaca API Secret</Label>
              <Input
                id="apiSecret"
                type="password"
                placeholder="Enter your Alpaca API secret"
                disabled
              />
            </div>
            <Button disabled className="w-full">
              Save API Credentials (Coming Soon)
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Management</CardTitle>
            <CardDescription>
              Configure risk parameters for your trading
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="maxPositionSize">Max Position Size (%)</Label>
              <Input
                id="maxPositionSize"
                type="number"
                placeholder="10"
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="stopLoss">Default Stop Loss (%)</Label>
              <Input
                id="stopLoss"
                type="number"
                placeholder="5"
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="takeProfit">Default Take Profit (%)</Label>
              <Input
                id="takeProfit"
                type="number"
                placeholder="10"
                disabled
              />
            </div>
            <Button disabled className="w-full">
              Save Risk Settings (Coming Soon)
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Manage your notification preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Trade Alerts</Label>
                <p className="text-xs text-muted-foreground">
                  Get notified when trades are executed
                </p>
              </div>
              <Button variant="outline" size="sm" disabled>
                Coming Soon
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label>Strategy Alerts</Label>
                <p className="text-xs text-muted-foreground">
                  Get notified about strategy performance
                </p>
              </div>
              <Button variant="outline" size="sm" disabled>
                Coming Soon
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label>Email Notifications</Label>
                <p className="text-xs text-muted-foreground">
                  Receive email updates
                </p>
              </div>
              <Button variant="outline" size="sm" disabled>
                Coming Soon
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>About This Application</CardTitle>
          <CardDescription>
            Current implementation status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h3 className="font-semibold">✅ Implemented Features:</h3>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              <li>User authentication and registration</li>
              <li>Strategy CRUD operations (Create, Read, Update, Delete)</li>
              <li>Portfolio overview and statistics</li>
              <li>Trade history tracking</li>
              <li>Position monitoring</li>
              <li>Real-time data from PostgreSQL database</li>
            </ul>
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold">🚧 Coming Soon:</h3>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              <li>Live trading execution via Alpaca API</li>
              <li>Real-time market data integration</li>
              <li>Advanced charting and analytics</li>
              <li>Backtesting engine integration</li>
              <li>Email and push notifications</li>
              <li>API key management</li>
              <li>Risk management rules engine</li>
            </ul>
          </div>
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <strong>Note:</strong> This is a development/testing environment. Live trading features require Alpaca API integration and additional safety measures before production use.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
