import React, { useState, useEffect } from 'react';
import { Layers, Database, RefreshCw, FileText, CheckCircle } from 'lucide-react';

export function EnvironmentInspector({ status }) {
  const [invoices, setInvoices] = useState([]);
  const [financeData, setFinanceData] = useState({ records: [], session_active: false });
  const [activeTab, setActiveTab] = useState('portal'); // 'portal' | 'finance'
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resPortal, resFinance] = await Promise.all([
        fetch('http://localhost:8000/api/portal/invoices'),
        fetch('http://localhost:8000/api/finance/records'),
      ]);
      if (resPortal.ok) setInvoices(await resPortal.json());
      if (resFinance.ok) setFinanceData(await resFinance.json());
    } catch (e) {
      console.error('Failed to fetch environment state:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [status]);

  return (
    <div className="glass-panel rounded-2xl p-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Live System Inspector</h2>
            <p className="text-xs text-slate-400">Directly inspect mock applications & stored state</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab('portal')}
              className={`px-3 py-1 rounded-md transition-colors ${
                activeTab === 'portal'
                  ? 'bg-indigo-600 text-white font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Invoice Portal ({invoices.length})
            </button>
            <button
              onClick={() => setActiveTab('finance')}
              className={`px-3 py-1 rounded-md transition-colors ${
                activeTab === 'finance'
                  ? 'bg-indigo-600 text-white font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Finance System ({financeData.records?.length || 0})
            </button>
          </div>

          <button
            onClick={fetchData}
            title="Refresh environment state"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="pt-4">
        {activeTab === 'portal' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300 font-mono">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="py-2 px-3 rounded-l-lg">Invoice ID</th>
                  <th className="py-2 px-3">Company</th>
                  <th className="py-2 px-3">Amount</th>
                  <th className="py-2 px-3">Due Date</th>
                  <th className="py-2 px-3 rounded-r-lg">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {invoices.map((inv) => (
                  <tr key={inv.invoice_id} className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-3 font-semibold text-indigo-300">{inv.invoice_id}</td>
                    <td className="py-2.5 px-3 text-slate-100">{inv.company}</td>
                    <td className="py-2.5 px-3 text-emerald-400">₹{inv.amount.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-slate-400">{inv.due_date}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] ${
                          inv.status === 'paid'
                            ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/40'
                            : 'bg-amber-950/60 text-amber-300 border border-amber-800/40'
                        }`}
                      >
                        {inv.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-4 text-xs font-mono bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-400">Session Status:</span>
              <span className={`font-semibold ${financeData.session_active ? 'text-emerald-400' : 'text-amber-400'}`}>
                {financeData.session_active ? 'Active ✓' : 'Inactive / Closed'}
              </span>
              <span className="text-slate-400 ml-auto">Submit Attempts:</span>
              <span className="font-semibold text-slate-200">{financeData.submit_attempts || 0}</span>
            </div>

            {financeData.records && financeData.records.length > 0 ? (
              <div className="space-y-2">
                {financeData.records.map((rec) => (
                  <div
                    key={rec.record_id}
                    className="p-3 bg-slate-900/80 rounded-xl border border-emerald-500/30 text-xs font-mono"
                  >
                    <div className="flex items-center justify-between text-indigo-400 font-semibold mb-1">
                      <span>Record #{rec.record_id}</span>
                      <span className="text-emerald-400 text-[10px] uppercase">Recorded in Ledger ✓</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-300 mt-2">
                      <div><span className="text-slate-500">Invoice:</span> {rec.invoice_no}</div>
                      <div><span className="text-slate-500">Vendor:</span> {rec.vendor}</div>
                      <div><span className="text-slate-500">Amount:</span> ₹{Number(rec.amount).toLocaleString()}</div>
                      <div><span className="text-slate-500">Due:</span> {rec.due_date}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-slate-500 text-xs font-mono">
                No invoices recorded in Finance System yet.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
