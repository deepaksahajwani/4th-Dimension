import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Mail, Phone, MapPin, FolderOpen, Edit } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ClientDetail({ user, onLogout }) {
  const { clientId } = useParams();
  const navigate = useNavigate();
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClientDetail();
  }, [clientId]);

  const fetchClientDetail = async () => {
    try {
      const response = await axios.get(`${API}/clients/${clientId}`);
      setClient(response.data);
    } catch (error) {
      toast.error('Failed to load client details');
      navigate('/clients');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <p className="text-slate-500">Loading...</p>
        </div>
      </Layout>
    );
  }

  if (!client) {
    return null;
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-6xl mx-auto">
        {/* Back button */}
        <Button
          variant="ghost"
          onClick={() => navigate('/clients')}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Clients
        </Button>

        {/* Client Header */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                  {client.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-slate-900 mb-2">{client.name}</h1>
                  {client.contact_person && (
                    <p className="text-lg text-slate-600 mb-3">{client.contact_person}</p>
                  )}
                  
                  <div className="flex flex-wrap gap-4 text-sm">
                    {client.phone && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <Phone className="w-4 h-4" />
                        <span>{client.phone}</span>
                      </div>
                    )}
                    {client.email && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <Mail className="w-4 h-4" />
                        <span>{client.email}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => navigate('/clients', { state: { editClientId: clientId } })}
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </Button>
            </div>

            {client.address && (
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-start gap-2 text-slate-600">
                  <MapPin className="w-4 h-4 mt-1" />
                  <span>{client.address}</span>
                </div>
              </div>
            )}

            {client.notes && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-slate-600 italic">{client.notes}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Related Projects */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-orange-500" />
              Projects ({client.projects?.length || 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {client.projects && client.projects.length > 0 ? (
              <div className="space-y-3">
                {client.projects.map((project) => (
                  <div
                    key={project.id}
                    className="p-4 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-sm font-medium text-orange-600">
                            {project.code}
                          </span>
                          <h3 className="font-semibold text-slate-900">{project.title}</h3>
                        </div>
                        <div className="flex gap-3 mt-2 text-sm text-slate-600">
                          <span className="capitalize">{project.type}</span>
                          <span>•</span>
                          <span className="capitalize">{project.status?.replace('_', ' ')}</span>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        View →
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                <p>No projects yet for this client</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
