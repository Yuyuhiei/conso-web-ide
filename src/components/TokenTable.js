import React, { useRef, useEffect, useState } from 'react';
import { VscListSelection } from 'react-icons/vsc';
import './TokenTable.css';

const TokenTable = ({ tokens }) => {
  const resizeHandleRef = useRef(null);
  const [width, setWidth] = useState(300); // Default width
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(0);

  // Setup resize handlers
  useEffect(() => {
    const handleMouseDown = (e) => {
      e.preventDefault();
      setIsDragging(true);
      setStartX(e.clientX);
      setStartWidth(width);
    };

    const handleMouseMove = (e) => {
      if (!isDragging) return;
      
      // Calculate new width, preventing it from getting too small
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
      style={{ width: `${width}px` }}
    >
      {/* Resize handle */}
      <div 
        ref={resizeHandleRef}
        className="resize-handle"
      />
      
      <div className="token-table-header">
        <VscListSelection />
        <span>LEXICAL ANALYSIS</span>
      </div>
      
      <div className="token-table-content">
        {!tokens || tokens.length === 0 ? (
          <div className="token-table-empty">
            <span>No tokens to display</span>
          </div>
        ) : (
          <table className="token-table">
            <thead>
              <tr>
                <th>Lexeme</th>
                <th>Token</th>
              </tr>
            </thead>
            <tbody>
              {tokens.map((token, index) => (
                <tr key={index}>
                  <td>{token.value}</td>
                  <td>{token.type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default TokenTable;
