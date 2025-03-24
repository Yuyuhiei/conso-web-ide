import React from 'react';

// Define themes with previews
const themes = [
  { 
    id: 'conso-dark', 
    name: 'Dark (Default)', 
    colors: {
      background: '#1E1E1E',
      text: '#D4D4D4',
      accent: '#0E639C'
    } 
  },
  { 
    id: 'conso-light', 
    name: 'Light', 
    colors: {
      background: '#FFFFFF',
      text: '#000000',
      accent: '#1976D2'
    } 
  },
  { 
    id: 'conso-monokai', 
    name: 'Monokai', 
    colors: {
      background: '#272822',
      text: '#F8F8F2',
      accent: '#A6E22E'
    } 
  },
  { 
    id: 'conso-dracula', 
    name: 'Dracula', 
    colors: {
      background: '#282A36',
      text: '#F8F8F2',
      accent: '#BD93F9'
    } 
  }
];

const ThemeSelector = ({ currentTheme, onThemeChange }) => {
  return (
    <div className="theme-selector">
      {themes.map(theme => (
        <div 
          key={theme.id}
          className={`theme-item ${currentTheme === theme.id ? 'active' : ''}`}
          onClick={() => onThemeChange(theme.id)}
          style={{
            padding: '8px 10px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: currentTheme === theme.id ? '#37373D' : 'transparent',
            borderLeft: currentTheme === theme.id ? '2px solid #0E639C' : '2px solid transparent',
            paddingLeft: currentTheme === theme.id ? '8px' : '10px'
          }}
        >
          <div 
            className="theme-preview" 
            style={{
              width: '20px',
              height: '20px',
              backgroundColor: theme.colors.background,
              border: `1px solid ${theme.colors.accent}`,
              position: 'relative',
              borderRadius: '3px',
              overflow: 'hidden'
            }}
          >
            <div style={{ 
              position: 'absolute',
              top: '3px',
              left: '3px',
              right: '3px',
              height: '3px',
              backgroundColor: theme.colors.text,
              opacity: 0.7
            }}></div>
            <div style={{ 
              position: 'absolute',
              bottom: '3px',
              left: '3px', 
              width: '5px',
              height: '5px',
              backgroundColor: theme.colors.accent,
              borderRadius: '50%'
            }}></div>
          </div>
          
          <span>{theme.name}</span>
          
          {currentTheme === theme.id && (
            <span style={{ marginLeft: 'auto', color: '#0E639C' }}>✓</span>
          )}
        </div>
      ))}
    </div>
  );
};

export default ThemeSelector;