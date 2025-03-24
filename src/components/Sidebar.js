import React, { useState, useRef } from 'react';
import FileExplorer from './FileExplorer';
import ThemeSelector from './ThemeSelector';

const Sidebar = ({
  files,
  currentFile,
  onFileSelect,
  onFileCreate,
  onFileRename,
  onFileDelete,
  currentTheme,
  onThemeChange,
  resizable = true
}) => {
  const [width, setWidth] = useState(250); // Default sidebar width
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(0);
  const resizeHandleRef = useRef(null);
  
  // Sidebar sections
  const [expandedSections, setExpandedSections] = useState({
    files: true,
    themes: false
  });

  // Toggle section expand/collapse
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Setup resize handlers
  React.useEffect(() => {
    if (!resizable) return;

    const handleMouseDown = (e) => {
      e.preventDefault();
      setIsDragging(true);
      setStartX(e.clientX);
      setStartWidth(width);
    };

    const handleMouseMove = (e) => {
      if (!isDragging) return;
      
      // Calculate new width
      const newWidth = Math.max(180, Math.min(400, startWidth + (e.clientX - startX)));
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    const resizeHandle = resizeHandleRef.current;
    if (resizeHandle) {
      resizeHandle.addEventListener('mousedown', handleMouseDown);
    }

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      if (resizeHandle) {
        resizeHandle.removeEventListener('mousedown', handleMouseDown);
      }
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, startX, startWidth, width, resizable]);

  return (
    <div 
      className="sidebar"
      style={{
        width: `${width}px`,
        height: '100%',
        backgroundColor: '#252526',
        borderRight: '1px solid #333',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        zIndex: 10
      }}
    >
      {/* Resize handle */}
      {resizable && (
        <div 
          ref={resizeHandleRef}
          className="resize-handle"
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '5px',
            height: '100%',
            cursor: 'ew-resize',
            zIndex: 20
          }}
        />
      )}
      
      {/* Files section */}
      <div className="sidebar-section">
        <div 
          className="sidebar-section-header"
          onClick={() => toggleSection('files')}
          style={{
            padding: '8px 10px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#2D2D2D',
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          <span style={{ fontWeight: 'bold' }}>FILES</span>
          <span>{expandedSections.files ? '▼' : '▶'}</span>
        </div>
        
        {expandedSections.files && (
          <div className="sidebar-section-content" style={{ padding: '8px 0' }}>
            <FileExplorer 
              files={files}
              currentFile={currentFile}
              onFileSelect={onFileSelect}
              onFileCreate={onFileCreate}
              onFileRename={onFileRename}
              onFileDelete={onFileDelete}
            />
          </div>
        )}
      </div>
      
      {/* Themes section */}
      <div className="sidebar-section">
        <div 
          className="sidebar-section-header"
          onClick={() => toggleSection('themes')}
          style={{
            padding: '8px 10px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#2D2D2D',
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          <span style={{ fontWeight: 'bold' }}>THEMES</span>
          <span>{expandedSections.themes ? '▼' : '▶'}</span>
        </div>
        
        {expandedSections.themes && (
          <div className="sidebar-section-content" style={{ padding: '8px 0' }}>
            <ThemeSelector
              currentTheme={currentTheme}
              onThemeChange={onThemeChange}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;