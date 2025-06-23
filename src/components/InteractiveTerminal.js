// src/components/InteractiveTerminal.js
import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import './InteractiveTerminal.css';
import { VscCheck, VscError, VscSync, VscInfo, VscChevronRight } from 'react-icons/vsc';

// --- Helper Components ---
const STATUS_TYPE = { INFO: 'info', SUCCESS: 'success', ERROR: 'error', RUNNING: 'running', PENDING: 'pending' };
const createStatus = (message = null, type = STATUS_TYPE.PENDING) => ({ message, type });

const StatusIcon = ({ type }) => {
  switch (type) {
    case STATUS_TYPE.SUCCESS: return <VscCheck className="status-type-success" />;
    case STATUS_TYPE.ERROR: return <VscError className="status-type-error" />;
    case STATUS_TYPE.RUNNING: return <VscSync className="status-type-running spin" />;
    case STATUS_TYPE.INFO: return <VscInfo className="status-type-info" />;
    case STATUS_TYPE.PENDING: default: return <VscChevronRight className="status-type-pending" />;
  }
};

const InteractiveTerminal = forwardRef(({
  lexicalStatus, syntaxStatus, semanticStatus, executionStatus,
  runId, websocketUrl, onProcessExit, isRunning
}, ref) => {
  const terminalContainerRef = useRef(null);
  const xtermInstanceRef = useRef(null);
  const fitAddonRef = useRef(null);
  const wsRef = useRef(null);
  const lineBufferRef = useRef('');
  const isTerminalOpen = useRef(false);

  const [activeTab, setActiveTab] = useState('status');
  const [hasRunOnce, setHasRunOnce] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [currentExecutionStatus, setCurrentExecutionStatus] = useState(executionStatus);

  // --- Auto-switch to console tab when a run starts ---
  useEffect(() => {
    if (isRunning) {
      setHasRunOnce(true);
      setActiveTab('console');
    }
  }, [isRunning]);

  // Expose methods to parent (App.js) via the ref
  useImperativeHandle(ref, () => ({
    clearTerminal: () => {
      if (xtermInstanceRef.current) {
        xtermInstanceRef.current.clear();
        xtermInstanceRef.current.write('\r\n$ ');
      }
      lineBufferRef.current = '';
      setCurrentExecutionStatus(createStatus("Terminal Cleared", STATUS_TYPE.INFO));
      setActiveTab('status'); // Switch back to status view on clear
    },
    focusTerminal: () => xtermInstanceRef.current?.focus()
  }));

  // --- Effect for Xterm Initialization and Resizing ---
  useEffect(() => {
    const term = new Terminal({
        cursorBlink: true, convertEol: true, fontFamily: 'Consolas, "Courier New", monospace', fontSize: 15,
        theme: {
            background: '#1e1e1e', foreground: '#d4d4d4', cursor: '#d4d4d4',
            selectionBackground: '#264f78', black: '#000000', red: '#cd3131',
            green: '#0dbc79', yellow: '#e5e510', blue: '#2472c8',
            magenta: '#bc3fbc', cyan: '#11a8cd', white: '#e5e5e5',
            brightBlack: '#666666', brightRed: '#f14c4c', brightGreen: '#23d18b',
            brightYellow: '#f5f543', brightBlue: '#3b8eea', brightMagenta: '#d670d6',
            brightCyan: '#29b8db', brightWhite: '#e5e5e5'
        }
    });
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    xtermInstanceRef.current = term;
    fitAddonRef.current = fitAddon;

    term.onData(data => {
        const code = data.charCodeAt(0);
        if (code === 13) { // Enter
            term.write('\r\n');
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'stdin', data: lineBufferRef.current + '\n' }));
            }
            lineBufferRef.current = '';
        } else if (code === 8 || code === 127) { // Backspace
            if (lineBufferRef.current.length > 0) {
                lineBufferRef.current = lineBufferRef.current.slice(0, -1);
                term.write('\b \b');
            }
        } else if (code >= 32) { // Printable characters
            lineBufferRef.current += data;
            term.write(data);
        }
    });

    // Use ResizeObserver to fit the terminal automatically.
    const resizeObserver = new ResizeObserver(() => {
        // Add a slight delay to avoid issues with rapid resizing
        setTimeout(() => fitAddon.fit(), 0);
    });
    
    // We must observe the container element.
    if (terminalContainerRef.current) {
        resizeObserver.observe(terminalContainerRef.current);
    }

    return () => {
        resizeObserver.disconnect();
        xtermInstanceRef.current?.dispose();
    };
  }, []); // Empty dependency array ensures this runs only ONCE.

  // --- Effect to OPEN terminal when tab becomes visible ---
  useEffect(() => {
    if (activeTab === 'console' && !isTerminalOpen.current && terminalContainerRef.current) {
        xtermInstanceRef.current.open(terminalContainerRef.current);
        xtermInstanceRef.current.write('$ ');
        isTerminalOpen.current = true;
    }
    // Always focus when tab is selected
    if (activeTab === 'console') {
        xtermInstanceRef.current?.focus();
    }
  }, [activeTab]);

  // --- WebSocket Connection Logic ---
  useEffect(() => {
    if (isRunning && websocketUrl && runId && xtermInstanceRef.current) {
        if (wsRef.current) { wsRef.current.close(); }
        const ws = new WebSocket(websocketUrl);
        wsRef.current = ws;
        ws.onopen = () => {
            setIsConnected(true);
            setCurrentExecutionStatus(createStatus("Process Started...", STATUS_TYPE.RUNNING));
            xtermInstanceRef.current?.write('\r\n\x1b[32m[Connected to process]\x1b[0m\r\n');
        };
        ws.onmessage = (event) => {
             try {
                 const message = JSON.parse(event.data);
                 if (message.type === 'stdout' && message.data) xtermInstanceRef.current?.write(message.data);
                 if (message.type === 'stderr' && message.data) xtermInstanceRef.current?.write(`\x1b[31m${message.data}\x1b[0m`);
                 if (message.type === 'exit') {
                     const exitCode = message.exit_code;
                     const exitMessage = `\r\n\x1b[${exitCode === 0 ? '32' : '31'}m[Process exited with code ${exitCode}]\x1b[0m\r\n$ `;
                     xtermInstanceRef.current?.write(exitMessage);
                     setCurrentExecutionStatus(createStatus(`Exited (${exitCode})`, exitCode === 0 ? STATUS_TYPE.SUCCESS : STATUS_TYPE.ERROR));
                     onProcessExit?.(exitCode);
                 }
             } catch (e) { console.error("Error processing WebSocket message:", e); }
        };
        ws.onclose = () => {
            setIsConnected(false);
            if (isRunning) {
                 setCurrentExecutionStatus(createStatus("Connection Lost", STATUS_TYPE.ERROR));
                 xtermInstanceRef.current?.write('\r\n\x1b[31m[Connection lost]\x1b[0m\r\n$ ');
            }
            if (wsRef.current === ws) { wsRef.current = null; }
        };
        ws.onerror = (error) => {
            console.error('Interactive WebSocket error:', error);
            setCurrentExecutionStatus(createStatus("Connection Error", STATUS_TYPE.ERROR));
            if (wsRef.current === ws) { wsRef.current = null; }
        };
    } else if (!isRunning && wsRef.current) {
        wsRef.current.close(1000, "Run finished or stopped by user");
        setIsConnected(false);
    }
    return () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.close(1000, "Component unmounting");
        }
    };
  }, [isRunning, websocketUrl, runId, onProcessExit]);

  useEffect(() => {
      if (!isConnected && !isRunning) {
          setCurrentExecutionStatus(executionStatus);
      }
  }, [executionStatus, isConnected, isRunning]);

  const renderStatusLine = (label, status) => {
    const { message, type } = status || { message: null, type: STATUS_TYPE.PENDING };
    const displayMessage = message === null ? (type === STATUS_TYPE.PENDING ? 'Pending...' : '...') : message;
    return (
      <div className="status-line">
        <span className="status-icon"><StatusIcon type={type} /></span>
        <span className="status-label">{label}:</span>
        <span className={`status-message status-type-${type}`}>{displayMessage}</span>
      </div>
    );
  };

  return (
    <div className="interactive-terminal-container">
      <div className="terminal-tabs">
        <button
          className={`tab-button ${activeTab === 'status' ? 'active' : ''}`}
          onClick={() => setActiveTab('status')}
        >
          Status
        </button>
        <button
          className={`tab-button ${activeTab === 'console' ? 'active' : ''}`}
          onClick={() => setActiveTab('console')}
          disabled={!hasRunOnce}
        >
          Console
        </button>
      </div>
      <div className="terminal-content-area">
        <div style={{ display: activeTab === 'status' ? 'block' : 'none', height: '100%' }}>
          <div className="terminal-status-view">
             {renderStatusLine("Lexical", lexicalStatus)}
             {renderStatusLine("Syntax", syntaxStatus)}
             {renderStatusLine("Semantic", semanticStatus)}
             {renderStatusLine("Execution", currentExecutionStatus)}
          </div>
        </div>
        <div 
          className="terminal-console-view" 
          style={{ 
            display: activeTab === 'console' ? 'flex' : 'none', 
            height: '100%' 
          }}
        >
            <div ref={terminalContainerRef} className="xterm-container">
                {/* xterm attaches here */}
            </div>
        </div>
      </div>
    </div>
  );
});

export default InteractiveTerminal;
