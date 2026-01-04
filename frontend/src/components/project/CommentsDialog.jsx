/**
 * Comments Dialog Component
 * Handles viewing and adding comments to drawings
 */

import React, { useState, useEffect, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Send, Mic, Square, Play, Pause, X, Upload, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { formatDateTime, getRelativeTime } from '@/utils/dateUtils';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function CommentsDialog({
  open,
  onOpenChange,
  drawing,
  currentUser,
  onCommentAdded
}) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [markForRevision, setMarkForRevision] = useState(false);
  
  // Voice recording
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const timerRef = useRef(null);
  
  // File attachment
  const [attachedFile, setAttachedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Fetch comments when dialog opens
  useEffect(() => {
    if (open && drawing) {
      fetchComments();
    }
  }, [open, drawing]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const fetchComments = async () => {
    if (!drawing) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(
        `${API}/drawings/${drawing.id}/comments`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setComments(res.data);
    } catch (error) {
      console.error('Error fetching comments:', error);
      toast.error('Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);
      
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Error starting recording:', error);
      toast.error('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const clearAudio = () => {
    setAudioBlob(null);
    setRecordingTime(0);
  };

  const handleSubmit = async () => {
    if (!newComment.trim() && !audioBlob && !attachedFile) {
      toast.error('Please enter a comment, record audio, or attach a file');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      
      if (audioBlob || attachedFile) {
        // Use multipart form data for files
        const formData = new FormData();
        formData.append('text', newComment);
        if (audioBlob) {
          formData.append('voice_note', audioBlob, 'voice_note.webm');
        }
        if (attachedFile) {
          formData.append('file', attachedFile);
        }
        
        await axios.post(
          `${API}/projects/${drawing.project_id}/comments`,
          formData,
          { 
            headers: { 
              Authorization: `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            } 
          }
        );
      } else {
        // Simple text comment on drawing
        await axios.post(
          `${API}/drawings/${drawing.id}/comments`,
          {
            comment_text: newComment,
            requires_revision: markForRevision
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }

      toast.success('Comment added');
      setNewComment('');
      setMarkForRevision(false);
      setAudioBlob(null);
      setAttachedFile(null);
      await fetchComments();
      onCommentAdded?.();
    } catch (error) {
      console.error('Error adding comment:', error);
      toast.error('Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
            Comments - {drawing?.name}
          </DialogTitle>
        </DialogHeader>

        {/* Comments List */}
        <div className="flex-1 overflow-y-auto space-y-3 min-h-[200px] max-h-[300px] p-2">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : comments.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No comments yet</p>
          ) : (
            comments.map((comment) => (
              <div
                key={comment.id}
                className={`p-3 rounded-lg ${
                  comment.user_id === currentUser?.id
                    ? 'bg-blue-50 ml-8'
                    : 'bg-gray-50 mr-8'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">
                    {comment.user_name}
                    <span className="text-gray-400 font-normal ml-2">
                      ({comment.user_role})
                    </span>
                  </span>
                  <span className="text-xs text-gray-400">
                    {getRelativeTime(comment.created_at)}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{comment.comment_text}</p>
                {comment.requires_revision && (
                  <span className="inline-block mt-2 text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                    Revision Requested
                  </span>
                )}
              </div>
            ))
          )}
        </div>

        {/* Add Comment Form */}
        <div className="border-t pt-4 space-y-3">
          <Textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Type your comment..."
            rows={3}
            disabled={submitting}
          />

          {/* Audio Recording */}
          {audioBlob && (
            <div className="flex items-center gap-2 p-2 bg-gray-100 rounded">
              <audio src={URL.createObjectURL(audioBlob)} controls className="h-8" />
              <Button variant="ghost" size="sm" onClick={clearAudio}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}

          {/* Attached File */}
          {attachedFile && (
            <div className="flex items-center gap-2 p-2 bg-gray-100 rounded">
              <span className="text-sm">{attachedFile.name}</span>
              <Button variant="ghost" size="sm" onClick={() => setAttachedFile(null)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}

          {/* Revision Checkbox */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="revision"
              checked={markForRevision}
              onCheckedChange={setMarkForRevision}
            />
            <Label htmlFor="revision" className="text-sm">
              Request revision for this drawing
            </Label>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              {/* Voice Recording Button */}
              <Button
                variant="outline"
                size="sm"
                onClick={isRecording ? stopRecording : startRecording}
                className={isRecording ? 'text-red-500' : ''}
              >
                {isRecording ? (
                  <>
                    <Square className="w-4 h-4 mr-1" />
                    {formatTime(recordingTime)}
                  </>
                ) : (
                  <Mic className="w-4 h-4" />
                )}
              </Button>

              {/* File Attachment */}
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={(e) => setAttachedFile(e.target.files?.[0])}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-4 h-4" />
              </Button>
            </div>

            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
