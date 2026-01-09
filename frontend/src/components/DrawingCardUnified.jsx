/**
 * Unified Drawing Card Component
 * Standardizes drawing display across all tabs and roles
 * 
 * Role-based button visibility:
 * - External (Client/Contractor/Consultant/Vendor): View, Download, Comment
 * - Team Leader: View, Download, Comment, Upload, Issue, Approve, N/A, Revise
 * - Owner: All buttons
 */

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Eye,
  Download,
  MessageSquare,
  Upload,
  Check,
  RefreshCw,
  X,
  Clock
} from 'lucide-react';

// External roles that have limited access
const EXTERNAL_ROLES = ['client', 'contractor', 'consultant', 'vendor'];

// Get status badge configuration
const getStatusConfig = (drawing) => {
  if (drawing.is_not_applicable) {
    return { label: 'N/A', className: 'bg-slate-100 text-slate-600 border-slate-200' };
  }
  if (drawing.is_issued) {
    return { label: 'Issued', className: 'bg-green-50 text-green-700 border-green-200' };
  }
  if (drawing.is_approved && !drawing.is_issued) {
    return { label: 'Ready to Issue', className: 'bg-blue-50 text-blue-700 border-blue-200' };
  }
  if (drawing.under_review) {
    return { label: 'Pending Approval', className: 'bg-amber-50 text-amber-700 border-amber-200' };
  }
  if (drawing.has_pending_revision) {
    return { label: 'Revision Needed', className: 'bg-red-50 text-red-700 border-red-200' };
  }
  if (!drawing.file_url) {
    return { label: 'Pending Upload', className: 'bg-slate-50 text-slate-600 border-slate-200' };
  }
  return { label: 'In Progress', className: 'bg-purple-50 text-purple-700 border-purple-200' };
};

// Format date helper
const formatDate = (dateStr) => {
  if (!dateStr) return null;
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
};

