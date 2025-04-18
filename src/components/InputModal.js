// src/components/InputModal.js
import React, { useState, useEffect, useRef } from 'react';
import './InputModal.css'; // We'll create this CSS file next

/**
 * A modal dialog component to collect user input based on prompts.
 *
 * Props:
 * - isVisible (boolean): Controls whether the modal is shown.
 * - prompts (array): An array of objects, each with { variable_name, prompt_text, line }.
 * - onSubmit (function): Callback function executed when the user submits inputs.
 * Receives an object mapping variable_name to user_input.
 * - onClose (function): Callback function executed when the user closes the modal.
 */
const InputModal = ({ isVisible, prompts, onSubmit, onClose }) => {
  // State to hold the current input values entered by the user
  const [inputValues, setInputValues] = useState({});
  // Ref to the first input element for autofocus
  const firstInputRef = useRef(null);

  // Effect to reset input values when prompts change (modal likely reopened)
  // and focus the first input field when the modal becomes visible.
  useEffect(() => {
    if (isVisible && prompts && prompts.length > 0) {
      // Initialize inputValues state with empty strings for each prompt
      const initialValues = prompts.reduce((acc, prompt) => {
        acc[prompt.variable_name] = ''; // Start with empty inputs
        return acc;
      }, {});
      setInputValues(initialValues);

      // Focus the first input element shortly after the modal appears
      // Use setTimeout to ensure the element is rendered and visible
      const timer = setTimeout(() => {
        firstInputRef.current?.focus();
      }, 100); // Small delay

      return () => clearTimeout(timer); // Cleanup timer on unmount or visibility change

    } else if (!isVisible) {
      // Clear inputs when modal is hidden
      setInputValues({});
    }
  }, [isVisible, prompts]); // Rerun effect if visibility or prompts change

  // Handler for input field changes
  const handleInputChange = (variableName, value) => {
    setInputValues(prev => ({
      ...prev,
      [variableName]: value
    }));
  };

  // Handler for form submission
  const handleSubmit = (event) => {
    event.preventDefault(); // Prevent default form submission behavior
    // Check if all required inputs are filled (optional, but good practice)
    const allFilled = prompts.every(p => inputValues[p.variable_name]?.trim() !== '');
    if (!allFilled) {
      alert('Please fill in all required inputs.');
      return;
    }
    onSubmit(inputValues); // Pass the collected inputs to the parent component
  };

  // Prevent rendering if not visible or no prompts
  if (!isVisible || !prompts || prompts.length === 0) {
    return null;
  }

  // Render the modal
  return (
    <div className="input-modal-overlay">
      <div className="input-modal-content">
        <h2>Input Required</h2>
        <p>Your Conso program needs the following inputs:</p>
        <form onSubmit={handleSubmit}>
          {/* Map through prompts to create input fields */}
          {prompts.map((prompt, index) => (
            <div key={prompt.variable_name} className="input-group">
              <label htmlFor={prompt.variable_name}>
                {/* Display the prompt text provided by the Conso code */}
                {prompt.prompt_text} (Variable: <code>{prompt.variable_name}</code>, Line: {prompt.line})
              </label>
              <input
                type="text" // Use text input for all; server handles type conversion
                id={prompt.variable_name}
                name={prompt.variable_name}
                value={inputValues[prompt.variable_name] || ''} // Controlled input
                onChange={(e) => handleInputChange(prompt.variable_name, e.target.value)}
                required // Make fields required
                autoComplete="off" // Disable browser autocomplete
                // Assign ref to the first input element
                ref={index === 0 ? firstInputRef : null}
              />
            </div>
          ))}
          <div className="modal-actions">
            {/* Submit button */}
            <button type="submit" className="submit-button">Submit Inputs</button>
            {/* Close button */}
            <button type="button" onClick={onClose} className="close-button">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InputModal;
