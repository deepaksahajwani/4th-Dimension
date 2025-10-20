import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Users, Settings as SettingsIcon } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Role hierarchy for grouping and display order
const ROLE_HIERARCHY = {
  owner: 0,
  senior_architect: 1,
  junior_architect: 2,
  '3d_visualizer': 3,
  senior_interior_designer: 4,
  junior_interior_designer: 5,
  landscape_designer: 6,
  associate_architect: 7,
  associate_interior_designer: 7,
  site_engineer: 8,
  site_supervisor: 8,
  intern: 9,
  administrator: 10,
  human_resource: 10,
  accountant: 10,
  office_staff: 11
};

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

export default function Team({ user, onLogout }) {
  const navigate = useNavigate();
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTeamMembers();
  }, []);

  const fetchTeamMembers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      
      // Separate owner from other members
      const owner = response.data.find(m => m.is_owner || m.email === 'deepaksahajwani@gmail.com');
      const otherMembers = response.data.filter(m => !m.is_owner && m.email !== 'deepaksahajwani@gmail.com');
      
      // Sort other members: first by role hierarchy, then by joining date within each role
      const sortedOthers = otherMembers.sort((a, b) => {
        const roleA = ROLE_HIERARCHY[a.role] || 99;
        const roleB = ROLE_HIERARCHY[b.role] || 99;
        
        // If different roles, sort by role hierarchy
        if (roleA !== roleB) {
          return roleA - roleB;
        }
        
        // Same role - sort by joining date (earliest first)
        const dateA = new Date(a.date_of_joining || a.created_at);
        const dateB = new Date(b.date_of_joining || b.created_at);
        return dateA - dateB;
      });
      
      // Put owner first, then others
      const finalList = owner ? [owner, ...sortedOthers] : sortedOthers;
      setTeamMembers(finalList);
    } catch (error) {
      toast.error('Failed to load team members');
    } finally {
      setLoading(false);
    }
  };

  // Group members by role (each role gets its own row)
  const groupedMembers = teamMembers.reduce((acc, member) => {
    const role = member.role;
    if (!acc[role]) {
      acc[role] = [];
    }
    acc[role].push(member);
    return acc;
  }, {});

  // Sort role groups by hierarchy
  const sortedRoleGroups = Object.keys(groupedMembers).sort((a, b) => {
    return (ROLE_HIERARCHY[a] || 99) - (ROLE_HIERARCHY[b] || 99);
  });

  const handleMemberClick = (memberId) => {
    navigate(`/team/${memberId}`);
  };

  const handleManageTeam = () => {
    navigate('/team/manage');
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <p className="text-slate-500">Loading team...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Our Team</h1>
            <p className="text-slate-600 mt-1">Meet the talented people behind 4th Dimension</p>
          </div>
          {user?.is_owner && (
            <Button onClick={handleManageTeam} className="bg-orange-500 hover:bg-orange-600">
              <SettingsIcon className="w-4 h-4 mr-2" />
              Manage Team
            </Button>
          )}
        </div>

        {/* Team Members Grid */}
        <div className="space-y-8">
          {sortedRoleGroups.map((role) => (
            <div key={role}>
              {/* Role section header (optional - can be removed if you don't want section titles) */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {groupedMembers[role].map((member) => (
                  <Card
                    key={member.id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => handleMemberClick(member.id)}
                  >
                    <CardContent className="p-6 text-center">
                      <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                        {member.name.charAt(0).toUpperCase()}
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-1">
                        {member.name}
                      </h3>
                      <p className="text-sm text-slate-600">
                        {ROLE_LABELS[member.role] || member.role}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>

        {teamMembers.length === 0 && (
          <div className="text-center py-12">
            <Users className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500">No team members yet</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
