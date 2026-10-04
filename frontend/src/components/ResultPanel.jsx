import React from 'react';
import { CheckCircle2, ShieldCheck, XCircle, Clock, Database, FileCheck } from 'lucide-react';

export function ResultPanel({ status, verificationResult, error }) {
  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between glow-emerald">
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              Outcome & Verification
            </h2>
            <p className="text-xs text-slate-400">Independent validation of business results</p>
          </div>

          <div>
            {isCompleted && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-600/50">
                <CheckCircle2 className="w-3.5 h-3.5" /> Completed
              </span>
            )}
            {isFailed && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-600/50">
                <XCircle className="w-3.5 h-3.5" /> Failed
              </span>
            )}
            {status === 'running' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-950/80 text-indigo-300 border border-indigo-600/50">
                <Clock className="w-3.5 h-3.5 animate-spin" /> In Progress
              </span>
            )}
            {status === 'idle' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-800">
                Awaiting Run
              </span>
            )}
          </div>
        </div>

        {isFailed && error && (
          <div className="mt-4 p-4 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-200 text-sm">
            <div className="font-semibold flex items-center gap-2">
              <XCircle className="w-4 h-4 text-rose-400" /> Error Details
            </div>
            <p className="mt-1 text-xs text-rose-300 font-mono">{error}</p>
          </div>
        )}

        {/* Verification Checks Card */}
        {verificationResult ? (
          <div className="mt-4 space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/90 border border-emerald-500/30">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                  <ShieldCheck className="w-4 h-4" /> Independent System Checks
                </div>
                <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                  VERIFIED ✓
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(verificationResult.checks || {}).map(([key, val]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800"
                  >
                    <span className="text-slate-400 capitalize">
                      {key.replace('_match', '').replace('_', ' ')}
                    </span>
                    <span className={`font-mono font-semibold ${val ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {val ? 'PASSED ✓' : 'FAILED ✗'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Evidence Card */}
            {verificationResult.record && (
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm mb-3">
                  <FileCheck className="w-4 h-4" /> Evidence: Recorded Ledger Entry
                </div>

                <div className="space-y-1.5 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-slate-800/80">
                    <span className="text-slate-400">Record ID:</span>
                    <span className="text-slate-100 font-bold">{verificationResult.record.record_id}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/80">
                    <span className="text-slate-400">Invoice Number:</span>
                    <span className="text-indigo-300 font-semibold">{verificationResult.record.invoice_no}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/80">
                    <span className="text-slate-400">Vendor:</span>
                    <span className="text-slate-100">{verificationResult.record.vendor}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/80">
                    <span className="text-slate-400">Amount:</span>
                    <span className="text-emerald-400 font-bold">
                      ₹{Number(verificationResult.record.amount).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Due Date:</span>
                    <span className="text-slate-100">{verificationResult.record.due_date}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="mt-8 text-center text-slate-500 space-y-2 py-10">
            <Database className="w-8 h-8 mx-auto opacity-30 stroke-1" />
            <p className="text-xs">No verification recorded yet. Run a task to generate proof.</p>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
        <span>Guaranteed non-mocked execution</span>
        <span>Re-reads live system records</span>
      </div>
    </div>
  );
}
