import React, { useState } from 'react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import {
  Circle,
  CheckCircle2,
  AlertCircle,
  Clock,
  Eye,
  Download,
  MessageSquare,
  Upload,
  CheckCheck,
  RotateCcw,
  FileText,
  MoreVertical
} from 'lucide-react';

/**
 * DrawingCard Component - Mobile-First, Role-Based UX
 * 
 * External Users (Client/Contractor/Consultant): Read-only + Comments
 * Team Leader: Upload, Revise, Approve (contextual)
 * Owner: Full access
 * 
 * Design: WhatsApp-like calm UI, minimal cognitive load
 */

const getStatusConfig = (drawing) => {
  if (drawing.has_pending_revision) {
    return { 
      icon: <AlertCircle className="w-4 h-4 text-amber-500" />,
      text: 'Revision Needed',
      bgColor: 'bg-amber-50',
      textColor: 'text-amber-700',
      borderColor: 'border-amber-200'
    };
  }
  if (drawing.is_issued) {
    return { 
      icon: <CheckCircle2 className="w-4 h-4 text-green-500" />,
      text: 'Issued',
      bgColor: 'bg-green-50',
      textColor: 'text-green-700',
      borderColor: 'border-green-200'
    };
  }
  if (drawing.is_approved) {
    return { 
      icon: <CheckCheck className="w-4 h-4 text-blue-500" />,
      text: 'Approved',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-700',
      borderColor: 'border-blue-200'
    };
  }
  if (drawing.under_review) {
    return { 
      icon: <Clock className="w-4 h-4 text-orange-500" />,
      text: 'Under Review',
      bgColor: 'bg-orange-50',
      textColor: 'text-orange-700',
      borderColor: 'border-orange-200'
    };
  }
  return { 
    icon: <Circle className="w-4 h-4 text-slate-400" />,
    text: 'Pending',
    bgColor: 'bg-slate-50',
    textColor: 'text-slate-600',
    borderColor: 'border-slate-200'
  };
};

