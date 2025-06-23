import React, { useState, useRef, useEffect } from 'react';
import FileExplorer from './FileExplorer';
import ThemeSelector from './ThemeSelector';
import ConsoChatbot from './ConsoChatbot'; // Import the new component
import { VscFiles, VscColorMode, VscBook, VscBeaker, VscCommentDiscussion } from 'react-icons/vsc'; // Add new icon
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
  onSampleSelect,
  resizable = true
}) => {
  const [width, setWidth] = useState(250);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(0);
  const resizeHandleRef = useRef(null);
  
  const [expandedSections, setExpandedSections] = useState({
    files: false,
    samples: false,
    themes: false,
    chatbot: false
  });

  const [sampleFiles, setSampleFiles] = useState([]); // State to hold sample filenames

  // Fetch the list of sample programs when the component mounts
  useEffect(() => {
    fetch('/samples/manifest.json')
      .then(response => response.json())
      .then(data => setSampleFiles(data))
      .catch(error => console.error("Could not load sample programs manifest:", error));
  }, []); // Empty array ensures this runs only once

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  // Function to load the content of a selected sample file
  const handleLoadSample = async (fileName) => {
    try {
      const response = await fetch(`/samples/${fileName}`);
      const content = await response.text();
      onSampleSelect({ name: fileName, content });
    } catch (error) {
      console.error(`Failed to load sample: ${fileName}`, error);
      // Optionally, show an error to the user
    }
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
    <div className="sidebar" style={{ width: `${width}px` }}>
      {resizable && <div ref={resizeHandleRef} className="resize-handle" />}
      
      {/* Files section */}
      <div className="sidebar-section">
        <div className="sidebar-section-header" onClick={() => toggleSection('files')}>
          <div className="section-title-container"><VscFiles /><span>FILES</span></div>
          <span className={`section-toggle-icon ${expandedSections.files ? 'expanded' : ''}`}>▶</span>
        </div>
        {expandedSections.files && (
          <div className="sidebar-section-content">
            <FileExplorer {...{ files, currentFileId, onFileSelect, onFileCreate, onFileRename, onFileDelete }} />
          </div>
        )}
      </div>
      
      {/* Sample Programs Section */}
      <div className="sidebar-section">
        <div className="sidebar-section-header" onClick={() => toggleSection('samples')}>
          <div className="section-title-container"><VscBeaker /><span>SAMPLE PROGRAMS</span></div>
          <span className={`section-toggle-icon ${expandedSections.samples ? 'expanded' : ''}`}>▶</span>
        </div>
        {expandedSections.samples && (
          <div className="sidebar-section-content">
            {sampleFiles.length > 0 ? (
              sampleFiles.map(fileName => (
                <div 
                  key={fileName} 
                  className="sample-item" 
                  onClick={() => handleLoadSample(fileName)}
                  title={`Load ${fileName}`}
                >
                  {fileName}
                </div>
              ))
            ) : (
              <div className="empty-list-message">Loading samples...</div>
            )}
          </div>
        )}
      </div>

      {/* Themes section */}
      <div className="sidebar-section">
        <div className="sidebar-section-header" onClick={() => toggleSection('themes')}>
          <div className="section-title-container"><VscColorMode /><span>THEMES</span></div>
          <span className={`section-toggle-icon ${expandedSections.themes ? 'expanded' : ''}`}>▶</span>
        </div>
        {expandedSections.themes && (
          <div className="sidebar-section-content">
            <ThemeSelector {...{ currentTheme, onThemeChange }} />
          </div>
        )}
      </div>
      
      {/* Documentation Section */}
      <div className="sidebar-section">
        <a href="/Conso_PL.pdf" target="_blank" rel="noopener noreferrer" className="sidebar-section-header">
          <div className="section-title-container"><VscBook /><span>DOCUMENTATION</span></div>
        </a>
      </div>

      {/* Chatbot Section */}
      <div className="sidebar-section">
        <div className="sidebar-section-header" onClick={() => toggleSection('chatbot')}>
          <div className="section-title-container"><VscCommentDiscussion /><span>CONSO-BOT</span></div>
          <span className={`section-toggle-icon ${expandedSections.chatbot ? 'expanded' : ''}`}>▶</span>
        </div>
        {expandedSections.chatbot && (
          <div className="sidebar-section-content">
            <ConsoChatbot />
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;