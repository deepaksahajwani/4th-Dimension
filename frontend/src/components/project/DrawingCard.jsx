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
  Calendar,
  ChevronDown,
  Eye,
  Download,
  MessageSquare,
  HardHat
} from 'lucide-react';
import { ContractorProgressTracker } from '../ContractorProgress';

const getDrawingStatusIcon = (drawing) => {
  if (drawing.has_pending_revision) {
    return <AlertCircle className="w-5 h-5 text-amber-500" />;
  }
  if (drawing.is_issued) {
    return <CheckCircle2 className="w-5 h-5 text-green-500" />;
  }
  if (drawing.is_approved) {
    return <CheckCircle2 className="w-5 h-5 text-blue-500" />;
  }
  if (drawing.under_review) {
    return <Circle className="w-5 h-5 text-orange-500 fill-orange-200" />;
  }
  return <Circle className="w-5 h-5 text-slate-300" />;
};

const getDrawingStatusText = (drawing) => {
  if (drawing.has_pending_revision) return 'Revision Needed';
  if (drawing.is_issued) return 'Issued';
  if (drawing.is_approved) return 'Approved';
  if (drawing.under_review) return 'Under Review';
  return 'Pending';
};

const getDrawingStatusColor = (drawing) => {
  if (drawing.has_pending_revision) return 'bg-amber-50 text-amber-700 border-amber-200';
  if (drawing.is_issued) return 'bg-green-50 text-green-700 border-green-200';
  if (drawing.is_approved) return 'bg-blue-50 text-blue-700 border-blue-200';
  if (drawing.under_review) return 'bg-orange-50 text-orange-700 border-orange-200';
  return 'bg-slate-50 text-slate-600 border-slate-200';
};

/**
 * DrawingCard Component with Role-Based Permission Controls
 * 
 * Drawing States:
 * 1. PENDING - No file uploaded yet → Show: Upload, N/A
 * 2. UNDER_REVIEW - File uploaded, awaiting approval → Show: Approve, Revise, PDF
 * 3. REVISION_PENDING - Revision requested → Show: Resolve
 * 4. APPROVED - Approved, ready to issue → Show: Issue, Revise, PDF
 * 5. ISSUED - Final state → Show: Revise, PDF, Progress
 */
