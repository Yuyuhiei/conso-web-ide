import React, { useState, useEffect, useRef, useCallback } from 'react'; // Import useCallback
import { v4 as uuidv4 } from 'uuid';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import CodeEditor from './components/NewEditor';
import InteractiveTerminal from './components/InteractiveTerminal';
import TokenTable from './components/TokenTable';
import Sidebar from './components/Sidebar';
import TranspiledCodeView from './components/TranspiledCodeView';
import { prepareRun } from './services/api';
import websocketService from './services/websocketService';
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
  const handleFileSelect = (fileId) => {
    if (fileId !== currentFileId) {
        setCurrentFileId(fileId);
        setLexicalStatus(createStatus("Loading file...", STATUS_TYPE.INFO));
        setSyntaxStatus(createStatus()); setSemanticStatus(createStatus()); setExecutionStatus(createStatus());
        setSyntaxValid(false); setTranspiledCode(''); setTokens([]);
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

  // --- Terminal Panel Resize Handlers ---
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
  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <header className="app-header" style={{ display: 'flex', alignItems: 'center', backgroundColor: '#252526', padding: '0 10px', borderBottom: '1px solid #333', flexShrink: 0 }}>
        {/* Logo and Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img src="/assets/revamped_cnslogo.svg" alt="Conso Logo" style={{ height: '32px', width: 'auto' }} />
          <div className="app-title" style={{ fontFamily: 'Segoe UI, Arial, sans-serif', fontSize: '20px', fontWeight: 'bold', padding: '10px 0', marginRight: '20px', color: '#ccc' }}>
            CNS Compiler
          </div>
        </div>
        {/* Current File Name */}
        <div className="file-name-container" style={{ flexGrow: 1, textAlign: 'center', color: '#aaa' }}>
          <span>{currentFile?.name || 'No file selected'}</span>
        </div>
        {/* Controls */}
        <div className="app-controls" style={{ display: 'flex', gap: '8px', padding: '5px 0' }}>
           <button onClick={handleSave} title="Save current file (Ctrl+S)" style={{ backgroundColor: '#0E639C', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Save</button>
           <input type="file" id="file-open" accept=".cns,.txt" style={{ display: 'none' }} onChange={handleOpenFromDisk} />
           <button onClick={() => document.getElementById('file-open').click()} title="Open file from disk" style={{ backgroundColor: '#0E639C', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Open</button>
           <button
             onClick={handleRun}
             disabled={!canRun}
             title={canRun ? "Run the code" : "Cannot run (check syntax or running status)"}
             style={{
               backgroundColor: canRun ? '#2e7d32' : '#444',
               color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px',
               cursor: canRun ? 'pointer' : 'not-allowed', opacity: canRun ? 1 : 0.6
             }}
           >
             {isRunning ? 'Running...' : 'Run'}
           </button>
           <button onClick={() => setShowTranspiledCode(true)} disabled={!transpiledCode} title={transpiledCode ? "View generated C code" : "No C code generated yet"} style={{ backgroundColor: transpiledCode ? '#4a148c' : '#444', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: transpiledCode ? 'pointer' : 'not-allowed', opacity: transpiledCode ? 1 : 0.6 }}>
             View C
           </button>
           <button onClick={saveTranspiledCode} disabled={!transpiledCode} title={transpiledCode ? "Save generated C code" : "No C code generated yet"} style={{ backgroundColor: transpiledCode ? '#ef6c00' : '#444', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: transpiledCode ? 'pointer' : 'not-allowed', opacity: transpiledCode ? 1 : 0.6 }}>
             Save C
           </button>
           <button onClick={clearTerminal} title="Clear terminal messages" style={{ backgroundColor: '#f44336', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Clear</button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'row', overflow: 'hidden', position: 'relative' }}>
        {/* Sidebar */}
        <Sidebar
          files={files}
          currentFileId={currentFileId}
          onFileSelect={handleFileSelect}
          onFileCreate={handleFileCreate}
          onFileRename={handleFileRename}
          onFileDelete={handleFileDelete}
          currentTheme={currentTheme}
          onThemeChange={handleThemeChange}
          resizable={true}
        />

        {/* Editor and Terminal Area */}
        <div className="editor-terminal-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
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
