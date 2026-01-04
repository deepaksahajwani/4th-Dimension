/**
 * ChatView Component - WhatsApp-like Chat UI
 * Reusable component for project and drawing comments
 * Mobile-first, clean, minimal cognitive load
 */

import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, Mic, Square, X, Paperclip, Loader2, Play, Pause } from 'lucide-react';
import { toast } from 'sonner';

// Format time for display (e.g., "10:30 AM")
const formatTime = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// Format recording time
const formatRecordingTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// Get day label for grouping
const getDayLabel = (dateString) => {
  const date = new Date(dateString);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  // Reset time for comparison
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const yesterdayOnly = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
  
  if (dateOnly.getTime() === todayOnly.getTime()) {
    return 'Today';
  } else if (dateOnly.getTime() === yesterdayOnly.getTime()) {
    return 'Yesterday';
  } else {
    return date.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });
  }
};

// Group messages by day
const groupMessagesByDay = (messages) => {
  if (!messages || messages.length === 0) return [];
  
  const groups = [];
  let currentDay = null;
  let currentGroup = null;
  
  // Sort by created_at ascending (oldest first for display)
  const sortedMessages = [...messages].sort((a, b) => 
    new Date(a.created_at) - new Date(b.created_at)
  );
  
  sortedMessages.forEach(message => {
    const dayLabel = getDayLabel(message.created_at);
    
    if (dayLabel !== currentDay) {
      currentDay = dayLabel;
      currentGroup = { day: dayLabel, messages: [] };
      groups.push(currentGroup);
    }
    
    currentGroup.messages.push(message);
  });
  
  return groups;
};

// Voice Note Player component
const VoiceNotePlayer = ({ src }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const audioRef = useRef(null);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <div className="flex items-center gap-2 min-w-[140px]">
      <audio 
        ref={audioRef}
        src={src}
        onLoadedMetadata={(e) => setDuration(e.target.duration)}
        onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
        onEnded={() => setIsPlaying(false)}
      />
      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0 rounded-full"
        onClick={togglePlay}
      >
        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
      </Button>
      <div className="flex-1">
        <div className="h-1 bg-white/30 rounded-full overflow-hidden">
          <div 
            className="h-full bg-white/70 transition-all"
            style={{ width: duration ? `${(currentTime / duration) * 100}%` : '0%' }}
          />
        </div>
        <span className="text-[10px] opacity-70">
          {formatRecordingTime(Math.floor(currentTime))} / {formatRecordingTime(Math.floor(duration || 0))}
        </span>
      </div>
    </div>
  );
};

// Single Message Bubble
const MessageBubble = ({ message, isOwn, backendUrl }) => {
  const voiceUrl = message.voice_note_url 
    ? (message.voice_note_url.startsWith('http') ? message.voice_note_url : `${backendUrl}${message.voice_note_url}`)
    : null;
  const fileUrl = message.file_url 
    ? (message.file_url.startsWith('http') ? message.file_url : `${backendUrl}${message.file_url}`)
    : null;
  
  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-1`}>
      <div
        className={`max-w-[85%] px-3 py-2 rounded-2xl ${
          isOwn
            ? 'bg-purple-600 text-white rounded-br-md'
            : 'bg-white text-slate-800 rounded-bl-md shadow-sm border border-slate-100'
        }`}
      >
        {/* Sender name (only for others) */}
        {!isOwn && (
          <p className="text-xs font-medium text-purple-600 mb-0.5">
            {message.user_name || message.userName || 'User'}
          </p>
        )}
        
        {/* Text content */}
        {(message.text || message.comment_text) && (
          <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
            {message.text || message.comment_text}
          </p>
        )}
        
        {/* Voice note */}
        {voiceUrl && (
          <div className="mt-1">
            <VoiceNotePlayer src={voiceUrl} />
          </div>
        )}
        
        {/* File attachment */}
        {fileUrl && (
          <a 
            href={fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex items-center gap-1 mt-1.5 text-xs ${
              isOwn ? 'text-purple-200 hover:text-white' : 'text-purple-600 hover:text-purple-700'
            }`}
          >
            <Paperclip className="w-3 h-3" />
            {message.file_name || 'View attachment'}
          </a>
        )}
        
        {/* Revision badge */}
        {message.requires_revision && (
          <span className={`inline-block mt-1.5 text-[10px] px-2 py-0.5 rounded-full ${
            isOwn 
              ? 'bg-white/20 text-white' 
              : 'bg-amber-100 text-amber-700'
          }`}>
            ⚠️ Revision Requested
          </span>
        )}
        
        {/* Timestamp */}
        <p className={`text-[10px] mt-1 ${isOwn ? 'text-purple-200' : 'text-slate-400'}`}>
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
};

