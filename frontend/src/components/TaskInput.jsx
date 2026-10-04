import React, { useState } from 'react';
import { Play, Sparkles, RefreshCw, Zap, ShieldCheck } from 'lucide-react';

export function TaskInput({ onStartTask, status, onReset }) {
  const [goal, setGoal] = useState('Process the latest invoice from ABC Ltd');

  const presets = [
    { label: 'ABC Ltd (with recovery)', text: 'Process the latest invoice from ABC Ltd' },
    { label: 'Email + Invoice + Send Confirmation', text: 'Search emails for latest invoice from ABC Ltd, process it into finance, and send confirmation email to manager@company.com' },
    { label: 'Invoice + File Report + Browser Evidence', text: 'Process latest invoice from XYZ Corp, save audit receipt file to reports/xyz_receipt.txt, and capture browser screenshot' },
    { label: 'Acme Industries', text: 'Find the newest invoice from Acme Industries, submit to billing, and verify' },
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!goal.trim() || status === 'running' || status === 'awaiting_approval') return;
    onStartTask(goal.trim());
  };

  const isBusy = status === 'running' || status === 'awaiting_approval';

  return (
    <div className="glass-panel rounded-2xl p-6 glow-primary">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-lg">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Business Goal</h2>
            <p className="text-xs text-slate-400">Enter a natural-language task for the autonomous worker</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onReset}
            disabled={isBusy}
            title="Reset environments and state"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors disabled:opacity-50"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset State
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            disabled={isBusy}
            rows={3}
            placeholder="e.g., Process the latest invoice from ABC Ltd and update the finance system"
            className="w-full bg-slate-900/90 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all disabled:opacity-60 resize-none"
          />
        </div>

        {/* Quick Presets */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-400 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-amber-400" /> Presets:
          </span>
          {presets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isBusy}
              onClick={() => setGoal(preset.text)}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/50 transition-colors disabled:opacity-50"
            >
              {preset.label}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1 text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" /> Self-Verifying Loop
            </span>
            <span>Bounded Retries (Max 2)</span>
          </div>

          <button
            type="submit"
            disabled={isBusy || !goal.trim()}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-medium text-sm text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isBusy ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Executing Autonomously...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Run Task Worker
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
