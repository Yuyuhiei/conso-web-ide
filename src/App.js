import React, { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import CodeEditor from './components/NewEditor';
import InteractiveTerminal from './components/InteractiveTerminal';
import TokenTable from './components/TokenTable';
import Sidebar from './components/Sidebar';
import TranspiledCodeView from './components/TranspiledCodeView';
import { prepareRun } from './services/api';
import websocketService from './services/websocketService';
import { VscRunAll, VscDebugStop, VscSave, VscFolder, VscEye, VscCloudDownload, VscTrash, VscInfo, VscGithub } from 'react-icons/vsc';
import './App.css';

const STATUS_TYPE = { INFO: 'info', SUCCESS: 'success', ERROR: 'error', RUNNING: 'running', PENDING: 'pending' };
const createStatus = (message = null, type = STATUS_TYPE.PENDING) => ({ message, type });

const MainApp = () => {
  // --- State Variables ---
  const [files, setFiles] = useState(() => {
    try {
        const savedFiles = localStorage.getItem('conso-files');
        if (savedFiles) {
            const parsedFiles = JSON.parse(savedFiles);
            if (Array.isArray(parsedFiles) && parsedFiles.every(f => f && f.id && typeof f.name === 'string' && typeof f.content === 'string')) {
                return parsedFiles;
            }
        }
    } catch (e) { console.error("Failed to load files:", e); }
    return [{ id: uuidv4(), name: 'Untitled.cns', content: '' }];
  });
  const [currentFileId, setCurrentFileId] = useState(() => {
     const savedCurrentId = localStorage.getItem('conso-current-file-id');
     const savedFiles = localStorage.getItem('conso-files');
     if (savedCurrentId && savedFiles) {
        try {
            const parsedFiles = JSON.parse(savedFiles);
            if (Array.isArray(parsedFiles) && parsedFiles.some(f => f.id === savedCurrentId)) {
                return savedCurrentId;
            }
        } catch (e) { console.error("Failed to load current file ID:", e); }
     }
     const firstFile = files.length > 0 ? files[0] : null;
     return firstFile ? firstFile.id : null;
  });
  const [lexicalStatus, setLexicalStatus] = useState(createStatus("Ready"));
  const [syntaxStatus, setSyntaxStatus] = useState(createStatus());
  const [semanticStatus, setSemanticStatus] = useState(createStatus());
  const [executionStatus, setExecutionStatus] = useState(createStatus());
  const [tokens, setTokens] = useState([]);
  const [syntaxValid, setSyntaxValid] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [transpiledCode, setTranspiledCode] = useState('');
  const [showTranspiledCode, setShowTranspiledCode] = useState(false);
  const [currentRunId, setCurrentRunId] = useState(null);
  const [interactiveWsUrl, setInteractiveWsUrl] = useState(null);
  const [showInfo, setShowInfo] = useState(false);
  const editorRef = useRef(null);
  const interactiveTerminalRef = useRef(null);
  const [currentTheme, setCurrentTheme] = useState(() => localStorage.getItem('conso-theme') || 'conso-dark');

  // --- State for Terminal Resizing ---
  const [terminalPanelHeight, setTerminalPanelHeight] = useState(300); // Initial height in pixels
  const isResizingTerminalPanelRef = useRef(false);
  const terminalResizerLastYRef = useRef(0);
  // --- End State for Terminal Resizing ---

  const currentFile = files.find(file => file.id === currentFileId) || files[0] || { id: null, name: '', content: '' };
  const canRun = syntaxValid && !isRunning && currentFile && currentFile.content.trim().length > 0;

  // --- Effects ---
  useEffect(() => {
    try {
        localStorage.setItem('conso-files', JSON.stringify(files));
        if (currentFileId) {
            localStorage.setItem('conso-current-file-id', currentFileId);
        }
    } catch (e) { console.error("Failed to save files:", e); }
  }, [files, currentFileId]);
  useEffect(() => {
    localStorage.setItem('conso-theme', currentTheme);
  }, [currentTheme]);

  // WebSocket Effect for Lex/Parse
  useEffect(() => {
    websocketService
      .on('open', () => setLexicalStatus(createStatus("WebSocket Connected", STATUS_TYPE.INFO)))
      .on('lexerResult', (data) => {
        setTokens(data.tokens || []);
        if (!data.success) {
          const errorMessages = (data.errors || []).map(err => `${err}`).join('; ');
          setLexicalStatus(createStatus(`Error: ${errorMessages}`, STATUS_TYPE.ERROR));
        } else {
          setLexicalStatus(createStatus("OK", STATUS_TYPE.SUCCESS));
        }
        setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
        setSyntaxValid(false); setTranspiledCode('');
      })
      .on('parserResult', (data) => {
         setSyntaxValid(data.syntaxValid || false);
         if (data.syntaxValid) {
             setSyntaxStatus(createStatus("OK", STATUS_TYPE.SUCCESS));
         } else {
             const errorMessages = (data.errors || []).join('; ');
             setSyntaxStatus(createStatus(`Error: ${errorMessages}`, STATUS_TYPE.ERROR));
         }
         setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
         setTranspiledCode('');
      })
      .on('error', (data) => {
          setLexicalStatus(createStatus(`WebSocket Error: ${data.message}`, STATUS_TYPE.ERROR));
          setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
          setSyntaxValid(false);
      })
      .on('close', () => {
          setLexicalStatus(createStatus("WebSocket Disconnected", STATUS_TYPE.INFO));
          setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
          setSyntaxValid(false);
      });

    websocketService.connect();

    if (currentFile && currentFile.content) {
         websocketService.sendCode(currentFile.content);
    } else {
        setLexicalStatus(createStatus("Ready"));
        setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
    }

    return () => { websocketService.disconnect(); };
  }, [currentFileId]); // Re-run only when file changes

  // --- Event Handlers ---

  // handleCodeChange
  const handleCodeChange = useCallback((newValue) => {
    setFiles(prevFiles =>
      prevFiles.map(file =>
        file.id === currentFileId ? { ...file, content: newValue } : file
      )
    );
    setLexicalStatus(createStatus("Analyzing...", STATUS_TYPE.RUNNING));
    setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
    setSyntaxValid(false); setTranspiledCode('');

    // Debounce analysis
    // Note: Simplified debounce, a library like lodash.debounce might be better
    if (!analyzing) {
      setAnalyzing(true); // Prevent multiple triggers
      const debounceTimer = setTimeout(() => {
        if (websocketService.isConnected) {
           websocketService.sendCode(newValue);
        } else {
            setLexicalStatus(createStatus("Error: WebSocket not connected", STATUS_TYPE.ERROR));
        }
        setAnalyzing(false); // Allow next analysis after delay
      }, 750); // 750ms delay
      // Cleanup function for the timeout if component unmounts or value changes again quickly
      return () => clearTimeout(debounceTimer);
    }
  }, [currentFileId, analyzing]); // Dependencies for useCallback

  // handleRun
  const handleRun = async () => {
    if (!canRun) {
       let reason = "Cannot run.";
       if (isRunning) reason = "Already running.";
       else if (!syntaxValid) reason = "Syntax errors detected.";
       else if (!currentFile || !currentFile.content.trim()) reason = "No code to run.";
       setExecutionStatus(createStatus(reason, STATUS_TYPE.ERROR));
      return;
    }

    setIsRunning(true);
    setTranspiledCode('');
    setCurrentRunId(null);
    setInteractiveWsUrl(null);
    setSemanticStatus(createStatus("Preparing...", STATUS_TYPE.RUNNING));
    setExecutionStatus(createStatus("Preparing...", STATUS_TYPE.RUNNING));
    interactiveTerminalRef.current?.clearTerminal();

    try {
      const prepareResult = await prepareRun(currentFile.content);
      if (prepareResult.success && prepareResult.runId && prepareResult.websocketUrl) {
        setSemanticStatus(createStatus("OK", STATUS_TYPE.SUCCESS));
        setExecutionStatus(createStatus("Connecting...", STATUS_TYPE.RUNNING));
        setTranspiledCode(prepareResult.transpiledCode || ''); // Store C code
        setCurrentRunId(prepareResult.runId);
        setInteractiveWsUrl(prepareResult.websocketUrl);
        interactiveTerminalRef.current?.focusTerminal();
      } else {
        const errorPhase = prepareResult.phase || 'prepare';
        const errorMsg = (prepareResult.errors || ['Unknown error during preparation']).join('; ');
        const statusMsg = `Error (${errorPhase}): ${errorMsg}`;
        if (errorPhase === 'semantic') {
            setSemanticStatus(createStatus(statusMsg, STATUS_TYPE.ERROR));
            setExecutionStatus(createStatus("Aborted", STATUS_TYPE.ERROR));
        } else {
            setSemanticStatus(createStatus("Not Run", STATUS_TYPE.PENDING));
            setExecutionStatus(createStatus(statusMsg, STATUS_TYPE.ERROR));
        }
        setIsRunning(false);
      }
    } catch (error) {
      setSemanticStatus(createStatus("Failed", STATUS_TYPE.ERROR));
      setExecutionStatus(createStatus(`Prepare Failed: ${error.message || 'Network Error'}`, STATUS_TYPE.ERROR));
      setIsRunning(false);
    }
  };

  // --- NEW: Add this complete handleStop function ---
  const handleStop = async () => {
    // This log should appear in your browser's console immediately on click.
    console.log('--- Stop Button Clicked ---');

    if (!isRunning || !currentRunId) {
      console.error('Stop clicked, but state is invalid.', { isRunning, currentRunId });
      return;
    }

    console.log(`Sending stop request for runId: ${currentRunId}`);
    setExecutionStatus(createStatus("Sending stop signal...", STATUS_TYPE.INFO));

    try {
      // Using the full URL to be explicit.
      const response = await fetch(`http://localhost:5000/api/run/${currentRunId}/stop`, {
        method: 'POST',
      });

      const result = await response.json();

      if (!response.ok) {
        console.error('Stop request failed. Server response:', result);
        setExecutionStatus(createStatus(`Stop failed: ${result.detail}`, STATUS_TYPE.ERROR));
        return;
      }

      console.log('Stop signal acknowledged by server:', result.message);
      // The UI will update fully once the WebSocket closes and onProcessExit is called.
      
    } catch (error) {
      console.error('A network or other error occurred while sending the stop signal:', error);
      setExecutionStatus(createStatus(`Stop failed: ${error.message}`, STATUS_TYPE.ERROR));
    }
  };

  // --- MODIFICATION: Wrap handleProcessExit in useCallback ---
  // Handler for Process Exit (called by InteractiveTerminal)
  const handleProcessExit = useCallback((exitCode) => {
      console.log(`App.js: Process exited callback received. Code: ${exitCode}`);
      setIsRunning(false); // Mark run as finished
      setCurrentRunId(null); // Clear run details
      setInteractiveWsUrl(null);
      // Update status based on exit code, ensuring it reflects the final state
      setExecutionStatus(createStatus(`Exited (${exitCode})`, exitCode === 0 ? STATUS_TYPE.SUCCESS : STATUS_TYPE.ERROR));
  }, []); // Empty dependency array means this function reference never changes
  // --- END MODIFICATION ---


  // Other Handlers
  const handleCloseTranspiledView = () => setShowTranspiledCode(false);
  const saveTranspiledCode = () => {
    if (!transpiledCode) return;
    const blob = new Blob([transpiledCode], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    const baseName = currentFile.name.replace(/\.cns$/i, '') || 'transpiled';
    link.download = `${baseName}.c`;
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link); link.click(); document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    setExecutionStatus(prev => ({...prev, message: `${prev.message || 'Exited'} (C code saved)`}));
   };
  const handleSave = () => {
    if (!currentFileId || !currentFile) return;
    const blob = new Blob([currentFile.content], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.download = currentFile.name;
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link); link.click(); document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    setLexicalStatus(prev => ({...prev, message: `${prev.message || 'OK'} (File Saved)`}));
   };
  const handleOpenFromDisk = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader(); 
      reader.onload = (e) => {
        const content = e.target.result;
        if (files.length >=30) { alert('Maximum of 30 files reached.'); return; }
        const newFile = { id: uuidv4(), name: file.name.endsWith('.cns') ? file.name : `${file.name}.cns`, content: content };
        setFiles(prevFiles => [...prevFiles, newFile]);
        setCurrentFileId(newFile.id);
      };
      reader.onerror = (e) => { setLexicalStatus(createStatus(`Error reading file: ${e.target.error}`, STATUS_TYPE.ERROR)); };
      reader.readAsText(file);
      event.target.value = null;
    }
   };
  const clearTerminal = () => {
      setLexicalStatus(createStatus("Terminal Cleared. Ready."));
      setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
      setTranspiledCode('');
      interactiveTerminalRef.current?.clearTerminal();
  };

  // --- File Management Handlers ---

  const handleFileSelect = (fileId) => {
    if (fileId !== currentFileId) {
        setCurrentFileId(fileId);
        setLexicalStatus(createStatus("Loading file...", STATUS_TYPE.INFO));
        setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
        setSyntaxValid(false); setTranspiledCode(''); setTokens([]);
    }
   };

  // Add this handler to manage loading sample programs
  const handleSampleSelect = (sample) => {
    // Check if a file with the same name already exists in the file explorer
    const existingFile = files.find(f => f.name === sample.name);

    if (existingFile) {
      // If it exists, just make it the active file
      setCurrentFileId(existingFile.id);
    } else {
      // If it's a new sample, create a new file object for it
      const newFile = {
        id: `sample-${Date.now()}`, // Give it a unique ID
        name: sample.name,
        content: sample.content,
      };
      // Add the new file to the list and make it active
      setFiles(prevFiles => [...prevFiles, newFile]);
      setCurrentFileId(newFile.id);
    }
  };

  const handleFileCreate = (name) => {
    if (files.length >= 30) { alert('Maximum of 30 files reached.'); return; }
    const newFile = { id: uuidv4(), name: name, content: '' };
    setFiles(prevFiles => [...prevFiles, newFile]);
    setCurrentFileId(newFile.id);
    setLexicalStatus(createStatus("New file created. Ready."));
    setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
    setTokens([]); setSyntaxValid(false); setTranspiledCode('');
   };
  const handleFileRename = (fileId, newName) => {
    setFiles(prevFiles => prevFiles.map(file => file.id === fileId ? { ...file, name: newName } : file));
   };
  const handleFileDelete = (fileId) => {
    if (files.length <= 1) { alert('Cannot delete the last file.'); return; }
    const fileToDelete = files.find(f => f.id === fileId);
    const remainingFiles = files.filter(file => file.id !== fileId);
    setFiles(remainingFiles);
    if (fileId === currentFileId) {
      const newCurrentFile = remainingFiles[0];
      setCurrentFileId(newCurrentFile.id);
      setLexicalStatus(createStatus(`Deleted ${fileToDelete?.name}. Loading ${newCurrentFile.name}...`, STATUS_TYPE.INFO));
      setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
      setSyntaxValid(false); setTranspiledCode(''); setTokens([]);
    } else {
         setLexicalStatus(createStatus(`Deleted ${fileToDelete?.name}`, STATUS_TYPE.INFO));
    }
   };
  const handleThemeChange = (themeId) => setCurrentTheme(themeId);

  // --- Terminal Panel ResizeHandlers ---
  const handleMouseDownOnTerminalResizer = (e) => {
    isResizingTerminalPanelRef.current = true;
    terminalResizerLastYRef.current = e.clientY;
    document.body.style.cursor = 'ns-resize'; // Change cursor globally
    e.preventDefault();

    const handleMouseMove = (moveEvent) => {
      if (!isResizingTerminalPanelRef.current) return;
      const deltaY = moveEvent.clientY - terminalResizerLastYRef.current;
      setTerminalPanelHeight(prevHeight => {
        const newHeight = prevHeight - deltaY; // Subtract deltaY because dragging down increases height from top
        const minHeight = 100; // Minimum height for the terminal panel
        const maxHeight = window.innerHeight - 200; // Max height (leave some space for editor & header)
        return Math.max(minHeight, Math.min(newHeight, maxHeight));
      });
      terminalResizerLastYRef.current = moveEvent.clientY;
    };

    const handleMouseUp = () => {
      isResizingTerminalPanelRef.current = false;
      document.body.style.cursor = 'default'; // Reset global cursor
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };
  // --- End Terminal Panel Resize Handlers ---

  // --- Render ---
  const renderWakeupBanner = () => (
    <div
      style={{
        position: 'fixed',
        right: 20,
        bottom: 20,
        zIndex: 200,
        background: '#1e1e1e', // Changed to match terminal/theme background
        color: '#eee',
        borderRadius: 10,
        boxShadow: '0 2px 12px #0008',
        padding: '18px 24px',
        minWidth: 340,
        maxWidth: 420,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: 10,
        fontSize: 15,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}>
        <b>Before using the IDE:</b>
        <button
          style={{
            background: 'none',
            border: 'none',
            color: '#0af',
            cursor: 'pointer',
            fontSize: 18,
            padding: 0,
          }}
          onClick={() => setShowInfo((v) => !v)}
          title="Why do I need to do this?"
        >
          <VscInfo />
        </button>
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <a
          href="https://conso-backend-v2.onrender.com/"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: '#0e639c',
            color: '#fff',
            border: 'none',
            borderRadius: 5,
            padding: '8px 14px',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          Wake Backend
        </a>
        <a
          href="https://conso-python-api-v2.onrender.com/"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: '#0e639c',
            color: '#fff',
            border: 'none',
            borderRadius: 5,
            padding: '8px 14px',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          Wake Python API
        </a>
        <a
          href="https://conso-websocket-v2.onrender.com/"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: '#0e639c',
            color: '#fff',
            border: 'none',
            borderRadius: 5,
            padding: '8px 14px',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          Wake WebSocket
        </a>
      </div>
      {showInfo && (
        <div
          style={{
            marginTop: 8,
            background: '#181a20',
            color: '#ccc',
            borderRadius: 6,
            padding: '10px 12px',
            fontSize: 14,
            boxShadow: '0 1px 4px #0006',
          }}
        >
          <b>Why do I need to do this?</b>
          <br />
          This IDE is hosted on Render's free tier. When not used for a while, each backend service (API, WebSocket, and Backend) "sleeps" to save resources. The first request after sleeping can take 30–60 seconds to start. <br /><br />
          <b>To avoid errors and delays</b>, please click each button above to open the backend services in new tabs. Wait for each to load (you should see a Render landing page or a simple message), then return here and use the IDE as normal.<br /><br />
          <b>Note:</b> Code execution (GCC compilation) may be slow, since it runs inside a Docker container on Render's free plan.
        </div>
      )}
    </div>
  );

  return (
    <div className="app-container" data-theme={currentTheme} style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <header className="app-header">
        {/* Logo and Title */}
        <div className="header-left">
          <img src="/assets/revamped_cnslogo.svg" alt="Conso Logo" />
          <div className="app-title">
            CNS Compiler
          </div>
        </div>
        {/* Current File Name */}
        <div className="file-name-container">
          <span>{currentFile?.name || 'No file selected'}</span>
        </div>
        {/* Controls */}
        <div className="app-controls">
           <div className="control-group">
             <button onClick={handleSave} title="Save current file (Ctrl+S)" className="control-button primary">
               <VscSave />
               <span>Save</span>
             </button>
             <input type="file" id="file-open" accept=".cns,.txt" style={{ display: 'none' }} onChange={handleOpenFromDisk} />
             <button onClick={() => document.getElementById('file-open').click()} title="Open file from disk" className="control-button">
               <VscFolder />
               <span>Open</span>
             </button>
           </div>
           
           <div className="control-group">
             {!isRunning ? (
               <button
                 onClick={handleRun}
                 disabled={!canRun}
                 title={canRun ? "Run the code" : "Cannot run (check syntax or running status)"}
                 className="control-button success"
               >
                 <VscRunAll />
                 <span>Run</span>
               </button>
             ) : (
               <button
                 onClick={handleStop}
                 title="Stop the running process"
                 className="control-button danger"
               >
                 <VscDebugStop />
                 <span>Stop</span>
               </button>
             )}
             <button onClick={clearTerminal} title="Clear terminal messages" className="control-button danger">
               <VscTrash />
               <span>Clear</span>
             </button>
           </div>
           
           <div className="control-group">
             <button onClick={() => setShowTranspiledCode(true)} disabled={!transpiledCode} title={transpiledCode ? "View generated C code" : "No C code generated yet"} className="control-button special">
               <VscEye />
               <span>View C</span>
             </button>
             <button onClick={saveTranspiledCode} disabled={!transpiledCode} title={transpiledCode ? "Save generated C code" : "No C code generated yet"} className="control-button warning">
               <VscCloudDownload />
               <span>Save C</span>
             </button>
           </div>

           {/* Spacer to push the GitHub button to the far right */}
           <div style={{ flex: 1 }}></div>

           {/* GitHub Star Button */}
           <div className="control-group">
                <a
                    href="https://github.com/Yuyuhiei/conso-web-ide"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="control-button github-button"
                    title="Star this project on GitHub!"
                    style={{ textDecoration: 'none' }}
                >
                    <VscGithub />
                    <span>Star on GitHub</span>
                </a>
            </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'row', overflow: 'hidden', position: 'relative' }}>
        <Sidebar
          files={files}
          currentFileId={currentFileId}
          onFileSelect={handleFileSelect}
          onFileCreate={handleFileCreate}
          onFileRename={handleFileRename}
          onFileDelete={handleFileDelete}
          currentTheme={currentTheme}
          onThemeChange={handleThemeChange}
          onSampleSelect={handleSampleSelect} // Pass the new handler here
        />
        <div className="editor-and-terminal-wrapper" style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div className="editor-pane" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            {/* Editor container */}
            <div className="editor-container" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
              <CodeEditor
                key={currentFileId} // Ensure editor remounts on file change if needed
                value={currentFile?.content || ''}
                onChange={handleCodeChange}
                onSave={handleSave}
                theme={currentTheme}
                editorRef={editorRef} // Pass ref if needed by CodeEditor internally
              />
              <TokenTable tokens={tokens} />
            </div>

            {/* Resizer for Terminal Panel */}
            <div
              className="terminal-panel-resizer"
              style={{
                height: '1px', // Height of the draggable area
                width: '100%',
                backgroundColor: '#333', // A slightly different color for the resizer
                cursor: 'ns-resize', // North-South resize cursor
                flexShrink: 0, // Prevent this from shrinking
                userSelect: 'none', // Prevent text selection on the handle
              }}
              onMouseDown={handleMouseDownOnTerminalResizer}
            />

            {/* InteractiveTerminal */}
            <div className="terminal-wrapper" style={{ height: `${terminalPanelHeight}px`, flexShrink: 0, display: 'flex', backgroundColor: '#1e1e1e' /* Ensure bg color */ }}>
              <InteractiveTerminal
                  ref={interactiveTerminalRef}
                  lexicalStatus={lexicalStatus}
                  syntaxStatus={syntaxStatus}
                  semanticStatus={semanticStatus}
                  executionStatus={executionStatus}
                  runId={currentRunId}
                  websocketUrl={interactiveWsUrl}
                  onProcessExit={handleProcessExit} // Pass the memoized callback
                  isRunning={isRunning}
                  transpiledCode={transpiledCode}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Transpiled Code Modal View */}
      {showTranspiledCode && (
         <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100 }}>
            <TranspiledCodeView
              code={transpiledCode}
              visible={showTranspiledCode}
              onClose={handleCloseTranspiledView}
              onSave={saveTranspiledCode}
            />
         </div>
      )}

      {/* Wakeup Banner - NEW SECTION ADDED HERE */}
      {renderWakeupBanner()}
    </div>
  );
};

// Debug Page Setup & Main App Router
const DebugHeader = () => (
  <header style={{ backgroundColor: '#252526', padding: '10px 20px', borderBottom: '1px solid #333', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <img src="/assets/revamped_cnslogo.svg" alt="Conso Logo" style={{ height: '32px', width: 'auto' }} />
      <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', fontSize: '20px', fontWeight: 'bold', color: '#ccc' }}>CNS Compiler - Debug Mode</div>
    </div>
    <div><Link to="/" style={{ color: '#0E639C', textDecoration: 'none' }}>Back to Editor</Link></div>
  </header>
);

const App = () => (
  <Router>
    <Routes>
      <Route path="/" element={<MainApp />} />
    </Routes>
  </Router>
);

export default App;
