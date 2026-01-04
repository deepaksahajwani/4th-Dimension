/**
 * Drawing status utilities and constants
 */

export const DRAWING_CATEGORIES = ['Architecture', 'Interior', 'Landscape', 'Planning'];

export const DRAWING_STATUSES = {
  PENDING: 'pending',
  UNDER_REVIEW: 'under_review',
  APPROVED: 'approved',
  ISSUED: 'issued',
  NOT_APPLICABLE: 'not_applicable'
};

/**
 * Get drawing status display info
 */
export function getDrawingStatus(drawing) {
  if (!drawing) return { label: 'Unknown', color: 'gray', variant: 'secondary' };
  
  if (drawing.is_not_applicable) {
    return { 
      label: 'N/A', 
      color: 'gray', 
      variant: 'outline',
      bgClass: 'bg-gray-100',
      textClass: 'text-gray-600'
    };
  }
  
  if (drawing.is_issued) {
    return { 
      label: 'Issued', 
      color: 'green', 
      variant: 'default',
      bgClass: 'bg-green-100',
      textClass: 'text-green-700'
    };
  }
  
  if (drawing.is_approved) {
    return { 
      label: 'Approved', 
      color: 'blue', 
      variant: 'secondary',
      bgClass: 'bg-blue-100',
      textClass: 'text-blue-700'
    };
  }
  
  if (drawing.under_review || drawing.file_url) {
    return { 
      label: 'Under Review', 
      color: 'amber', 
      variant: 'outline',
      bgClass: 'bg-amber-100',
      textClass: 'text-amber-700'
    };
  }
  
  return { 
    label: 'Pending', 
    color: 'gray', 
    variant: 'outline',
    bgClass: 'bg-gray-100',
    textClass: 'text-gray-600'
  };
}

/**
 * Calculate project progress from drawings
 */
export function calculateProjectProgress(drawings) {
  if (!drawings || drawings.length === 0) return 0;
  
  const applicableDrawings = drawings.filter(d => !d.is_not_applicable);
  if (applicableDrawings.length === 0) return 100;
  
  const completedDrawings = applicableDrawings.filter(d => d.is_issued || d.is_approved);
  return Math.round((completedDrawings.length / applicableDrawings.length) * 100);
}

/**
 * Get progress breakdown
 */
export function getProgressBreakdown(drawings) {
  if (!drawings || drawings.length === 0) {
    return {
      total: 0,
      pending: 0,
      underReview: 0,
      approved: 0,
      issued: 0,
      notApplicable: 0
    };
  }
  
  return {
    total: drawings.length,
    pending: drawings.filter(d => !d.file_url && !d.is_approved && !d.is_issued && !d.is_not_applicable).length,
    underReview: drawings.filter(d => d.file_url && !d.is_approved && !d.is_issued && !d.is_not_applicable).length,
    approved: drawings.filter(d => d.is_approved && !d.is_issued).length,
    issued: drawings.filter(d => d.is_issued).length,
    notApplicable: drawings.filter(d => d.is_not_applicable).length
  };
}

/**
 * Sort drawings by category and status
 */
export function sortDrawings(drawings, sortBy = 'category') {
  if (!drawings) return [];
  
  const sorted = [...drawings];
  
  switch (sortBy) {
    case 'category':
      return sorted.sort((a, b) => {
        const catOrder = DRAWING_CATEGORIES.indexOf(a.category) - DRAWING_CATEGORIES.indexOf(b.category);
        if (catOrder !== 0) return catOrder;
        return (a.name || '').localeCompare(b.name || '');
      });
    
    case 'status':
      const statusOrder = ['pending', 'under_review', 'approved', 'issued', 'not_applicable'];
      return sorted.sort((a, b) => {
        const aStatus = getDrawingStatusKey(a);
        const bStatus = getDrawingStatusKey(b);
        return statusOrder.indexOf(aStatus) - statusOrder.indexOf(bStatus);
      });
    
    case 'due_date':
      return sorted.sort((a, b) => {
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return new Date(a.due_date) - new Date(b.due_date);
      });
    
    case 'name':
      return sorted.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
    
    default:
      return sorted;
  }
}

function getDrawingStatusKey(drawing) {
  if (drawing.is_not_applicable) return 'not_applicable';
  if (drawing.is_issued) return 'issued';
  if (drawing.is_approved) return 'approved';
  if (drawing.file_url) return 'under_review';
  return 'pending';
}

/**
 * Group drawings by category
 */
export function groupDrawingsByCategory(drawings) {
  if (!drawings) return {};
  
  return drawings.reduce((groups, drawing) => {
    const category = drawing.category || 'Other';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(drawing);
    return groups;
  }, {});
}

/**
 * Filter drawings
 */
export function filterDrawings(drawings, filters = {}) {
  if (!drawings) return [];
  
  let filtered = [...drawings];
  
  if (filters.category && filters.category !== 'all') {
    filtered = filtered.filter(d => d.category === filters.category);
  }
  
  if (filters.status && filters.status !== 'all') {
    filtered = filtered.filter(d => {
      const status = getDrawingStatusKey(d);
      return status === filters.status;
    });
  }
  
  if (filters.search) {
    const searchLower = filters.search.toLowerCase();
    filtered = filtered.filter(d => 
      (d.name || '').toLowerCase().includes(searchLower) ||
      (d.category || '').toLowerCase().includes(searchLower)
    );
  }
  
  if (filters.overdue) {
    const now = new Date();
    filtered = filtered.filter(d => {
      if (!d.due_date || d.is_issued) return false;
      return new Date(d.due_date) < now;
    });
  }
  
  return filtered;
}

export default {
  DRAWING_CATEGORIES,
  DRAWING_STATUSES,
  getDrawingStatus,
  calculateProjectProgress,
  getProgressBreakdown,
  sortDrawings,
  groupDrawingsByCategory,
  filterDrawings
};
