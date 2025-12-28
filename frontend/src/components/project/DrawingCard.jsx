import React, { useState, useEffect } from 'react';
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
  Trash2,
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
  return <Circle className="w-5 h-5 text-slate-300" />;
};

const getDrawingStatusText = (drawing) => {
  if (drawing.has_pending_revision) return 'Revision Needed';
  if (drawing.is_issued) return 'Issued';
  return 'Pending';
};

const getDrawingStatusColor = (drawing) => {
  if (drawing.has_pending_revision) return 'bg-amber-50 text-amber-700 border-amber-200';
  if (drawing.is_issued) return 'bg-green-50 text-green-700 border-green-200';
  return 'bg-slate-50 text-slate-600 border-slate-200';
};

export const DrawingCard = ({
  drawing,
  user,
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
  onDeleteDrawing,
  onProgressUpdate
}) => {
  const [showProgress, setShowProgress] = useState(false);
  
  // Only show contractor progress for issued drawings
  const canShowProgress = drawing.is_issued && projectContractors.length > 0;
  
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
          {/* STATE 1: PENDING - Show UPLOAD button */}
          {!drawing.file_url && drawing.has_pending_revision !== true && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onToggleIssued(drawing)}
              className="flex-1 sm:flex-none text-xs h-8"
            >
              Upload
            </Button>
          )}
          
          {/* STATE 3: REVISION PENDING - Show RESOLVE button */}
          {drawing.has_pending_revision === true && (
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
          
          {/* STATE 2 & 5: UNDER REVIEW or ISSUED - Show REVISE button */}
          {(drawing.under_review || drawing.is_issued) && drawing.has_pending_revision !== true && (
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
          
          {/* STATE 2: UNDER REVIEW - Show APPROVE button */}
          {drawing.under_review && !drawing.is_approved && drawing.has_pending_revision !== true && (
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
          
          {/* STATE 4: APPROVED - Show ISSUE button */}
          {drawing.is_approved && !drawing.is_issued && drawing.has_pending_revision !== true && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onOpenIssueDialog(drawing)}
              className="flex-1 sm:flex-none text-xs h-8 border-blue-500 text-blue-600"
              title="Issue Drawing"
            >
              Issue Drawing
            </Button>
          )}
          
          {/* PDF Button */}
          {drawing.file_url && (drawing.under_review || drawing.is_approved || drawing.is_issued || drawing.has_pending_revision === true) && (
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
                <DropdownMenuItem onClick={() => onDownloadPDF(drawing)}>
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          
          {/* Comment Button */}
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
          
          {/* Mark as N/A Button */}
          {!drawing.is_issued && (
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
          
          {user?.role === 'owner' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDeleteDrawing(drawing.id)}
              className="text-red-600 hover:text-red-700 text-xs h-8 px-2 sm:px-3"
            >
              <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
            </Button>
          )}
        </div>
      </div>
    </CardContent>
  </Card>
);
