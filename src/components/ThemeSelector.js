import React from 'react';
import { themes } from '../utils/themes'; // Import themes

// Define themes with previews -- This array is now imported from ../utils/themes
/*
const themes = [
...
];
*/

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