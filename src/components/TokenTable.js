import React, { useRef, useEffect, useState } from 'react';

const TokenTable = ({ tokens }) => {
  const resizeHandleRef = useRef(null);
  const [width, setWidth] = useState(300); // Default width
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(0);

  // Setup resize handlers
  useEffect(() => {
    const handleMouseDown = (e) => {
      setIsDragging(true);
      setStartX(e.clientX);
      setStartWidth(width);
    };

    const handleMouseMove = (e) => {
      if (!isDragging) return;
      
      // Calculate new width
      const newWidth = Math.max(200, startWidth + (startX - e.clientX));
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
  }, [isDragging, startX, startWidth, width]);

  return (
    <div 
      className="token-table-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        position: 'absolute',
        top: 0,
        right: 0,
        width: `${width}px`,
        height: '100%',
        borderLeft: '1px solid #333',
        backgroundColor: '#1e1e1e',
        zIndex: 10,
        overflow: 'hidden'
      }}
    >
      {/* Resize handle */}
      <div 
        ref={resizeHandleRef}
        className="resize-handle"
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: 0,
          width: '10px',
          cursor: 'ew-resize',
          zIndex: 100
        }}
      />
      
      <div 
        className="token-table-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          padding: '5px 10px',
          backgroundColor: '#252526',
          borderBottom: '1px solid #333',
          color: '#d4d4d4',
          userSelect: 'none'
        }}
      >
        <div>Lexical Analysis</div>
      </div>
      
      <div 
        className="token-table-content"
        style={{
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
          flexGrow: 1,
          overflowY: 'auto',
          position: 'relative',
          paddingLeft: '10px',
          scrollbarWidth: 'thin', // For Firefox
          scrollbarColor: '#649ad1 #1e1e1e', // For Firefox
        }}
      >
        {!tokens || tokens.length === 0 ? (
          <div 
            className="token-table-empty"
            style={{
              padding: '10px',
              color: '#888',
              fontStyle: 'italic',
              display: 'flex',
              alignItems: 'center',
              height: '100%'
            }}
          >
            <div 
              className="terminal-cursor" 
              style={{ 
                position: 'absolute',
                left: '10px',
                top: '50px',
                width: '8px',
                height: '16px',
                backgroundColor: '#d4d4d4',
                opacity: 0.7,
                animation: 'blink 1s step-end infinite'
              }}
            />
            <span style={{ marginLeft: '15px' }}>No tokens to display</span>
          </div>
        ) : (
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '14px',
              fontFamily: 'Consolas, monospace'
            }}
          >
            <thead>
              <tr>
                <th style={{
                  padding: '8px 15px',
                  textAlign: 'left',
                  borderBottom: '1px solid #333',
                  position: 'sticky',
                  top: 0,
                  backgroundColor: '#252526',
                  zIndex: 1
                }}>Lexeme</th>
                <th style={{
                  padding: '8px 15px',
                  textAlign: 'left',
                  borderBottom: '1px solid #333',
                  position: 'sticky',
                  top: 0,
                  backgroundColor: '#252526',
                  zIndex: 1
                }}>Token</th>
              </tr>
            </thead>
            <tbody>
              {tokens.map((token, index) => (
                <tr 
                  key={index}
                  style={{
                    backgroundColor: index % 2 === 0 ? '#1e1e1e' : '#252526'
                  }}
                >
                  <td style={{ padding: '6px 15px', borderBottom: '1px solid #333' }}>
                    {token.value}
                  </td>
                  <td style={{ padding: '6px 15px', borderBottom: '1px solid #333' }}>
                    {token.type}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <style>
          {`
            @keyframes blink {
              0%, 100% { opacity: 0; }
              50% { opacity: 0.7; }
            }
            
            /* Webkit (Chrome, Safari, Edge) scrollbar styles */
            .token-table-content::-webkit-scrollbar {
              width: 8px;
            }

            .token-table-content::-webkit-scrollbar-track {
              background: #1e1e1e;
              border-radius: 4px;
            }

            .token-table-content::-webkit-scrollbar-thumb {
              background: #649ad1;
              border-radius: 4px;
            }

            .token-table-content::-webkit-scrollbar-thumb:hover {
              background: #5a8ac0;
            }
          `}
        </style>
      </div>
    </div>
  );
};

export default TokenTable;
