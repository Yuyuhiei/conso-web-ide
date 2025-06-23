export const themes = [
  { 
    id: 'conso-dark', 
    name: 'Dark (Default)', 
    colors: { background: '#1E1E1E', text: '#D4D4D4', accent: '#0E639C' } 
  },
  { 
    id: 'conso-monokai', 
    name: 'Monokai', 
    colors: { background: '#272822', text: '#F8F8F2', accent: '#A6E22E' } 
  },
  { 
    id: 'conso-dracula', 
    name: 'Dracula', 
    colors: { background: '#282A36', text: '#F8F8F2', accent: '#BD93F9' } 
  },
  { 
    id: 'conso-sunset', 
    name: 'Sunset', 
    colors: { background: '#2C2C2C', text: '#F2F2F2', accent: '#FF8C00' } 
  },
  { 
    id: 'conso-forest', 
    name: 'Forest', 
    colors: { background: '#222725', text: '#CAD2C5', accent: '#84A98C' } 
  },
  { 
    id: 'conso-oceanic', 
    name: 'Oceanic', 
    colors: { background: '#263238', text: '#B0BEC5', accent: '#00ACC1' } 
  },
  { 
    id: 'conso-crimson', 
    name: 'Crimson', 
    colors: { background: '#212121', text: '#EEEEEE', accent: '#E53935' } 
  },
  { 
    id: 'conso-cyberpunk', 
    name: 'Cyberpunk', 
    colors: { background: '#1A101F', text: '#D9D9D9', accent: '#F92672' } 
  },
  { 
    id: 'conso-graphite', 
    name: 'Graphite', 
    colors: { background: '#343A40', text: '#F8F9FA', accent: '#ADB5BD' } 
  },
  { 
    id: 'conso-solarized-dark', 
    name: 'Solarized Dark', 
    colors: { background: '#002B36', text: '#839496', accent: '#268BD2' } 
  }
];

// This function registers the themes with Monaco editor
export const registerMonacoThemes = (monaco) => {
  if (!monaco) return;

  monaco.editor.defineTheme('conso-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#1E1E1E',
    }
  });

  monaco.editor.defineTheme('conso-monokai', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#272822',
    }
  });

  monaco.editor.defineTheme('conso-dracula', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#282A36',
    }
  });

  monaco.editor.defineTheme('conso-sunset', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#2C2C2C',
    }
  });

  monaco.editor.defineTheme('conso-forest', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#222725',
    }
  });

  monaco.editor.defineTheme('conso-oceanic', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#263238',
    }
  });

  monaco.editor.defineTheme('conso-crimson', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#212121',
    }
  });

  monaco.editor.defineTheme('conso-cyberpunk', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#1A101F',
    }
  });

  monaco.editor.defineTheme('conso-graphite', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#343A40',
    }
  });

  monaco.editor.defineTheme('conso-solarized-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#002B36',
    }
  });
};