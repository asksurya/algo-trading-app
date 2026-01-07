"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bell, BellOff, Check, CheckCheck, Trash2, Settings, Loader2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Notification {
  id: string;
  type: string;
  priority: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  data?: any;
}

interface NotificationStats {
  total_unread: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  recent_count: number;
}

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-500",
  medium: "bg-blue-500",
  high: "bg-orange-500",
  urgent: "bg-red-500",
};

export default function NotificationsPage() {
  const [activeTab, setActiveTab] = useState("all");
  const queryClient = useQueryClient();

  // Fetch notifications
  const { data: notifications, isLoading } = useQuery<Notification[]>({
    queryKey: ["notifications"],
    queryFn: async () => {
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/v1/notifications", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch notifications");
      return response.json();
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch stats
  const { data: stats } = useQuery<NotificationStats>({
    queryKey: ["notification-stats"],
    queryFn: async () => {
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/v1/notifications/stats", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch stats");
      return response.json();
    },
  });

  // Mark as read mutation
  const markReadMutation = useMutation({
    mutationFn: async (notificationId: string) => {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:8000/api/v1/notifications/${notificationId}/read`,
        {
          method: "PUT",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!response.ok) throw new Error("Failed to mark as read");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
    },
  });

  // Mark all read mutation
  const markAllReadMutation = useMutation({
    mutationFn: async () => {
      const token = localStorage.getItem("token");
      const response = await fetch(
        "http://localhost:8000/api/v1/notifications/mark-all-read",
        {
          method: "PUT",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!response.ok) throw new Error("Failed to mark all as read");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (notificationId: string) => {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:8000/api/v1/notifications/${notificationId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!response.ok) throw new Error("Failed to delete notification");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
    },
  });

  const getPriorityBadge = (priority: string) => {
    const color = PRIORITY_COLORS[priority.toLowerCase()] || "bg-gray-500";
    return <Badge className={color}>{priority.toUpperCase()}</Badge>;
  };

  const filteredNotifications = notifications?.filter((n) => {
    if (activeTab === "all") return true;
    if (activeTab === "unread") return !n.is_read;
    if (activeTab === "urgent") return n.priority.toLowerCase() === "urgent";
    return true;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen" data-testid="notifications-loading">
        <Loader2 className="h-8 w-8 animate-spin" data-testid="notifications-loading-spinner" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6" data-testid="notifications-container">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bell className="h-8 w-8" />
            Notifications
          </h1>
          <p className="text-muted-foreground">Stay updated with your trading activity</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending || !stats?.total_unread}
            data-testid="notifications-mark-all-read"
          >
            <CheckCheck className="h-4 w-4 mr-2" />
            Mark All Read
          </Button>
          <Button variant="outline" data-testid="notifications-preferences">
            <Settings className="h-4 w-4 mr-2" />
            Preferences
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4" data-testid="notifications-stats">
        <Card data-testid="notifications-stat-unread">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Unread</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_unread || 0}</div>
          </CardContent>
        </Card>
        <Card data-testid="notifications-stat-recent">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Recent (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.recent_count || 0}</div>
          </CardContent>
        </Card>
        <Card data-testid="notifications-stat-high">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">High Priority</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-500">
              {stats?.by_priority?.high || 0}
            </div>
          </CardContent>
        </Card>
        <Card data-testid="notifications-stat-urgent">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Urgent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {stats?.by_priority?.urgent || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Notifications List */}
      <Card data-testid="notifications-card">
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab} data-testid="notifications-filter-tabs">
            <TabsList data-testid="notifications-tabs-list">
              <TabsTrigger value="all" data-testid="notifications-filter-all">All</TabsTrigger>
              <TabsTrigger value="unread" data-testid="notifications-filter-unread">
                Unread {stats?.total_unread ? `(${stats.total_unread})` : ""}
              </TabsTrigger>
              <TabsTrigger value="urgent" data-testid="notifications-filter-urgent">Urgent</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] pr-4" data-testid="notifications-scroll-area">
            {filteredNotifications && filteredNotifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground" data-testid="notifications-empty-state">
                <BellOff className="h-12 w-12 mb-4" />
                <p>No notifications</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredNotifications?.map((notification) => (
                  <Card
                    key={notification.id}
                    className={`transition-colors ${
                      !notification.is_read ? "bg-accent/50" : ""
                    }`}
                    data-testid={`notifications-item-${notification.id}`}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <CardTitle className="text-base">{notification.title}</CardTitle>
                            {getPriorityBadge(notification.priority)}
                            {!notification.is_read && (
                              <Badge variant="secondary" className="text-xs">
                                NEW
                              </Badge>
                            )}
                          </div>
                          <CardDescription className="text-xs">
                            {formatDistanceToNow(new Date(notification.created_at), {
                              addSuffix: true,
                            })}
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-1">
                          {!notification.is_read && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => markReadMutation.mutate(notification.id)}
                              data-testid={`notifications-mark-read-${notification.id}`}
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (confirm("Delete this notification?")) {
                                deleteMutation.mutate(notification.id);
                              }
                            }}
                            data-testid={`notifications-delete-${notification.id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm">{notification.message}</p>
                      {notification.data && (
                        <div className="mt-2 text-xs text-muted-foreground">
                          <details>
                            <summary className="cursor-pointer">Details</summary>
                            <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto">
                              {JSON.stringify(notification.data, null, 2)}
                            </pre>
                          </details>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
