import React, { useRef, useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import { analyzeSemantics, runConsoCode } from '../services/api';

const Terminal = forwardRef(({ output, codeChanged, transpiledCode, programOutput, code, onRunComplete }, ref) => {
  const terminalRef = useRef(null);
  const resizeHandleRef = useRef(null);
  const [height, setHeight] = useState(200); // Default height
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(0);
  const [showTranspiledInTerminal, setShowTranspiledInTerminal] = useState(false);

  const [categoryMessages, setCategoryMessages] = useState({
    lexical: null,
    syntax: null,
    semantic: null,
    execution: null // For program execution results
  });

  // New state for run logic
  const [isRunning, setIsRunning] = useState(false);
  const [runOutput, setRunOutput] = useState('');
  const [runError, setRunError] = useState('');
  const [runTranspiledCode, setRunTranspiledCode] = useState('');

  // In the Terminal.js component, add debugging
  useEffect(() => {
    console.log("Terminal received programOutput:", programOutput);
  }, [programOutput]);

  // Auto scroll to bottom when new output is added
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [categoryMessages, showTranspiledInTerminal, programOutput, runOutput, runError]);

  // Clear semantic analysis message when code changes
  useEffect(() => {
    if (codeChanged) {
      setCategoryMessages(prev => ({
        ...prev,
        semantic: null,
        execution: null // Also clear execution results
      }));
      setRunOutput('');
      setRunError('');
      setRunTranspiledCode('');
    }
  }, [codeChanged]);

  // Update execution results when program output changes
  useEffect(() => {
    if (programOutput) {
      setCategoryMessages(prev => ({
        ...prev,
        execution: "Program executed successfully"
      }));
    }
  }, [programOutput]);

  // Setup resize handlers
  useEffect(() => {
    const handleMouseDown = (e) => {
      setIsDragging(true);
      setStartY(e.clientY);
      setStartHeight(height);
    };

    const handleMouseMove = (e) => {
      if (!isDragging) return;

      // Calculate new height (negative value because we're dragging upward to increase height)
      const newHeight = Math.max(100, startHeight - (e.clientY - startY));
      setHeight(newHeight);
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
  }, [isDragging, startY, startHeight, height]);

  // Process output to extract the latest message for each category
  useEffect(() => {
    if (!output) {
      setCategoryMessages({
        lexical: null,
        syntax: null,
        semantic: null,
        execution: null
      });
      return;
    }

    // Split output into lines
    const lines = output.split('\n').filter(line => line.trim() !== '');

    // Extract the latest message for each category
    const newCategoryMessages = {
      lexical: null,
      syntax: null,
      semantic: codeChanged ? null : categoryMessages.semantic, // If code has changed, clear semantic message
      execution: codeChanged ? null : categoryMessages.execution // If code has changed, clear execution results
    };

    lines.forEach(line => {
      // Lexical Analysis messages
      if (line.includes('Lexer') || line.includes('Lexical')) {
        newCategoryMessages.lexical = line;
      }
      // Syntax Analysis messages
      else if (line.includes('Parser') || line.includes('Syntax') ||
        line.includes('Input accepted') || line.includes('Input rejected') ||
        line.includes('Syntactically correct')) {
        newCategoryMessages.syntax = line;
      }
      // Semantic Analysis messages
      else if (line.includes('Semantic') && !codeChanged) {
        // Only update semantic message if code hasn't changed
        newCategoryMessages.semantic = line;
      }
      // Execution messages
      else if ((line.includes('executed') || line.includes('Running')) && !codeChanged) {
        // Only update execution message if code hasn't changed
        newCategoryMessages.execution = line;
      }
    });

    setCategoryMessages(newCategoryMessages);
  }, [output, categoryMessages.semantic, categoryMessages.execution, codeChanged]);

  // Get line type based on content to apply appropriate styling
  const getLineType = (line) => {
    if (!line) return 'info';

    if (line.includes('Error') || line.includes('❌') || line.includes('rejected') || line.includes('failed')) {
      return 'error';
    } else if (line.includes('✅') || line.includes('accepted') ||
      line.includes('Syntactically correct') || line.includes('successfully')) {
      return 'success';
    } else if (line.includes('Warning')) {
      return 'warning';
    } else {
      return 'info';
    }
  };

  // Toggle showing transpiled code in terminal
  const toggleTranspiledCode = () => {
    setShowTranspiledInTerminal(!showTranspiledInTerminal);
  };

  // Run button logic
  const handleRun = async () => {
    setIsRunning(true);
    setRunOutput('');
    setRunError('');
    setRunTranspiledCode('');
    try {
      // 1. Call semantic analyzer
      const semanticResult = await analyzeSemantics(code);
      if (!semanticResult.success) {
        const errorMsg = `Semantic Error: ${semanticResult.errors.join('\n')}`;
        setRunError(errorMsg);
        if (onRunComplete) onRunComplete({ output: '', error: errorMsg, transpiledCode: '' });
        setIsRunning(false);
        return;
      }
      // 2. If semantic passes, call transpiler/run
      const runResult = await runConsoCode(code);
      if (!runResult.success) {
        const errorMsg = (runResult.errors && runResult.errors.length > 0)
          ? runResult.errors.join('\n')
          : 'Unknown error during execution';
        setRunError(errorMsg);
        setRunTranspiledCode(runResult.transpiledCode || '');
        if (onRunComplete) onRunComplete({ output: '', error: errorMsg, transpiledCode: runResult.transpiledCode || '' });
        setIsRunning(false);
        return;
      }
      setRunTranspiledCode(runResult.transpiledCode || '');
      const outputValue = runResult.output || '(Program executed but produced no output)';
      setRunOutput(outputValue);
      if (onRunComplete) onRunComplete({ output: runResult.output, error: '', transpiledCode: runResult.transpiledCode || '' });
    } catch (err) {
      setRunError(`Error: ${err.message}`);
      if (onRunComplete) onRunComplete({ output: '', error: `Error: ${err.message}`, transpiledCode: '' });
    } finally {
      setIsRunning(false);
    }
  };

  // Expose run method to parent via ref
  useImperativeHandle(ref, () => ({
    run: handleRun
  }));

  // Convert category messages to array for rendering
  const getDisplayLines = () => {
    const result = [];

    if (categoryMessages.lexical) {
      result.push({
        category: 'Lexical',
        text: categoryMessages.lexical,
        type: getLineType(categoryMessages.lexical)
      });
    }

    if (categoryMessages.syntax) {
      result.push({
        category: 'Syntax',
        text: categoryMessages.syntax,
        type: getLineType(categoryMessages.syntax)
      });
    }

    if (categoryMessages.semantic) {
      result.push({
        category: 'Semantic',
        text: categoryMessages.semantic,
        type: getLineType(categoryMessages.semantic)
      });
    }

    if (categoryMessages.execution) {
      result.push({
        category: 'Execution',
        text: categoryMessages.execution,
        type: getLineType(categoryMessages.execution)
      });
    }

    return result;
  };

  const displayLines = getDisplayLines();

  // Determine if Run button should be enabled
  const canRun =
    categoryMessages.lexical &&
    categoryMessages.syntax &&
    getLineType(categoryMessages.lexical) !== 'error' &&
    getLineType(categoryMessages.syntax) !== 'error' &&
    !isRunning &&
    code && code.trim().length > 0;

  return (
    <div
      className="terminal-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: `${height}px`,
        position: 'relative',
        width: '100%',
        borderTop: '1px solid #333'
      }}
    >
      {/* Resize handle */}
      <div
        ref={resizeHandleRef}
        className="resize-handle"
        style={{
          position: 'absolute',
          top: '-5px',
          left: 0,
          right: 0,
          height: '10px',
          cursor: 'ns-resize',
          zIndex: 100
        }}
      />

      <div
        className="terminal-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          padding: '5px 10px',
          backgroundColor: '#252526',
          borderBottom: '1px solid #333',
          userSelect: 'none'
        }}
      >
        <div>Terminal</div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {transpiledCode && (
            <button
              onClick={toggleTranspiledCode}
              style={{
                backgroundColor: 'rgba(255,255,255,0.1)',
                border: 'none',
                color: 'white',
                padding: '2px 8px',
                borderRadius: '3px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              {showTranspiledInTerminal ? 'Hide C Code' : 'Show C Code'}
            </button>
          )}
        </div>
      </div>

      <div
        ref={terminalRef}
        className="terminal-content"
        style={{
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
          fontFamily: 'Consolas, monospace',
          fontSize: '14px',
          padding: '10px',
          flexGrow: 1,
          overflowY: 'auto',
          whiteSpace: 'pre-wrap',
          position: 'relative'
        }}
      >
        <div
          className="terminal-cursor"
          style={{
            position: 'absolute',
            left: '10px',
            top: '10px',
            width: '8px',
            height: '16px',
            backgroundColor: '#d4d4d4',
            opacity: 0.7,
            animation: 'blink 1s step-end infinite'
          }}
        />
        <style>
          {`
            @keyframes blink {
              0%, 100% { opacity: 0; }
              50% { opacity: 0.7; }
            }
          `}
        </style>

        {displayLines.length === 0 && !programOutput && !runOutput && !runError ? (
          <div className="terminal-line info" style={{ marginLeft: '15px' }}>
            Ready
          </div>
        ) : (
          <>
            {displayLines.map((item, index) => (
              <div
                key={index}
                className={`terminal-line ${item.type}`}
                style={{
                  color: item.type === 'error' ? '#f48771' :
                    item.type === 'success' ? '#89d185' :
                      item.type === 'warning' ? '#cca700' : '#d4d4d4',
                  marginBottom: '10px',
                  padding: '5px 0',
                  marginLeft: '15px',
                  borderBottom: (index < displayLines.length - 1 || programOutput || runOutput || runError) ? '1px solid #333' : 'none'
                }}
              >
                <span style={{ fontWeight: 'bold', marginRight: '8px' }}>
                  {item.category}:
                </span>
                {item.text}
              </div>
            ))}

            {/* Show semantic/transpiler run error */}
            {runError && (
              <div
                className="terminal-line error"
                style={{
                  color: '#f48771',
                  marginBottom: '10px',
                  padding: '5px 0',
                  marginLeft: '15px',
                  borderBottom: '1px solid #333'
                }}
              >
                <span style={{ fontWeight: 'bold', marginRight: '8px' }}>
                  Run Error:
                </span>
                {runError}
              </div>
            )}

            {/* Program output section */}
            {(runOutput || programOutput) && (
              <div
                className="program-output"
                style={{
                  marginTop: '15px',
                  marginLeft: '15px',
                  borderTop: displayLines.length > 0 ? '1px solid #555' : 'none',
                  paddingTop: displayLines.length > 0 ? '10px' : '0'
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '10px', color: '#89d185' }}>
                  Program Output:
                </div>
                <pre
                  style={{
                    backgroundColor: '#2d2d2d',
                    padding: '10px',
                    borderRadius: '4px',
                    overflowX: 'auto',
                    color: '#ffffff',
                    fontSize: '14px',
                    fontFamily: 'Consolas, monospace',
                    lineHeight: '1.4',
                    marginTop: '5px'
                  }}
                >
                  {runOutput || programOutput}
                </pre>
              </div>
            )}

            {/* Show transpiled code in terminal if requested */}
            {showTranspiledInTerminal && (runTranspiledCode || transpiledCode) && (
              <div
                className="transpiled-code-in-terminal"
                style={{
                  marginTop: '15px',
                  marginLeft: '15px',
                  borderTop: '1px solid #555',
                  paddingTop: '10px'
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '10px', color: '#89d185' }}>
                  Generated C Code:
                </div>
                <pre
                  style={{
                    backgroundColor: '#2d2d2d',
                    padding: '10px',
                    borderRadius: '4px',
                    overflowX: 'auto',
                    color: '#d4d4d4',
                    fontSize: '13px',
                    fontFamily: 'Consolas, monospace',
                    lineHeight: '1.4',
                    marginTop: '5px'
                  }}
                >
                  {runTranspiledCode || transpiledCode}
                </pre>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
});

export default Terminal;
