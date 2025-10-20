import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Mail, Phone, MapPin, Calendar, Heart, Briefcase } from 'lucide-react';
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMemberDetails();
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
          <CardContent className="p-8">
            <div className="flex items-start gap-6">
              <div className="w-32 h-32 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-white text-4xl font-bold flex-shrink-0">
                {member.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-slate-900 mb-2">{member.name}</h1>
                <p className="text-lg text-orange-600 font-medium mb-4">
                  {ROLE_LABELS[member.role] || member.role}
                </p>

                {/* Contact Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {member.mobile && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Phone className="w-4 h-4" />
                      <span>{member.mobile}</span>
                    </div>
                  )}
                  {member.email && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Mail className="w-4 h-4" />
                      <span>{member.email}</span>
                    </div>
                  )}
                  {member.date_of_joining && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Calendar className="w-4 h-4" />
                      <span>Joined {new Date(member.date_of_joining).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

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

        {!member.writeup && !member.passions && !member.contribution && (
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
