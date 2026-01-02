import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Mail, Phone, MapPin, Calendar, Heart, Briefcase, FolderKanban, Clock, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ROLE_LABELS = {
  owner: 'Principal Architect',
  senior_architect: 'Senior Architect',
  senior_interior_designer: 'Senior Interior Designer',
  associate_architect: 'Associate Architect',
  associate_interior_designer: 'Associate Interior Designer',
  junior_architect: 'Junior Architect',
  junior_interior_designer: 'Junior Interior Designer',
  landscape_designer: 'Landscape Designer',
  '3d_visualizer': '3D Visualizer',
  site_engineer: 'Site Engineer',
  site_supervisor: 'Site Supervisor',
  intern: 'Intern',
  administrator: 'Administrator',
  human_resource: 'Human Resource',
  accountant: 'Accountant',
  office_staff: 'Office Staff'
};

export default function TeamMemberDetail({ user, onLogout }) {
  const { memberId } = useParams();
  const navigate = useNavigate();
  const [member, setMember] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingProjects, setLoadingProjects] = useState(true);

  useEffect(() => {
    fetchMemberDetails();
    fetchMemberProjects();
  }, [memberId]);

  const fetchMemberDetails = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      const foundMember = response.data.find(m => m.id === memberId);
      if (foundMember) {
        setMember(foundMember);
      } else {
        toast.error('Team member not found');
        navigate('/team');
      }
    } catch (error) {
      toast.error('Failed to load team member details');
      navigate('/team');
    } finally {
      setLoading(false);
    }
  };

  const fetchMemberProjects = async () => {
    try {
      const response = await axios.get(`${API}/users/${memberId}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to load projects:', error);
      // Don't show error - user may not have permission
    } finally {
      setLoadingProjects(false);
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

  if (!member) {
    return null;
  }

  const activeProjects = projects.filter(p => !p.archived);
  const archivedProjects = projects.filter(p => p.archived);

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-4xl mx-auto">
        {/* Back button */}
        <Button
          variant="ghost"
          onClick={() => navigate('/team')}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Team
        </Button>

        {/* Member Profile */}
        <Card className="mb-6">
          <CardContent className="p-4 sm:p-8">
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-6">
              <div className="w-24 h-24 sm:w-32 sm:h-32 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-white text-3xl sm:text-4xl font-bold flex-shrink-0">
                {member.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 text-center sm:text-left">
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-2">{member.name}</h1>
                <p className="text-base sm:text-lg text-orange-600 font-medium mb-4">
                  {ROLE_LABELS[member.role] || member.role}
                </p>

                {/* Contact Info */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {member.mobile && (
                    <a href={`tel:${member.mobile}`} className="flex items-center justify-center sm:justify-start gap-2 text-slate-600 hover:text-orange-600">
                      <Phone className="w-4 h-4" />
                      <span>{member.mobile}</span>
                    </a>
                  )}
                  {member.email && (
                    <a href={`mailto:${member.email}`} className="flex items-center justify-center sm:justify-start gap-2 text-slate-600 hover:text-orange-600">
                      <Mail className="w-4 h-4" />
                      <span className="truncate">{member.email}</span>
                    </a>
                  )}
                  {member.date_of_joining && (
                    <div className="flex items-center justify-center sm:justify-start gap-2 text-slate-600">
                      <Calendar className="w-4 h-4" />
                      <span>Joined {new Date(member.date_of_joining).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Projects Section - Only visible to owner */}
        {user?.is_owner && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderKanban className="w-5 h-5 text-orange-500" />
                Assigned Projects ({projects.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingProjects ? (
                <div className="text-center py-4">
                  <p className="text-slate-500">Loading projects...</p>
                </div>
              ) : projects.length === 0 ? (
                <div className="text-center py-6 bg-slate-50 rounded-lg">
                  <FolderKanban className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <p className="text-slate-500">No projects assigned as Team Leader</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Active Projects */}
                  {activeProjects.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                        <Clock className="w-4 h-4 text-blue-500" />
                        Active Projects ({activeProjects.length})
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {activeProjects.map(project => (
                          <div
                            key={project.id}
                            onClick={() => navigate(`/projects/${project.id}`)}
                            className="p-3 bg-white border border-slate-200 rounded-lg hover:border-orange-300 hover:shadow-md cursor-pointer transition-all"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <p className="text-xs text-orange-600 font-mono">{project.code}</p>
                                <h5 className="font-medium text-slate-900 truncate">{project.title}</h5>
                                <p className="text-xs text-slate-500 mt-1">
                                  {project.status?.replace(/_/g, ' ') || 'Lead'}
                                </p>
                              </div>
                              {project.pending_drawings_count > 0 && (
                                <span className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded-full">
                                  {project.pending_drawings_count} pending
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                              <span>{project.drawings_count || 0} drawings</span>
                              {project.start_date && (
                                <span>Started {new Date(project.start_date).toLocaleDateString()}</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Archived Projects */}
                  {archivedProjects.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                        Completed Projects ({archivedProjects.length})
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {archivedProjects.map(project => (
                          <div
                            key={project.id}
                            onClick={() => navigate(`/projects/${project.id}`)}
                            className="p-3 bg-slate-50 border border-slate-200 rounded-lg hover:border-slate-300 cursor-pointer transition-all"
                          >
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-slate-500 font-mono">{project.code}</p>
                              <h5 className="font-medium text-slate-700 truncate">{project.title}</h5>
                            </div>
                            <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                              <span>{project.drawings_count || 0} drawings</span>
                              {project.end_date && (
                                <span>Completed {new Date(project.end_date).toLocaleDateString()}</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* About Section */}
        {member.writeup && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>About</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700 whitespace-pre-wrap">{member.writeup}</p>
            </CardContent>
          </Card>
        )}

        {/* Passions & Hobbies */}
        {member.passions && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5 text-orange-500" />
                Passions & Hobbies
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700 whitespace-pre-wrap">{member.passions}</p>
            </CardContent>
          </Card>
        )}

        {/* Contribution */}
        {member.contribution && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-orange-500" />
                Contribution to 4th Dimension
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700 whitespace-pre-wrap">{member.contribution}</p>
            </CardContent>
          </Card>
        )}

        {!member.writeup && !member.passions && !member.contribution && !user?.is_owner && (
          <Card>
            <CardContent className="p-8 text-center">
              <p className="text-slate-500">No additional information available yet.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