export const DrawingCard = ({
  drawing,
  user,
  permissions = {},
  onToggleIssued,
  onResolveRevision,
  onOpenRevisionDialog,
  onApproveDrawing,
  onOpenIssueDialog,
  onViewPDF,
  onDownloadPDF,
  onOpenComments
}) => {
  // Determine user type
  const isExternalUser = ['client', 'contractor', 'consultant', 'vendor'].includes(user?.role);
  const isTeamLeader = user?.role === 'team_leader' || user?.role?.includes('designer');
  const isOwner = user?.is_owner === true;
  
  // Permission checks - strict for external users
  const canUpload = !isExternalUser && (permissions.can_upload_drawing ?? (isOwner || isTeamLeader));
  const canApprove = !isExternalUser && (permissions.can_approve_drawing ?? (isOwner || isTeamLeader));
  const canIssue = !isExternalUser && (permissions.can_issue_drawing ?? (isOwner || isTeamLeader));
  const canRevise = !isExternalUser && (permissions.can_edit_drawing ?? (isOwner || isTeamLeader));
  const canDownload = true; // Everyone can download
  const canComment = true; // Everyone can comment
  
  // Drawing state
  const isPending = !drawing.file_url && !drawing.under_review && !drawing.is_approved && !drawing.is_issued;
  const isUnderReview = drawing.under_review && !drawing.is_approved && !drawing.is_issued;
  const isApproved = drawing.is_approved && !drawing.is_issued;
  const isIssued = drawing.is_issued;
  const hasRevisionPending = drawing.has_pending_revision === true;
  const hasFile = !!drawing.file_url;
  
  const status = getStatusConfig(drawing);
  
  // Determine which single primary action to show (contextual)
  const getPrimaryAction = () => {
    if (hasRevisionPending && canUpload) {
      return { action: 'resolve', label: 'Resolve', icon: <Upload className="w-4 h-4" />, color: 'text-green-600 border-green-300 hover:bg-green-50' };
    }
    if (isPending && canUpload) {
      return { action: 'upload', label: 'Upload', icon: <Upload className="w-4 h-4" />, color: 'text-blue-600 border-blue-300 hover:bg-blue-50' };
    }
    if (isUnderReview && canApprove) {
      return { action: 'approve', label: 'Approve', icon: <CheckCheck className="w-4 h-4" />, color: 'text-green-600 border-green-300 hover:bg-green-50' };
    }
    if (isApproved && canIssue) {
      return { action: 'issue', label: 'Issue', icon: <CheckCircle2 className="w-4 h-4" />, color: 'text-blue-600 border-blue-300 hover:bg-blue-50' };
    }
    return null;
  };
  
  const primaryAction = getPrimaryAction();
  
  const handlePrimaryAction = () => {
    if (!primaryAction) return;
    switch (primaryAction.action) {
      case 'resolve': onResolveRevision?.(drawing); break;
      case 'upload': onToggleIssued?.(drawing); break;
      case 'approve': onApproveDrawing?.(drawing); break;
      case 'issue': onOpenIssueDialog?.(drawing); break;
      default: break;
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow duration-200 border border-slate-100 rounded-xl overflow-hidden">
      <CardContent className="p-4">
        {/* Header Row - Status icon, Name, Badge */}
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            {status.icon}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm text-slate-900 leading-tight line-clamp-2">
              {drawing.name}
            </h4>
            <div className="flex items-center gap-2 mt-1.5">
              <span className={`inline-flex px-2 py-0.5 text-[11px] font-medium rounded-full ${status.bgColor} ${status.textColor}`}>
                {status.text}
              </span>
              {drawing.revision_count > 0 && (
                <span className="text-[11px] text-slate-500">
                  R{drawing.revision_count}
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Action Row - Clean, minimal buttons */}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
          {/* Left side - View/Download */}
          <div className="flex items-center gap-1">
            {hasFile && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onViewPDF?.(drawing)}
                className="h-8 px-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                title="View PDF"
              >
                <Eye className="w-4 h-4" />
                <span className="ml-1 text-xs hidden sm:inline">View</span>
              </Button>
            )}
            {hasFile && canDownload && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDownloadPDF?.(drawing)}
                className="h-8 px-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                title="Download"
              >
                <Download className="w-4 h-4" />
              </Button>
            )}
          </div>
          
          {/* Right side - Actions */}
          <div className="flex items-center gap-1">
            {/* Revise button - Only for Team Leader/Owner on issued/reviewed drawings */}
            {canRevise && hasFile && (isUnderReview || isApproved || isIssued) && !hasRevisionPending && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onOpenRevisionDialog?.(drawing)}
                className="h-8 px-2 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                title="Request Revision"
              >
                <RotateCcw className="w-4 h-4" />
              </Button>
            )}
            
            {/* Primary Action Button - Contextual */}
            {primaryAction && (
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrimaryAction}
                className={`h-8 px-3 text-xs font-medium ${primaryAction.color}`}
              >
                {primaryAction.icon}
                <span className="ml-1.5">{primaryAction.label}</span>
              </Button>
            )}
            
            {/* Comment Button - Always visible */}
            {canComment && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onOpenComments?.(drawing)}
                className="h-8 px-2 text-purple-600 hover:text-purple-700 hover:bg-purple-50 relative"
                title="Comments"
              >
                <MessageSquare className="w-4 h-4" />
                {(drawing.comment_count > 0 || drawing.unread_comments > 0) && (
                  <span className={`absolute -top-1 -right-1 min-w-[16px] h-4 px-1 text-[10px] font-medium rounded-full flex items-center justify-center ${
                    drawing.unread_comments > 0 
                      ? 'bg-red-500 text-white animate-pulse' 
                      : 'bg-purple-100 text-purple-700'
                  }`}>
                    {drawing.unread_comments || drawing.comment_count}
                  </span>
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
