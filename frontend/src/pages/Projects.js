import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, FolderOpen, Calendar, Archive } from 'lucide-react';
import { toast } from 'sonner';
import { formatErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PROJECT_TYPES = ['Architecture', 'Interior', 'Landscape', 'Planning'];

export default function Projects({ user, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [projects, setProjects] = useState([]);
  const [clients, setClients] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [archiveConfirmOpen, setArchiveConfirmOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');
  
  const [formData, setFormData] = useState({
    code: '',
    title: '',
    project_types: [],
    status: 'Lead',
    client_id: '',
    team_leader_id: '',
    project_manager_id: '',
    lead_architect_id: '',
    start_date: '',
    end_date: '',
    site_address: '',
    notes: '',
    // Fixed Contractors/Consultants/Suppliers
    civil_contractor: { name: '', email: '', phone: '' },
    structural_consultant: { name: '', email: '', phone: '' },
    tile_marble_contractor: { name: '', email: '', phone: '' },
    furniture_contractor: { name: '', email: '', phone: '' },
    electrical_contractor: { name: '', email: '', phone: '' },
    electrical_consultant: { name: '', email: '', phone: '' },
    plumbing_consultant: { name: '', email: '', phone: '' },
    plumbing_contractor: { name: '', email: '', phone: '' },
    false_ceiling_contractor: { name: '', email: '', phone: '' },
    furniture_material_supplier: { name: '', email: '', phone: '' },
    kitchen_contractor: { name: '', email: '', phone: '' },
    modular_contractor: { name: '', email: '', phone: '' },
    color_contractor: { name: '', email: '', phone: '' },
    landscape_consultant: { name: '', email: '', phone: '' },
    landscape_contractor: { name: '', email: '', phone: '' },
    automation_consultant: { name: '', email: '', phone: '' },
    readymade_furniture_supplier: { name: '', email: '', phone: '' },
    lights_supplier: { name: '', email: '', phone: '' },
    // Custom contacts
    custom_contacts: {},
    brands: []
  });

  const [contactTypes, setContactTypes] = useState([]);
  const [showAddContactType, setShowAddContactType] = useState(false);
  const [newContactTypeName, setNewContactTypeName] = useState('');
  const [contractors, setContractors] = useState([]);
  const [consultants, setConsultants] = useState([]);
  const [assignedContractors, setAssignedContractors] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  // Handle edit project from location state
  useEffect(() => {
    if (location.state?.editProjectId && projects.length > 0) {
      const projectToEdit = projects.find(p => p.id === location.state.editProjectId);
      if (projectToEdit) {
        openEditDialog(projectToEdit);
        // Clear the location state
        navigate(location.pathname, { replace: true, state: {} });
      }
    }
  }, [location.state, projects]);

  const fetchData = async () => {
    try {
      const [projectsRes, clientsRes, contactTypesRes, teamRes, contractorsRes, consultantsRes] = await Promise.all([
        axios.get(`${API}/projects`).catch(() => ({ data: [] })),
        axios.get(`${API}/clients`).catch(() => ({ data: [] })),
        axios.get(`${API}/contact-types`).catch(() => ({ data: [] })),
        axios.get(`${API}/users`).catch(() => ({ data: [] })),
        axios.get(`${API}/contractors`).catch(() => ({ data: [] })),
        axios.get(`${API}/consultants`).catch(() => ({ data: [] }))
      ]);
      setProjects(projectsRes.data || []);
      setClients(clientsRes.data || []);
      setContactTypes(contactTypesRes.data || []);
      setTeamMembers(teamRes.data || []);
      setContractors(contractorsRes.data || []);
      setConsultants(consultantsRes.data || []);
    } catch (error) {
      console.error('Error fetching projects data:', error);
      // Don't show error toast - let empty states handle it
      setProjects([]);
      setClients([]);
      setContactTypes([]);
      setTeamMembers([]);
      setContractors([]);
      setConsultants([]);
    } finally {
      setLoading(false);
    }
  };

  const handleProjectTypeToggle = (type) => {
    const currentTypes = formData.project_types || [];
    if (currentTypes.includes(type)) {
      setFormData({ 
        ...formData, 
        project_types: currentTypes.filter(t => t !== type) 
      });
    } else {
      setFormData({ 
        ...formData, 
        project_types: [...currentTypes, type] 
      });
    }
  };

  const updateContactField = (contactType, field, value) => {
    setFormData({
      ...formData,
      [contactType]: {
        ...formData[contactType],
        [field]: value
      }
    });
  };

  const updateCustomContactField = (typeId, field, value) => {
    setFormData({
      ...formData,
      custom_contacts: {
        ...formData.custom_contacts,
        [typeId]: {
          ...formData.custom_contacts[typeId],
          [field]: value
        }
      }
    });
  };

  const handleAddContactType = async () => {
    if (!newContactTypeName.trim()) {
      toast.error('Please enter a contact type name');
      return;
    }
    
    try {
      await axios.post(`${API}/contact-types`, { type_name: newContactTypeName });
      toast.success('Contact type added successfully!');
      setNewContactTypeName('');
      setShowAddContactType(false);
      // Refresh contact types
      const contactTypesRes = await axios.get(`${API}/contact-types`);
      setContactTypes(contactTypesRes.data);
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to add contact type'));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Clean up empty contacts
      const cleanedData = { ...formData };
      
      // Convert empty string IDs to null
      if (cleanedData.lead_architect_id === '') {
        cleanedData.lead_architect_id = null;
      }
      if (cleanedData.project_manager_id === '') {
        cleanedData.project_manager_id = null;
      }
      
      // Remove empty contact objects
      const contactFields = [
        'civil_contractor', 'structural_consultant', 'tile_marble_contractor', 'furniture_contractor',
        'electrical_contractor', 'electrical_consultant', 'plumbing_consultant',
        'plumbing_contractor', 'false_ceiling_contractor', 'furniture_material_supplier',
        'kitchen_contractor', 'modular_contractor', 'color_contractor',
        'landscape_consultant', 'landscape_contractor', 'automation_consultant',
        'readymade_furniture_supplier', 'lights_supplier'
      ];

      contactFields.forEach(field => {
        const contact = cleanedData[field];
        if (!contact.name && !contact.email && !contact.phone) {
          cleanedData[field] = null;
        }
      });

      // Clean up empty custom contacts
      const customContacts = {};
      Object.entries(cleanedData.custom_contacts || {}).forEach(([typeId, contact]) => {
        if (contact.name || contact.email || contact.phone) {
          customContacts[typeId] = contact;
        }
      });
      cleanedData.custom_contacts = customContacts;
      
      // Add assigned contractors
      cleanedData.assigned_contractors = assignedContractors;

      if (editingProject) {
        // Check if end date was added during edit
        const wasArchived = editingProject.archived;
        const hasNewEndDate = cleanedData.end_date && !editingProject.end_date;
        
        if (hasNewEndDate && !wasArchived) {
          // Show confirmation dialog for archiving
          setArchiveConfirmOpen(true);
          return;
        }
        
        await axios.put(`${API}/projects/${editingProject.id}`, cleanedData);
        toast.success('Project updated successfully!');
      } else {
        await axios.post(`${API}/projects`, cleanedData);
        toast.success('Project created successfully!');
      }
      
      setDialogOpen(false);
      setArchiveConfirmOpen(false);
      resetForm();
      setEditingProject(null);
      fetchData();
    } catch (error) {
      toast.error(formatErrorMessage(error, editingProject ? 'Failed to update project' : 'Failed to create project'));
    }
  };

  const handleArchiveConfirm = async () => {
    try {
      const cleanedData = { ...formData };
      cleanedData.archived = true;
      
      await axios.put(`${API}/projects/${editingProject.id}`, cleanedData);
      toast.success('Project updated and archived successfully!');
      
      setDialogOpen(false);
      setArchiveConfirmOpen(false);
      resetForm();
      setEditingProject(null);
      fetchData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to update project'));
    }
  };

  const handleUpdateWithoutArchive = async () => {
    try {
      setArchiveConfirmOpen(false);
      const cleanedData = { ...formData };
      if (cleanedData.lead_architect_id === '') {
        cleanedData.lead_architect_id = null;
      }
      if (cleanedData.project_manager_id === '') {
        cleanedData.project_manager_id = null;
      }
      
      await axios.put(`${API}/projects/${editingProject.id}`, cleanedData);
      toast.success('Project updated successfully!');
      setDialogOpen(false);
      resetForm();
      setEditingProject(null);
      fetchData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to update project'));
    }
  };

  const openEditDialog = (project) => {
    setEditingProject(project);
    
    // Populate assigned contractors state with existing data
    setAssignedContractors(project.assigned_contractors || {});
    
    setFormData({
      code: project.code || '',
      title: project.title || '',
      project_types: project.project_types || [],
      status: project.status || 'Lead',
      client_id: project.client_id || '',
      project_manager_id: project.project_manager_id || '',
      lead_architect_id: project.lead_architect_id || '',
      start_date: project.start_date ? project.start_date.split('T')[0] : '',
      end_date: project.end_date ? project.end_date.split('T')[0] : '',
      site_address: project.site_address || '',
      notes: project.notes || '',
      civil_contractor: project.civil_contractor || { name: '', email: '', phone: '' },
      structural_consultant: project.structural_consultant || { name: '', email: '', phone: '' },
      tile_marble_contractor: project.tile_marble_contractor || { name: '', email: '', phone: '' },
      furniture_contractor: project.furniture_contractor || { name: '', email: '', phone: '' },
      electrical_contractor: project.electrical_contractor || { name: '', email: '', phone: '' },
      electrical_consultant: project.electrical_consultant || { name: '', email: '', phone: '' },
      plumbing_consultant: project.plumbing_consultant || { name: '', email: '', phone: '' },
      plumbing_contractor: project.plumbing_contractor || { name: '', email: '', phone: '' },
      false_ceiling_contractor: project.false_ceiling_contractor || { name: '', email: '', phone: '' },
      furniture_material_supplier: project.furniture_material_supplier || { name: '', email: '', phone: '' },
      kitchen_contractor: project.kitchen_contractor || { name: '', email: '', phone: '' },
      modular_contractor: project.modular_contractor || { name: '', email: '', phone: '' },
      color_contractor: project.color_contractor || { name: '', email: '', phone: '' },
      landscape_consultant: project.landscape_consultant || { name: '', email: '', phone: '' },
      landscape_contractor: project.landscape_contractor || { name: '', email: '', phone: '' },
      automation_consultant: project.automation_consultant || { name: '', email: '', phone: '' },
      readymade_furniture_supplier: project.readymade_furniture_supplier || { name: '', email: '', phone: '' },
      lights_supplier: project.lights_supplier || { name: '', email: '', phone: '' },
      custom_contacts: project.custom_contacts || {},
      brands: project.brands || []
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setFormData({
      code: '',
      title: '',
      project_types: [],
      status: 'Lead',
      client_id: '',
      project_manager_id: '',
      lead_architect_id: '',
      start_date: '',
      end_date: '',
      site_address: '',
      notes: '',
      civil_contractor: { name: '', email: '', phone: '' },
      structural_consultant: { name: '', email: '', phone: '' },
      tile_marble_contractor: { name: '', email: '', phone: '' },
      furniture_contractor: { name: '', email: '', phone: '' },
      electrical_contractor: { name: '', email: '', phone: '' },
      electrical_consultant: { name: '', email: '', phone: '' },
      plumbing_consultant: { name: '', email: '', phone: '' },
      plumbing_contractor: { name: '', email: '', phone: '' },
      false_ceiling_contractor: { name: '', email: '', phone: '' },
      furniture_material_supplier: { name: '', email: '', phone: '' },
      kitchen_contractor: { name: '', email: '', phone: '' },
      modular_contractor: { name: '', email: '', phone: '' },
      color_contractor: { name: '', email: '', phone: '' },
      landscape_consultant: { name: '', email: '', phone: '' },
      landscape_contractor: { name: '', email: '', phone: '' },
      automation_consultant: { name: '', email: '', phone: '' },
      readymade_furniture_supplier: { name: '', email: '', phone: '' },
      lights_supplier: { name: '', email: '', phone: '' },
      custom_contacts: {},
      brands: []
    });
    setAssignedContractors({});
    setActiveTab('basic');
  };

  const ContactSection = ({ title, fieldName }) => (
    <div className="p-4 border border-slate-200 rounded-lg bg-slate-50">
      <h4 className="font-medium text-sm text-slate-900 mb-3">{title}</h4>
      <div className="grid grid-cols-3 gap-3">
        <Input
          placeholder="Name"
          value={formData[fieldName]?.name || ''}
          onChange={(e) => updateContactField(fieldName, 'name', e.target.value)}
        />
        <Input
          placeholder="Email"
          type="email"
          value={formData[fieldName]?.email || ''}
          onChange={(e) => updateContactField(fieldName, 'email', e.target.value)}
        />
        <Input
          placeholder="Phone"
          value={formData[fieldName]?.phone || ''}
          onChange={(e) => updateContactField(fieldName, 'phone', e.target.value)}
        />
      </div>
    </div>
  );

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">Projects</h1>
            <p className="text-sm sm:text-base text-slate-600 mt-1">{projects.length} total projects</p>
          </div>
          <Button 
            onClick={() => setDialogOpen(true)}
            className="bg-orange-500 hover:bg-orange-600 w-full sm:w-auto"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {projects.map((project) => {
            const client = clients.find((c) => c.id === project.client_id);
            return (
              <Card 
                key={project.id} 
                className="hover:shadow-lg transition-shadow cursor-pointer active:scale-[0.98]"
                onClick={() => navigate(`/projects/${project.id}`)}
              >
                <CardContent className="p-4 sm:p-6">
                  <div className="flex items-start justify-between mb-3 sm:mb-4">
                    <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
                      <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-orange-400 to-orange-600 rounded-lg flex items-center justify-center text-white font-bold text-sm sm:text-base flex-shrink-0">
                        {project.code || project.title?.charAt(0) || 'P'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-slate-900 text-sm sm:text-base truncate">{project.title}</h3>
                        {client && (
                          <p className="text-xs sm:text-sm text-slate-500 truncate">{client.name}</p>
                        )}
                      </div>
                    </div>
                    {project.archived && (
                      <Archive className="w-4 h-4 sm:w-5 sm:h-5 text-amber-500 flex-shrink-0" />
                    )}
                  </div>
                  
                  {/* Project Types */}
                  {project.project_types && project.project_types.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                      {project.project_types.map((type) => (
                        <span 
                          key={type} 
                          className="px-2 py-0.5 sm:py-1 text-[10px] sm:text-xs bg-orange-50 text-orange-700 rounded border border-orange-200"
                        >
                          {type}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="space-y-1.5 sm:space-y-2 text-xs sm:text-sm">
                    {project.start_date && (
                      <div className="flex items-center gap-1.5 sm:gap-2 text-slate-600">
                        <Calendar className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                        <span className="truncate">Started: {new Date(project.start_date).toLocaleDateString()}</span>
                      </div>
                    )}
                    {project.end_date && (
                      <div className="flex items-center gap-1.5 sm:gap-2 text-slate-600">
                        <Calendar className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                        <span className="truncate">Ended: {new Date(project.end_date).toLocaleDateString()}</span>
                      </div>
                    )}
                    {!project.start_date && !project.end_date && (
                      <div className="flex items-center gap-1.5 sm:gap-2 text-slate-600">
                        <Calendar className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                        <span className="truncate">Created: {new Date(project.created_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {projects.length === 0 && (
          <div className="text-center py-12 px-4">
            <FolderOpen className="w-12 h-12 sm:w-16 sm:h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-base sm:text-lg font-medium text-slate-900 mb-2">No projects yet</h3>
            <p className="text-sm sm:text-base text-slate-500 mb-4">Create your first project to get started</p>
            <Button 
              onClick={() => setDialogOpen(true)}
              className="bg-orange-500 hover:bg-orange-600 w-full sm:w-auto"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Project
            </Button>
          </div>
        )}

        {/* Create Project Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingProject ? 'Edit Project' : 'Create New Project'}</DialogTitle>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid grid-cols-2 sm:grid-cols-4 w-full gap-1">
                  <TabsTrigger value="basic" className="text-xs sm:text-sm px-2 py-2">Basic Info</TabsTrigger>
                  <TabsTrigger value="team" className="text-xs sm:text-sm px-2 py-2">Team</TabsTrigger>
                  <TabsTrigger value="contractors" className="text-xs sm:text-sm px-2 py-2">Contractors</TabsTrigger>
                  <TabsTrigger value="brands" className="text-xs sm:text-sm px-2 py-2">Brands</TabsTrigger>
                </TabsList>

                {/* Basic Info Tab */}
                <TabsContent value="basic" className="space-y-4 mt-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium">Project Code *</Label>
                      <Input
                        value={formData.code}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        placeholder="e.g., PRJ-2024-001"
                        required
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Project Title *</Label>
                      <Input
                        value={formData.title}
                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                        placeholder="e.g., Residence at Bandra"
                        required
                        className="mt-1"
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Project Types *</Label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2">
                      {PROJECT_TYPES.map((type) => (
                        <label key={type} className="flex items-center gap-2 cursor-pointer p-2 rounded border hover:bg-slate-50">
                          <input
                            type="checkbox"
                            checked={formData.project_types.includes(type)}
                            onChange={() => handleProjectTypeToggle(type)}
                            className="w-4 h-4 text-orange-500 border-slate-300 rounded focus:ring-orange-500"
                          />
                          <span className="text-xs sm:text-sm text-slate-700">{type}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium">Client *</Label>
                      <select
                        className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm mt-1"
                        value={formData.client_id}
                        onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                        required
                      >
                        <option value="">Select client</option>
                        {clients.map((client) => (
                          <option key={client.id} value={client.id}>
                            {client.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Team Leader *</Label>
                      <select
                        className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm mt-1"
                        value={formData.team_leader_id}
                        onChange={(e) => setFormData({ ...formData, team_leader_id: e.target.value })}
                        required
                      >
                        <option value="">Select team leader</option>
                        {teamMembers
                          .filter(member => member.approval_status === 'approved' && 
                            member.role !== 'client' && member.role !== 'contractor' && 
                            member.role !== 'vendor' && member.role !== 'consultant')
                          .map((member) => (
                            <option key={member.id} value={member.id}>
                              {member.name} {member.role ? `(${member.role.replace(/_/g, ' ')})` : ''}
                            </option>
                          ))}
                      </select>
                      <p className="text-xs text-slate-500 mt-1">Team leader will receive all project notifications</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium">Status</Label>
                      <select
                        className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm mt-1"
                        value={formData.status}
                        onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      >
                        <option value="Lead">Lead</option>
                        <option value="Concept">Concept</option>
                        <option value="Layout_Dev">Layout Development</option>
                        <option value="Elevation_3D">Elevation & 3D</option>
                        <option value="Structural_Coord">Structural Coordination</option>
                        <option value="Working_Drawings">Working Drawings</option>
                        <option value="Execution">Execution</option>
                        <option value="OnHold">On Hold</option>
                        <option value="Closed">Closed</option>
                      </select>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <Label className="text-sm font-medium">Start Date</Label>
                        <Input
                          type="date"
                          value={formData.start_date}
                          onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium">End Date</Label>
                      <Input
                        type="date"
                        value={formData.end_date}
                        onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Priority</Label>
                      <select
                        className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm mt-1"
                        value={formData.priority}
                        onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                      >
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Site Address</Label>
                    <Input
                      value={formData.site_address}
                      onChange={(e) => setFormData({ ...formData, site_address: e.target.value })}
                      placeholder="Complete site address"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Notes</Label>
                    <textarea
                      className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm mt-1"
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="Additional project notes"
                    />
                  </div>
                </TabsContent>

                {/* Team Tab */}
                <TabsContent value="team" className="space-y-6 mt-4">
                  {/* Team Members Section */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-semibold text-slate-900 mb-3 text-sm sm:text-base">👥 Team Members</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs sm:text-sm font-medium">Project Manager</Label>
                        <select 
                          className="w-full mt-1 p-2 border border-slate-300 rounded text-sm"
                          value={formData.project_manager_id || ''}
                          onChange={(e) => setFormData({...formData, project_manager_id: e.target.value})}
                        >
                          <option value="">Select Project Manager</option>
                          {teamMembers.filter(m => m.role === 'project_manager' || m.role === 'owner').map((member) => (
                            <option key={member.id} value={member.id}>{member.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <Label className="text-xs sm:text-sm font-medium">Lead Architect</Label>
                        <select 
                          className="w-full mt-1 p-2 border border-slate-300 rounded text-sm"
                          value={formData.lead_architect_id || ''}
                          onChange={(e) => setFormData({...formData, lead_architect_id: e.target.value})}
                        >
                          <option value="">Select Lead Architect</option>
                          {teamMembers.filter(m => m.role === 'architect' || m.role === 'owner').map((member) => (
                            <option key={member.id} value={member.id}>{member.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Consultants Section */}
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h3 className="font-semibold text-slate-900 mb-3 text-sm sm:text-base">🏗️ Consultants</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs sm:text-sm font-medium">Structural Consultant</Label>
                        <select className="w-full mt-1 p-2 border border-slate-300 rounded text-sm">
                          <option value="">Select Consultant</option>
                          {consultants.filter(c => c.type === 'Structure').map((consultant) => (
                            <option key={consultant.id} value={consultant.id}>{consultant.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <Label className="text-xs sm:text-sm font-medium">MEP Consultant</Label>
                        <select className="w-full mt-1 p-2 border border-slate-300 rounded text-sm">
                          <option value="">Select Consultant</option>
                          {consultants.filter(c => c.type === 'MEP').map((consultant) => (
                            <option key={consultant.id} value={consultant.id}>{consultant.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Vendors Section */}
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h3 className="font-semibold text-slate-900 mb-3 text-sm sm:text-base">🏪 Vendors</h3>
                    <div className="space-y-3">
                      {contactTypes.map((type) => (
                        <div key={type.id} className="grid grid-cols-1 sm:grid-cols-3 gap-2 p-3 bg-white rounded border border-slate-200">
                          <div className="sm:col-span-3 mb-2 sm:mb-0">
                            <Label className="text-xs sm:text-sm font-medium text-purple-700">{type.type_name}</Label>
                          </div>
                          <div>
                            <Input
                              placeholder="Vendor name"
                              value={formData.custom_contacts[type.id]?.name || ''}
                              onChange={(e) => setFormData({
                                ...formData,
                                custom_contacts: {
                                  ...formData.custom_contacts,
                                  [type.id]: {
                                    ...formData.custom_contacts[type.id],
                                    name: e.target.value
                                  }
                                }
                              })}
                              className="text-sm"
                            />
                          </div>
                          <div>
                            <Input
                              placeholder="Email"
                              type="email"
                              value={formData.custom_contacts[type.id]?.email || ''}
                              onChange={(e) => setFormData({
                                ...formData,
                                custom_contacts: {
                                  ...formData.custom_contacts,
                                  [type.id]: {
                                    ...formData.custom_contacts[type.id],
                                    email: e.target.value
                                  }
                                }
                              })}
                              className="text-sm"
                            />
                          </div>
                          <div>
                            <Input
                              placeholder="Phone"
                              value={formData.custom_contacts[type.id]?.phone || ''}
                              onChange={(e) => setFormData({
                                ...formData,
                                custom_contacts: {
                                  ...formData.custom_contacts,
                                  [type.id]: {
                                    ...formData.custom_contacts[type.id],
                                    phone: e.target.value
                                  }
                                }
                              })}
                              className="text-sm"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </TabsContent>

                {/* Brands Tab */}
                <TabsContent value="brands" className="space-y-4 mt-4">
                  <p className="text-sm text-slate-600">
                    Brands can be added and managed after creating the project.
                  </p>
                </TabsContent>

                {/* Contractors Tab */}
                <TabsContent value="contractors" className="space-y-4 mt-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <h4 className="font-medium text-blue-900 mb-2">Assign Contractors to Project</h4>
                    <p className="text-sm text-blue-700">
                      Select contractors for different categories. They will receive project access automatically.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      'Civil', 'Plumbing', 'Electrical', 'Air Conditioning',
                      'Marble and Tile', 'False Ceiling', 'Furniture', 'Modular',
                      'Kitchen', 'Landscape', 'Glass', 'Profile', 'Gardner', 'Fabricator'
                    ].map(type => {
                      const typeContractors = contractors.filter(c => c.contractor_type === type);
                      return (
                        <div key={type}>
                          <Label className="text-sm font-medium text-slate-700">{type}</Label>
                          <select
                            value={assignedContractors[type] || ''}
                            onChange={(e) => setAssignedContractors({
                              ...assignedContractors,
                              [type]: e.target.value
                            })}
                            className="w-full p-2 border rounded mt-1 text-sm"
                          >
                            <option value="">-- Select {type} Contractor --</option>
                            {typeContractors.map(contractor => (
                              <option key={contractor.id} value={contractor.id}>
                                {contractor.name} {contractor.company_name ? `(${contractor.company_name})` : ''}
                              </option>
                            ))}
                          </select>
                          {typeContractors.length === 0 && (
                            <p className="text-xs text-slate-500 mt-1">
                              No contractors available. <a href="/contractors" className="text-blue-600 hover:underline">Add one →</a>
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </TabsContent>
              </Tabs>

              <div className="flex justify-end gap-3 mt-6 pt-6 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setDialogOpen(false);
                    resetForm();
                  }}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  className="bg-orange-500 hover:bg-orange-600"
                >
                  {editingProject ? 'Update Project' : 'Create Project'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Archive Confirmation Dialog */}
        <Dialog open={archiveConfirmOpen} onOpenChange={setArchiveConfirmOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Archive Project?</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <p className="text-slate-700 mb-3">
                You've entered an end date for this project. Would you like to archive it?
              </p>
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                <p className="text-sm text-orange-800">
                  Archiving will mark the project as completed.
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button 
                variant="outline" 
                onClick={handleUpdateWithoutArchive}
              >
                No, Just Update
              </Button>
              <Button 
                onClick={handleArchiveConfirm}
                className="bg-orange-600 hover:bg-orange-700 text-white"
              >
                Yes, Archive It
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
