// Configuration for Conso language in Monaco Editor

export const configureConsoLanguage = (monaco) => {
  // Register the language
  monaco.languages.register({ id: 'conso' });

  // Define the token provider (syntax highlighting)
  monaco.languages.setMonarchTokensProvider('conso', {
    // Set defaultToken to invalid to see what you do not tokenize yet
    defaultToken: 'invalid',

    keywords: [
      'npt', 'prnt', 'nt', 'dbl', 'strng', 'bln', 'chr', 
      'f', 'ls', 'lsf', 'swtch', 'fr', 'whl', 'd', 'mn', 'cs', 
      'dflt', 'brk', 'cnst', 'tr', 'fls', 'fnctn', 'rtrn', 'nll',
      'end', 'cntn', 'strct', 'dfstrct', 'vd'
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
        // identifiers and keywords
        [/[a-z_$][\w$]*/, {
          cases: {
            '@keywords': 'keyword',
            '@default': 'identifier'
          }
        }],

        // whitespace
        { include: '@whitespace' },

        // delimiters and operators
        [/[{}()\[\]]/, '@brackets'],
        [/[<>](?!@symbols)/, '@brackets'],
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

export default configureConsoLanguage;