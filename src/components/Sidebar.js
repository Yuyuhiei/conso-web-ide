import React, { useState, useRef } from 'react';
import FileExplorer from './FileExplorer';
import ThemeSelector from './ThemeSelector';
import { VscFiles, VscColorMode } from 'react-icons/vsc';
import './Sidebar.css';

const Sidebar = ({
  files,
  currentFileId,
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
      style={{ width: `${width}px` }}
    >
      {/* Resize handle */}
      {resizable && (
        <div 
          ref={resizeHandleRef}
          className="resize-handle"
        />
      )}
      
      {/* Files section */}
      <div className="sidebar-section">
        <div 
          className="sidebar-section-header"
          onClick={() => toggleSection('files')}
        >
          <div className="section-title-container">
            <VscFiles />
            <span>FILES</span>
          </div>
          <span className={`section-toggle-icon ${expandedSections.files ? 'expanded' : ''}`}>▶</span>
        </div>
        
        {expandedSections.files && (
          <div className="sidebar-section-content">
            <FileExplorer 
              files={files}
              currentFileId={currentFileId}
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
        >
          <div className="section-title-container">
            <VscColorMode />
            <span>THEMES</span>
          </div>
          <span className={`section-toggle-icon ${expandedSections.themes ? 'expanded' : ''}`}>▶</span>
        </div>
        
        {expandedSections.themes && (
          <div className="sidebar-section-content">
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