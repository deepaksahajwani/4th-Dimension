/**
 * Comments Dialog Component - WhatsApp-like UI
 * Mobile-first, clean, minimal cognitive load
 * Available to ALL users (including external users)
 */

import React, { useState, useEffect, useRef } from 'react';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Send, Mic, Square, X, Paperclip, Loader2, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Format time for voice recording
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// Format relative time
const getRelativeTime = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
};

export default function CommentsDialog({
  open,
  onOpenChange,
  drawing,
  currentUser,
  onCommentAdded,
  canRequestRevision = false // Only team leader/owner can request revision
}) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newComment, setNewComment] = useState('');
  
  // Voice recording
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const timerRef = useRef(null);
  
  // File attachment
  const [attachedFile, setAttachedFile] = useState(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Fetch comments when dialog opens
  useEffect(() => {
    if (open && drawing) {
      fetchComments();
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [open, drawing]);

  // Scroll to bottom when comments change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [comments]);

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
        setRecordingTime(t => t + 1);
      }, 1000);
    } catch (error) {
      toast.error('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    setIsRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const clearAudio = () => {
    setAudioBlob(null);
    setRecordingTime(0);
  };

  const handleSubmit = async () => {
    if (!newComment.trim() && !audioBlob && !attachedFile) return;
    
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      
      formData.append('comment_text', newComment.trim() || '');
      formData.append('requires_revision', 'false'); // Simplified - no revision checkbox
      
      if (audioBlob) {
        formData.append('voice_note', audioBlob, 'voice_note.webm');
      }
      
      if (attachedFile) {
        formData.append('file', attachedFile);
      }

      await axios.post(
        `${API}/drawings/${drawing.id}/comments`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      // Reset form
      setNewComment('');
      setAudioBlob(null);
      setAttachedFile(null);
      
      // Refresh comments
      await fetchComments();
      onCommentAdded?.();
      
    } catch (error) {
      console.error('Error posting comment:', error);
      toast.error('Failed to send comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isOwnMessage = (comment) => comment.user_id === currentUser?.id;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[85vh] p-0 gap-0 overflow-hidden flex flex-col rounded-2xl">
        {/* Header - WhatsApp style */}
        <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white">
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-8 w-8 p-0 text-white hover:bg-white/20 sm:hidden"
            onClick={() => onOpenChange(false)}
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-sm truncate">{drawing?.name}</h3>
            <p className="text-xs text-purple-200">
              {comments.length} {comments.length === 1 ? 'message' : 'messages'}
            </p>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50 min-h-[300px] max-h-[400px]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
            </div>
          ) : comments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <div className="w-16 h-16 rounded-full bg-slate-200 flex items-center justify-center mb-3">
                <Send className="w-8 h-8 text-slate-400" />
              </div>
              <p className="text-sm">No messages yet</p>
              <p className="text-xs mt-1">Start the conversation</p>
            </div>
          ) : (
            <>
              {comments.map((comment) => (
                <div
                  key={comment.id}
                  className={`flex ${isOwnMessage(comment) ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                      isOwnMessage(comment)
                        ? 'bg-purple-600 text-white rounded-br-md'
                        : 'bg-white text-slate-800 rounded-bl-md shadow-sm'
                    }`}
                  >
                    {/* Sender name (only for others' messages) */}
                    {!isOwnMessage(comment) && (
                      <p className={`text-xs font-medium mb-1 ${
                        isOwnMessage(comment) ? 'text-purple-200' : 'text-purple-600'
                      }`}>
                        {comment.user_name}
                      </p>
                    )}
                    
                    {/* Message text */}
                    {comment.comment_text && (
                      <p className="text-sm whitespace-pre-wrap break-words">
                        {comment.comment_text}
                      </p>
                    )}
                    
                    {/* Voice note */}
                    {comment.voice_note_url && (
                      <audio 
                        src={`${process.env.REACT_APP_BACKEND_URL}${comment.voice_note_url}`} 
                        controls 
                        className="mt-2 h-8 w-full max-w-[200px]"
                      />
                    )}
                    
                    {/* File attachment */}
                    {comment.file_url && (
                      <a 
                        href={`${process.env.REACT_APP_BACKEND_URL}${comment.file_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`block mt-2 text-xs underline ${
                          isOwnMessage(comment) ? 'text-purple-200' : 'text-purple-600'
                        }`}
                      >
                        📎 View attachment
                      </a>
                    )}
                    
                    {/* Revision badge */}
                    {comment.requires_revision && (
                      <span className={`inline-block mt-2 text-[10px] px-2 py-0.5 rounded-full ${
                        isOwnMessage(comment) 
                          ? 'bg-white/20 text-white' 
                          : 'bg-amber-100 text-amber-700'
                      }`}>
                        ⚠️ Revision Requested
                      </span>
                    )}
                    
                    {/* Timestamp */}
                    <p className={`text-[10px] mt-1 ${
                      isOwnMessage(comment) ? 'text-purple-200' : 'text-slate-400'
                    }`}>
                      {getRelativeTime(comment.created_at)}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area - WhatsApp style */}
        <div className="p-3 bg-white border-t border-slate-100">
          {/* Attached file preview */}
          {attachedFile && (
            <div className="flex items-center gap-2 px-3 py-2 mb-2 bg-slate-100 rounded-lg">
              <Paperclip className="w-4 h-4 text-slate-500" />
              <span className="flex-1 text-xs text-slate-600 truncate">{attachedFile.name}</span>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => setAttachedFile(null)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}
          
          {/* Voice recording preview */}
          {audioBlob && (
            <div className="flex items-center gap-2 px-3 py-2 mb-2 bg-purple-50 rounded-lg">
              <audio src={URL.createObjectURL(audioBlob)} controls className="h-8 flex-1" />
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={clearAudio}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}
          
          <div className="flex items-end gap-2">
            {/* Attachment button */}
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={(e) => setAttachedFile(e.target.files?.[0])}
              accept="image/*,.pdf,.doc,.docx"
            />
            <Button
              variant="ghost"
              size="sm"
              className="h-10 w-10 p-0 text-slate-500 hover:text-slate-700 flex-shrink-0"
              onClick={() => fileInputRef.current?.click()}
              disabled={submitting}
            >
              <Paperclip className="w-5 h-5" />
            </Button>
            
            {/* Text input */}
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                className="w-full px-4 py-2.5 bg-slate-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 pr-12"
                disabled={submitting || isRecording}
              />
            </div>
            
            {/* Voice / Send button */}
            {newComment.trim() || audioBlob || attachedFile ? (
              <Button
                size="sm"
                className="h-10 w-10 p-0 rounded-full bg-purple-600 hover:bg-purple-700 flex-shrink-0"
                onClick={handleSubmit}
                disabled={submitting}
              >
                {submitting ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </Button>
            ) : (
              <Button
                size="sm"
                className={`h-10 w-10 p-0 rounded-full flex-shrink-0 ${
                  isRecording 
                    ? 'bg-red-500 hover:bg-red-600' 
                    : 'bg-slate-200 hover:bg-slate-300 text-slate-600'
                }`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={submitting}
              >
                {isRecording ? (
                  <Square className="w-4 h-4 text-white" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </Button>
            )}
          </div>
          
          {/* Recording indicator */}
          {isRecording && (
            <div className="flex items-center justify-center gap-2 mt-2 text-red-500 text-xs">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              Recording {formatTime(recordingTime)}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
