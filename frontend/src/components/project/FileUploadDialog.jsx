/**
 * File Upload Dialog Component
 * Handles uploading files to drawings (issue/revision)
 */

import React, { useState, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Upload, X, FileText } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function FileUploadDialog({
  open,
  onOpenChange,
  drawing,
  uploadType = 'issue', // 'issue' or 'revision'
  onSuccess
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      if (!allowedTypes.includes(file.type)) {
        toast.error('Please upload a PDF or image file');
        return;
      }
      
      // Validate file size (50MB max)
      if (file.size > 50 * 1024 * 1024) {
        toast.error('File size must be less than 50MB');
        return;
      }
      
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !drawing) return;

    setUploading(true);
    setProgress(0);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', selectedFile);

      const endpoint = uploadType === 'issue' 
        ? `${API}/drawings/${drawing.id}/issue`
        : `${API}/drawings/${drawing.id}/upload-revision`;

      await axios.post(endpoint, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        }
      });

      toast.success(
        uploadType === 'issue' 
          ? 'Drawing issued successfully' 
          : 'Revision uploaded successfully'
      );
      
      setSelectedFile(null);
      setProgress(0);
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      setSelectedFile(null);
      setProgress(0);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {uploadType === 'issue' ? 'Issue Drawing' : 'Upload Revision'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {drawing && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="font-medium">{drawing.name}</p>
              <p className="text-sm text-gray-500">{drawing.category}</p>
            </div>
          )}

          {/* File Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              selectedFile ? 'border-green-500 bg-green-50' : 'border-gray-300 hover:border-gray-400'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            {selectedFile ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="w-8 h-8 text-green-600" />
                <div className="text-left">
                  <p className="font-medium text-green-700">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            ) : (
              <>
                <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600 font-medium">
                  Click to upload or drag and drop
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  PDF, PNG, or JPG (max 50MB)
                </p>
              </>
            )}
          </div>

          {/* Progress Bar */}
          {uploading && (
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-center text-gray-500">
                Uploading... {progress}%
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={uploading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
          >
            {uploading ? 'Uploading...' : (uploadType === 'issue' ? 'Issue Drawing' : 'Upload Revision')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
