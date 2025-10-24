"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Plus, Shield, AlertTriangle, Trash2, Edit } from "lucide-react";

interface RiskRule {
  id: string;
  name: string;
  description: string;
  rule_type: string;
  threshold_value: number;
  threshold_unit: string;
  action: string;
  is_active: boolean;
  breach_count: number;
  last_breach_at: string | null;
  created_at: string;
}

const RULE_TYPES = [
  { value: "max_daily_loss", label: "Max Daily Loss" },
  { value: "max_position_size", label: "Max Position Size" },
  { value: "max_drawdown", label: "Max Drawdown" },
  { value: "position_limit", label: "Position Limit" },
  { value: "max_leverage", label: "Max Leverage" },
];

const ACTIONS = [
  { value: "alert", label: "Alert Only" },
  { value: "block", label: "Block Order" },
  { value: "reduce_size", label: "Reduce Size" },
  { value: "close_position", label: "Close Position" },
];

export default function RiskRulesPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<RiskRule | null>(null);
  const queryClient = useQueryClient();

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    rule_type: "max_daily_loss",
    threshold_value: 500,
    threshold_unit: "dollars",
    action: "alert",
    is_active: true,
  });

  // Fetch risk rules
  const { data: rules, isLoading } = useQuery<RiskRule[]>({
    queryKey: ["risk-rules"],
    queryFn: async () => {
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/v1/risk-rules", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch risk rules");
      return response.json();
    },
  });

  // Create risk rule mutation
  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/v1/risk-rules", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error("Failed to create risk rule");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risk-rules"] });
      setIsCreateOpen(false);
      resetForm();
    },
  });

  // Delete risk rule mutation
  const deleteMutation = useMutation({
    mutationFn: async (ruleId: string) => {
      const token = localStorage.getItem("token");
      const response = await fetch(`http://localhost:8000/api/v1/risk-rules/${ruleId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to delete risk rule");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risk-rules"] });
    },
  });

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      rule_type: "max_daily_loss",
      threshold_value: 500,
      threshold_unit: "dollars",
      action: "alert",
      is_active: true,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const getRuleTypeLabel = (type: string) => {
    return RULE_TYPES.find(t => t.value === type)?.label || type;
  };

  const getActionBadge = (action: string) => {
    const colors: Record<string, string> = {
      alert: "bg-blue-500",
      block: "bg-red-500",
      reduce_size: "bg-yellow-500",
      close_position: "bg-orange-500",
    };
    return <Badge className={colors[action] || "bg-gray-500"}>{action.toUpperCase()}</Badge>;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="h-8 w-8" />
            Risk Management Rules
          </h1>
          <p className="text-muted-foreground">Configure risk rules to protect your portfolio</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Rule
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>Create Risk Rule</DialogTitle>
                <DialogDescription>
                  Configure a new risk management rule to protect your portfolio
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Rule Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Daily Loss Limit"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Optional description"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rule_type">Rule Type</Label>
                  <Select
                    value={formData.rule_type}
                    onValueChange={(value) => setFormData({ ...formData, rule_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {RULE_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="threshold_value">Threshold Value</Label>
                    <Input
                      id="threshold_value"
                      type="number"
                      step="0.01"
                      value={formData.threshold_value}
                      onChange={(e) =>
                        setFormData({ ...formData, threshold_value: parseFloat(e.target.value) })
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="threshold_unit">Unit</Label>
                    <Select
                      value={formData.threshold_unit}
                      onValueChange={(value) => setFormData({ ...formData, threshold_unit: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="dollars">Dollars</SelectItem>
                        <SelectItem value="percent">Percent</SelectItem>
                        <SelectItem value="shares">Shares</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="action">Action</Label>
                  <Select
                    value={formData.action}
                    onValueChange={(value) => setFormData({ ...formData, action: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ACTIONS.map((action) => (
                        <SelectItem key={action.value} value={action.value}>
                          {action.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    "Create Rule"
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {rules && rules.length === 0 ? (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            No risk rules configured. Create your first rule to protect your portfolio.
          </AlertDescription>
        </Alert>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {rules?.map((rule) => (
            <Card key={rule.id} className={!rule.is_active ? "opacity-60" : ""}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">{rule.name}</CardTitle>
                    <CardDescription>{getRuleTypeLabel(rule.rule_type)}</CardDescription>
                  </div>
                  {getActionBadge(rule.action)}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {rule.description && (
                  <p className="text-sm text-muted-foreground">{rule.description}</p>
                )}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Threshold:</span>
                  <span className="font-medium">
                    {rule.threshold_value} {rule.threshold_unit}
                  </span>
                </div>
                {rule.breach_count > 0 && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Breaches:</span>
                    <Badge variant="destructive">{rule.breach_count}</Badge>
                  </div>
                )}
                <div className="flex items-center gap-2 pt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex-1"
                    onClick={() => setSelectedRule(rule)}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex-1 text-destructive"
                    onClick={() => {
                      if (confirm("Are you sure you want to delete this rule?")) {
                        deleteMutation.mutate(rule.id);
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
