// src/components/InputModal.js
import React, { useState, useEffect, useRef } from 'react';
import './InputModal.css'; // Make sure CSS is imported

/**
 * Parses the type string to get base type and isArray flag.
 * @param {string} typeString - The type string from the prompt (e.g., 'nt', 'chr[100]').
 * @returns {{baseType: string, isArray: boolean}}
 */
const parseVariableType = (typeString) => {
  if (!typeString || typeof typeString !== 'string') {
    return { baseType: 'unknown', isArray: false };
  }
  const match = typeString.match(/^([a-z]+)(\[.*\])?$/i); // Match type name and optional brackets
  if (match) {
    const baseType = match[1];
    const isArray = !!match[2]; // Check if the bracket part exists
    return { baseType, isArray };
  }
  // Fallback if format is unexpected
  return { baseType: typeString, isArray: false };
};


/**
 * Input Validation Function - Updated for Arrays
 * @param {string} value - The input value string.
 * @param {string} baseType - The base Conso type ('nt', 'dbl', 'bln', 'chr', 'strng').
 * @param {boolean} isArray - Flag indicating if the input is for an array.
 * @returns {string|null} - Error message string if invalid, null if valid.
 */
const validateInput = (value, baseType, isArray) => {

  if (isArray) {
    // --- Array Input Validation ---

    if (baseType === 'chr') {
      // Character array: No spaces allowed. Check the raw value.
      if (/\s/.test(value)) { // Check if value contains any whitespace
        return 'Invalid input: Character array input cannot contain spaces.';
      }
      // Optional: Add length check against declared size if available from backend
      // e.g., if (value.length > prompt.size) return `Input exceeds max length (${prompt.size})`;
      return null; // Valid if no spaces
    } else {
      // Other array types (nt, dbl, bln, strng): Space-separated elements
      const trimmedValue = value.trim(); // Trim leading/trailing whitespace before splitting

      // Allow empty input for arrays initially, but maybe require on submit?
      // Or handle empty array case specifically if needed.
      // If empty after trimming, it's valid for now, submit logic might check required.
      if (trimmedValue === '') {
          return null; // Allow empty input during typing
      }

      const elements = trimmedValue.split(/\s+/); // Split by one or more spaces

      for (let i = 0; i < elements.length; i++) {
        const element = elements[i];
        let error = null;

        // Validate each element based on the base type
        switch (baseType) {
          case 'nt':
            if (!/^-?\d+$/.test(element)) {
              error = `Element ${i + 1} ("${element}"): Expected an integer.`;
            }
            break;
          case 'dbl':
             // Use isFinite which handles integers, decimals, scientific notation
             // Also check it's not empty as isFinite('') is true.
            if (element === '' || !isFinite(element)) {
              error = `Element ${i + 1} ("${element}"): Expected a number.`;
            }
            break;
          case 'bln':
            const lowerElement = element.toLowerCase();
            if (lowerElement !== 'tr' && lowerElement !== 'fls') {
              error = `Element ${i + 1} ("${element}"): Expected "tr" or "fls".`;
            }
            break;
          case 'strng':
            // Individual string elements are generally valid unless specific rules apply
            // Optional: Add length checks per element if needed
            // e.g., if (element.length > 50) error = `Element ${i+1} is too long.`;
            break;
          default:
            // Unknown type for array element validation?
            console.warn(`Unknown array element validation type: ${baseType}`);
            break;
        }
        if (error) {
          return error; // Return the first error found
        }
      }
      return null; // All elements are valid
    }
  } else {
    // --- Single Value Validation (Existing Logic) ---
    const trimmedValue = value.trim();
    switch (baseType) {
      case 'nt':
        if (!/^-?\d+$/.test(trimmedValue)) {
          return 'Invalid input: Expected an integer (e.g., 123, -45).';
        }
        return null;
      case 'dbl':
        if (trimmedValue === '' || !isFinite(trimmedValue)) {
           return 'Invalid input: Expected a number (e.g., 123, -45.67).';
        }
        return null;
      case 'bln':
        const lowerValue = trimmedValue.toLowerCase();
        if (lowerValue !== 'tr' && lowerValue !== 'fls') {
          return 'Invalid input: Expected "tr" or "fls".';
        }
        return null;
      case 'chr':
         // Single character validation (no trim needed here as length is checked)
        if (value.length !== 1) {
            return 'Invalid input: Expected exactly one character.';
        }
        return null;
      case 'strng':
        // Single string validation
        // Optional: Add length checks if desired.
        // if (trimmedValue.length > 100) { return 'Input too long (max 100 chars).'; }
        return null;
      case 'unknown':
         console.warn("Cannot validate input: variable type is unknown.");
         return null; // Skip validation if type is unknown
      default:
        console.warn(`Unknown validation type: ${baseType}`);
        return null; // Skip validation for unrecognized types
    }
  }
};


