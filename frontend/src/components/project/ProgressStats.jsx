/**
 * Progress Stats Component
 * Displays drawing progress statistics
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, Circle, AlertCircle, Clock, FileText } from 'lucide-react';

export default function ProgressStats({ drawings = [] }) {
  // Calculate statistics
  const stats = React.useMemo(() => {
    const total = drawings.length;
    const notApplicable = drawings.filter(d => d.is_not_applicable).length;
    const applicable = total - notApplicable;
    const issued = drawings.filter(d => d.is_issued).length;
    const approved = drawings.filter(d => d.is_approved && !d.is_issued).length;
    const underReview = drawings.filter(d => d.file_url && !d.is_approved && !d.is_issued && !d.is_not_applicable).length;
    const pending = drawings.filter(d => !d.file_url && !d.is_approved && !d.is_issued && !d.is_not_applicable).length;
    
    const completed = issued + approved;
    const progress = applicable > 0 ? Math.round((completed / applicable) * 100) : 0;

    // Count overdue
    const now = new Date();
    const overdue = drawings.filter(d => {
      if (!d.due_date || d.is_issued || d.is_not_applicable) return false;
      return new Date(d.due_date) < now;
    }).length;

    return {
      total,
      applicable,
      issued,
      approved,
      underReview,
      pending,
      notApplicable,
      progress,
      overdue
    };
  }, [drawings]);

  const statItems = [
    {
      label: 'Issued',
      value: stats.issued,
      icon: CheckCircle2,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      label: 'Approved',
      value: stats.approved,
      icon: CheckCircle2,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      label: 'Under Review',
      value: stats.underReview,
      icon: Clock,
      color: 'text-amber-600',
      bgColor: 'bg-amber-100'
    },
    {
      label: 'Pending',
      value: stats.pending,
      icon: Circle,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100'
    }
  ];

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center gap-6">
          {/* Progress Circle */}
          <div className="flex items-center gap-4">
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  className="text-gray-200"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${stats.progress * 2.26} 226`}
                  className="text-green-500 transition-all duration-500"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold">{stats.progress}%</span>
              </div>
            </div>
            <div>
              <p className="font-semibold text-lg">Project Progress</p>
              <p className="text-sm text-gray-500">
                {stats.issued + stats.approved} of {stats.applicable} drawings complete
              </p>
              {stats.notApplicable > 0 && (
                <p className="text-xs text-gray-400">
                  ({stats.notApplicable} marked N/A)
                </p>
              )}
            </div>
          </div>

          {/* Stat Cards */}
          <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {statItems.map((item) => (
              <div
                key={item.label}
                className={`${item.bgColor} rounded-lg p-3 text-center`}
              >
                <item.icon className={`w-5 h-5 mx-auto mb-1 ${item.color}`} />
                <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
                <p className="text-xs text-gray-600">{item.label}</p>
              </div>
            ))}
          </div>

          {/* Overdue Warning */}
          {stats.overdue > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <div>
                <p className="font-medium text-red-700">{stats.overdue} Overdue</p>
                <p className="text-xs text-red-600">Drawings past due date</p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
