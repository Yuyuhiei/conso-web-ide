// src/components/InputModal.js
import React, { useState, useEffect, useRef } from 'react';
import './InputModal.css'; // Make sure CSS is imported

/**
 * Input Validation Function
 * @param {string} value - The input value string.
 * @param {string} type - The expected Conso type ('nt', 'dbl', 'bln', 'chr', 'strng').
 * @returns {string|null} - Error message string if invalid, null if valid.
 */
const validateInput = (value, type) => {
  const trimmedValue = value.trim();

  switch (type) {
    case 'nt':
      // Integer: Must be only digits, optionally preceded by '-'
      if (!/^-?\d+$/.test(trimmedValue)) {
        return 'Invalid input: Expected an integer (e.g., 123, -45).';
      }
      // Optional: Add range checks if needed
      return null; // Valid

    case 'dbl':
      // Double: Use isFinite which handles integers, decimals, scientific notation
      // Also check it's not empty after trimming, as isFinite('') is true.
      if (trimmedValue === '' || !isFinite(trimmedValue)) {
         return 'Invalid input: Expected a number (e.g., 123, -45.67).';
      }
       // Optional: Check for specific formats if needed (e.g., no scientific notation)
      // if (!/^-?\d+(\.\d*)?$/.test(trimmedValue) && !/^-?\.\d+$/.test(trimmedValue)) {
      //    return 'Invalid format: Use digits and at most one decimal point.';
      // }
      return null; // Valid

    case 'bln':
      // Boolean: Must be 'tr' or 'fls' (case-insensitive)
      const lowerValue = trimmedValue.toLowerCase();
      if (lowerValue !== 'tr' && lowerValue !== 'fls') {
        return 'Invalid input: Expected "tr" or "fls".';
      }
      return null; // Valid

    case 'chr':
      // Character: Must be exactly one character
      // Note: We trim first, so whitespace chars are invalid unless intended.
      // If whitespace chars should be allowed, use value.length instead of trimmedValue.length
      if (value.length !== 1) {
          return 'Invalid input: Expected exactly one character.';
      }
      // You could add checks for specific character ranges if needed
      return null; // Valid

    case 'strng':
      // String: Any input is generally valid from a type perspective.
      // Optional: Add length checks if desired.
      // if (trimmedValue.length > 100) { return 'Input too long (max 100 chars).'; }
      return null; // Valid

    case 'unknown':
       // Handle cases where type lookup failed on backend
       console.warn("Cannot validate input: variable type is unknown.");
       return null; // Skip validation if type is unknown

    default:
      // Should not happen if backend sends correct types
      console.warn(`Unknown validation type: ${type}`);
      return null; // Skip validation for unrecognized types
  }
};


/**
 * A modal dialog component to collect user input based on prompts,
 * now with real-time input validation.
 *
 * Props:
 * - isVisible (boolean): Controls whether the modal is shown.
 * - prompts (array): Array of objects { variable_name, prompt_text, line, variable_type }.
 * - onSubmit (function): Callback function executed when the user submits valid inputs.
 * - onClose (function): Callback function executed when the user closes the modal.
 */
const InputModal = ({ isVisible, prompts, onSubmit, onClose }) => {
  const [inputValues, setInputValues] = useState({});
  // --- NEW: State for validation errors ---
  const [validationErrors, setValidationErrors] = useState({});
  // --- NEW: State to track overall form validity ---
  const [isFormValid, setIsFormValid] = useState(false);

  const firstInputRef = useRef(null);

  // Helper function to check overall form validity
  const checkFormValidity = (currentErrors, currentValues) => {
      if (!prompts || prompts.length === 0) return false;
      // Check if all prompts have a corresponding value entered
      const allInputsEntered = prompts.every(p => currentValues[p.variable_name]?.trim() !== '');
      // Check if there are any error messages present
      const hasErrors = Object.values(currentErrors).some(error => error !== null);
      return allInputsEntered && !hasErrors;
  };

  // Effect to reset state when modal opens/prompts change
  useEffect(() => {
    if (isVisible && prompts && prompts.length > 0) {
      const initialValues = {};
      const initialErrors = {};
      prompts.forEach(p => {
        initialValues[p.variable_name] = ''; // Start empty
        initialErrors[p.variable_name] = null; // Start with no errors
      });
      setInputValues(initialValues);
      setValidationErrors(initialErrors);
      setIsFormValid(false); // Form is initially invalid as inputs are empty

      const timer = setTimeout(() => {
        firstInputRef.current?.focus();
      }, 100);
      return () => clearTimeout(timer);

    } else if (!isVisible) {
      setInputValues({});
      setValidationErrors({});
      setIsFormValid(false);
    }
  }, [isVisible, prompts]);

  // Handler for input field changes with validation
  const handleInputChange = (variableName, value, variableType) => {
    // Update the input value state
    const newInputValues = { ...inputValues, [variableName]: value };
    setInputValues(newInputValues);

    // Validate the changed input
    const errorMessage = validateInput(value, variableType);

    // Update the validation errors state
    const newErrors = { ...validationErrors, [variableName]: errorMessage };
    setValidationErrors(newErrors);

    // Update overall form validity
    setIsFormValid(checkFormValidity(newErrors, newInputValues));
  };

  // Handler for form submission
  const handleSubmit = (event) => {
    event.preventDefault();
    // Double-check validity before submitting
    if (!isFormValid) {
      // Optionally find the first error and alert or focus
      console.error("Submit blocked due to validation errors:", validationErrors);
      alert("Please fix the errors before submitting.");
      return;
    }
    onSubmit(inputValues); // Pass the collected (and now validated) inputs
  };

  if (!isVisible || !prompts || prompts.length === 0) {
    return null;
  }

  return (
    <div className="input-modal-overlay">
      <div className="input-modal-content">
        <h2>Input Required</h2>
        <p>Your Conso program needs the following inputs:</p>
        <form onSubmit={handleSubmit} noValidate> {/* Add noValidate to prevent default HTML5 validation */}
          {prompts.map((prompt, index) => (
            <div key={prompt.variable_name} className="input-group">
              <label htmlFor={prompt.variable_name}>
                {prompt.prompt_text}
                (Variable: <code>{prompt.variable_name}</code>, Type: <code>{prompt.variable_type || 'unknown'}</code>, Line: {prompt.line})
              </label>
              <input
                type="text" // Keep as text, validation handles format
                id={prompt.variable_name}
                name={prompt.variable_name}
                value={inputValues[prompt.variable_name] || ''}
                onChange={(e) => handleInputChange(prompt.variable_name, e.target.value, prompt.variable_type)}
                required // Keep required for basic presence check by browser (optional)
                autoComplete="off"
                ref={index === 0 ? firstInputRef : null}
                // --- NEW: Add aria-invalid and class based on error ---
                aria-invalid={!!validationErrors[prompt.variable_name]}
                className={validationErrors[prompt.variable_name] ? 'input-error' : ''}
              />
              {/* --- NEW: Display validation error message --- */}
              {validationErrors[prompt.variable_name] && (
                <div className="error-message">
                  {validationErrors[prompt.variable_name]}
                </div>
              )}
            </div>
          ))}
          <div className="modal-actions">
            <button
              type="submit"
              className="submit-button"
              // --- NEW: Disable button if form is invalid ---
              disabled={!isFormValid}
              title={isFormValid ? "Submit inputs" : "Please fix errors or fill all inputs"}
            >
              Submit Inputs
            </button>
            <button type="button" onClick={onClose} className="close-button">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InputModal;
