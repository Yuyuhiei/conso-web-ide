// src/components/Terminal.js
import React, { useRef, useEffect, useState, forwardRef } from 'react';

// Define status types locally for styling keys
const STATUS_TYPE = {
  INFO: 'info',
  SUCCESS: 'success',
  ERROR: 'error',
  RUNNING: 'running',
  PENDING: 'pending'
};

// Helper to get style based on status type
const getStatusStyle = (type) => {
  switch (type) {
    case STATUS_TYPE.SUCCESS:
      return { color: '#89d185' }; // Green
    case STATUS_TYPE.ERROR:
      return { color: '#f48771' }; // Red/Orange
    case STATUS_TYPE.RUNNING:
      return { color: '#649ad1', fontStyle: 'italic' }; // Blue Italic
    case STATUS_TYPE.INFO:
      return { color: '#cca700' }; // Yellow/Gold
    case STATUS_TYPE.PENDING:
    default:
      return { color: '#888', fontStyle: 'italic' }; // Grey Italic
  }
};

// Terminal component displays status lines passed via props
const Terminal = forwardRef(({
  lexicalStatus,
  syntaxStatus,
  semanticStatus,
  executionStatus,
  programOutput, // Still needed
  transpiledCode // Still needed
}, ref) => {
  const terminalContentRef = useRef(null);
  const resizeHandleRef = useRef(null);
  const containerRef = useRef(null);

  const [height, setHeight] = useState(() => {
      const savedHeight = localStorage.getItem('conso-terminal-height');
      return savedHeight ? Math.max(100, parseInt(savedHeight, 10)) : 200;
  });
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(0);
  const [showTranspiledInTerminal, setShowTranspiledInTerminal] = useState(false);

  // Auto scroll to bottom when content changes
  useEffect(() => {
    if (terminalContentRef.current) {
      terminalContentRef.current.scrollTop = terminalContentRef.current.scrollHeight;
    }
    // Update scroll on any status change or output change
  }, [lexicalStatus, syntaxStatus, semanticStatus, executionStatus, programOutput, showTranspiledInTerminal, transpiledCode]);

  // Resize handlers (Keep as is)
  useEffect(() => {
    const handleMouseDown = (e) => {
      e.preventDefault(); setIsDragging(true); setStartY(e.clientY); setStartHeight(height);
      document.body.style.userSelect = 'none';
    };
    const handleMouseMove = (e) => {
      if (!isDragging) return;
      const newHeight = Math.max(100, startHeight - (e.clientY - startY));
      setHeight(newHeight);
    };
    const handleMouseUp = () => {
      if (isDragging) {
          setIsDragging(false); document.body.style.userSelect = '';
          localStorage.setItem('conso-terminal-height', height.toString());
      }
    };
    const resizeHandle = resizeHandleRef.current;
    if (resizeHandle) { resizeHandle.addEventListener('mousedown', handleMouseDown); }
    if (isDragging) { document.addEventListener('mousemove', handleMouseMove); document.addEventListener('mouseup', handleMouseUp); }
    return () => {
      if (resizeHandle) { resizeHandle.removeEventListener('mousedown', handleMouseDown); }
      document.removeEventListener('mousemove', handleMouseMove); document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
    };
  }, [isDragging, startY, startHeight, height]);

  // Toggle C code view (Keep as is)
  const toggleTranspiledCode = () => {
    setShowTranspiledInTerminal(!showTranspiledInTerminal);
  };

  // Helper to render a single status line
  const renderStatusLine = (label, status) => {
    const { message, type } = status || { message: null, type: STATUS_TYPE.PENDING };
    const style = getStatusStyle(type);
    const displayMessage = message === null ? (type === STATUS_TYPE.PENDING ? 'Pending...' : '...') : message;

    return (
      <div className={`terminal-line status-${type}`} style={{ display: 'flex', alignItems: 'center', minHeight: '20px', marginBottom: '2px', marginLeft: '15px' }}>
        <span style={{ fontWeight: 'bold', color: '#aaa', minWidth: '100px', marginRight: '10px' }}>{label}:</span>
        <span style={style}>{displayMessage}</span>
      </div>
    );
  };


  return (
    <div
      ref={containerRef}
      className="terminal-container"
      style={{
        display: 'flex', flexDirection: 'column', height: `${height}px`,
        position: 'relative', width: '100%', borderTop: '1px solid #333',
        backgroundColor: '#1e1e1e', flexShrink: 0
      }}
    >
      {/* Resize handle (Keep as is) */}
      <div ref={resizeHandleRef} className="resize-handle" style={{ position: 'absolute', top: '-5px', left: 0, right: 0, height: '10px', cursor: 'ns-resize', zIndex: 100 }} />

      {/* Terminal Header (Keep as is) */}
      <div className="terminal-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 10px', backgroundColor: '#252526', borderBottom: '1px solid #333', userSelect: 'none', color: '#ccc', flexShrink: 0 }}>
        <span>Terminal</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          {transpiledCode && (
            <button onClick={toggleTranspiledCode} title={showTranspiledInTerminal ? "Hide C code" : "Show C code"} style={{ backgroundColor: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '2px 8px', borderRadius: '3px', cursor: 'pointer', fontSize: '12px' }}>
              {showTranspiledInTerminal ? 'Hide C' : 'Show C'}
            </button>
          )}
        </div>
      </div>

      {/* Terminal Content Area */}
      <div
        ref={terminalContentRef}
        className="terminal-content"
        style={{
          color: '#d4d4d4', fontFamily: 'Consolas, "Courier New", monospace', fontSize: '14px',
          padding: '10px', flexGrow: 1, overflowY: 'auto', whiteSpace: 'pre-wrap',
          wordBreak: 'break-word', // Changed from break-all for better readability
          position: 'relative', scrollbarWidth: 'thin', scrollbarColor: '#649ad1 #1e1e1e',
        }}
      >
         {/* Render Fixed Status Lines */}
         {renderStatusLine("Lexical", lexicalStatus)}
         {renderStatusLine("Syntax", syntaxStatus)}
         {renderStatusLine("Semantic", semanticStatus)}
         {renderStatusLine("Execution", executionStatus)}

         {/* Display Program Output (if any) */}
         {programOutput && (
            <div className="program-output" style={{ marginTop: '10px', borderTop: '1px dashed #89d185', paddingTop: '10px' }}>
                <div style={{ fontWeight: 'bold', color: '#89d185', marginBottom: '5px', marginLeft: '15px' }}>Program Output:</div>
                <pre
                  style={{
                    backgroundColor: '#2d2d2d', padding: '10px', borderRadius: '4px',
                    overflowX: 'auto', color: '#ffffff', fontSize: '14px',
                    fontFamily: 'Consolas, "Courier New", monospace', lineHeight: '1.4',
                    marginTop: '5px', marginLeft: '15px', marginRight: '10px'
                  }}
                >
                  {programOutput}
                </pre>
            </div>
         )}

         {/* Display Transpiled Code (if toggled) */}
         {showTranspiledInTerminal && transpiledCode && (
           <div className="transpiled-code-in-terminal" style={{ marginTop: '10px', borderTop: '1px dashed #649ad1', paddingTop: '10px' }}>
             <div style={{ fontWeight: 'bold', color: '#649ad1', marginBottom: '5px', marginLeft: '15px' }}>Generated C Code:</div>
             <pre
               style={{
                 backgroundColor: '#2d2d2d', padding: '10px', borderRadius: '4px',
                 overflowX: 'auto', color: '#d4d4d4', fontSize: '13px',
                 fontFamily: 'Consolas, "Courier New", monospace', lineHeight: '1.4',
                 marginTop: '5px', marginLeft: '15px', marginRight: '10px'
               }}
             >
               {transpiledCode}
             </pre>
           </div>
         )}

         {/* Blinking cursor simulation at the end (Optional) */}
         {/* You might remove this or adjust its position based on the fixed status lines */}
         {/* <div style={{ display: 'flex', alignItems: 'center', marginLeft: '15px', marginTop: '10px' }}>
             <span>&gt; </span>
             <div className="terminal-cursor" style={{ display: 'inline-block', width: '8px', height: '16px', backgroundColor: '#d4d4d4', opacity: 0.7, animation: 'blink 1s step-end infinite', marginLeft: '4px' }}/>
         </div> */}
         <style>
          {`
            @keyframes blink { 0%, 100% { opacity: 0; } 50% { opacity: 0.7; } }
            .terminal-content::-webkit-scrollbar { width: 8px; }
            .terminal-content::-webkit-scrollbar-track { background: #1e1e1e; border-radius: 4px; }
            .terminal-content::-webkit-scrollbar-thumb { background: #649ad1; border-radius: 4px; }
            .terminal-content::-webkit-scrollbar-thumb:hover { background: #5a8ac0; }
          `}
        </style>
      </div>
    </div>
  );
});

export default Terminal;
