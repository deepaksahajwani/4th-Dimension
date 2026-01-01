import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  CheckCircle2, 
  XCircle, 
  MessageSquare, 
  Mail, 
  Phone, 
  Bell,
  RefreshCw,
  Filter,
  AlertTriangle,
  Clock,
  TrendingUp,
  Server
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function SystemLogs({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [failures, setFailures] = useState(null);
  const [logs, setLogs] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [filters, setFilters] = useState({
    channel: '',
    success: '',
    hours: 24
  });

  useEffect(() => {
    fetchData();
  }, [filters.hours]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [statusRes, statsRes, failuresRes, logsRes] = await Promise.all([
        axios.get(`${API}/ops/status`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/ops/logs/notifications/stats?hours=${filters.hours}`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/ops/logs/notifications/failures?hours=${filters.hours}`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/ops/logs/notifications?limit=100`, { headers }).catch(() => ({ data: { logs: [] } }))
      ]);

      setSystemStatus(statusRes.data);
      setStats(statsRes.data);
      setFailures(failuresRes.data);
      setLogs(logsRes.data?.logs || []);
    } catch (error) {
      console.error('Error fetching logs:', error);
      toast.error('Failed to fetch system logs');
    } finally {
      setLoading(false);
    }
  };

  const getChannelIcon = (channel) => {
    switch (channel) {
      case 'whatsapp':
      case 'whatsapp_template':
        return <MessageSquare className="w-4 h-4 text-green-600" />;
      case 'sms':
        return <Phone className="w-4 h-4 text-blue-600" />;
      case 'email':
        return <Mail className="w-4 h-4 text-purple-600" />;
      case 'in_app':
        return <Bell className="w-4 h-4 text-orange-600" />;
      default:
        return <Activity className="w-4 h-4 text-slate-600" />;
    }
  };

  const getChannelBadge = (channel) => {
    const colors = {
      whatsapp: 'bg-green-100 text-green-700 border-green-200',
      whatsapp_template: 'bg-green-100 text-green-700 border-green-200',
      sms: 'bg-blue-100 text-blue-700 border-blue-200',
      email: 'bg-purple-100 text-purple-700 border-purple-200',
      in_app: 'bg-orange-100 text-orange-700 border-orange-200'
    };
    return colors[channel] || 'bg-slate-100 text-slate-700 border-slate-200';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading && !stats) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-orange-500" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">System Logs</h1>
            <p className="text-slate-600 mt-1">Monitor notifications and system health</p>
          </div>
          <div className="flex gap-2">
            <select
              value={filters.hours}
              onChange={(e) => setFilters({ ...filters, hours: parseInt(e.target.value) })}
              className="border rounded-md px-3 py-2 text-sm"
            >
              <option value={1}>Last 1 hour</option>
              <option value={6}>Last 6 hours</option>
              <option value={24}>Last 24 hours</option>
              <option value={72}>Last 3 days</option>
              <option value={168}>Last 7 days</option>
            </select>
            <Button onClick={fetchData} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="failures">Failures</TabsTrigger>
            <TabsTrigger value="system">System Status</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* Total Sent */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Total Sent</p>
                      <p className="text-3xl font-bold text-slate-900">
                        {failures?.total_sent || 0}
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-blue-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Success Rate */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Success Rate</p>
                      <p className="text-3xl font-bold text-green-600">
                        {failures?.success_rate || 100}%
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Failed */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Failed</p>
                      <p className="text-3xl font-bold text-red-600">
                        {failures?.total_failed || 0}
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                      <XCircle className="w-6 h-6 text-red-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Period */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Period</p>
                      <p className="text-3xl font-bold text-slate-900">
                        {filters.hours}h
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center">
                      <Clock className="w-6 h-6 text-slate-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Stats by Channel */}
            {stats?.by_channel && stats.by_channel.length > 0 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="text-lg">By Channel</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {stats.by_channel.map((stat) => (
                      <div 
                        key={stat._id} 
                        className="p-4 bg-slate-50 rounded-lg border"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          {getChannelIcon(stat._id)}
                          <span className="font-medium capitalize">{stat._id?.replace('_', ' ')}</span>
                        </div>
                        <div className="text-2xl font-bold">{stat.total}</div>
                        <div className="flex gap-2 text-sm mt-1">
                          <span className="text-green-600">✓ {stat.success}</span>
                          <span className="text-red-600">✗ {stat.failed}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Recent Notifications
                </CardTitle>
              </CardHeader>
              <CardContent>
                {logs.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <Bell className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>No notification logs found</p>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[600px] overflow-y-auto">
                    {logs.map((log, idx) => (
                      <div 
                        key={log.id || idx}
                        className={`p-4 rounded-lg border ${
                          log.success ? 'bg-white' : 'bg-red-50 border-red-200'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            {log.success ? (
                              <CheckCircle2 className="w-5 h-5 text-green-500" />
                            ) : (
                              <XCircle className="w-5 h-5 text-red-500" />
                            )}
                            <div>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className={getChannelBadge(log.channel)}>
                                  {getChannelIcon(log.channel)}
                                  <span className="ml-1 capitalize">{log.channel?.replace('_', ' ')}</span>
                                </Badge>
                                <span className="text-sm text-slate-500">
                                  {log.notification_type?.replace(/_/g, ' ')}
                                </span>
                              </div>
                              <p className="text-sm mt-1">
                                <span className="text-slate-600">To:</span> {log.recipient}
                              </p>
                              {log.subject && (
                                <p className="text-sm text-slate-500 mt-1">
                                  {log.subject}
                                </p>
                              )}
                              {!log.success && log.error_message && (
                                <p className="text-sm text-red-600 mt-2 bg-red-100 px-2 py-1 rounded">
                                  ⚠️ {log.error_message}
                                </p>
                              )}
                            </div>
                          </div>
                          <span className="text-xs text-slate-400">
                            {formatTimestamp(log.created_at)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Failures Tab */}
          <TabsContent value="failures">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  Failure Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                {failures?.failures_by_channel && failures.failures_by_channel.length > 0 ? (
                  <div className="space-y-4">
                    {failures.failures_by_channel.map((failure, idx) => (
                      <div 
                        key={idx}
                        className="p-4 bg-red-50 rounded-lg border border-red-200"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline" className="bg-red-100 text-red-700 border-red-300">
                                {failure._id?.channel || 'Unknown'}
                              </Badge>
                              {failure._id?.error_code && (
                                <Badge variant="outline" className="bg-slate-100">
                                  Error: {failure._id.error_code}
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-red-700 font-medium">
                              {failure.last_error || 'Unknown error'}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="text-2xl font-bold text-red-600">{failure.count}</span>
                            <p className="text-xs text-slate-500">occurrences</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <CheckCircle2 className="w-12 h-12 mx-auto mb-4 text-green-300" />
                    <p>No failures in the selected period 🎉</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Status Tab */}
          <TabsContent value="system">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Service Status */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Server className="w-5 h-5" />
                    Service Status
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {systemStatus?.services ? (
                    <div className="space-y-4">
                      {/* Twilio Status */}
                      <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <MessageSquare className="w-5 h-5 text-green-600" />
                          <div>
                            <p className="font-medium">Twilio (WhatsApp/SMS)</p>
                            <p className="text-xs text-slate-500">
                              WhatsApp: {systemStatus.services.twilio?.whatsapp_enabled ? '✓' : '✗'} | 
                              SMS: {systemStatus.services.twilio?.sms_enabled ? '✓' : '✗'}
                            </p>
                          </div>
                        </div>
                        <Badge className={systemStatus.services.twilio?.configured 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                        }>
                          {systemStatus.services.twilio?.configured ? 'Connected' : 'Not Configured'}
                        </Badge>
                      </div>

                      {/* SendGrid Status */}
                      <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <Mail className="w-5 h-5 text-purple-600" />
                          <div>
                            <p className="font-medium">SendGrid (Email)</p>
                            <p className="text-xs text-slate-500">
                              From: {systemStatus.services.sendgrid?.sender_email}
                            </p>
                          </div>
                        </div>
                        <Badge className={systemStatus.services.sendgrid?.configured 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                        }>
                          {systemStatus.services.sendgrid?.configured ? 'Connected' : 'Not Configured'}
                        </Badge>
                      </div>

                      {/* Database Status */}
                      <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <Server className="w-5 h-5 text-blue-600" />
                          <div>
                            <p className="font-medium">MongoDB</p>
                            <p className="text-xs text-slate-500">
                              Database: {systemStatus.services.database?.database}
                            </p>
                          </div>
                        </div>
                        <Badge className="bg-green-100 text-green-700">
                          Connected
                        </Badge>
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-500">Unable to fetch system status</p>
                  )}
                </CardContent>
              </Card>

              {/* Quick Stats */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Notification Types</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats?.by_type && stats.by_type.length > 0 ? (
                    <div className="space-y-2 max-h-[300px] overflow-y-auto">
                      {stats.by_type.map((stat, idx) => (
                        <div 
                          key={idx}
                          className="flex items-center justify-between p-2 hover:bg-slate-50 rounded"
                        >
                          <span className="text-sm capitalize">
                            {stat._id?.replace(/_/g, ' ') || 'Unknown'}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">{stat.total}</span>
                            <Badge variant="outline" className="text-xs">
                              {Math.round((stat.success / stat.total) * 100)}% success
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500">No data available</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
