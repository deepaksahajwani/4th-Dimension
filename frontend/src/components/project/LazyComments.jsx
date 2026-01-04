/**
 * Lazy Comments Section
 * Comments load only when user clicks "Show Comments"
 */

import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { MessageCircle, Loader2, Send, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { getRelativeTime } from '@/utils/dateUtils';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function LazyComments({
  drawingId,
  commentCount = 0,
  currentUser,
  onCommentAdded
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [localCount, setLocalCount] = useState(commentCount);

  const loadComments = useCallback(async () => {
    if (loaded || loading) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/drawings/${drawingId}/comments`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setComments(response.data);
      setLocalCount(response.data.length);
      setLoaded(true);
    } catch (error) {
      console.error('Error loading comments:', error);
      toast.error('Failed to load comments');
    } finally {
      setLoading(false);
    }
  }, [drawingId, loaded, loading]);

  const toggleExpanded = () => {
    if (!isExpanded && !loaded) {
      loadComments();
    }
    setIsExpanded(!isExpanded);
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/drawings/${drawingId}/comments`,
        { comment_text: newComment, requires_revision: false },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Add to local comments
      const newCommentObj = {
        id: Date.now().toString(),
        user_id: currentUser?.id,
        user_name: currentUser?.name || 'You',
        user_role: currentUser?.role,
        comment_text: newComment,
        created_at: new Date().toISOString()
      };

      setComments(prev => [newCommentObj, ...prev]);
      setLocalCount(prev => prev + 1);
      setNewComment('');
      toast.success('Comment added');
      onCommentAdded?.();
    } catch (error) {
      console.error('Error submitting comment:', error);
      toast.error('Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="border-t pt-3 mt-3">
      {/* Toggle button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={toggleExpanded}
        className="w-full justify-between text-gray-600 hover:text-gray-900"
      >
        <span className="flex items-center gap-2">
          <MessageCircle className="w-4 h-4" />
          Comments {localCount > 0 && `(${localCount})`}
        </span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </Button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="mt-3 space-y-3">
          {/* Loading state */}
          {loading && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            </div>
          )}

          {/* Comments list */}
          {loaded && (
            <>
              {comments.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-2">
                  No comments yet
                </p>
              ) : (
                <div className="max-h-48 overflow-y-auto space-y-2">
                  {comments.map((comment) => (
                    <div
                      key={comment.id}
                      className={`p-2 rounded-lg text-sm ${
                        comment.user_id === currentUser?.id
                          ? 'bg-blue-50 ml-4'
                          : 'bg-gray-50 mr-4'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-xs">
                          {comment.user_name}
                        </span>
                        <span className="text-xs text-gray-400">
                          {getRelativeTime(comment.created_at)}
                        </span>
                      </div>
                      <p className="text-gray-700">{comment.comment_text}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Add comment input */}
              <div className="flex gap-2">
                <Textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a comment..."
                  rows={2}
                  className="text-sm"
                  disabled={submitting}
                />
                <Button
                  size="sm"
                  onClick={submitComment}
                  disabled={!newComment.trim() || submitting}
                  className="self-end"
                >
                  {submitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
