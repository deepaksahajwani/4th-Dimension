import { useState, useEffect } from 'react';
import { 
  Book, FileText, Video, Download, ExternalLink, Search,
  FolderOpen, Bookmark, CheckCircle, Clock, Star,
  FileImage, File, FileSpreadsheet, Presentation
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

// Resource categories with icons and colors
const CATEGORIES = {
  onboarding: { label: 'Onboarding', icon: CheckCircle, color: 'bg-green-100 text-green-700' },
  standards: { label: 'Company Standards', icon: Book, color: 'bg-blue-100 text-blue-700' },
  templates: { label: 'Templates', icon: FileText, color: 'bg-purple-100 text-purple-700' },
  tutorials: { label: 'Tutorials', icon: Video, color: 'bg-orange-100 text-orange-700' },
  policies: { label: 'Policies', icon: FolderOpen, color: 'bg-red-100 text-red-700' },
  tools: { label: 'Tools & Software', icon: ExternalLink, color: 'bg-cyan-100 text-cyan-700' }
};

// File type icons
const getFileIcon = (type) => {
  switch(type) {
    case 'pdf': return FilePdf;
    case 'image': return FileImage;
    case 'spreadsheet': return FileSpreadsheet;
    case 'presentation': return Presentation;
    case 'video': return Video;
    default: return FileText;
  }
};

// Sample resources data (this would come from backend in production)
const SAMPLE_RESOURCES = [
  // Onboarding
  {
    id: '1',
    title: 'Welcome to 4th Dimension',
    description: 'Introduction to our firm, culture, and values',
    category: 'onboarding',
    type: 'pdf',
    url: '#',
    featured: true,
    dateAdded: '2024-01-15'
  },
  {
    id: '2',
    title: 'Employee Handbook',
    description: 'Complete guide to company policies, benefits, and procedures',
    category: 'onboarding',
    type: 'pdf',
    url: '#',
    featured: true,
    dateAdded: '2024-01-15'
  },
  {
    id: '3',
    title: 'IT Setup Guide',
    description: 'How to set up your workstation, email, and software',
    category: 'onboarding',
    type: 'pdf',
    url: '#',
    dateAdded: '2024-01-15'
  },
  // Company Standards
  {
    id: '4',
    title: 'Drawing Standards Manual',
    description: 'Standard conventions for architectural drawings',
    category: 'standards',
    type: 'pdf',
    url: '#',
    featured: true,
    dateAdded: '2024-02-01'
  },
  {
    id: '5',
    title: 'CAD Layer Standards',
    description: 'AutoCAD layer naming conventions and colors',
    category: 'standards',
    type: 'pdf',
    url: '#',
    dateAdded: '2024-02-01'
  },
  {
    id: '6',
    title: 'Brand Guidelines',
    description: 'Logo usage, colors, fonts, and presentation standards',
    category: 'standards',
    type: 'pdf',
    url: '#',
    dateAdded: '2024-02-01'
  },
  // Templates
  {
    id: '7',
    title: 'Project Proposal Template',
    description: 'Standard template for client proposals',
    category: 'templates',
    type: 'document',
    url: '#',
    dateAdded: '2024-02-15'
  },
  {
    id: '8',
    title: 'Site Visit Report Template',
    description: 'Template for documenting site visits',
    category: 'templates',
    type: 'document',
    url: '#',
    dateAdded: '2024-02-15'
  },
  {
    id: '9',
    title: 'Meeting Minutes Template',
    description: 'Standard format for meeting documentation',
    category: 'templates',
    type: 'document',
    url: '#',
    dateAdded: '2024-02-15'
  },
  {
    id: '10',
    title: 'Invoice Template',
    description: 'Standard invoice format for billing',
    category: 'templates',
    type: 'spreadsheet',
    url: '#',
    dateAdded: '2024-02-15'
  },
  // Tutorials
  {
    id: '11',
    title: 'Portal User Guide',
    description: 'How to use the 4th Dimension project portal',
    category: 'tutorials',
    type: 'video',
    url: '#',
    featured: true,
    dateAdded: '2024-03-01'
  },
  {
    id: '12',
    title: 'Drawing Upload Tutorial',
    description: 'Step-by-step guide to uploading and managing drawings',
    category: 'tutorials',
    type: 'video',
    url: '#',
    dateAdded: '2024-03-01'
  },
  {
    id: '13',
    title: 'Client Communication Best Practices',
    description: 'Tips for effective client communication',
    category: 'tutorials',
    type: 'pdf',
    url: '#',
    dateAdded: '2024-03-01'
  },
  // Policies
  {
    id: '14',
    title: 'Leave Policy',
    description: 'Guidelines for leave applications and approvals',
    category: 'policies',
    type: 'pdf',
    url: '#',
    dateAdded: '2024-01-20'
  },
  {
    id: '15',
    title: 'Work From Home Policy',
    description: 'Remote work guidelines and expectations',
    category: 'policies',
    type: 'pdf',
    url: '#',
    dateAdded: '2024-01-20'
  },
  {
    id: '16',
    title: 'Expense Reimbursement Policy',
    description: 'How to submit and get reimbursed for expenses',
    category: 'policies',
    type: 'pdf',
    url: '#',
    dateAdded: '2024-01-20'
  },
  // Tools & Software
  {
    id: '17',
    title: 'AutoCAD Quick Reference',
    description: 'Keyboard shortcuts and common commands',
    category: 'tools',
    type: 'pdf',
    url: '#',
    dateAdded: '2024-02-10'
  },
  {
    id: '18',
    title: 'SketchUp Tips & Tricks',
    description: 'Advanced techniques for 3D modeling',
    category: 'tools',
    type: 'video',
    url: '#',
    dateAdded: '2024-02-10'
  },
  {
    id: '19',
    title: 'Software Download Links',
    description: 'Licensed software and installation guides',
    category: 'tools',
    type: 'link',
    url: '#',
    dateAdded: '2024-02-10'
  }
];

export default function Resources() {
  const [resources, setResources] = useState(SAMPLE_RESOURCES);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [bookmarked, setBookmarked] = useState([]);

  // Filter resources based on search and category
  const filteredResources = resources.filter(resource => {
    const matchesSearch = resource.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         resource.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || resource.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Get featured resources
  const featuredResources = resources.filter(r => r.featured);

  // Toggle bookmark
  const toggleBookmark = (id) => {
    setBookmarked(prev => 
      prev.includes(id) ? prev.filter(b => b !== id) : [...prev, id]
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 mb-2">
            📚 Resources
          </h1>
          <p className="text-slate-600">
            Access company documents, templates, tutorials, and more
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
            <Input
              placeholder="Search resources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Featured Resources */}
        {selectedCategory === 'all' && !searchQuery && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" />
              Getting Started
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {featuredResources.map(resource => {
                const CategoryIcon = CATEGORIES[resource.category]?.icon || FileText;
                const FileIcon = getFileIcon(resource.type);
                return (
                  <Card key={resource.id} className="hover:shadow-md transition-shadow border-l-4 border-l-indigo-500">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className={`p-2 rounded-lg ${CATEGORIES[resource.category]?.color}`}>
                          <CategoryIcon className="w-5 h-5" />
                        </div>
                        <FileIcon className="w-4 h-4 text-slate-400" />
                      </div>
                      <h3 className="font-semibold text-slate-800 mb-1 line-clamp-1">
                        {resource.title}
                      </h3>
                      <p className="text-sm text-slate-500 line-clamp-2 mb-3">
                        {resource.description}
                      </p>
                      <Button variant="outline" size="sm" className="w-full">
                        <Download className="w-4 h-4 mr-2" />
                        View
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Category Tabs */}
        <Tabs defaultValue="all" className="w-full" onValueChange={setSelectedCategory}>
          <TabsList className="flex flex-wrap h-auto gap-2 bg-transparent p-0 mb-6">
            <TabsTrigger 
              value="all" 
              className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white"
            >
              All Resources
            </TabsTrigger>
            {Object.entries(CATEGORIES).map(([key, { label, icon: Icon }]) => (
              <TabsTrigger 
                key={key} 
                value={key}
                className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white"
              >
                <Icon className="w-4 h-4 mr-1" />
                {label}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value={selectedCategory} className="mt-0">
            {filteredResources.length === 0 ? (
              <Card className="p-8 text-center">
                <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-500">No resources found</p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredResources.map(resource => {
                  const CategoryIcon = CATEGORIES[resource.category]?.icon || FileText;
                  const FileIcon = getFileIcon(resource.type);
                  const isBookmarked = bookmarked.includes(resource.id);
                  
                  return (
                    <Card key={resource.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <Badge className={CATEGORIES[resource.category]?.color}>
                            {CATEGORIES[resource.category]?.label}
                          </Badge>
                          <div className="flex items-center gap-2">
                            <button 
                              onClick={() => toggleBookmark(resource.id)}
                              className={`p-1 rounded hover:bg-slate-100 ${isBookmarked ? 'text-yellow-500' : 'text-slate-400'}`}
                            >
                              <Bookmark className="w-4 h-4" fill={isBookmarked ? 'currentColor' : 'none'} />
                            </button>
                            <FileIcon className="w-4 h-4 text-slate-400" />
                          </div>
                        </div>
                        
                        <h3 className="font-semibold text-slate-800 mb-2">
                          {resource.title}
                        </h3>
                        <p className="text-sm text-slate-500 mb-4 line-clamp-2">
                          {resource.description}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(resource.dateAdded).toLocaleDateString()}
                          </span>
                          <Button variant="outline" size="sm">
                            <Download className="w-4 h-4 mr-1" />
                            Download
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Quick Links Section */}
        <div className="mt-8 p-6 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl text-white">
          <h3 className="text-lg font-semibold mb-4">📌 Quick Links</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a href="#" className="flex items-center gap-2 bg-white/20 rounded-lg p-3 hover:bg-white/30 transition">
              <ExternalLink className="w-4 h-4" />
              <span className="text-sm">AutoCAD Download</span>
            </a>
            <a href="#" className="flex items-center gap-2 bg-white/20 rounded-lg p-3 hover:bg-white/30 transition">
              <ExternalLink className="w-4 h-4" />
              <span className="text-sm">SketchUp Pro</span>
            </a>
            <a href="#" className="flex items-center gap-2 bg-white/20 rounded-lg p-3 hover:bg-white/30 transition">
              <ExternalLink className="w-4 h-4" />
              <span className="text-sm">Company Drive</span>
            </a>
            <a href="#" className="flex items-center gap-2 bg-white/20 rounded-lg p-3 hover:bg-white/30 transition">
              <ExternalLink className="w-4 h-4" />
              <span className="text-sm">HR Portal</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
