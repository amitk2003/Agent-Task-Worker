import React from 'react';
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react';

export function ApprovalDialog({ request, onApprove, onReject }) {
  if (!request) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="glass-panel border-amber-500/50 rounded-2xl max-w-lg w-full p-6 shadow-2xl glow-primary animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-amber-500/20 text-amber-400 rounded-xl shrink-0">
            <AlertCircle className="w-6 h-6" />
          </div>

          <div className="flex-1">
            <span className="text-xs font-mono uppercase tracking-wider text-amber-400 font-semibold">
              Human-in-the-Loop Required
            </span>
            <h3 className="text-lg font-semibold text-white mt-1">Approval Required</h3>
            <p className="mt-2 text-sm text-slate-300 leading-relaxed whitespace-pre-line">
              {request.message}
            </p>

            {request.data && (
              <div className="mt-4 p-3 bg-slate-900/90 rounded-xl border border-slate-800 text-xs font-mono text-slate-300 space-y-1">
                <div className="text-slate-400 text-[11px] mb-1">Target Action:</div>
                <div className="text-indigo-400 font-semibold">{request.data.tool}</div>
              </div>
            )}

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => onReject(false)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium text-rose-300 bg-rose-950/60 hover:bg-rose-900/60 border border-rose-800/60 transition-colors cursor-pointer"
              >
                <XCircle className="w-4 h-4" /> Reject Action
              </button>

              <button
                onClick={() => onApprove(true)}
                className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-600/30 transition-all cursor-pointer"
              >
                <CheckCircle className="w-4 h-4" /> Approve & Continue
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
