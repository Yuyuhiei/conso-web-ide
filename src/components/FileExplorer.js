import React, { useState } from 'react';

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
      // Make sure file has .cns extension
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
      // Make sure file has .cns extension
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
      <div 
        className="file-explorer-actions" 
        style={{ 
          padding: '0 10px 8px',
          display: 'flex',
          justifyContent: 'space-between',
          borderBottom: '1px solid #333'
        }}
      >
        <button 
          onClick={handleCreateNewFile}
          style={{
            backgroundColor: '#0E639C',
            color: 'white',
            border: 'none',
            padding: '4px 8px',
            borderRadius: '2px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          New File
        </button>
        
        <span style={{ color: '#888', fontSize: '12px' }}>
          {files.length} / 10 files
        </span>
      </div>
      
      {/* New file input */}
      {isCreatingNew && (
        <div style={{ padding: '8px 10px', borderBottom: '1px solid #333' }}>
          <form onSubmit={handleNewFileSubmit}>
            <input
              type="text"
              value={newFileInput}
              onChange={handleNewFileChange}
              placeholder="filename.cns"
              autoFocus
              style={{
                width: '100%',
                backgroundColor: '#3C3C3C',
                color: 'white',
                border: '1px solid #0E639C',
                padding: '4px',
                outline: 'none',
                fontSize: '12px'
              }}
            />
          </form>
        </div>
      )}
      
      {/* Files list */}
      <div className="file-list" style={{ overflowY: 'auto' }}>
        {files.length === 0 ? (
          <div style={{ padding: '10px', color: '#888', fontSize: '12px', fontStyle: 'italic' }}>
            No files. Create a new file to get started.
          </div>
        ) : (
          files.map(file => (
            <div 
              key={file.id}
              className={`file-item ${currentFile && currentFile.id === file.id ? 'active' : ''}`}
              style={{
                padding: '6px 10px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                backgroundColor: currentFile && currentFile.id === file.id ? '#37373D' : 'transparent',
                borderLeft: currentFile && currentFile.id === file.id ? '2px solid #0E639C' : '2px solid transparent',
                paddingLeft: currentFile && currentFile.id === file.id ? '8px' : '10px'
              }}
            >
              {editingFile === file.id ? (
                <form onSubmit={handleRenameSubmit} style={{ flex: 1 }}>
                  <input
                    type="text"
                    value={newFileName}
                    onChange={handleRenameChange}
                    autoFocus
                    style={{
                      width: '100%',
                      backgroundColor: '#3C3C3C',
                      color: 'white',
                      border: '1px solid #0E639C',
                      padding: '2px 4px',
                      outline: 'none',
                      fontSize: '12px'
                    }}
                  />
                </form>
              ) : (
                <>
                  <div 
                    className="file-name" 
                    onClick={() => onFileSelect(file.id)}
                    style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                  >
                    {file.name}
                  </div>
                  
                  <div className="file-actions" style={{ display: 'flex', gap: '4px' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRenameStart(file);
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#CCC',
                        cursor: 'pointer',
                        padding: '2px',
                        fontSize: '10px'
                      }}
                      title="Rename file"
                    >
                      ✏️
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteFile(file.id);
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#CCC',
                        cursor: 'pointer',
                        padding: '2px',
                        fontSize: '10px'
                      }}
                      title="Delete file"
                    >
                      🗑️
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