export default function DrawingCardUnified({
  drawing,
  userRole,
  isOwner = false,
  onView,
  onDownload,
  onComment,
  onUpload,
  onIssue,
  onApprove,
  onMarkNA,
  onRequestRevision,
  showRevisionHistory = false,
  onToggleHistory,
  className = ''
}) {
  // Determine user type for button visibility
  const isExternal = EXTERNAL_ROLES.includes(userRole);
  const isTeamLeader = !isExternal && !isOwner;
  const hasFile = !!drawing.file_url;
  
  // Get status configuration
  const statusConfig = getStatusConfig(drawing);
  
  // Determine which action buttons to show based on role and drawing state
  const showViewButton = hasFile;
  const showDownloadButton = hasFile;
  const showCommentButton = true;
  
  // Team Leader and Owner only buttons
  const showUploadButton = !isExternal && !drawing.is_issued && (drawing.has_pending_revision || !hasFile);
  const showApproveButton = !isExternal && drawing.under_review && !drawing.is_approved;
  const showIssueButton = !isExternal && drawing.is_approved && !drawing.is_issued && hasFile;
  const showMarkNAButton = !isExternal && !drawing.is_issued && !drawing.is_not_applicable;
  const showRevisionButton = !isExternal && drawing.is_issued;
  
  // Hide most actions for N/A drawings
  const isNA = drawing.is_not_applicable;
  
  return (
    <div className={`bg-white border rounded-lg p-3 sm:p-4 ${className}`}>
      {/* Main content row */}
      <div className="flex flex-col sm:flex-row sm:items-start gap-3">
        {/* Drawing info - takes full width on mobile */}
        <div className="flex-1 min-w-0">
          {/* Drawing name - NO TRUNCATION, allow 2-line wrap */}
          <p className="font-medium text-sm sm:text-base text-slate-900 leading-tight break-words">
            {drawing.name}
          </p>
          
          {/* Category and metadata */}
          <div className="flex flex-wrap items-center gap-2 mt-1.5">
            {drawing.category && (
              <span className="text-xs text-slate-500">{drawing.category}</span>
            )}
            {drawing.current_revision > 0 && (
              <span className="text-xs text-slate-400">• R{drawing.current_revision}</span>
            )}
          </div>
          
          {/* Status badge row */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <Badge variant="outline" className={statusConfig.className}>
              {statusConfig.label}
            </Badge>
            
            {/* Show issued date for issued drawings */}
            {drawing.is_issued && drawing.issued_date && (
              <span className="text-xs text-slate-400">
                {formatDate(drawing.issued_date)}
              </span>
            )}
            
            {/* Show updated date for non-issued */}
            {!drawing.is_issued && drawing.updated_at && (
              <span className="text-xs text-slate-400">
                Updated: {formatDate(drawing.updated_at)}
              </span>
            )}
          </div>
        </div>
        
        {/* Action buttons - right aligned */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 shrink-0">
          {/* View button */}
          {showViewButton && onView && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onView(drawing)}
              title="View"
              className="p-2 h-8 w-8"
            >
              <Eye className="w-4 h-4" />
            </Button>
          )}
          
          {/* Download button */}
          {showDownloadButton && onDownload && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onDownload(drawing)}
              title="Download"
              className="p-2 h-8 w-8"
            >
              <Download className="w-4 h-4" />
            </Button>
          )}
          
          {/* Comment button */}
          {showCommentButton && onComment && !isNA && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onComment(drawing)}
              title="Comment"
              className="p-2 h-8 w-8"
            >
              <MessageSquare className="w-4 h-4" />
            </Button>
          )}
          
          {/* Upload button - Team Leader / Owner only */}
          {showUploadButton && onUpload && !isNA && (
            <Button
              size="sm"
              onClick={() => onUpload(drawing)}
              title="Upload"
              className={`p-2 h-8 ${drawing.has_pending_revision ? 'bg-red-600 hover:bg-red-700' : 'bg-orange-600 hover:bg-orange-700'}`}
            >
              <Upload className="w-4 h-4" />
            </Button>
          )}
          
          {/* Approve button - Team Leader / Owner only */}
          {showApproveButton && onApprove && !isNA && (
            <Button
              size="sm"
              onClick={() => onApprove(drawing)}
              title="Approve"
              className="bg-green-600 hover:bg-green-700 p-2 h-8"
            >
              <Check className="w-4 h-4" />
            </Button>
          )}
          
          {/* Issue button - Team Leader / Owner only */}
          {showIssueButton && onIssue && !isNA && (
            <Button
              size="sm"
              onClick={() => onIssue(drawing)}
              title="Issue"
              className="bg-blue-600 hover:bg-blue-700 px-3 h-8"
            >
              <Check className="w-4 h-4 mr-1" />
              Issue
            </Button>
          )}
          
          {/* Request Revision button - Team Leader / Owner only, for issued drawings */}
          {showRevisionButton && onRequestRevision && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onRequestRevision(drawing)}
              title="Request Revision"
              className="p-2 h-8 w-8 text-orange-600 border-orange-300 hover:bg-orange-50"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          )}
          
          {/* Mark N/A button - Team Leader / Owner only */}
          {showMarkNAButton && onMarkNA && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onMarkNA(drawing)}
              title="Mark as N/A"
              className="p-2 h-8 w-8 text-slate-500 hover:bg-slate-100"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
          
          {/* History toggle button */}
          {drawing.revision_history?.length > 0 && onToggleHistory && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onToggleHistory(drawing.id)}
              title="Revision History"
              className="p-2 h-8 w-8"
            >
              <Clock className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
      
      {/* Revision History (expandable) */}
      {showRevisionHistory && drawing.revision_history && drawing.revision_history.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <p className="text-xs font-medium text-slate-600 mb-2">Revision History:</p>
          <div className="space-y-1">
            {drawing.revision_history.map((rev, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs bg-slate-50 p-2 rounded">
                <span className="text-slate-600">Rev {rev.revision || idx + 1}</span>
                <span className="text-slate-500">
                  {rev.issued_date ? formatDate(rev.issued_date) : 'N/A'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
