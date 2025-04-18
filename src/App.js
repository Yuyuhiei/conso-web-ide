import React, { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import CodeEditor from './components/NewEditor';
import Terminal from './components/Terminal'; // Terminal component
import TokenTable from './components/TokenTable';
import Sidebar from './components/Sidebar';
import TranspiledCodeView from './components/TranspiledCodeView';
import DebugTest from './components/DebugTest';
import InputModal from './components/InputModal'; // Import the new modal component
// Import the updated API functions
import { analyzeSemantics, initiateRun, executeRunWithInput } from './services/api'; // Assuming analyzeSemantics might still be useful elsewhere, but not called directly on parse success
import websocketService from './services/websocketService';
import './App.css';

// Define status types for clarity and styling
const STATUS_TYPE = {
  INFO: 'info',
  SUCCESS: 'success',
  ERROR: 'error',
  RUNNING: 'running',
  PENDING: 'pending' // Indicates phase hasn't run yet or is cleared
};

// Helper to create status objects
const createStatus = (message = null, type = STATUS_TYPE.PENDING) => ({ message, type });

// Main application component
const MainApp = () => {
  // --- State Variables ---
  // File management (Keep as is)
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
     const firstFile = files.length > 0 ? files[0] : null; // Check if files array exists and has items
     return firstFile ? firstFile.id : null;
  });


  // Editor and Analysis
  // --- NEW Status States ---
  const [lexicalStatus, setLexicalStatus] = useState(createStatus("Ready"));
  const [syntaxStatus, setSyntaxStatus] = useState(createStatus()); // Starts pending
  const [semanticStatus, setSemanticStatus] = useState(createStatus()); // Starts pending
  const [executionStatus, setExecutionStatus] = useState(createStatus()); // Starts pending
  // --- End NEW Status States ---

  const [tokens, setTokens] = useState([]); // Lexer tokens
  const [syntaxValid, setSyntaxValid] = useState(false); // Keep track if syntax passed for enabling Run
  const [semanticValid, setSemanticValid] = useState(false); // Keep track if semantic passed (set during run)
  const [analyzing, setAnalyzing] = useState(false); // Debounce flag for real-time analysis
  const [isRunning, setIsRunning] = useState(false); // Flag for execution process

  // Transpiler and Execution
  const [transpiledCode, setTranspiledCode] = useState(''); // Stores generated C code
  const [programOutput, setProgramOutput] = useState(''); // Stores C program's stdout
  const [showTranspiledCode, setShowTranspiledCode] = useState(false); // Transpiled code view visibility

  // Input Modal State
  const [isInputModalVisible, setIsInputModalVisible] = useState(false);
  const [requiredPrompts, setRequiredPrompts] = useState([]); // Prompts from the backend

  // Refs
  const editorRef = useRef(null);

  // Theme
  const [currentTheme, setCurrentTheme] = useState(() => localStorage.getItem('conso-theme') || 'conso-dark');

  // --- Derived State ---
  const currentFile = files.find(file => file.id === currentFileId) || files[0] || { id: null, name: '', content: '' };
  // Run button enabled only if syntax is valid (checked real-time) and not currently running
  const canRun = syntaxValid && !isRunning && currentFile && currentFile.content.trim().length > 0;

  // --- Effects ---
  // Save files and current file ID (Keep as is)
  useEffect(() => {
    try {
        localStorage.setItem('conso-files', JSON.stringify(files));
        if (currentFileId) {
            localStorage.setItem('conso-current-file-id', currentFileId);
        }
    } catch (e) { console.error("Failed to save files:", e); }
  }, [files, currentFileId]);

  // Save theme (Keep as is)
  useEffect(() => {
    localStorage.setItem('conso-theme', currentTheme);
  }, [currentTheme]);

  // WebSocket connection and message handling
  useEffect(() => {
    websocketService
      .on('open', () => setLexicalStatus(createStatus("WebSocket Connected", STATUS_TYPE.INFO))) // Update lexical status on connect
      .on('lexerResult', (data) => {
        setTokens(data.tokens || []);
        // Update Lexical Status
        if (!data.success) {
          const errorMessages = (data.errors || []).map(err => `${err}`).join('; ');
          setLexicalStatus(createStatus(`Error: ${errorMessages}`, STATUS_TYPE.ERROR));
        } else {
          setLexicalStatus(createStatus("OK", STATUS_TYPE.SUCCESS));
        }
        // Clear subsequent statuses on new lexer result
        setSyntaxStatus(createStatus());
        setSemanticStatus(createStatus());
        setExecutionStatus(createStatus());
        setSyntaxValid(false); // Reset validation flags
        setSemanticValid(false);
        setProgramOutput(''); // Clear old outputs
        setTranspiledCode('');
      })
      .on('parserResult', (data) => {
         // Update Syntax Status
         setSyntaxValid(data.syntaxValid || false); // Update syntax validity flag
         if (data.syntaxValid) {
             setSyntaxStatus(createStatus("OK", STATUS_TYPE.SUCCESS));
         } else {
             const errorMessages = (data.errors || []).join('; ');
             setSyntaxStatus(createStatus(`Error: ${errorMessages}`, STATUS_TYPE.ERROR));
         }
         // Clear subsequent statuses (Semantic/Execution) as parser result came in
         setSemanticStatus(createStatus());
         setExecutionStatus(createStatus());
         setSemanticValid(false); // Reset semantic validity flag
         setProgramOutput(''); // Clear old outputs
         setTranspiledCode('');
         // --- DO NOT trigger semantic analysis here ---
      })
      .on('error', (data) => {
          // Display WebSocket errors potentially in lexical status or a general error area
          setLexicalStatus(createStatus(`WebSocket Error: ${data.message}`, STATUS_TYPE.ERROR));
          // Clear other statuses as connection is problematic
          setSyntaxStatus(createStatus());
          setSemanticStatus(createStatus());
          setExecutionStatus(createStatus());
          setSyntaxValid(false);
          setSemanticValid(false);
      })
      .on('close', () => {
          setLexicalStatus(createStatus("WebSocket Disconnected", STATUS_TYPE.INFO));
          // Optionally clear other statuses or indicate pending
          setSyntaxStatus(createStatus());
          setSemanticStatus(createStatus());
          setExecutionStatus(createStatus());
          setSyntaxValid(false);
          setSemanticValid(false);
      });

    websocketService.connect();

    // Initial analysis for the current file on load
    if (currentFile && currentFile.content) {
         websocketService.sendCode(currentFile.content);
    } else {
        // Set initial state if no file content
        setLexicalStatus(createStatus("Ready"));
        setSyntaxStatus(createStatus());
        setSemanticStatus(createStatus());
        setExecutionStatus(createStatus());
    }

    return () => {
      websocketService.disconnect();
    };
  // Rerun effect ONLY when the current file ID changes, triggering analysis for the new file's content
  }, [currentFileId]); // Dependency only on currentFileId

  // --- Event Handlers ---

  // Debounced code analysis via WebSocket
  const handleCodeChange = useCallback((newValue) => {
    setFiles(prevFiles =>
      prevFiles.map(file =>
        file.id === currentFileId ? { ...file, content: newValue } : file
      )
    );

    // Update lexical status immediately to indicate typing
    setLexicalStatus(createStatus("Analyzing...", STATUS_TYPE.RUNNING));
    // Clear subsequent statuses immediately on change
    setSyntaxStatus(createStatus());
    setSemanticStatus(createStatus());
    setExecutionStatus(createStatus());
    setSyntaxValid(false);
    setSemanticValid(false);
    setProgramOutput('');
    setTranspiledCode('');

    // Debounce the analysis call
    if (!analyzing) {
      setAnalyzing(true);
      const debounceTimer = setTimeout(() => {
        if (websocketService.isConnected) {
           websocketService.sendCode(newValue);
        } else {
            setLexicalStatus(createStatus("Error: WebSocket not connected", STATUS_TYPE.ERROR));
        }
        setAnalyzing(false);
      }, 750);

      return () => clearTimeout(debounceTimer);
    }
  }, [currentFileId, analyzing]); // Keep dependencies minimal

  // Handle the entire run process (initiation + execution)
  const handleRun = async () => {
    if (!canRun) {
      // Update execution status to show why it can't run
      let reason = "Cannot run.";
      if (isRunning) reason = "Already running.";
      else if (!syntaxValid) reason = "Syntax errors detected.";
      else if (!currentFile || !currentFile.content.trim()) reason = "No code to run.";
      setExecutionStatus(createStatus(reason, STATUS_TYPE.ERROR));
      return;
    }

    setIsRunning(true);
    setProgramOutput('');
    setTranspiledCode('');
    // Update statuses to show progress
    setSemanticStatus(createStatus("Running...", STATUS_TYPE.RUNNING));
    setExecutionStatus(createStatus("Waiting for Semantic...", STATUS_TYPE.RUNNING));


    try {
      // Step 1: Initiate Run (Validation + Input Check)
      // This now includes the semantic check on the backend
      const initiateResult = await initiateRun(currentFile.content);

      // Handle Semantic Result first (based on initiateResult structure)
      if (initiateResult.phase === 'semantic' && !initiateResult.success) {
          const errorMsg = (initiateResult.errors || ['Unknown semantic error']).join('; ');
          setSemanticStatus(createStatus(`Error: ${errorMsg}`, STATUS_TYPE.ERROR));
          setExecutionStatus(createStatus("Aborted due to Semantic Error", STATUS_TYPE.ERROR)); // Clear execution status
          setSemanticValid(false);
          setIsRunning(false);
          return; // Stop the run process here
      }
      // If semantic check passed (implicitly or explicitly)
      setSemanticStatus(createStatus("OK", STATUS_TYPE.SUCCESS));
      setSemanticValid(true); // Mark semantic as valid


      // Now handle the rest of the initiateResult
      if (initiateResult.status === "input_required") {
        setExecutionStatus(createStatus("Input Required", STATUS_TYPE.INFO));
        setRequiredPrompts(initiateResult.prompts || []);
        setIsInputModalVisible(true);
        // isRunning remains true
      } else if (initiateResult.success) {
        // Direct execution success (no input needed)
        setTranspiledCode(initiateResult.transpiledCode || '');
        setProgramOutput(initiateResult.output || '(No output)');
        const warnings = (initiateResult.errors || []).join('; '); // C Warnings might be in errors
        setExecutionStatus(createStatus(`Execution OK ${warnings ? `(Warnings: ${warnings})` : ''}`, STATUS_TYPE.SUCCESS));
        setIsRunning(false);
      } else {
        // Error during direct execution (transpile, compile, run C)
        const errorPhase = initiateResult.phase || 'execution';
        const errorMsg = (initiateResult.errors || ['Unknown execution error']).join('; ');
        setExecutionStatus(createStatus(`Error (${errorPhase}): ${errorMsg}`, STATUS_TYPE.ERROR));
        setTranspiledCode(initiateResult.transpiledCode || ''); // Show C code even on C error
        setIsRunning(false);
      }
    } catch (error) {
      // Catch errors from the API call itself
      setSemanticStatus(createStatus(`Error: ${error.message}`, STATUS_TYPE.ERROR)); // Show error possibly in semantic phase
      setExecutionStatus(createStatus("Failed", STATUS_TYPE.ERROR));
      setSemanticValid(false);
      setIsRunning(false);
    }
  };

  // Handle submission of inputs from the modal
  const handleInputSubmit = async (userInputs) => {
    setIsInputModalVisible(false);
    setExecutionStatus(createStatus("Executing with inputs...", STATUS_TYPE.RUNNING));
    // isRunning is still true

    try {
      // Step 2: Execute with Inputs
      const executeResult = await executeRunWithInput(currentFile.content, userInputs);

      if (executeResult.success) {
        setTranspiledCode(executeResult.transpiledCode || '');
        setProgramOutput(executeResult.output || '(No output)');
        const warnings = (executeResult.errors || []).join('; '); // C Warnings
        setExecutionStatus(createStatus(`Execution OK ${warnings ? `(Warnings: ${warnings})` : ''}`, STATUS_TYPE.SUCCESS));
      } else {
        // Error during execution with input (transpile, compile, run C)
        const errorPhase = executeResult.phase || 'execution';
        const errorMsg = (executeResult.errors || ['Unknown execution error']).join('; ');
        setExecutionStatus(createStatus(`Error (${errorPhase}): ${errorMsg}`, STATUS_TYPE.ERROR));
        setTranspiledCode(executeResult.transpiledCode || ''); // Show C code even on C error
      }
    } catch (error) {
      setExecutionStatus(createStatus(`Execution Failed: ${error.message}`, STATUS_TYPE.ERROR));
    } finally {
      setIsRunning(false); // Ensure running flag is reset
      setRequiredPrompts([]);
    }
  };

  // Handle closing the input modal without submitting
  const handleInputModalClose = () => {
    setIsInputModalVisible(false);
    setIsRunning(false); // Stop the run process
    setExecutionStatus(createStatus("Run cancelled by user", STATUS_TYPE.INFO));
    setRequiredPrompts([]);
  };


  // --- Other Handlers (File Management, Theme, etc. - Keep as is) ---
  const handleCloseTranspiledView = () => setShowTranspiledCode(false);
  const saveTranspiledCode = () => { /* Keep implementation */
    if (!transpiledCode) return;
    const blob = new Blob([transpiledCode], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    const baseName = currentFile.name.replace(/\.cns$/i, '') || 'transpiled';
    link.download = `${baseName}.c`;
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    // Update status instead of output log
    setExecutionStatus(prev => ({...prev, message: `${prev.message} (C code saved)`}));
   };
  const handleSave = () => { /* Keep implementation */
    if (!currentFileId || !currentFile) return;
    const blob = new Blob([currentFile.content], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.download = currentFile.name;
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    setLexicalStatus(prev => ({...prev, message: `${prev.message} (File Saved)`})); // Indicate save
   };
  const handleOpenFromDisk = (event) => { /* Keep implementation, ensure handleCodeChange is called */
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target.result;
        if (files.length >= 10) { alert('Maximum of 10 files reached.'); return; }
        const newFile = { id: uuidv4(), name: file.name.endsWith('.cns') ? file.name : `${file.name}.cns`, content: content };
        setFiles(prevFiles => [...prevFiles, newFile]);
        setCurrentFileId(newFile.id); // Switch to the newly opened file
        // handleCodeChange will be triggered by useEffect dependency on currentFileId
      };
      reader.onerror = (e) => { setLexicalStatus(createStatus(`Error reading file: ${e.target.error}`, STATUS_TYPE.ERROR)); };
      reader.readAsText(file);
      event.target.value = null;
    }
   };
  const clearTerminal = () => {
      // Reset all status messages
      setLexicalStatus(createStatus("Terminal Cleared. Ready."));
      setSyntaxStatus(createStatus());
      setSemanticStatus(createStatus());
      setExecutionStatus(createStatus());
      setProgramOutput('');
      setTranspiledCode(''); // Optionally clear C code view as well
      // Note: Tokens are typically cleared by handleCodeChange or file switching
  };
  const handleFileSelect = (fileId) => { /* Keep implementation, ensure states are reset */
    if (fileId !== currentFileId) {
        setCurrentFileId(fileId);
        // useEffect dependency on currentFileId will trigger analysis for the new file
        // Reset statuses manually for immediate feedback
        setLexicalStatus(createStatus("Loading file...", STATUS_TYPE.INFO));
        setSyntaxStatus(createStatus());
        setSemanticStatus(createStatus());
        setExecutionStatus(createStatus());
        setSyntaxValid(false);
        setSemanticValid(false);
        setProgramOutput('');
        setTranspiledCode('');
        setTokens([]);
    }
   };
  const handleFileCreate = (name) => { /* Keep implementation, ensure states are reset */
    if (files.length >= 10) { alert('Maximum of 10 files reached.'); return; }
    const newFile = { id: uuidv4(), name: name, content: '' };
    setFiles(prevFiles => [...prevFiles, newFile]);
    setCurrentFileId(newFile.id);
    // Reset states for the new empty file
    setLexicalStatus(createStatus("New file created. Ready."));
    setSyntaxStatus(createStatus());
    setSemanticStatus(createStatus());
    setExecutionStatus(createStatus());
    setTokens([]);
    setSyntaxValid(false);
    setSemanticValid(false);
    setProgramOutput('');
    setTranspiledCode('');
    // No need to call handleCodeChange('') as useEffect handles the switch
   };
  const handleFileRename = (fileId, newName) => { /* Keep implementation */
    setFiles(prevFiles => prevFiles.map(file => file.id === fileId ? { ...file, name: newName } : file));
   };
  const handleFileDelete = (fileId) => { /* Keep implementation, ensure state update on switch */
    if (files.length <= 1) { alert('Cannot delete the last file.'); return; }
    const fileToDelete = files.find(f => f.id === fileId); // Get name before deleting
    const remainingFiles = files.filter(file => file.id !== fileId);
    setFiles(remainingFiles);

    if (fileId === currentFileId) {
      const newCurrentFile = remainingFiles[0];
      setCurrentFileId(newCurrentFile.id);
      // Reset states for the new file, useEffect will handle analysis
       setLexicalStatus(createStatus(`Deleted ${fileToDelete?.name}. Loading ${newCurrentFile.name}...`, STATUS_TYPE.INFO));
       setSyntaxStatus(createStatus());
       setSemanticStatus(createStatus());
       setExecutionStatus(createStatus());
       setSyntaxValid(false);
       setSemanticValid(false);
       setProgramOutput('');
       setTranspiledCode('');
       setTokens([]);
    } else {
         setLexicalStatus(createStatus(`Deleted ${fileToDelete?.name}`, STATUS_TYPE.INFO)); // Update status
    }
   };
  const handleThemeChange = (themeId) => setCurrentTheme(themeId);


  // --- Render ---
  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header (Keep as is, ensure Run button uses 'canRun' for disabled state) */}
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
         {/* Debug Link */}
         <div style={{ marginRight: '20px' }}>
           <Link to="/debug" style={{ color: '#0E639C', textDecoration: 'none' }}>Debug Mode</Link>
         </div>
         {/* Controls */}
         <div className="app-controls" style={{ display: 'flex', gap: '8px', padding: '5px 0' }}>
            <button onClick={handleSave} title="Save current file (Ctrl+S)" style={{ backgroundColor: '#0E639C', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Save</button>
            <input type="file" id="file-open" accept=".cns,.txt" style={{ display: 'none' }} onChange={handleOpenFromDisk} />
            <button onClick={() => document.getElementById('file-open').click()} title="Open file from disk" style={{ backgroundColor: '#0E639C', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Open</button>
            <button
              onClick={handleRun}
              disabled={!canRun} // Use derived state 'canRun'
              title={canRun ? "Run the code" : "Cannot run (check syntax or running status)"}
              style={{
                backgroundColor: canRun ? '#2e7d32' : '#444', // Green when runnable
                color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px',
                cursor: canRun ? 'pointer' : 'not-allowed',
                opacity: canRun ? 1 : 0.6
              }}
            >
              {isRunning ? 'Running...' : 'Run'}
            </button>
            <button
              onClick={() => setShowTranspiledCode(true)}
              disabled={!transpiledCode}
              title={transpiledCode ? "View generated C code" : "No C code generated yet"}
              style={{
                backgroundColor: transpiledCode ? '#4a148c' : '#444', // Purple when available
                color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px',
                cursor: transpiledCode ? 'pointer' : 'not-allowed',
                opacity: transpiledCode ? 1 : 0.6
              }}
            >
              View C
            </button>
            <button
              onClick={saveTranspiledCode}
              disabled={!transpiledCode}
              title={transpiledCode ? "Save generated C code" : "No C code generated yet"}
              style={{
                backgroundColor: transpiledCode ? '#ef6c00' : '#444', // Orange when available
                color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px',
                cursor: transpiledCode ? 'pointer' : 'not-allowed',
                opacity: transpiledCode ? 1 : 0.6
              }}
            >
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
              key={currentFileId}
              value={currentFile?.content || ''}
              onChange={handleCodeChange}
              onSave={handleSave}
              theme={currentTheme}
              editorRef={editorRef}
            />
            <TokenTable tokens={tokens} />
          </div>

          {/* Terminal container - Pass new status props */}
          <Terminal
            lexicalStatus={lexicalStatus}
            syntaxStatus={syntaxStatus}
            semanticStatus={semanticStatus}
            executionStatus={executionStatus}
            programOutput={programOutput} // Still needed for final output display
            transpiledCode={transpiledCode} // Still needed for C code toggle
          />
        </div>
      </div>

      {/* Transpiled Code Modal View (Keep as is) */}
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

       {/* Input Modal (Keep as is) */}
       <InputModal
         isVisible={isInputModalVisible}
         prompts={requiredPrompts}
         onSubmit={handleInputSubmit}
         onClose={handleInputModalClose}
       />
    </div>
  );
};

// --- Debug Page Setup --- (Keep as is)
const DebugHeader = () => (
  <header style={{ backgroundColor: '#252526', padding: '10px 20px', borderBottom: '1px solid #333', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <img src="/assets/revamped_cnslogo.svg" alt="Conso Logo" style={{ height: '32px', width: 'auto' }} />
      <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', fontSize: '20px', fontWeight: 'bold', color: '#ccc' }}>CNS Compiler - Debug Mode</div>
    </div>
    <div><Link to="/" style={{ color: '#0E639C', textDecoration: 'none' }}>Back to Editor</Link></div>
  </header>
);

const DebugTestWithHeader = () => (
  <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#1e1e1e', color: '#d4d4d4' }}>
    <DebugHeader />
    <DebugTest />
  </div>
);

// --- Main App Router --- (Keep as is)
const App = () => (
  <Router>
    <Routes>
      <Route path="/" element={<MainApp />} />
      <Route path="/debug" element={<DebugTestWithHeader />} />
    </Routes>
  </Router>
);

export default App;
