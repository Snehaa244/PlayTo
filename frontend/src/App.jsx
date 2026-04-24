import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ArrowUpRight, 
  History, 
  Send, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  RefreshCcw,
  ShieldCheck,
  CreditCard,
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  TrendingUp,
  ChevronRight,
  ExternalLink
} from 'lucide-react';

const MERCHANT_ID = 'f4387e9c-f3c6-4bb1-ad30-345ae1fa5e06';
const API_BASE = 'http://localhost:8000/api/v1';

const App = () => {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [amount, setAmount] = useState('');
  const [bankAccount, setBankAccount] = useState('');
  const [idempotencyKey, setIdempotencyKey] = useState(crypto.randomUUID());
  const [status, setStatus] = useState(null);

  const fetchDashboard = async () => {
    try {
      const balanceRes = await axios.get(`${API_BASE}/merchants/${MERCHANT_ID}/balance`);
      setBalance(balanceRes.data.balance_paise);
      const txRes = await axios.get(`${API_BASE}/merchants/${MERCHANT_ID}/transactions`);
      setTransactions(txRes.data);
    } catch (err) {
      console.error("Fetch error", err);
    }
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 5000);
    return () => clearInterval(interval);
  }, []);

  const handlePayout = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: 'info', message: 'Validating with banking gateway...' });

    try {
      await axios.post(`${API_BASE}/payouts`, {
        merchant_id: MERCHANT_ID,
        amount_paise: parseInt(amount),
        bank_account_id: bankAccount
      }, {
        headers: { 'Idempotency-Key': idempotencyKey }
      });

      setStatus({ type: 'success', message: 'Payout successfully queued' });
      setAmount('');
      setBankAccount('');
      setIdempotencyKey(crypto.randomUUID());
      fetchDashboard();
    } catch (err) {
      setStatus({ 
        type: 'error', 
        message: err.response?.data?.error || 'Transaction rejected by ledger' 
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (paise) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-slate-200 font-sans selection:bg-blue-500/30">
      
      {/* Top Header */}
      <header className="border-b border-white/5 bg-[#0A0A0B]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-600/20">
                <ShieldCheck className="text-white" size={18} />
              </div>
              <span className="font-bold text-lg tracking-tight text-white">Playto</span>
            </div>
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
              <a href="#" className="text-white">Balances</a>
              <a href="#" className="hover:text-white transition-colors">Payouts</a>
              <a href="#" className="hover:text-white transition-colors">Developers</a>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <div className="bg-white/5 border border-white/10 rounded-full px-3 py-1 flex items-center gap-2 text-[11px] font-mono text-slate-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Live Environment
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-slate-800 to-slate-700 border border-white/10" />
          </div>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-10">
        
        {/* Hero Section */}
        <div className="mb-12">
          <h1 className="text-3xl font-bold text-white mb-2">Payouts</h1>
          <p className="text-slate-500">Manage your outbound transfers and real-time ledger balance.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column */}
          <div className="lg:col-span-8 space-y-8">
            
            {/* Balance Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-[#141415] border border-white/5 p-6 rounded-2xl shadow-sm">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Available for payout</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-white tracking-tight">{formatCurrency(balance)}</span>
                  <span className="text-slate-500 font-medium">INR</span>
                </div>
                <div className="mt-6 flex items-center gap-2 text-[11px] text-emerald-500 font-bold bg-emerald-500/5 w-fit px-2.5 py-1 rounded-md border border-emerald-500/10">
                  <ArrowUpRight size={12} />
                  Calculated from 1,204 transactions
                </div>
              </div>
              <div className="bg-[#141415] border border-white/5 p-6 rounded-2xl shadow-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4">
                   <TrendingUp className="text-blue-500/20" size={48} />
                </div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Held in reserve</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-white/40 tracking-tight">₹0</span>
                  <span className="text-slate-500/40 font-medium">INR</span>
                </div>
                <p className="mt-6 text-[11px] text-slate-600 font-medium">No funds currently held by risk engine</p>
              </div>
            </div>

            {/* Transactions Table */}
            <div className="bg-[#141415] border border-white/5 rounded-2xl shadow-sm">
              <div className="p-6 border-b border-white/5 flex items-center justify-between">
                <h3 className="font-bold text-white">Recent activity</h3>
                <div className="flex items-center gap-3">
                  <button className="p-2 hover:bg-white/5 rounded-lg text-slate-400 transition-colors"><Search size={18}/></button>
                  <button className="p-2 hover:bg-white/5 rounded-lg text-slate-400 transition-colors"><Filter size={18}/></button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="text-[11px] text-slate-500 uppercase tracking-wider border-b border-white/5">
                      <th className="px-6 py-4 font-bold">Amount</th>
                      <th className="px-6 py-4 font-bold">Status</th>
                      <th className="px-6 py-4 font-bold">Description</th>
                      <th className="px-6 py-4 font-bold">Date</th>
                      <th className="px-6 py-4"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {transactions.map((tx) => (
                      <tr key={tx.id} className="hover:bg-white/[0.02] transition-colors group cursor-pointer">
                        <td className="px-6 py-4">
                          <span className={`font-bold ${tx.type === 'CREDIT' ? 'text-white' : 'text-white/80'}`}>
                            {tx.type === 'CREDIT' ? '' : '-'}{formatCurrency(tx.amount_paise)}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className={`flex items-center gap-1.5 text-[11px] font-bold ${tx.type === 'CREDIT' ? 'text-emerald-500' : 'text-slate-400'}`}>
                            <div className={`w-1.5 h-1.5 rounded-full ${tx.type === 'CREDIT' ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                            {tx.type === 'CREDIT' ? 'Succeeded' : 'Debit'}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                           <span className="text-xs text-slate-400 font-medium">{tx.description}</span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-xs text-slate-500">{new Date(tx.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <ChevronRight size={16} className="text-slate-700 group-hover:text-slate-400 transition-colors inline" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-4 border-top border-white/5 flex justify-center">
                 <button className="text-[11px] font-bold text-blue-500 hover:text-blue-400 transition-colors uppercase tracking-widest">View all activity</button>
              </div>
            </div>
          </div>

          {/* Right Column: Actions */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Payout Form */}
            <div className="bg-white border border-white/5 p-6 rounded-2xl shadow-xl shadow-blue-500/5">
               <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-blue-600 rounded-lg">
                    <Plus className="text-white" size={20} />
                  </div>
                  <h3 className="text-slate-900 font-bold text-lg">Send a payout</h3>
               </div>
               
               <form onSubmit={handlePayout} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Amount (Paise)</label>
                    <div className="relative">
                      <input 
                        type="number" 
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 font-bold focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all placeholder:text-slate-400"
                        placeholder="0"
                        required
                      />
                      <div className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">INR</div>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Destination Account</label>
                    <input 
                      type="text" 
                      value={bankAccount}
                      onChange={(e) => setBankAccount(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 font-bold focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="ACC_12345678"
                      required
                    />
                  </div>
                  <button 
                    disabled={loading}
                    className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-[0.98] shadow-lg shadow-slate-900/10"
                  >
                    {loading ? <RefreshCcw className="animate-spin" size={18} /> : <Send size={18} />}
                    {loading ? 'Processing...' : 'Send payout'}
                  </button>
               </form>

               {status && (
                <div className={`mt-4 p-4 rounded-xl text-[11px] font-bold flex items-center gap-2 border ${
                  status.type === 'success' ? 'bg-emerald-50 border-emerald-100 text-emerald-600' : 
                  status.type === 'error' ? 'bg-rose-50 border-rose-100 text-rose-600' :
                  'bg-blue-50 border-blue-100 text-blue-600'
                }`}>
                  {status.type === 'success' ? <CheckCircle2 size={16} /> : 
                   status.type === 'error' ? <XCircle size={16} /> : <Clock size={16} />}
                  {status.message}
                </div>
              )}
            </div>

            {/* Quick Tips */}
            <div className="bg-[#141415] border border-white/5 p-6 rounded-2xl">
               <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-4">Security Overview</h4>
               <div className="space-y-4">
                  <div className="flex gap-3">
                    <div className="p-1.5 bg-blue-500/10 rounded-md h-fit"><CreditCard className="text-blue-500" size={14}/></div>
                    <div>
                      <p className="text-xs font-bold text-white mb-0.5">Idempotent Requests</p>
                      <p className="text-[10px] text-slate-500 leading-relaxed">Each request is protected by a unique key to prevent double-charging.</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="p-1.5 bg-emerald-500/10 rounded-md h-fit"><ShieldCheck className="text-emerald-500" size={14}/></div>
                    <div>
                      <p className="text-xs font-bold text-white mb-0.5">Atomic Ledger</p>
                      <p className="text-[10px] text-slate-500 leading-relaxed">Funds are locked and deducted at the database level before processing.</p>
                    </div>
                  </div>
               </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
