import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  RotateCw, 
  HelpCircle, 
  Mail,
  Folder,
  Save,
  Globe,
  Camera,
  Search, 
  FileText, 
  Lock, 
  Send, 
  CheckSquare, 
  Brain,
  ChevronDown,
  ChevronRight,
  AlertTriangle
} from 'lucide-react';

export function ExecutionLog({ events, status }) {
  const [expandedIndices, setExpandedIndices] = useState({});

  const toggleExpand = (index) => {
    setExpandedIndices((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const getEventIcon = (event) => {
    switch (event.event_type) {
      case 'thinking':
        return <Brain className="w-4 h-4 text-purple-400 animate-pulse" />;
      case 'step_start':
        const tool = event.data?.tool;
        if (tool === 'search_invoices') return <Search className="w-4 h-4 text-blue-400" />;
        if (tool === 'read_invoice_details') return <FileText className="w-4 h-4 text-cyan-400" />;
        if (tool === 'open_finance_system') return <Lock className="w-4 h-4 text-amber-400" />;
        if (tool === 'fill_invoice_form') return <FileText className="w-4 h-4 text-indigo-400" />;
        if (tool === 'submit_invoice') return <Send className="w-4 h-4 text-emerald-400" />;
        if (tool === 'verify_submission') return <CheckSquare className="w-4 h-4 text-teal-400" />;
        // Email tools
        if (tool === 'search_emails' || tool === 'read_email') return <Mail className="w-4 h-4 text-sky-400" />;
        if (tool === 'send_email') return <Send className="w-4 h-4 text-emerald-400" />;
        // File tools
        if (tool === 'list_files' || tool === 'read_file') return <Folder className="w-4 h-4 text-amber-300" />;
        if (tool === 'save_file') return <Save className="w-4 h-4 text-indigo-400" />;
        // Browser tools
        if (tool === 'browser_navigate') return <Globe className="w-4 h-4 text-blue-400" />;
        if (tool === 'browser_screenshot') return <Camera className="w-4 h-4 text-pink-400" />;
        return <Brain className="w-4 h-4 text-indigo-400" />;
      case 'step_complete':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'step_failed':
        return <XCircle className="w-4 h-4 text-rose-400" />;
      case 'recovery_attempt':
        return <RotateCw className="w-4 h-4 text-amber-400 animate-spin" />;
      case 'approval_needed':
        return <HelpCircle className="w-4 h-4 text-amber-400" />;
      case 'verification_result':
        return <CheckSquare className="w-4 h-4 text-teal-400" />;
      case 'task_complete':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'task_failed':
        return <XCircle className="w-4 h-4 text-rose-500" />;
      default:
        return <Brain className="w-4 h-4 text-slate-400" />;
    }
  };

  const getEventBadgeClass = (type) => {
    switch (type) {
      case 'step_complete':
      case 'task_complete':
        return 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50';
      case 'step_failed':
      case 'task_failed':
        return 'bg-rose-950/60 text-rose-300 border-rose-800/50';
      case 'recovery_attempt':
        return 'bg-amber-950/60 text-amber-300 border-amber-800/50 animate-pulse';
      case 'approval_needed':
        return 'bg-amber-950/60 text-amber-300 border-amber-800/50';
      case 'thinking':
        return 'bg-purple-950/60 text-purple-300 border-purple-800/50';
      default:
        return 'bg-slate-900 text-slate-300 border-slate-800';
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col h-[580px]">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            Execution Trace
            {status === 'running' && (
              <span className="flex h-2.5 w-2.5 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400">Observe → Decide → Act cycle in real time</p>
        </div>

        <div className="text-xs text-slate-400">
          Total Events: <span className="font-mono text-slate-200">{events.length}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pt-4 pr-1 scrollbar-thin">
        {events.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
            <Brain className="w-10 h-10 stroke-1 opacity-40" />
            <p className="text-sm">Agent idle. Submit a goal to see live autonomous execution.</p>
          </div>
        ) : (
          events.map((evt, idx) => {
            const hasData = evt.data && Object.keys(evt.data).length > 0;
            const isExpanded = expandedIndices[idx];

            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border text-sm transition-all ${getEventBadgeClass(
                  evt.event_type
                )}`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 shrink-0">{getEventIcon(evt)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-mono uppercase tracking-wider opacity-75">
                        {evt.event_type.replace('_', ' ')}
                      </span>
                      {evt.timestamp && (
                        <span className="text-[10px] font-mono text-slate-400">
                          {new Date(evt.timestamp).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-slate-200 font-medium break-words leading-relaxed">
                      {evt.message}
                    </p>

                    {evt.event_type === 'recovery_attempt' && (
                      <div className="mt-2 text-xs flex items-center gap-1.5 text-amber-300 font-medium">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Autonomous Recovery: Agent detected failure and will re-plan next action
                      </div>
                    )}

                    {hasData && (
                      <div className="mt-2">
                        <button
                          onClick={() => toggleExpand(idx)}
                          className="flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                        >
                          {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                          {isExpanded ? 'Hide Details' : 'Show Details'}
                        </button>
                        {isExpanded && (
                          <pre className="mt-2 p-2.5 bg-slate-950/80 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800">
                            {JSON.stringify(evt.data, null, 2)}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
