import React, { useState } from 'react';
import { VscNewFile, VscEdit, VscTrash } from 'react-icons/vsc';
import './FileExplorer.css'; // Import the new CSS file

const FileExplorer = ({
  files,
  currentFile,
  onFileSelect,
  onFileCreate,
  onFileRename,
  onFileDelete
}) => {
  const [editingFile, setEditingFile] = useState(null);
  const [newFileName, setNewFileName] = useState('');
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newFileInput, setNewFileInput] = useState('');

  // Handle file renaming
  const handleRenameStart = (file) => {
    setEditingFile(file.id);
    setNewFileName(file.name);
  };

  const handleRenameChange = (e) => {
    setNewFileName(e.target.value);
  };

  const handleRenameSubmit = (e) => {
    e.preventDefault();
    
    if (newFileName.trim()) {
      let name = newFileName.trim();
      if (!name.endsWith('.cns')) {
        name += '.cns';
      }
      onFileRename(editingFile, name);
    }
    
    setEditingFile(null);
    setNewFileName('');
  };

  // Handle new file creation
  const handleCreateNewFile = () => {
    setIsCreatingNew(true);
    setNewFileInput('');
  };

  const handleNewFileChange = (e) => {
    setNewFileInput(e.target.value);
  };

  const handleNewFileSubmit = (e) => {
    e.preventDefault();
    
    if (newFileInput.trim()) {
      let name = newFileInput.trim();
      if (!name.endsWith('.cns')) {
        name += '.cns';
      }
      onFileCreate(name);
    }
    
    setIsCreatingNew(false);
    setNewFileInput('');
  };

  // Handle file deletion with confirmation
  const handleDeleteFile = (fileId) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      onFileDelete(fileId);
    }
  };

  return (
    <div className="file-explorer">
      <div className="file-explorer-header">
        <button 
          onClick={handleCreateNewFile}
          className="new-file-button"
        >
          <VscNewFile />
          <span>New File</span>
        </button>
        
        <span className="file-count">
          {files.length} / 30 files
        </span>
      </div>
      
      {/* New file input */}
      {isCreatingNew && (
        <div className="new-file-input-wrapper">
          <form onSubmit={handleNewFileSubmit}>
            <input
              type="text"
              value={newFileInput}
              onChange={handleNewFileChange}
              onBlur={() => setIsCreatingNew(false)} // Hide on blur
              placeholder="filename.cns"
              autoFocus
              className="file-input"
            />
          </form>
        </div>
      )}
      
      {/* Files list */}
      <div className="file-list">
        {files.length === 0 && !isCreatingNew ? (
          <div className="empty-list-message">
            No files. Create one to start.
          </div>
        ) : (
          files.map(file => (
            <div 
              key={file.id}
              className={`file-item ${currentFile && currentFile.id === file.id ? 'active' : ''}`}
              onClick={() => editingFile !== file.id && onFileSelect(file.id)}
            >
              {editingFile === file.id ? (
                <form onSubmit={handleRenameSubmit} className="file-rename-form">
                  <input
                    type="text"
                    value={newFileName}
                    onChange={handleRenameChange}
                    onBlur={handleRenameSubmit} // Submit on blur
                    autoFocus
                    className="file-input"
                  />
                </form>
              ) : (
                <>
                  <div className="file-name">
                    {file.name}
                  </div>
                  
                  <div className="file-item-actions">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRenameStart(file);
                      }}
                      className="action-button"
                      title="Rename file"
                    >
                      <VscEdit />
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteFile(file.id);
                      }}
                      className="action-button delete-button"
                      title="Delete file"
                    >
                      <VscTrash />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default FileExplorer;