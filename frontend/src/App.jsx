import React from 'react';
import { Bot, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';
import { useTaskRunner } from './hooks/useTaskRunner';
import { TaskInput } from './components/TaskInput';
import { ExecutionLog } from './components/ExecutionLog';
import { ResultPanel } from './components/ResultPanel';
import { ApprovalDialog } from './components/ApprovalDialog';
import { EnvironmentInspector } from './components/EnvironmentInspector';

export default function App() {
  const {
    task,
    events,
    status,
    error,
    approvalRequest,
    verificationResult,
    backendHealth,
    startTask,
    sendApproval,
    resetAll,
  } = useTaskRunner();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/25">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                Autonomous AI Task Worker
                <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                  v1.0 Prototype
                </span>
              </h1>
              <p className="text-[11px] text-slate-400">
                Observe → Decide → Act → Recover → Verify Architecture
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {/* Backend Health Badge */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
              {backendHealth?.status === 'healthy' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="text-slate-300 font-mono">Backend Online</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                  <span className="text-rose-300 font-mono">Backend Offline</span>
                </>
              )}
            </div>

            {/* LLM Model Badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span>{backendHealth?.model || 'llama-3.1-70b (Groq)'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Dashboard */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Top: Task Input & Presets */}
        <TaskInput onStartTask={startTask} status={status} onReset={resetAll} />

        {/* Middle: 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Live Execution Trace */}
          <div className="lg:col-span-7">
            <ExecutionLog events={events} status={status} />
          </div>

          {/* Right Column: Outcomes & Independent Verification */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <ResultPanel status={status} verificationResult={verificationResult} error={error} />
          </div>
        </div>

        {/* Bottom: Simulated Environment Inspector */}
        <EnvironmentInspector status={status} />
      </main>

      {/* Human-in-the-Loop Approval Modal */}
      <ApprovalDialog
        request={approvalRequest}
        onApprove={() => sendApproval(true)}
        onReject={() => sendApproval(false)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        Autonomous AI Task Worker Prototype • Built with React, Tailwind, FastAPI & Groq Function Calling
      </footer>
    </div>
  );
}
