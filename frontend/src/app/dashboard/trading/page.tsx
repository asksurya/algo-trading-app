'use client';

export default function TradingPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">Live Trading Test</h1>
      <p>This is a test to see if routing works at a different path...</p>
      <a href="/dashboard/live-trading" className="text-blue-600 underline">Try original live-trading path</a>
    </div>
  );
}
