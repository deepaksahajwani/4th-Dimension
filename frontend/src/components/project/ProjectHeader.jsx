/**
 * Project Header Component
 * Displays project info, client details, and action buttons
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Archive,
  ChevronDown,
  Phone,
  Mail,
  Building,
  Users,
  Calendar
} from 'lucide-react';
import { formatDate } from '@/utils/dateUtils';

export default function ProjectHeader({
  project,
  client,
  teamLeader,
  onEdit,
  onDelete,
  onArchive,
  isOwner = false
}) {
  const navigate = useNavigate();

  if (!project) return null;

  return (
    <div className="space-y-4">
      {/* Back Button and Actions */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Projects
        </Button>

        {isOwner && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="gap-2">
                Actions
                <ChevronDown className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onEdit}>
                <Edit className="w-4 h-4 mr-2" />
                Edit Project
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onArchive}>
                <Archive className="w-4 h-4 mr-2" />
                Archive Project
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={onDelete}
                className="text-red-600 focus:text-red-600"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Project
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Project Info Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
            {/* Project Details */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">{project.title || project.name}</h1>
                {project.project_code && (
                  <Badge variant="outline">{project.project_code}</Badge>
                )}
              </div>
              
              {project.description && (
                <p className="text-gray-600 max-w-2xl">{project.description}</p>
              )}

              <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                {project.start_date && (
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Started: {formatDate(project.start_date)}
                  </div>
                )}
                {project.end_date && (
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Due: {formatDate(project.end_date)}
                  </div>
                )}
              </div>
            </div>

            {/* Client & Team Info */}
            <div className="flex flex-col sm:flex-row gap-4 lg:gap-6">
              {/* Client Card */}
              {client && (
                <div className="bg-gray-50 rounded-lg p-4 min-w-[200px]">
                  <div className="flex items-center gap-2 mb-2">
                    <Building className="w-4 h-4 text-gray-400" />
                    <span className="text-xs font-medium text-gray-500 uppercase">Client</span>
                  </div>
                  <p className="font-medium">{client.name}</p>
                  {client.contact_person && (
                    <p className="text-sm text-gray-600">{client.contact_person}</p>
                  )}
                  <div className="mt-2 space-y-1">
                    {client.phone && (
                      <a
                        href={`tel:${client.phone}`}
                        className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
                      >
                        <Phone className="w-3 h-3" />
                        {client.phone}
                      </a>
                    )}
                    {client.email && (
                      <a
                        href={`mailto:${client.email}`}
                        className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
                      >
                        <Mail className="w-3 h-3" />
                        {client.email}
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* Team Leader Card */}
              {teamLeader && (
                <div className="bg-blue-50 rounded-lg p-4 min-w-[200px]">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-medium text-blue-500 uppercase">Team Leader</span>
                  </div>
                  <p className="font-medium">{teamLeader.name}</p>
                  <p className="text-sm text-gray-600">{teamLeader.role}</p>
                  {teamLeader.mobile && (
                    <a
                      href={`tel:${teamLeader.mobile}`}
                      className="flex items-center gap-1 text-sm text-blue-600 hover:underline mt-2"
                    >
                      <Phone className="w-3 h-3" />
                      {teamLeader.mobile}
                    </a>
                  )}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
