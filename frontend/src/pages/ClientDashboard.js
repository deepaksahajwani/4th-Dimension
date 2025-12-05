import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { 
  FolderOpen, 
  DollarSign, 
  CheckCircle, 
  Clock, 
  TrendingUp,
  Plus,
  FileText 
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ClientDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_mode: 'online',
    payment_date: new Date().toISOString().split('T')[0],
    notes: ''
  });

  useEffect(() => {
    if (user && user.role === 'client') {
      fetchClientData();
    } else {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const fetchClientData = async () => {
    try {
      setLoading(true);

      // Fetch client's projects
      const projectsResponse = await axios.get(`${API}/projects`);
      const clientProjects = projectsResponse.data.filter(p => p.client_id === user.id);
      setProjects(clientProjects);

      // Fetch client's payments
      const paymentsResponse = await axios.get(`${API}/payments/client/${user.id}`);
      setPayments(paymentsResponse.data.payments || []);

    } catch (error) {
      console.error('Error fetching client data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkPayment = (project) => {
    setSelectedProject(project);
    setPaymentDialogOpen(true);
  };

  const handleSubmitPayment = async () => {
    if (!paymentData.amount || parseFloat(paymentData.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      await axios.post(`${API}/payments/client-paid?client_id=${user.id}`, {
        project_id: selectedProject.id,
        amount: parseFloat(paymentData.amount),
        payment_mode: paymentData.payment_mode,
        payment_date: paymentData.payment_date,
        notes: paymentData.notes
      });

      toast.success('Payment notification sent to owner');
      setPaymentDialogOpen(false);
      setPaymentData({
        amount: '',
        payment_mode: 'online',
        payment_date: new Date().toISOString().split('T')[0],
        notes: ''
      });
      fetchClientData(); // Refresh data

    } catch (error) {
      console.error('Error submitting payment:', error);
      toast.error('Failed to submit payment notification');
    }
  };

  const calculateProjectFinancials = (project) => {
    const projectPayments = payments.filter(p => p.project_id === project.id);
    const totalPaid = projectPayments.reduce((sum, p) => sum + (p.amount || 0), 0);
    const totalFees = project.budget || 0;
    const pending = Math.max(0, totalFees - totalPaid);
    
    return { totalPaid, totalFees, pending };
  };

  const getStatusColor = (status) => {
    const colors = {
      'Lead': 'bg-blue-100 text-blue-800',
      'Live': 'bg-green-100 text-green-800',
      'On Hold': 'bg-yellow-100 text-yellow-800',
      'Completed': 'bg-purple-100 text-purple-800',
      'Closed': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-slate-600">Loading your dashboard...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Client Dashboard</h1>
            <p className="text-slate-600 mt-1">Welcome, {user.name}!</p>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Projects</CardTitle>
              <FolderOpen className="h-4 w-4 text-slate-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projects.length}</div>
              <p className="text-xs text-slate-600 mt-1">Active and completed</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Paid</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                ₹{payments.reduce((sum, p) => sum + (p.amount || 0), 0).toLocaleString()}
              </div>
              <p className="text-xs text-slate-600 mt-1">Across all projects</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Projects</CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {projects.filter(p => p.status === 'Live').length}
              </div>
              <p className="text-xs text-slate-600 mt-1">Currently in progress</p>
            </CardContent>
          </Card>
        </div>

        {/* Projects List */}
        <Card>
          <CardHeader>
            <CardTitle>My Projects</CardTitle>
          </CardHeader>
          <CardContent>
            {projects.length === 0 ? (
              <div className="text-center py-12">
                <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-600">No projects yet</p>
              </div>
            ) : (
              <div className="space-y-4">
                {projects.map((project) => {
                  const { totalPaid, totalFees, pending } = calculateProjectFinancials(project);
                  
                  return (
                    <Card key={project.id} className="border-l-4 border-l-blue-500">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-slate-900">{project.title}</h3>
                            <p className="text-sm text-slate-600">{project.code}</p>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                            {project.status}
                          </span>
                        </div>

                        {/* Project Details */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="text-xs text-slate-500">Project Types</p>
                            <p className="text-sm font-medium">
                              {project.project_types?.join(', ') || 'N/A'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500">Start Date</p>
                            <p className="text-sm font-medium">
                              {project.start_date ? new Date(project.start_date).toLocaleDateString() : 'N/A'}
                            </p>
                          </div>
                        </div>

                        {/* Payment Summary */}
                        <div className="bg-slate-50 rounded-lg p-4 mb-4">
                          <h4 className="text-sm font-semibold text-slate-900 mb-3">Payment Summary</h4>
                          <div className="grid grid-cols-3 gap-4">
                            <div>
                              <p className="text-xs text-slate-500">Total Fees</p>
                              <p className="text-lg font-bold text-slate-900">
                                ₹{totalFees.toLocaleString()}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500">Paid</p>
                              <p className="text-lg font-bold text-green-600">
                                ₹{totalPaid.toLocaleString()}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500">Pending</p>
                              <p className="text-lg font-bold text-orange-600">
                                ₹{pending.toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2">
                          <Button
                            onClick={() => navigate(`/projects/${project.id}`)}
                            variant="outline"
                            size="sm"
                            className="flex-1"
                          >
                            <FileText className="w-4 h-4 mr-2" />
                            View Project
                          </Button>
                          <Button
                            onClick={() => handleMarkPayment(project)}
                            size="sm"
                            className="flex-1 bg-green-600 hover:bg-green-700"
                          >
                            <Plus className="w-4 h-4 mr-2" />
                            Mark Payment
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Payment History */}
        {payments.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Payment History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {payments.slice(0, 5).map((payment) => {
                  const project = projects.find(p => p.id === payment.project_id);
                  return (
                    <div key={payment.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-900">
                          {project?.title || 'Project'}
                        </p>
                        <p className="text-xs text-slate-500">
                          {new Date(payment.payment_date).toLocaleDateString()} • {payment.payment_mode}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-green-600">
                          ₹{payment.amount.toLocaleString()}
                        </p>
                        <p className="text-xs text-slate-500">{payment.status}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Mark Payment Dialog */}
        <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Mark Payment Made</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {selectedProject && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                  <p className="text-sm font-medium text-blue-900">{selectedProject.title}</p>
                  <p className="text-xs text-blue-600">{selectedProject.code}</p>
                </div>
              )}

              <div>
                <Label htmlFor="amount">Amount Paid *</Label>
                <input
                  id="amount"
                  type="number"
                  value={paymentData.amount}
                  onChange={(e) => setPaymentData({ ...paymentData, amount: e.target.value })}
                  placeholder="Enter amount"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <Label htmlFor="payment_mode">Payment Mode *</Label>
                <select
                  id="payment_mode"
                  value={paymentData.payment_mode}
                  onChange={(e) => setPaymentData({ ...paymentData, payment_mode: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="cash">Cash</option>
                  <option value="cheque">Cheque</option>
                  <option value="online">Online Transfer</option>
                  <option value="bank_transfer">Bank Transfer</option>
                </select>
              </div>

              <div>
                <Label htmlFor="payment_date">Payment Date *</Label>
                <input
                  id="payment_date"
                  type="date"
                  value={paymentData.payment_date}
                  onChange={(e) => setPaymentData({ ...paymentData, payment_date: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <Label htmlFor="notes">Notes (Optional)</Label>
                <textarea
                  id="notes"
                  value={paymentData.notes}
                  onChange={(e) => setPaymentData({ ...paymentData, notes: e.target.value })}
                  placeholder="Add any notes about this payment"
                  rows={3}
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-xs text-amber-800">
                  ℹ️ The owner will be notified and can verify this payment.
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setPaymentDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSubmitPayment} className="bg-green-600 hover:bg-green-700">
                Submit Payment
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
