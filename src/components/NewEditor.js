import React, { useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { configureConsoLanguage } from '../utils/consoLanguageConfig';

const CodeEditor = ({ 
  value, 
  onChange, 
  onSave,
}) => {
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  
  // Initialize Monaco editor and configure language
  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    
    // Configure the Conso language
    configureConsoLanguage(monaco);
    
    // Set the editor language to Conso
    monaco.editor.setModelLanguage(editor.getModel(), 'conso');
    
    // Add keyboard shortcuts for save
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      if (onSave) onSave();
    });
    
    // Set editor options
    editor.updateOptions({
      tabSize: 4,
      insertSpaces: true,
      autoIndent: 'full',
      contextmenu: true,
      fontFamily: 'Consolas, "Courier New", monospace',
      fontSize: 16,
      lineHeight: 24,
    });
  };
  
  // This effect runs when the value prop changes
  useEffect(() => {
    if (editorRef.current && value !== editorRef.current.getValue()) {
      editorRef.current.setValue(value);
    }
  }, [value]);
  
  return (
    <div className="editor-container" style={{ height: "100%", width: "100%" }}>
      <Editor
        height="100%"
        width="100%"
        defaultLanguage="conso"
        defaultValue={value}
        onChange={onChange}
        onMount={handleEditorDidMount}
        theme="vs-dark"
        options={{
          selectOnLineNumbers: true,
          roundedSelection: false,
          readOnly: false,
          cursorStyle: 'line',
          automaticLayout: true,
          tabSize: 4,
          fontSize: 16,
          minimap: { enabled: true },
          scrollBeyondLastLine: false,
          wordWrap: 'on',
        }}
      />
    </div>
  );
};

export default CodeEditor;