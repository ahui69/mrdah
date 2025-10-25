import React, { useState, useCallback, useRef } from 'react';
import { Upload, X, File, Image as ImageIcon } from 'lucide-react';

interface DragDropUploadProps {
  onFilesSelected: (files: File[]) => void;
  maxFiles?: number;
  maxSizeMB?: number;
  acceptedTypes?: string[];
  className?: string;
}

interface FilePreview {
  file: File;
  preview: string;
  id: string;
}

export const DragDropUpload: React.FC<DragDropUploadProps> = ({
  onFilesSelected,
  maxFiles = 5,
  maxSizeMB = 10,
  acceptedTypes = ['image/*', 'text/*', '.pdf', '.doc', '.docx', '.txt', '.md'],
  className = ''
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [filePreviews, setFilePreviews] = useState<FilePreview[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    // Check file size
    const maxBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxBytes) {
      return `Plik ${file.name} jest za duży (max ${maxSizeMB}MB)`;
    }

    // Check file type
    const fileType = file.type || '';
    const fileName = file.name.toLowerCase();
    
    const isAccepted = acceptedTypes.some(type => {
      if (type.startsWith('.')) {
        // Extension check
        return fileName.endsWith(type);
      } else if (type.endsWith('/*')) {
        // MIME category check
        const category = type.split('/')[0];
        return fileType.startsWith(category + '/');
      } else {
        // Exact MIME type check
        return fileType === type;
      }
    });

    if (!isAccepted) {
      return `Nieprawidłowy typ pliku: ${file.name}`;
    }

    return null;
  };

  const processFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;

    setError(null);
    const fileArray = Array.from(files);

    // Check max files limit
    if (filePreviews.length + fileArray.length > maxFiles) {
      setError(`Maksymalna liczba plików: ${maxFiles}`);
      return;
    }

    // Validate files
    const validFiles: File[] = [];
    for (const file of fileArray) {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    // Create previews
    const newPreviews: FilePreview[] = validFiles.map(file => {
      const id = Math.random().toString(36).substring(7);
      let preview = '';

      // Generate preview for images
      if (file.type.startsWith('image/')) {
        preview = URL.createObjectURL(file);
      }

      return { file, preview, id };
    });

    setFilePreviews(prev => [...prev, ...newPreviews]);
    onFilesSelected(validFiles);

  }, [filePreviews.length, maxFiles, onFilesSelected]);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only set false if we're leaving the drop zone entirely
    if (e.currentTarget === e.target) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    processFiles(files);
  }, [processFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    processFiles(e.target.files);
    // Reset input value to allow re-selecting the same file
    e.target.value = '';
  }, [processFiles]);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const removeFile = (id: string) => {
    setFilePreviews(prev => {
      const updated = prev.filter(fp => fp.id !== id);
      
      // Revoke object URL to free memory
      const removed = prev.find(fp => fp.id === id);
      if (removed && removed.preview) {
        URL.revokeObjectURL(removed.preview);
      }
      
      return updated;
    });
  };

  const clearAll = () => {
    // Revoke all object URLs
    filePreviews.forEach(fp => {
      if (fp.preview) {
        URL.revokeObjectURL(fp.preview);
      }
    });
    setFilePreviews([]);
    setError(null);
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <ImageIcon className="w-5 h-5 text-blue-400" />;
    }
    return <File className="w-5 h-5 text-gray-400" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className={`drag-drop-upload ${className}`}>
      {/* Drop Zone */}
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        className={`
          relative border-2 border-dashed rounded-lg p-8
          transition-all duration-200 cursor-pointer
          ${isDragging 
            ? 'border-blue-500 bg-blue-500/10 scale-[1.02]' 
            : 'border-gray-600 hover:border-gray-500 bg-gray-800/50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center space-y-4">
          <Upload className={`w-12 h-12 ${isDragging ? 'text-blue-400' : 'text-gray-400'}`} />
          
          <div className="text-center">
            <p className="text-lg font-medium text-gray-200">
              {isDragging ? 'Upuść pliki tutaj' : 'Przeciągnij i upuść pliki'}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              lub kliknij, aby wybrać ({maxFiles} plików max, {maxSizeMB}MB każdy)
            </p>
          </div>

          <div className="text-xs text-gray-500">
            Akceptowane: {acceptedTypes.slice(0, 3).join(', ')}
            {acceptedTypes.length > 3 && ` +${acceptedTypes.length - 3} more`}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* File Previews */}
      {filePreviews.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-300">
              Wybrane pliki ({filePreviews.length}/{maxFiles})
            </p>
            <button
              onClick={clearAll}
              className="text-xs text-gray-400 hover:text-gray-300 underline"
            >
              Wyczyść wszystkie
            </button>
          </div>

          <div className="space-y-2">
            {filePreviews.map((fp) => (
              <div
                key={fp.id}
                className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
              >
                {/* Preview/Icon */}
                {fp.preview ? (
                  <img
                    src={fp.preview}
                    alt={fp.file.name}
                    className="w-12 h-12 object-cover rounded"
                  />
                ) : (
                  <div className="w-12 h-12 flex items-center justify-center bg-gray-700 rounded">
                    {getFileIcon(fp.file)}
                  </div>
                )}

                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-200 truncate">
                    {fp.file.name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatFileSize(fp.file.size)} • {fp.file.type || 'unknown type'}
                  </p>
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removeFile(fp.id)}
                  className="p-1 hover:bg-gray-700 rounded transition-colors"
                  title="Usuń plik"
                >
                  <X className="w-4 h-4 text-gray-400 hover:text-red-400" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DragDropUpload;
