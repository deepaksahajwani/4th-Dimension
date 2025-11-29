import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import Layout from '../components/Layout';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Plus,
  FileText
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function Accounting({ user, onLogout }) {
  const [summary, setSummary] = useState(null);
  const [incomeRecords, setIncomeRecords] = useState([]);
  const [incomeAccounts, setIncomeAccounts] = useState([]);
  const [incomeEntries, setIncomeEntries] = useState([]);
  const [expenseAccounts, setExpenseAccounts] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [activeTab, setActiveTab] = useState('income');
  
  // Dialogs
  const [incomeDialogOpen, setIncomeDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [paymentHistoryDialogOpen, setPaymentHistoryDialogOpen] = useState(false);
  const [incomeAccountDialogOpen, setIncomeAccountDialogOpen] = useState(false);
  const [incomeEntryDialogOpen, setIncomeEntryDialogOpen] = useState(false);
  const [expenseAccountDialogOpen, setExpenseAccountDialogOpen] = useState(false);
  const [expenseDialogOpen, setExpenseDialogOpen] = useState(false);
  const [selectedProjectPayments, setSelectedProjectPayments] = useState([]);
  
  // Forms
  const [incomeForm, setIncomeForm] = useState({
    total_fee: '',
    received_amount: '',
    notes: ''
  });
  const [paymentForm, setPaymentForm] = useState({
    amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_mode: 'Bank Transfer',
    bank_account: '',
    reference_number: '',
    notes: ''
  });
  const [incomeAccountForm, setIncomeAccountForm] = useState({
    name: '',
    description: ''
  });
  const [incomeEntryForm, setIncomeEntryForm] = useState({
    income_account_id: '',
    amount: '',
    income_date: new Date().toISOString().split('T')[0],
    description: '',
    payment_mode: 'Bank Transfer',
    bank_account: '',
    reference_number: '',
    source_name: '',
    notes: ''
  });
  const [expenseAccountForm, setExpenseAccountForm] = useState({
    name: '',
    description: ''
  });
  const [expenseForm, setExpenseForm] = useState({
    expense_account_id: '',
    amount: '',
    expense_date: new Date().toISOString().split('T')[0],
    description: '',
    payment_mode: 'Bank Transfer',
    bank_account: '',
    reference_number: '',
    vendor_name: '',
    project_id: '',
    notes: ''
  });

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [summaryRes, incomeRes, incomeAccountsRes, incomeEntriesRes, expenseAccountsRes, expensesRes, projectsRes] = await Promise.all([
        axios.get(`${API}/api/accounting/summary`, { headers }),
        axios.get(`${API}/api/accounting/income`, { headers }),
        axios.get(`${API}/api/accounting/income-accounts`, { headers }),
        axios.get(`${API}/api/accounting/income-entries`, { headers }),
        axios.get(`${API}/api/accounting/expense-accounts`, { headers }),
        axios.get(`${API}/api/accounting/expenses`, { headers }),
        axios.get(`${API}/api/projects`, { headers })
      ]);

      setSummary(summaryRes.data);
      setIncomeRecords(incomeRes.data);
      setIncomeAccounts(incomeAccountsRes.data);
      setIncomeEntries(incomeEntriesRes.data);
      setExpenseAccounts(expenseAccountsRes.data);
      setExpenses(expensesRes.data);
      setProjects(projectsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching accounting data:', error);
      toast.error('Failed to load accounting data');
      setLoading(false);
    }
  };

  const handleUpdateIncome = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/api/accounting/income/${selectedProject.id}`,
        incomeForm,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Income updated successfully');
      setIncomeDialogOpen(false);
      fetchAllData();
    } catch (error) {
      console.error('Error updating income:', error);
      toast.error('Failed to update income');
    }
  };

  const handleAddPayment = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/api/accounting/income/${selectedProject.id}/payment`,
        paymentForm,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Payment added successfully');
      setPaymentDialogOpen(false);
      setPaymentForm({
        amount: '',
        payment_date: new Date().toISOString().split('T')[0],
        payment_mode: 'Bank Transfer',
        bank_account: '',
        reference_number: '',
        notes: ''
      });
      fetchAllData();
    } catch (error) {
      console.error('Error adding payment:', error);
      toast.error('Failed to add payment');
    }
  };

  const handleCreateIncomeAccount = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/api/accounting/income-accounts`,
        incomeAccountForm,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Income account created successfully');
      setIncomeAccountDialogOpen(false);
      setIncomeAccountForm({ name: '', description: '' });
      fetchAllData();
    } catch (error) {
      console.error('Error creating income account:', error);
      toast.error('Failed to create income account');
    }
  };

  const handleCreateIncomeEntry = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/api/accounting/income-entries`,
        incomeEntryForm,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Income entry added successfully');
      setIncomeEntryDialogOpen(false);
      setIncomeEntryForm({
        income_account_id: '',
        amount: '',
        income_date: new Date().toISOString().split('T')[0],
        description: '',
        payment_mode: 'Bank Transfer',
        bank_account: '',
        reference_number: '',
        source_name: '',
        notes: ''
      });
      fetchAllData();
    } catch (error) {
      console.error('Error creating income entry:', error);
      toast.error('Failed to create income entry');
    }
  };

  const handleCreateExpenseAccount = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/api/accounting/expense-accounts`,
        expenseAccountForm,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Expense account created successfully');
      setExpenseAccountDialogOpen(false);
      setExpenseAccountForm({ name: '', description: '' });
      fetchAllData();
    } catch (error) {
      console.error('Error creating expense account:', error);
      toast.error('Failed to create expense account');
    }
  };

  const handleViewPaymentHistory = async (project) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/api/accounting/income/${project.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setSelectedProject(project);
      setSelectedProjectPayments(response.data.payments || []);
      setPaymentHistoryDialogOpen(true);
    } catch (error) {
      console.error('Error fetching payment history:', error);
      toast.error('Failed to load payment history');
    }
  };

  const handleCreateExpense = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/api/accounting/expenses`,
        expenseForm,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Expense added successfully');
      setExpenseDialogOpen(false);
      setExpenseForm({
        expense_account_id: '',
        amount: '',
        expense_date: new Date().toISOString().split('T')[0],
        description: '',
        payment_mode: 'Bank Transfer',
        bank_account: '',
        reference_number: '',
        vendor_name: '',
        project_id: '',
        notes: ''
      });
      fetchAllData();
    } catch (error) {
      console.error('Error creating expense:', error);
      toast.error('Failed to create expense');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-600">Loading accounting data...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900">Accounting</h1>
          <p className="text-slate-600 mt-1">Manage income and expenses</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Total Fees</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(summary?.income?.total_fee)}
                </p>
              </div>
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Received</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(summary?.income?.received)}
                </p>
              </div>
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Pending</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatCurrency(summary?.income?.pending)}
                </p>
              </div>
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-orange-600" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Total Expenses</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatCurrency(summary?.expenses?.total)}
                </p>
              </div>
              <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <TrendingDown className="w-5 h-5 text-red-600" />
              </div>
            </div>
          </Card>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-slate-200">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('income')}
              className={`px-4 py-3 font-medium border-b-2 transition-colors ${
                activeTab === 'income'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              Income & Fees
            </button>
            <button
              onClick={() => setActiveTab('expenses')}
              className={`px-4 py-3 font-medium border-b-2 transition-colors ${
                activeTab === 'expenses'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              Expenses
            </button>
          </div>
        </div>

        {/* Income Tab */}
        {activeTab === 'income' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-slate-900">Project Fees</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => {
                const income = incomeRecords.find(r => r.project_id === project.id);
                const totalFee = income?.total_fee || 0;
                const received = income?.received_amount || 0;
                const pending = totalFee - received;

                return (
                  <Card key={project.id} className="p-4 hover:shadow-md transition-shadow">
                    <h3 className="font-semibold text-slate-900 mb-2">{project.title}</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Total Fee:</span>
                        <span className="font-medium">{formatCurrency(totalFee)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Received:</span>
                        <span className="font-medium text-green-600">{formatCurrency(received)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Pending:</span>
                        <span className="font-medium text-orange-600">{formatCurrency(pending)}</span>
                      </div>
                    </div>
                    <div className="space-y-2 mt-4">
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1"
                          onClick={() => {
                            setSelectedProject(project);
                            setIncomeForm({
                              total_fee: totalFee || '',
                              received_amount: received || '',
                              notes: income?.notes || ''
                            });
                            setIncomeDialogOpen(true);
                          }}
                        >
                          Edit Fees
                        </Button>
                        {pending > 0 && (
                          <Button
                            size="sm"
                            className="flex-1"
                            onClick={() => {
                              setSelectedProject(project);
                              setPaymentDialogOpen(true);
                            }}
                          >
                            Add Payment
                          </Button>
                        )}
                      </div>
                      {received > 0 && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-full"
                          onClick={() => handleViewPaymentHistory(project)}
                        >
                          <FileText className="w-4 h-4 mr-2" />
                          Payment History
                        </Button>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Expenses Tab */}
        {activeTab === 'expenses' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-slate-900">Expense Accounts</h2>
              <Button onClick={() => setExpenseAccountDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                New Account
              </Button>
            </div>

            {/* Expense Accounts */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {expenseAccounts.map((account) => (
                <Card key={account.id} className="p-4">
                  <h3 className="font-semibold text-slate-900 mb-1">{account.name}</h3>
                  {account.description && (
                    <p className="text-sm text-slate-600 mb-2">{account.description}</p>
                  )}
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency(account.total_expenses)}
                  </p>
                </Card>
              ))}
            </div>

            {/* Add Expense Button */}
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-slate-900">Recent Expenses</h2>
              <Button onClick={() => setExpenseDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Expense
              </Button>
            </div>

            {/* Expenses List */}
            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Date</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Description</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Account</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Vendor</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-slate-600">Amount</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Mode</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {expenses.map((expense) => (
                      <tr key={expense.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 text-sm text-slate-900">
                          {new Date(expense.expense_date).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-900">{expense.description}</td>
                        <td className="px-4 py-3 text-sm text-slate-600">{expense.expense_account_name}</td>
                        <td className="px-4 py-3 text-sm text-slate-600">{expense.vendor_name || '-'}</td>
                        <td className="px-4 py-3 text-sm font-medium text-red-600 text-right">
                          {formatCurrency(expense.amount)}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-600">{expense.payment_mode}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* Income Dialog */}
        <Dialog open={incomeDialogOpen} onOpenChange={setIncomeDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Update Project Fees - {selectedProject?.title}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Total Fee</Label>
                <input
                  type="number"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={incomeForm.total_fee}
                  onChange={(e) => setIncomeForm({...incomeForm, total_fee: e.target.value})}
                />
              </div>
              <div>
                <Label>Received Amount</Label>
                <input
                  type="number"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={incomeForm.received_amount}
                  onChange={(e) => setIncomeForm({...incomeForm, received_amount: e.target.value})}
                />
              </div>
              <div>
                <Label>Notes</Label>
                <textarea
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  rows="3"
                  value={incomeForm.notes}
                  onChange={(e) => setIncomeForm({...incomeForm, notes: e.target.value})}
                />
              </div>
              <Button onClick={handleUpdateIncome} className="w-full">
                Update Fees
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Payment Dialog */}
        <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Add Payment - {selectedProject?.title}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Amount</Label>
                <input
                  type="number"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={paymentForm.amount}
                  onChange={(e) => setPaymentForm({...paymentForm, amount: e.target.value})}
                />
              </div>
              <div>
                <Label>Payment Date</Label>
                <input
                  type="date"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={paymentForm.payment_date}
                  onChange={(e) => setPaymentForm({...paymentForm, payment_date: e.target.value})}
                />
              </div>
              <div>
                <Label>Payment Mode</Label>
                <select
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={paymentForm.payment_mode}
                  onChange={(e) => setPaymentForm({...paymentForm, payment_mode: e.target.value})}
                >
                  <option>Cash</option>
                  <option>Bank Transfer</option>
                  <option>Cheque</option>
                  <option>UPI</option>
                  <option>Card</option>
                  <option>Other</option>
                </select>
              </div>
              <div>
                <Label>Bank Account / Reference</Label>
                <input
                  type="text"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  placeholder="Account or reference number"
                  value={paymentForm.reference_number}
                  onChange={(e) => setPaymentForm({...paymentForm, reference_number: e.target.value})}
                />
              </div>
              <Button onClick={handleAddPayment} className="w-full">
                Add Payment
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Expense Account Dialog */}
        <Dialog open={expenseAccountDialogOpen} onOpenChange={setExpenseAccountDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Create Expense Account</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Account Name</Label>
                <input
                  type="text"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={expenseAccountForm.name}
                  onChange={(e) => setExpenseAccountForm({...expenseAccountForm, name: e.target.value})}
                  placeholder="e.g., Office Supplies, Travel, Salaries"
                />
              </div>
              <div>
                <Label>Description</Label>
                <textarea
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  rows="3"
                  value={expenseAccountForm.description}
                  onChange={(e) => setExpenseAccountForm({...expenseAccountForm, description: e.target.value})}
                />
              </div>
              <Button onClick={handleCreateExpenseAccount} className="w-full">
                Create Account
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Expense Dialog */}
        <Dialog open={expenseDialogOpen} onOpenChange={setExpenseDialogOpen}>
          <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add Expense</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Expense Account *</Label>
                <select
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={expenseForm.expense_account_id}
                  onChange={(e) => setExpenseForm({...expenseForm, expense_account_id: e.target.value})}
                >
                  <option value="">Select Account</option>
                  {expenseAccounts.map((account) => (
                    <option key={account.id} value={account.id}>{account.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Amount *</Label>
                <input
                  type="number"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={expenseForm.amount}
                  onChange={(e) => setExpenseForm({...expenseForm, amount: e.target.value})}
                />
              </div>
              <div>
                <Label>Expense Date *</Label>
                <input
                  type="date"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={expenseForm.expense_date}
                  onChange={(e) => setExpenseForm({...expenseForm, expense_date: e.target.value})}
                />
              </div>
              <div>
                <Label>Description *</Label>
                <textarea
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  rows="2"
                  value={expenseForm.description}
                  onChange={(e) => setExpenseForm({...expenseForm, description: e.target.value})}
                />
              </div>
              <div>
                <Label>Payment Mode</Label>
                <select
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={expenseForm.payment_mode}
                  onChange={(e) => setExpenseForm({...expenseForm, payment_mode: e.target.value})}
                >
                  <option>Cash</option>
                  <option>Bank Transfer</option>
                  <option>Cheque</option>
                  <option>UPI</option>
                  <option>Card</option>
                  <option>Other</option>
                </select>
              </div>
              <div>
                <Label>Vendor Name</Label>
                <input
                  type="text"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={expenseForm.vendor_name}
                  onChange={(e) => setExpenseForm({...expenseForm, vendor_name: e.target.value})}
                />
              </div>
              <div>
                <Label>Link to Project (Optional)</Label>
                <select
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={expenseForm.project_id}
                  onChange={(e) => setExpenseForm({...expenseForm, project_id: e.target.value})}
                >
                  <option value="">None</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>{project.title}</option>
                  ))}
                </select>
              </div>
              <Button onClick={handleCreateExpense} className="w-full">
                Add Expense
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Payment History Dialog */}
        <Dialog open={paymentHistoryDialogOpen} onOpenChange={setPaymentHistoryDialogOpen}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Payment History - {selectedProject?.title}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {selectedProjectPayments.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p>No payment history yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {selectedProjectPayments.sort((a, b) => 
                    new Date(b.payment_date) - new Date(a.payment_date)
                  ).map((payment, index) => (
                    <Card key={payment.id || index} className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-medium text-lg text-green-600">
                            {formatCurrency(payment.amount)}
                          </p>
                          <p className="text-sm text-slate-600">
                            {new Date(payment.payment_date).toLocaleDateString('en-IN', {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric'
                            })}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-slate-900">{payment.payment_mode}</p>
                          {payment.reference_number && (
                            <p className="text-xs text-slate-500">Ref: {payment.reference_number}</p>
                          )}
                        </div>
                      </div>
                      {payment.bank_account && (
                        <p className="text-sm text-slate-600">Bank: {payment.bank_account}</p>
                      )}
                      {payment.notes && (
                        <p className="text-sm text-slate-600 mt-2 italic">{payment.notes}</p>
                      )}
                    </Card>
                  ))}
                </div>
              )}
              
              <div className="border-t pt-4 mt-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-slate-900">Total Received:</span>
                  <span className="text-xl font-bold text-green-600">
                    {formatCurrency(
                      selectedProjectPayments.reduce((sum, p) => sum + (p.amount || 0), 0)
                    )}
                  </span>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