// Day Separator
const DaySeparator = ({ label }) => (
  <div className="flex items-center justify-center my-3">
    <span className="px-3 py-1 bg-slate-200/80 text-slate-600 text-xs rounded-full font-medium">
      {label}
    </span>
  </div>
);

// Main ChatView Component
export default function ChatView({
  messages = [],
  currentUserId,
  onSendMessage,
  loading = false,
  placeholder = "Type a message...",
  backendUrl = process.env.REACT_APP_BACKEND_URL,
  className = "",
  showVoiceRecording = true,
  showFileAttachment = true,
  emptyStateText = "No messages yet",
  emptyStateSubtext = "Start the conversation"
}) {
  const [newMessage, setNewMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  
  // Voice recording
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
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
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
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
    if (!newMessage.trim() && !audioBlob && !attachedFile) return;
    
    setSubmitting(true);
    try {
      await onSendMessage({
        text: newMessage.trim(),
        file: attachedFile,
        voiceNote: audioBlob
      });
      
      // Reset form
      setNewMessage('');
      setAudioBlob(null);
      setAttachedFile(null);
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
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

  const isOwnMessage = (message) => {
    return message.user_id === currentUserId || message.userId === currentUserId;
  };

  const groupedMessages = groupMessagesByDay(messages);
  const hasContent = newMessage.trim() || audioBlob || attachedFile;

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-3 py-2 bg-slate-50/50 min-h-[200px]">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <div className="w-14 h-14 rounded-full bg-slate-200 flex items-center justify-center mb-2">
              <Send className="w-6 h-6 text-slate-400" />
            </div>
            <p className="text-sm">{emptyStateText}</p>
            <p className="text-xs mt-0.5">{emptyStateSubtext}</p>
          </div>
        ) : (
          <>
            {groupedMessages.map((group, groupIndex) => (
              <div key={groupIndex}>
                <DaySeparator label={group.day} />
                {group.messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    isOwn={isOwnMessage(message)}
                    backendUrl={backendUrl}
                  />
                ))}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-2 bg-white border-t border-slate-100">
        {/* Attached file preview */}
        {attachedFile && (
          <div className="flex items-center gap-2 px-3 py-1.5 mb-2 bg-slate-100 rounded-lg text-sm">
            <Paperclip className="w-4 h-4 text-slate-500" />
            <span className="flex-1 text-slate-600 truncate text-xs">{attachedFile.name}</span>
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => setAttachedFile(null)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        )}
        
        {/* Voice recording preview */}
        {audioBlob && (
          <div className="flex items-center gap-2 px-3 py-1.5 mb-2 bg-purple-50 rounded-lg">
            <audio src={URL.createObjectURL(audioBlob)} controls className="h-7 flex-1" />
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={clearAudio}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        )}
        
        <div className="flex items-end gap-1.5">
          {/* Attachment button */}
          {showFileAttachment && (
            <>
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
                className="h-9 w-9 p-0 text-slate-500 hover:text-slate-700 shrink-0"
                onClick={() => fileInputRef.current?.click()}
                disabled={submitting}
              >
                <Paperclip className="w-5 h-5" />
              </Button>
            </>
          )}
          
          {/* Text input */}
          <div className="flex-1">
            <input
              ref={inputRef}
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="w-full px-4 py-2 bg-slate-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={submitting || isRecording}
            />
          </div>
          
          {/* Voice / Send button */}
          {hasContent ? (
            <Button
              size="sm"
              className="h-9 w-9 p-0 rounded-full bg-purple-600 hover:bg-purple-700 shrink-0"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          ) : showVoiceRecording ? (
            <Button
              size="sm"
              className={`h-9 w-9 p-0 rounded-full shrink-0 ${
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
                <Mic className="w-4 h-4" />
              )}
            </Button>
          ) : (
            <Button
              size="sm"
              className="h-9 w-9 p-0 rounded-full bg-slate-200 text-slate-400 shrink-0"
              disabled
            >
              <Send className="w-4 h-4" />
            </Button>
          )}
        </div>
        
        {/* Recording indicator */}
        {isRecording && (
          <div className="flex items-center justify-center gap-2 mt-1.5 text-red-500 text-xs">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            Recording {formatRecordingTime(recordingTime)}
          </div>
        )}
      </div>
    </div>
  );
}
