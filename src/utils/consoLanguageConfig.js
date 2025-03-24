// Configuration for Conso language in Monaco Editor

export const configureConsoLanguage = (monaco) => {
  // Register the language
  monaco.languages.register({ id: 'conso' });

  // Define the token provider (syntax highlighting)
  monaco.languages.setMonarchTokensProvider('conso', {
    // Set defaultToken to a neutral color instead of invalid
    defaultToken: 'text',

    keywords: [
      'npt', 'prnt', 'nt', 'dbl', 'strng', 'bln', 'chr', 
      'f', 'ls', 'lsf', 'swtch', 'fr', 'whl', 'd', 'mn', 'cs', 
      'dflt', 'brk', 'cnst', 'tr', 'fls', 'fnctn', 'rtrn', 'nll',
      'end', 'cntn', 'strct', 'dfstrct', 'vd'
    ],

    typeKeywords: [
      'nt', 'dbl', 'strng', 'bln', 'chr', 'vd'
    ],

    operators: [
      '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
      '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^', '%',
      '+=', '-=', '*=', '/=', '&=', '|=', '^=', '%='
    ],

    // we include these common regular expressions
    symbols: /[=><!~?:&|+\-*\/\^%]+/,
    escapes: /\\(?:[abfnrtv\\"']|x[0-9A-Fa-f]{1,4}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})/,
    digits: /\d+(_+\d+)*/,
    octaldigits: /[0-7]+(_+[0-7]+)*/,
    binarydigits: /[0-1]+(_+[0-1]+)*/,
    hexdigits: /[[0-9a-fA-F]+(_+[0-9a-fA-F]+)*/,

    // The main tokenizer for our languages
    tokenizer: {
      root: [
        // identifiers and keywords - handling both lowercase and uppercase identifiers
        [/[a-zA-Z_$][\w$]*/, {
          cases: {
            '@keywords': 'keyword',
            '@typeKeywords': 'type',
            '@default': 'identifier'
          }
        }],

        // whitespace
        { include: '@whitespace' },

        // semicolons - make them white like normal text
        [/;/, 'delimiter.semicolon'],
        
        // delimiters and operators
        [/[{}()\[\]]/, 'delimiter'],
        [/[<>](?!@symbols)/, 'delimiter'],
        [/[,.]/, 'delimiter'],
        [/@symbols/, {
          cases: {
            '@operators': 'operator',
            '@default': ''
          }
        }],

        // numbers
        [/(@digits)[eE]([\-+]?(@digits))?/, 'number.float'],
        [/(@digits)\.(@digits)([eE][\-+]?(@digits))?/, 'number.float'],
        [/~(@digits)/, 'number.negative'],
        [/~(@digits)\.(@digits)/, 'number.negative.float'],
        [/0[xX](@hexdigits)/, 'number.hex'],
        [/0[oO]?(@octaldigits)/, 'number.octal'],
        [/0[bB](@binarydigits)/, 'number.binary'],
        [/(@digits)/, 'number'],

        // strings
        [/"([^"\\]|\\.)*$/, 'string.invalid'],  // non-terminated string
        [/'([^'\\]|\\.)*$/, 'string.invalid'],  // non-terminated string
        [/"/, 'string', '@string_double'],
        [/'/, 'string', '@string_single'],
      ],

      whitespace: [
        [/[ \t\r\n]+/, 'white'],
        [/#.*$/, 'comment'],
      ],

      string_double: [
        [/[^\\"]+/, 'string'],
        [/@escapes/, 'string.escape'],
        [/\\./, 'string.escape.invalid'],
        [/"/, 'string', '@pop']
      ],

      string_single: [
        [/[^\\']+/, 'string'],
        [/@escapes/, 'string.escape'],
        [/\\./, 'string.escape.invalid'],
        [/'/, 'string', '@pop']
      ],
    }
  });

  // Define language configuration for editor behaviors
  monaco.languages.setLanguageConfiguration('conso', {
    comments: {
      lineComment: '#',
    },
    brackets: [
      ['{', '}'],
      ['[', ']'],
      ['(', ')']
    ],
    autoClosingPairs: [
      { open: '{', close: '}' },
      { open: '[', close: ']' },
      { open: '(', close: ')' },
      { open: '"', close: '"' },
      { open: "'", close: "'" },
    ],
    surroundingPairs: [
      { open: '{', close: '}' },
      { open: '[', close: ']' },
      { open: '(', close: ')' },
      { open: '"', close: '"' },
      { open: "'", close: "'" },
    ],
  });

  // Define themes
  defineEditorThemes(monaco);

  // Add basic completions for Conso keywords
  monaco.languages.registerCompletionItemProvider('conso', {
    provideCompletionItems: (model, position) => {
      const suggestions = [
        ...['npt', 'prnt', 'nt', 'dbl', 'strng', 'bln', 'chr'].map(keyword => ({
          label: keyword,
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: keyword,
          detail: 'Type keyword'
        })),
        ...['f', 'ls', 'lsf', 'swtch', 'fr', 'whl', 'd'].map(keyword => ({
          label: keyword,
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: keyword,
          detail: 'Control flow keyword'
        })),
        ...['fnctn', 'rtrn', 'vd'].map(keyword => ({
          label: keyword,
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: keyword,
          detail: 'Function keyword'
        })),
        
        // Snippets for common constructs
        {
          label: 'fnctn definition',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'fnctn ${1:vd} ${2:name}(${3}) {\n\t${4}\n}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          detail: 'Function definition'
        },
        {
          label: 'if statement',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'f (${1:condition}) {\n\t${2}\n}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          detail: 'If statement'
        },
        {
          label: 'for loop',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'fr (${1:initialization}; ${2:condition}; ${3:increment}) {\n\t${4}\n}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          detail: 'For loop'
        },
        {
          label: 'main function',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'mn() {\n\t${1}\n}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          detail: 'Main function'
        }
      ];
      
      return { suggestions };
    }
  });
};

// Define multiple editor themes
function defineEditorThemes(monaco) {
  // Default Dark Theme
  monaco.editor.defineTheme('conso-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'delimiter.semicolon', foreground: 'D4D4D4' }, // White semicolons
      { token: 'identifier', foreground: 'D4D4D4' },          // White identifiers
      { token: 'type', foreground: '569CD6' },                // Blue for type keywords
      { token: 'keyword', foreground: '569CD6' },             // Blue for other keywords
      { token: 'number', foreground: 'B5CEA8' },              // Light green for numbers
      { token: 'string', foreground: 'CE9178' },              // Orange-brown for strings
      { token: 'comment', foreground: '6A9955' }              // Green for comments
    ],
    colors: {
      'editor.background': '#1E1E1E',
      'editor.foreground': '#D4D4D4',
      'editorCursor.foreground': '#FFFFFF',
      'editor.lineHighlightBackground': '#2D2D30',
      'editorLineNumber.foreground': '#858585',
      'editor.selectionBackground': '#264F78',
      'editor.inactiveSelectionBackground': '#3A3D41',
      'editorIndentGuide.background': '#404040'
    }
  });

  // Light Theme
  monaco.editor.defineTheme('conso-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'delimiter.semicolon', foreground: '000000' }, // Black semicolons
      { token: 'identifier', foreground: '000000' },          // Black identifiers
      { token: 'type', foreground: '0000FF' },                // Blue for type keywords
      { token: 'keyword', foreground: '0000FF' },             // Blue for other keywords
      { token: 'number', foreground: '098658' },              // Green for numbers
      { token: 'string', foreground: 'A31515' },              // Red for strings
      { token: 'comment', foreground: '008000' }              // Green for comments
    ],
    colors: {
      'editor.background': '#FFFFFF',
      'editor.foreground': '#000000',
      'editorCursor.foreground': '#000000',
      'editor.lineHighlightBackground': '#F5F5F5',
      'editorLineNumber.foreground': '#237893',
      'editor.selectionBackground': '#ADD6FF',
      'editor.inactiveSelectionBackground': '#E5EBF1',
      'editorIndentGuide.background': '#D3D3D3'
    }
  });

  // Monokai Theme
  monaco.editor.defineTheme('conso-monokai', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'delimiter.semicolon', foreground: 'F8F8F2' }, // Light gray semicolons
      { token: 'identifier', foreground: 'F8F8F2' },          // Light gray identifiers
      { token: 'type', foreground: '66D9EF' },                // Light blue for type keywords
      { token: 'keyword', foreground: 'F92672' },             // Pink for keywords
      { token: 'number', foreground: 'AE81FF' },              // Purple for numbers
      { token: 'string', foreground: 'E6DB74' },              // Yellow for strings
      { token: 'comment', foreground: '75715E' }              // Gray for comments
    ],
    colors: {
      'editor.background': '#272822',
      'editor.foreground': '#F8F8F2',
      'editorCursor.foreground': '#F8F8F2',
      'editor.lineHighlightBackground': '#3E3D32',
      'editorLineNumber.foreground': '#90908A',
      'editor.selectionBackground': '#49483E',
      'editor.inactiveSelectionBackground': '#40403A',
      'editorIndentGuide.background': '#3B3A32'
    }
  });

  // Dracula Theme
  monaco.editor.defineTheme('conso-dracula', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'delimiter.semicolon', foreground: 'F8F8F2' }, // Light gray semicolons
      { token: 'identifier', foreground: 'F8F8F2' },          // Light gray identifiers
      { token: 'type', foreground: '8BE9FD' },                // Cyan for type keywords
      { token: 'keyword', foreground: 'FF79C6' },             // Pink for keywords
      { token: 'number', foreground: 'BD93F9' },              // Purple for numbers
      { token: 'string', foreground: 'F1FA8C' },              // Yellow for strings
      { token: 'comment', foreground: '6272A4' }              // Blue for comments
    ],
    colors: {
      'editor.background': '#282A36',
      'editor.foreground': '#F8F8F2',
      'editorCursor.foreground': '#F8F8F2',
      'editor.lineHighlightBackground': '#44475A',
      'editorLineNumber.foreground': '#6272A4',
      'editor.selectionBackground': '#44475A',
      'editor.inactiveSelectionBackground': '#3A3D41',
      'editorIndentGuide.background': '#424450'
    }
  });
}

export default configureConsoLanguage;