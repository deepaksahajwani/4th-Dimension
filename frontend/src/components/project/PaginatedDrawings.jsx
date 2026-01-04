/**
 * Paginated Drawings List Component
 * Loads drawings 10 at a time for better performance
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, ChevronDown } from 'lucide-react';
import axios from 'axios';
import { DrawingCard } from './DrawingCard';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const PAGE_SIZE = 10;

export default function PaginatedDrawings({
  projectId,
  category = null,
  status = null,
  onDrawingAction,
  permissions = {},
  currentUser
}) {
  const [drawings, setDrawings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchDrawings = useCallback(async (pageNum = 1, append = false) => {
    if (!projectId) return;

    const isFirstPage = pageNum === 1;
    if (isFirstPage) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        limit: PAGE_SIZE.toString(),
        skip: ((pageNum - 1) * PAGE_SIZE).toString()
      });

      if (category) params.append('category', category);
      if (status) params.append('status', status);

      const response = await axios.get(
        `${API}/v2/projects/${projectId}/drawings?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const data = response.data;
      
      if (append) {
        setDrawings(prev => [...prev, ...data.drawings]);
      } else {
        setDrawings(data.drawings);
      }
      
      setHasMore(data.has_more);
      setTotal(data.total);
      setPage(pageNum);
    } catch (error) {
      console.error('Error fetching drawings:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [projectId, category, status]);

  useEffect(() => {
    fetchDrawings(1, false);
  }, [fetchDrawings]);

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      fetchDrawings(page + 1, true);
    }
  };

  const refresh = () => {
    fetchDrawings(1, false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-500">Loading drawings...</span>
      </div>
    );
  }

  if (drawings.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No drawings found</p>
        {(category || status) && (
          <p className="text-sm mt-2">Try adjusting your filters</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Drawing count */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>Showing {drawings.length} of {total} drawings</span>
      </div>

      {/* Drawings grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {drawings.map((drawing) => (
          <DrawingCard
            key={drawing.id}
            drawing={drawing}
            onAction={(action) => {
              onDrawingAction?.(action, drawing);
              // Refresh after action
              setTimeout(refresh, 500);
            }}
            permissions={permissions}
            currentUser={currentUser}
          />
        ))}
      </div>

      {/* Load more button */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <Button
            variant="outline"
            onClick={loadMore}
            disabled={loadingMore}
            className="gap-2"
          >
            {loadingMore ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading...
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                Load More ({total - drawings.length} remaining)
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
