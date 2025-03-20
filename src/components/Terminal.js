import React, { useRef, useEffect } from 'react';

const Terminal = ({ output }) => {
  const terminalRef = useRef(null);
  
  // Auto scroll to bottom when new output is added
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);
  
  // Apply styling to different message types
  const formatOutput = (text) => {
    if (!text) return [];
    
    // Split by lines for processing
    return text.split('\n').map((line, index) => {
      if (line.includes('Error')) {
        return <div key={index} className="error-message">{line}</div>;
      } else if (line.includes('successfully')) {
        return <div key={index} className="success-message">{line}</div>;
      } else if (line.includes('Semantic errors found')) {
        return <div key={index} className="warning-message">{line}</div>;
      } else {
        return <div key={index}>{line}</div>;
      }
    });
  };
  
  return (
    <div className="terminal-container">
      <div className="terminal-header">Terminal</div>
      <div 
        ref={terminalRef}
        className="terminal-content"
        style={{
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
          fontFamily: 'Consolas, monospace',
          fontSize: '14px',
          padding: '10px',
          height: '100%',
          overflowY: 'auto',
          whiteSpace: 'pre-wrap'
        }}
      >
        {formatOutput(output)}
      </div>
    </div>
  );
};

export default Terminal;