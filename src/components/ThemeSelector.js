import React from 'react';
import { themes } from '../utils/themes'; // Import themes
import { VscCheck } from 'react-icons/vsc'; // Import a check icon
import './ThemeSelector.css'; // Import the new CSS file

const ThemeSelector = ({ currentTheme, onThemeChange }) => {
  return (
    <div className="theme-selector">
      {themes.map(theme => (
        <div 
          key={theme.id}
          className={`theme-item ${currentTheme === theme.id ? 'active' : ''}`}
          onClick={() => onThemeChange(theme.id)}
        >
          <div 
            className="theme-preview" 
            style={{
              backgroundColor: theme.colors.background,
              border: `1px solid ${theme.colors.accent}`,
            }}
          >
            <div 
              className="preview-text-line" 
              style={{ backgroundColor: theme.colors.text }}
            ></div>
            <div 
              className="preview-accent-dot" 
              style={{ backgroundColor: theme.colors.accent }}
            ></div>
          </div>
          
          <span className="theme-name">{theme.name}</span>
          
          {currentTheme === theme.id && (
            <VscCheck className="active-checkmark" />
          )}
        </div>
      ))}
    </div>
  );
};

export default ThemeSelector;