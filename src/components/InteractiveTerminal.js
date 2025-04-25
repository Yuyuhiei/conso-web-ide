// src/components/InteractiveTerminal.js
import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { Terminal } from 'xterm'; // Import Terminal class
import { FitAddon } from 'xterm-addon-fit'; // Import FitAddon
import 'xterm/css/xterm.css'; // Import xterm.css

// --- Define helpers within this file's scope ---
const STATUS_TYPE = { INFO: 'info', SUCCESS: 'success', ERROR: 'error', RUNNING: 'running', PENDING: 'pending' };

const createStatus = (message = null, type = STATUS_TYPE.PENDING) => ({ message, type });

const getStatusStyle = (type) => {
    switch (type) {
        case STATUS_TYPE.SUCCESS: return { color: '#89d185' }; // Green
        case STATUS_TYPE.ERROR: return { color: '#f48771' }; // Red/Orange
        case STATUS_TYPE.RUNNING: return { color: '#649ad1', fontStyle: 'italic' }; // Blue Italic
        case STATUS_TYPE.INFO: return { color: '#cca700' }; // Yellow/Gold
        case STATUS_TYPE.PENDING: default: return { color: '#888', fontStyle: 'italic' }; // Grey Italic
    }
};
// --- End helper definitions ---

const InteractiveTerminal = forwardRef(({
  // Status Props (for displaying pre-run info)
  lexicalStatus,
  syntaxStatus,
  semanticStatus,
  executionStatus, // Initial execution status from App.js
  // Props needed for interaction
  runId, // The prop containing the run ID
  websocketUrl,
  onProcessExit,
  isRunning, // Prop indicating if a process is actively running
  transpiledCode
}, ref) => {

  const terminalContainerRef = useRef(null); // Ref for the container DIV
  const xtermInstanceRef = useRef(null); // Ref to store the xterm Terminal instance
  const fitAddonRef = useRef(null); // Ref for the FitAddon instance
  const wsRef = useRef(null); // Ref for the WebSocket instance
  const onDataListenerRef = useRef(null); // Ref to store the onData listener disposable
  const lineBufferRef = useRef(''); // Ref to store the current input line

  const [showTranspiledInTerminal, setShowTranspiledInTerminal] = useState(false);
  const [isConnected, setIsConnected] = useState(false); // WebSocket connection status
  // Local state to manage execution status during the interactive session
  const [currentExecutionStatus, setCurrentExecutionStatus] = useState(executionStatus);

  // Expose methods to parent (App.js) via the ref
  useImperativeHandle(ref, () => ({
    clearTerminal: () => {
      if (xtermInstanceRef.current) {
        xtermInstanceRef.current.clear(); // Clear the terminal buffer
        xtermInstanceRef.current.write('\r\n$ '); // Add a fresh prompt after clearing
        lineBufferRef.current = ''; // Clear the input buffer too
        // Reset status only if not currently running
        if (!isRunning) {
           setCurrentExecutionStatus(createStatus("Terminal Cleared", STATUS_TYPE.INFO));
        }
      }
    },
    focusTerminal: () => {
        console.log("App.js attempting to focus terminal via ref..."); // DEBUG
        xtermInstanceRef.current?.focus(); // Focus the terminal for input
    }
  }));

  // --- Effect for Xterm Initialization and Cleanup ---
  useEffect(() => {
    let term; // Declare term variable here
    let fitAddon; // Declare fitAddon here
    let resizeListenerCleanup = () => {}; // Initialize cleanup function

    // Only initialize if the container exists and we don't have an instance yet
    if (terminalContainerRef.current && !xtermInstanceRef.current) {
        console.log("Initializing xterm instance...");
        term = new Terminal({
            cursorBlink: true,
            convertEol: true,
            fontFamily: 'Consolas, "Courier New", monospace',
            fontSize: 15,
            theme: { /* ... VS Code Dark+ theme ... */
                background: '#1e1e1e', foreground: '#d4d4d4', cursor: '#d4d4d4',
                selectionBackground: '#264f78', black: '#000000', red: '#cd3131',
                green: '#0dbc79', yellow: '#e5e510', blue: '#2472c8',
                magenta: '#bc3fbc', cyan: '#11a8cd', white: '#e5e5e5',
                brightBlack: '#666666', brightRed: '#f14c4c', brightGreen: '#23d18b',
                brightYellow: '#f5f543', brightBlue: '#3b8eea', brightMagenta: '#d670d6',
                brightCyan: '#29b8db', brightWhite: '#e5e5e5'
            }
        });
        fitAddon = new FitAddon();
        fitAddonRef.current = fitAddon; // Store addon ref

        term.loadAddon(fitAddon);
        term.open(terminalContainerRef.current); // Attach to container
        fitAddon.fit(); // Initial fit
        term.write('\r\n$ '); // Initial prompt

        xtermInstanceRef.current = term; // Store the terminal instance

        // --- MODIFICATION: Attach onData listener with Line Buffering & Echo ---
        onDataListenerRef.current = term.onData(data => {
            const term = xtermInstanceRef.current; // Get current terminal instance
            if (!term) return; // Should not happen, but safety check

            const code = data.charCodeAt(0); // Get ASCII code

            // --- Enter key ---
            if (code === 13) { // 13 is Carriage Return (Enter)
                term.write('\r\n'); // Move to next line in terminal
                console.log(`[onData] Enter pressed. Sending buffer: "${lineBufferRef.current}"`); // DEBUG

                // Send the buffered line + newline character to backend
                if (wsRef.current) {
                    if (wsRef.current.readyState === WebSocket.OPEN) {
                        // Send the complete line + a newline character expected by fgets/scanf
                        const messageToSend = lineBufferRef.current + '\n';
                        const message = JSON.stringify({ type: 'stdin', data: messageToSend });
                        console.log(`[onData] Sending WebSocket message:`, message); // DEBUG
                        wsRef.current.send(message);
                    } else {
                        console.warn(`[onData] WebSocket exists but is not OPEN. State: ${wsRef.current.readyState}. Cannot send line.`);
                    }
                } else {
                    console.warn("[onData] WebSocket reference is null. Cannot send line.");
                }
                lineBufferRef.current = ''; // Clear the buffer

            // --- Backspace key ---
            } else if (code === 8 || code === 127) { // 8 is Backspace, 127 is Delete/Backspace on some systems
                if (lineBufferRef.current.length > 0) {
                    // Remove last character from buffer
                    lineBufferRef.current = lineBufferRef.current.slice(0, -1);
                    // Move cursor back, write space, move cursor back again (visual backspace)
                    term.write('\b \b');
                    console.log(`[onData] Backspace. Buffer: "${lineBufferRef.current}"`); // DEBUG
                }
            // --- Printable characters ---
            } else if (code >= 32) { // Check if it's a printable character (ASCII 32 and above)
                lineBufferRef.current += data; // Add character to buffer
                term.write(data); // Echo character to the terminal
                // console.log(`[onData] Char typed. Buffer: "${lineBufferRef.current}"`); // DEBUG (optional, can be noisy)
            } else {
                 console.log(`[onData] Non-printable character code received: ${code}`); // DEBUG
            }
        });
        console.log("Attached onData listener with line buffering."); // DEBUG
        // --- END MODIFICATION ---

        // Resize listener setup
        const handleResize = () => fitAddonRef.current?.fit();
        window.addEventListener('resize', handleResize);
        resizeListenerCleanup = () => window.removeEventListener('resize', handleResize); // Store cleanup

    }

    // --- Cleanup for this effect ---
    return () => {
        console.log("Running xterm cleanup effect");
        resizeListenerCleanup(); // Remove resize listener
        if (onDataListenerRef.current) {
            console.log("Disposing onData listener");
            onDataListenerRef.current.dispose(); // Dispose the listener
            onDataListenerRef.current = null;
        }
        if (xtermInstanceRef.current) {
            console.log("Disposing xterm instance.");
            xtermInstanceRef.current.dispose(); // Dispose the terminal itself
            xtermInstanceRef.current = null;
        }
        fitAddonRef.current = null; // Clear addon ref
    };
  }, []); // Empty dependency array: Initialize xterm only once on mount

  // --- Effect for WebSocket Connection ---
  useEffect(() => {
    // Only connect if we should be running and have the necessary details
    if (isRunning && websocketUrl && runId && xtermInstanceRef.current) {
        // --- Close existing WebSocket if any ---
        if (wsRef.current) {
            console.log("Closing previous WebSocket connection (in WS effect).");
            wsRef.current.close();
            wsRef.current = null;
            setIsConnected(false);
        }

        // --- Initialize new WebSocket ---
        console.log(`Connecting WebSocket to: ${websocketUrl}`);
        const ws = new WebSocket(websocketUrl);
        wsRef.current = ws; // Store WebSocket instance

        ws.onopen = () => {
            console.log(`Interactive WebSocket connected (readyState: ${ws.readyState})`); // DEBUG: Log state on open
            setIsConnected(true);
            setCurrentExecutionStatus(createStatus("Process Started...", STATUS_TYPE.RUNNING));
            if (xtermInstanceRef.current) {
                xtermInstanceRef.current.write('\r\n\x1b[32m[Connected to process]\x1b[0m\r\n');
                console.log("WebSocket opened, attempting to focus terminal shortly...");
                setTimeout(() => {
                    if (xtermInstanceRef.current) {
                        console.log("Setting focus now (inside setTimeout)");
                        xtermInstanceRef.current.focus();
                    } else {
                        console.log("Terminal ref gone before focus timeout");
                    }
                }, 100);
            } else {
                 console.log("WebSocket opened, but terminal ref is missing.");
            }
        };

        ws.onmessage = (event) => {
             try {
                 const message = JSON.parse(event.data);
                 if (message.type === 'stdout' && message.data) {
                     xtermInstanceRef.current?.write(message.data);
                 } else if (message.type === 'stderr' && message.data) {
                     xtermInstanceRef.current?.write(`\x1b[31m${message.data}\x1b[0m`);
                 } else if (message.type === 'exit') {
                     console.log(`Received 'exit' message from WebSocket. Code: ${message.exit_code}`); // DEBUG
                     const exitCode = message.exit_code;
                     const exitMessage = `\r\n\x1b[${exitCode === 0 ? '32' : '31'}m[Process exited with code ${exitCode}]\x1b[0m\r\n$ `;
                     xtermInstanceRef.current?.write(exitMessage);
                     setCurrentExecutionStatus(createStatus(`Exited (${exitCode})`, exitCode === 0 ? STATUS_TYPE.SUCCESS : STATUS_TYPE.ERROR));
                     if (onProcessExit) onProcessExit(exitCode);
                     // ws.close(); // Let the onclose handler manage the state and ref clearing
                 }
             } catch (e) {
                 console.error("Error processing WebSocket message:", e);
                 xtermInstanceRef.current?.write("\r\n\x1b[31m[Error processing message from server]\x1b[0m\r\n$ ");
             }
        };

        ws.onclose = (event) => {
            console.log(`Interactive WebSocket disconnected. Code: ${event.code}, Reason: ${event.reason}, Was Clean: ${event.wasClean}, Current State: ${ws.readyState}`); // DEBUG
            setIsConnected(false);
            // Only set Connection Lost status if the process was supposed to be running *when* it closed
            if (isRunning && currentExecutionStatus.type === STATUS_TYPE.RUNNING) {
                 setCurrentExecutionStatus(createStatus("Connection Lost", STATUS_TYPE.ERROR));
                 if (xtermInstanceRef.current) {
                    xtermInstanceRef.current.write('\r\n\x1b[31m[Connection lost]\x1b[0m\r\n$ ');
                 }
            }
            // Check if the current ref is the one that closed before nulling
            if (wsRef.current === ws) {
                wsRef.current = null; // Clear ref on close
            }
        };

        ws.onerror = (error) => {
            console.error('Interactive WebSocket error:', error); // DEBUG
            setCurrentExecutionStatus(createStatus("Connection Error", STATUS_TYPE.ERROR));
            if (xtermInstanceRef.current) {
                xtermInstanceRef.current.write('\r\n\x1b[31m[WebSocket Connection Error]\x1b[0m\r\n$ ');
            }
             // Check if the current ref is the one that errored before nulling
            if (wsRef.current === ws) {
                wsRef.current = null; // Clear ref on error
            }
        };

    } else if (!isRunning && wsRef.current) {
        // Explicitly close WebSocket if isRunning becomes false
        console.log("Closing WebSocket because isRunning became false (in WS effect).");
        wsRef.current.close(1000, "Run finished or stopped by user");
        // wsRef.current = null; // Let onclose handle clearing the ref
        setIsConnected(false);
        if (currentExecutionStatus.type === STATUS_TYPE.RUNNING) {
            setCurrentExecutionStatus(createStatus("Stopped", STATUS_TYPE.INFO));
        }
    }

    // --- Cleanup for WebSocket effect ---
    return () => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log("Running WebSocket cleanup effect: Closing WebSocket.");
            wsRef.current.close(1000, "Component unmounting or dependencies changing"); // Close cleanly
        } else if (wsRef.current) {
             console.log(`Running WebSocket cleanup effect: WebSocket exists but state is ${wsRef.current.readyState}. Not closing explicitly.`);
        }
    };

  }, [isRunning, websocketUrl, runId, onProcessExit]); // Dependencies for WebSocket connection


  // Effect to update local execution status when the prop changes
  useEffect(() => {
      if (!isConnected && !isRunning) {
          setCurrentExecutionStatus(executionStatus);
      }
  }, [executionStatus, isConnected, isRunning]);


  const toggleTranspiledCode = () => setShowTranspiledInTerminal(!showTranspiledInTerminal);

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
      className="terminal-container interactive-terminal"
      style={{ display: 'flex', flexDirection: 'column', height: '100%',
               backgroundColor: '#1e1e1e', flexGrow: 1, overflow: 'hidden' }}
      // Add onClick handler to help focus
      onClick={() => {
          console.log("Terminal container clicked, attempting focus...");
          xtermInstanceRef.current?.focus();
      }}
    >
      {/* Header for Status Lines */}
      {!isRunning && !isConnected && (
          <div className="terminal-status-header" style={{ padding: '5px 10px', backgroundColor: '#252526', borderBottom: '1px solid #333', flexShrink: 0 }}>
             {renderStatusLine("Lexical", lexicalStatus)}
             {renderStatusLine("Syntax", syntaxStatus)}
             {renderStatusLine("Semantic", semanticStatus)}
             {renderStatusLine("Execution", currentExecutionStatus)}
          </div>
      )}

       {/* Header for xterm controls */}
       <div className="terminal-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 10px', backgroundColor: '#252526', borderBottom: '1px solid #333', userSelect: 'none', color: '#ccc', flexShrink: 0 }}>
           <span>{isRunning && runId ? `Interactive Console (PID: ${runId.substring(0,6)}...)` : 'Interactive Console'}</span>
           <div style={{ display: 'flex', gap: '8px' }}>
               {transpiledCode && (
                   <button onClick={toggleTranspiledCode} title={showTranspiledInTerminal ? "Hide C code" : "Show C code"}
                           style={{ backgroundColor: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '2px 8px', borderRadius: '3px', cursor: 'pointer', fontSize: '12px' }}>
                       {showTranspiledInTerminal ? 'Hide C' : 'Show C'}
                   </button>
               )}
           </div>
       </div>

      {/* Div container where xterm will attach */}
      <div ref={terminalContainerRef} style={{ flexGrow: 1, width: '100%', overflow: 'hidden', padding: '2px 5px' }}>
          {/* xterm attaches here */}
      </div>

      {/* Optional: Display Transpiled Code below xterm if toggled */}
      {showTranspiledInTerminal && transpiledCode && (
        <div className="transpiled-code-in-terminal" style={{ flexShrink: 0, maxHeight: '150px', overflowY: 'auto', borderTop: '1px dashed #649ad1', padding: '10px', backgroundColor: '#2d2d2d', fontFamily: 'monospace', fontSize: '13px' }}>
          <pre style={{ color: '#d4d4d4', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {transpiledCode}
          </pre>
        </div>
      )}

    </div>
  );
});

export default InteractiveTerminal;