/**
 * A modal dialog component to collect user input based on prompts,
 * now with real-time input validation for single values and arrays.
 *
 * Props:
 * - isVisible (boolean): Controls whether the modal is shown.
 * - prompts (array): Array of objects { variable_name, prompt_text, line, variable_type }.
 * **NOTE:** Assumes `variable_type` string includes array info (e.g., 'chr[100]').
 * - onSubmit (function): Callback function executed when the user submits valid inputs.
 * - onClose (function): Callback function executed when the user closes the modal.
 */
const InputModal = ({ isVisible, prompts, onSubmit, onClose }) => {
  const [inputValues, setInputValues] = useState({});
  // State for validation errors
  const [validationErrors, setValidationErrors] = useState({});
  // State to track overall form validity
  const [isFormValid, setIsFormValid] = useState(false);

  const firstInputRef = useRef(null);

  // Helper function to check overall form validity
  const checkFormValidity = (currentErrors, currentValues) => {
      if (!prompts || prompts.length === 0) return false;
      // Check if all prompts have a corresponding value entered (trimming matters here)
      const allInputsEntered = prompts.every(p => {
          const { isArray } = parseVariableType(p.variable_type);
          // For char arrays, don't trim because spaces are disallowed but empty might be valid?
          // For other arrays/single values, trim before checking emptiness.
          const valueToCheck = isArray && parseVariableType(p.variable_type).baseType === 'chr'
                               ? currentValues[p.variable_name]
                               : currentValues[p.variable_name]?.trim();
          return valueToCheck !== '';
      });
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
        const { baseType, isArray } = parseVariableType(p.variable_type);
        initialErrors[p.variable_name] = validateInput('', baseType, isArray);
      });
      setInputValues(initialValues);
      setValidationErrors(initialErrors);
      // Initial check for validity (likely false due to empty inputs)
      setIsFormValid(checkFormValidity(initialErrors, initialValues));

      // Focus first input on mount
      const timer = setTimeout(() => {
        firstInputRef.current?.focus();
      }, 100);
      return () => clearTimeout(timer);

    } else if (!isVisible) {
      // Reset state when modal closes
      setInputValues({});
      setValidationErrors({});
      setIsFormValid(false);
    }
  }, [isVisible, prompts]); // Rerun effect if prompts change while modal is open

  // Handler for input field changes with validation
  const handleInputChange = (variableName, value, variableTypeString) => { // Removed isArray param
    // Update the input value state
    const newInputValues = { ...inputValues, [variableName]: value };
    setInputValues(newInputValues);

    // --- CHANGE: Determine isArray and baseType from variableTypeString ---
    const { baseType, isArray } = parseVariableType(variableTypeString);

    // Validate the changed input, passing determined baseType and isArray flag
    const errorMessage = validateInput(value, baseType, isArray); // Pass parsed info

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
      const firstErrorKey = Object.keys(validationErrors).find(key => validationErrors[key]);
      if (firstErrorKey) {
          const errorInput = document.getElementById(firstErrorKey);
          errorInput?.focus();
      }
      alert("Please fix the errors or fill all required inputs before submitting.");
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
          {prompts.map((prompt, index) => {
            // --- CHANGE: Parse type string for display ---
            const { baseType, isArray } = parseVariableType(prompt.variable_type);
            const displayType = isArray ? `${baseType}[]` : baseType;

            return (
              <div key={prompt.variable_name} className="input-group">
                <label htmlFor={prompt.variable_name}>
                  {prompt.prompt_text}
                  {/* Update label to show parsed type */}
                  (Variable: <code>{prompt.variable_name}</code>, Type: <code>{displayType}</code>, Line: {prompt.line})
                </label>
                <input
                  type="text" // Keep as text, validation handles format
                  id={prompt.variable_name}
                  name={prompt.variable_name}
                  value={inputValues[prompt.variable_name] || ''}
                  onChange={(e) => handleInputChange(
                      prompt.variable_name,
                      e.target.value,
                      prompt.variable_type // Pass the original type string
                  )}
                  required // Keep required for basic presence check by browser (optional)
                  autoComplete="off"
                  ref={index === 0 ? firstInputRef : null}
                  // Add aria-invalid and class based on error
                  aria-invalid={!!validationErrors[prompt.variable_name]}
                  className={validationErrors[prompt.variable_name] ? 'input-error' : ''}
                />
                {/* Display validation error message */}
                {validationErrors[prompt.variable_name] && (
                  <div className="error-message">
                    {validationErrors[prompt.variable_name]}
                  </div>
                )}
              </div>
            );
          })}
          <div className="modal-actions">
            <button
              type="submit"
              className="submit-button"
              // Disable button if form is invalid
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