export const DrawingCard = ({
  drawing,
  user,
  permissions = {},
  projectContractors = [],
  onToggleIssued,
  onResolveRevision,
  onOpenRevisionDialog,
  onApproveDrawing,
  onOpenIssueDialog,
  onViewPDF,
  onDownloadPDF,
  onOpenComments,
  onMarkAsNotApplicable,
  onProgressUpdate
}) => {
  const [showProgress, setShowProgress] = useState(false);
  
  // Permission checks with fallback to user-based check for backward compatibility
  const canUpload = permissions.can_upload_drawing ?? (user?.is_owner || user?.role === 'team_leader');
  const canApprove = permissions.can_approve_drawing ?? (user?.is_owner || user?.role === 'team_leader');
  const canIssue = permissions.can_issue_drawing ?? (user?.is_owner || user?.role === 'team_leader');
  const canMarkNA = permissions.can_mark_na ?? (user?.is_owner || user?.role === 'team_leader');
  const canDownload = permissions.can_download_drawing ?? true;
  const canRevise = permissions.can_edit_drawing ?? (user?.is_owner || user?.role === 'team_leader');
  
  // Determine drawing state
  const isPending = !drawing.file_url && !drawing.under_review && !drawing.is_approved && !drawing.is_issued;
  const isUnderReview = drawing.under_review && !drawing.is_approved && !drawing.is_issued;
  const isApproved = drawing.is_approved && !drawing.is_issued;
  const isIssued = drawing.is_issued;
  const hasRevisionPending = drawing.has_pending_revision === true;
  const hasFile = !!drawing.file_url;
  
  // Only show contractor progress for issued drawings
  const canShowProgress = isIssued && projectContractors.length > 0;
  
  return (
  <Card id={`drawing-${drawing.id}`} className="hover:shadow-md transition-all duration-300">
    <CardContent className="p-3 sm:p-4">
      <div className="flex flex-col sm:flex-row sm:items-start gap-3">
        <div className="flex items-start gap-2 sm:gap-3 flex-1 min-w-0">
          <div className="flex-shrink-0 mt-0.5">
            {getDrawingStatusIcon(drawing)}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm sm:text-base text-slate-900 break-words">{drawing.name}</h4>
            <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-2">
              <span className={`px-2 py-0.5 text-[10px] sm:text-xs rounded border ${getDrawingStatusColor(drawing)}`}>
                {getDrawingStatusText(drawing)}
              </span>
              {drawing.revision_count > 0 && (
                <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-blue-50 text-blue-700 rounded border border-blue-200">
                  R{drawing.revision_count}
                </span>
              )}
              {drawing.due_date && (
                <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-slate-100 text-slate-600 rounded border border-slate-200 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span className="hidden sm:inline">{new Date(drawing.due_date).toLocaleDateString()}</span>
                  <span className="sm:hidden">{new Date(drawing.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                </span>
              )}
            </div>
            {drawing.notes && (
              <p className="text-xs sm:text-sm text-slate-600 mt-2 line-clamp-2">{drawing.notes}</p>
            )}
          </div>
        </div>
        
        <div className="flex flex-wrap sm:flex-nowrap gap-1.5 sm:gap-2 sm:ml-4">
          
          {/* ============ STATE 1: PENDING (No file yet) ============ */}
          {/* UPLOAD button - Only when NO file AND NOT issued/approved/under_review */}
          {canUpload && isPending && !hasRevisionPending && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onToggleIssued(drawing)}
              className="flex-1 sm:flex-none text-xs h-8"
            >
              Upload
            </Button>
          )}
          
          {/* ============ STATE 2: REVISION PENDING ============ */}
          {/* RESOLVE button - Only when revision is pending */}
          {canUpload && hasRevisionPending && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onResolveRevision(drawing)}
              className="flex-1 sm:flex-none text-xs h-8 border-green-500 text-green-600"
              title="Upload Revised Drawing"
            >
              Resolve
            </Button>
          )}
          
          {/* ============ STATE 3: UNDER REVIEW ============ */}
          {/* APPROVE button - Only when under_review AND NOT approved/issued */}
          {canApprove && isUnderReview && !hasRevisionPending && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onApproveDrawing(drawing)}
              className="flex-1 sm:flex-none text-xs h-8 border-green-500 text-green-600"
              title="Approve for Issuance"
            >
              Approve
            </Button>
          )}
          
          {/* ============ STATE 4: APPROVED ============ */}
          {/* ISSUE button - Only when approved AND NOT issued */}
          {canIssue && isApproved && !hasRevisionPending && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onOpenIssueDialog(drawing)}
              className="flex-1 sm:flex-none text-xs h-8 border-blue-500 text-blue-600"
              title="Issue Drawing"
            >
              Issue
            </Button>
          )}
          
          {/* ============ REVISE button - For any state with a file (except pending revision) ============ */}
          {canRevise && hasFile && !hasRevisionPending && (isUnderReview || isApproved || isIssued) && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onOpenRevisionDialog(drawing)}
              className="flex-1 sm:flex-none text-xs h-8 border-amber-500 text-amber-600"
              title="Request Revision"
            >
              Revise
            </Button>
          )}
          
          {/* ============ PDF Button - Only when file exists ============ */}
          {hasFile && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 sm:flex-none text-xs h-8 border-blue-500 text-blue-600"
                >
                  📄 PDF <ChevronDown className="w-3 h-3 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => onViewPDF(drawing)}>
                  <Eye className="w-4 h-4 mr-2" />
                  View
                </DropdownMenuItem>
                {canDownload && (
                  <DropdownMenuItem onClick={() => onDownloadPDF(drawing)}>
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          
          {/* ============ COMMENTS Button - Always available ============ */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenComments(drawing)}
            className="flex-1 sm:flex-none text-xs h-8 border-purple-500 text-purple-600 relative"
            title="Comments"
          >
            <MessageSquare className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
            Comments
            {drawing.comment_count > 0 && !drawing.unread_comments && (
              <span className="absolute -top-1 -right-1 bg-purple-600 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
                {drawing.comment_count}
              </span>
            )}
            {drawing.unread_comments > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-600 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center animate-pulse">
                {drawing.unread_comments}
              </span>
            )}
          </Button>
          
          {/* ============ N/A Button - Only for pending drawings (not issued/approved) ============ */}
          {canMarkNA && isPending && !hasRevisionPending && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onMarkAsNotApplicable(drawing.id)}
              className="flex-1 sm:flex-none text-xs h-8 border-slate-400 text-slate-600 hover:bg-slate-50"
              title="Mark this drawing as not applicable for this project"
            >
              N/A
            </Button>
          )}
          
          {/* ============ Progress Button - Only for issued drawings ============ */}
          {canShowProgress && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowProgress(!showProgress)}
              className={`flex-1 sm:flex-none text-xs h-8 ${
                showProgress 
                  ? 'border-orange-500 text-orange-600 bg-orange-50' 
                  : 'border-slate-300 text-slate-600'
              }`}
              title="View contractor progress"
            >
              <HardHat className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
              Progress
            </Button>
          )}
        </div>
      </div>
      
      {/* Contractor Progress Section for Issued Drawings */}
      {canShowProgress && showProgress && (
        <div className="mt-4 pt-4 border-t border-slate-200">
          <div className="flex items-center gap-2 mb-3">
            <HardHat className="w-4 h-4 text-orange-600" />
            <span className="text-sm font-medium text-slate-700">Contractor Progress</span>
          </div>
          <div className="space-y-2">
            {projectContractors.map((contractor) => (
              <ContractorProgressTracker
                key={contractor.id}
                drawingId={drawing.id}
                contractorId={contractor.id}
                contractorName={contractor.name}
                contractorType={contractor.contractor_type || contractor.type || 'Other'}
                user={user}
                onProgressUpdate={onProgressUpdate}
              />
            ))}
          </div>
        </div>
      )}
    </CardContent>
  </Card>
  );
};
