"""
Conso to C Transpiler (V6 - Token-Based Sequential - Global/Default Fix)
This module converts Conso code to C code using a token stream provided
by earlier compiler phases (Lexer, Parser, Semantic Analyzer).
Processes top-level blocks sequentially based on tokens.
Includes fixes for global declarations, array initializers, and default values.
Does NOT expect an EOF token in the input list.
"""
import sys
import re

# --- Custom Exception Class ---
class TranspilerError(Exception):
    """Custom exception for errors during the transpilation process."""
    def __init__(self, message, line_num=None):
        self.message = message
        self.line_num = line_num
        super().__init__(self.message)

    def __str__(self):
        if self.line_num is not None:
            return f"Transpiler Error at line {self.line_num}: {self.message}"
        else:
            return f"Transpiler Error: {self.message}"

# --- Transpiler Class ---
class ConsoTranspilerTokenBased:
    # --- MODIFIED __init__ ---
    # Add user_inputs to __init__
    def __init__(self, token_list, symbol_table=None, user_inputs=None): # Added user_inputs
        """
        Initializes the transpiler.

        Args:
            token_list: List of tokens from the lexer (EOF token should be removed).
            symbol_table: The symbol table (or relevant scope) for type lookups.
            user_inputs: A dictionary mapping variable names to user-provided input strings.
        """
        self.tokens = token_list
        self.symbol_table = symbol_table
        # Store user inputs, defaulting to an empty dict if None
        self.user_inputs = user_inputs if user_inputs is not None else {}
        self.current_pos = 0
        self.output_parts = []
        self.current_indent_level = 0

        # Mappings (Keep existing mappings)
        self.type_mapping = {
            "nt": "int", "dbl": "double", "strng": "char*",
            "bln": "int", "chr": "char", "vd": "void",
            "dfstrct": "struct"
        }
        self.keyword_mapping = {
            "f": "if", "ls": "else", "lsf": "else if", "whl": "while",
            "fr": "for", "d": "do", "swtch": "switch", "cs": "case",
            "dflt": "default", "brk": "break", "cntn": "continue"
        }
        self.bool_mapping = {"tr": "1", "fls": "0"}
        self.default_values = {
            "nt": "0",
            "dbl": "0.00",
            "strng": "NULL",
            "bln": "0",
            "chr": "'\\0'"
        }

    # --- Token Helpers ---
    def _get_token_info(self, token):
        """Safely extracts type, value, line from token tuple or object."""
        token_type, token_value, line = None, None, '?'
        if isinstance(token, tuple):
            token_type = token[0] if len(token) > 0 else None
            token_value = token[1] if len(token) > 1 else None
            line = token[2] if len(token) > 2 else '?'
        elif hasattr(token, 'type'):
            token_type = token.type
            token_value = getattr(token, 'value', None)
            line = getattr(token, 'line', '?')
        return token_type, token_value, line

    def _peek(self, offset=0):
        """Look at the token type at current position + offset."""
        peek_pos = self.current_pos + offset
        if 0 <= peek_pos < len(self.tokens):
            token = self.tokens[peek_pos]
            token_type, _, _ = self._get_token_info(token)
            return token_type
        return None

    def _consume(self, expected_type=None, expected_value=None):
        """Consume current token, check expectations, return (type, value, full_token)."""
        if self.current_pos >= len(self.tokens):
             raise TranspilerError("Unexpected end of token stream")
        token = self.tokens[self.current_pos]
        token_type, token_value, line = self._get_token_info(token)
        if expected_type and token_type != expected_type:
            raise TranspilerError(f"Expected token type '{expected_type}' but got '{token_type}'", line)
        if expected_value and token_value != expected_value:
            raise TranspilerError(f"Expected token value '{expected_value}' but got '{token_value}'", line)
        self.current_pos += 1
        return token_type, token_value, token

    def _skip_token(self, count=1):
        """Advance the current position."""
        self.current_pos = min(self.current_pos + count, len(self.tokens))

    # --- Core Transpilation Method ---
    def transpile(self):
        """Transpile the token stream sequentially, handling globals."""
        self.output_parts = [
            self._generate_headers(),
            self._generate_helper_functions()
        ]
        struct_defs_c = []; global_vars_c = []; func_defs_c = []; main_func_c = None

        while self.current_pos < len(self.tokens):
            token_type = self._peek()
            if token_type is None: break

            start_pos_before_statement = self.current_pos
            processed_something = False

            try:
                if token_type == 'strct':
                    struct_def = self._process_struct_definition_from_tokens()
                    if struct_def: struct_defs_c.append(struct_def)
                    processed_something = True
                elif token_type == 'fnctn':
                    func_def = self._process_function_definition_from_tokens()
                    if func_def: func_defs_c.append(func_def)
                    processed_something = True
                elif token_type == 'mn':
                    main_def = self._process_main_definition_from_tokens()
                    if main_def: main_func_c = main_def
                    processed_something = True
                elif token_type in self.type_mapping and token_type != 'dfstrct':
                    global_decl_c = self._process_statement_from_tokens(is_global=True)
                    if global_decl_c: global_vars_c.append(global_decl_c)
                    processed_something = True
                elif token_type == 'dfstrct':
                    global_inst_c = self._process_statement_from_tokens(is_global=True)
                    if global_inst_c: global_vars_c.append(global_inst_c)
                    processed_something = True
                else:
                    line = '?'; 
                    try: token = self.tokens[self.current_pos]; line = self._get_token_info(token)[2]
                    except IndexError: pass
                    print(f"Warning: Ignoring unexpected top-level token '{token_type}' near line {line}")
                    self._skip_token(); processed_something = True

            except TranspilerError as e:
                 print(f"Error during top-level processing: {e}", file=sys.stderr)
                 if self.current_pos == start_pos_before_statement: self._skip_token()
                 processed_something = True
            except Exception as e:
                 print(f"Unexpected error during top-level processing: {e}", file=sys.stderr)
                 if self.current_pos == start_pos_before_statement: self._skip_token()
                 processed_something = True

            if not processed_something and self.current_pos == start_pos_before_statement:
                 print(f"Failsafe: Advancing past unhandled token {self._peek()}")
                 self._skip_token()

        # --- Assemble the final C code in Order ---
        if struct_defs_c: self.output_parts.extend(["// Struct Definitions"] + struct_defs_c + [""])
        if global_vars_c: self.output_parts.extend(["// Global Declarations"] + global_vars_c + [""])
        if func_defs_c: self.output_parts.extend(["// Function Definitions"] + func_defs_c + [""])
        if main_func_c: self.output_parts.extend(["// Main Function", main_func_c, ""])
        else: self.output_parts.extend(["// ERROR: 'mn' function block not found or failed to process.", ""])

        return "\n".join(self.output_parts)


    # --- Token-Based Definition Processors ---
    def _process_struct_definition_from_tokens(self):
        """Processes struct definition from tokens."""
        start_pos = self.current_pos; struct_name = "<unknown>"
        try:
            self._consume('strct'); _, struct_name, _ = self._consume('id'); self._consume('{')
            definition_lines = [f"typedef struct {struct_name} {{"]; indent = "    "
            while self._peek() != '}':
                if self._peek() is None: raise TranspilerError(f"Unexpected end of stream inside struct {struct_name}")
                member_line = self._process_statement_from_tokens(is_struct_member=True)
                if member_line: definition_lines.append(indent + member_line)
            self._consume('}')
            if self._peek() == ';': self._consume(';')
            definition_lines.append(f"}} {struct_name};")
            return "\n".join(definition_lines)
        except TranspilerError as e: print(f"Error processing struct '{struct_name}': {e}"); self.current_pos = start_pos; 
        try: self._consume('strct') 
        except: pass; return None

    def _process_function_definition_from_tokens(self):
        """Processes function definition from tokens."""
        start_pos = self.current_pos; func_name = "<unknown>"
        try:
            self._consume('fnctn'); type_token = self._consume(); return_type_conso = type_token[0]
            c_return_type = self.type_mapping.get(return_type_conso, return_type_conso)
            _, func_name, _ = self._consume('id'); self._consume('(')
            params_c = self._process_parameters_from_tokens(); self._consume(')')
            self._consume('{'); definition_lines = [f"{c_return_type} {func_name}({params_c}) {{"]
            self.current_indent_level = 1
            
            # Process function body until we find the closing brace
            brace_level = 1  # We're already inside the function
            while brace_level > 0:
                if self._peek() is None: 
                    raise TranspilerError(f"Unexpected end of stream inside function '{func_name}'")
                
                # Track brace level to ensure we process the entire function body
                if self._peek() == '{':
                    self._consume('{')
                    brace_level += 1
                    statement_c = "{"
                elif self._peek() == '}':
                    self._consume('}')
                    brace_level -= 1
                    if brace_level == 0:  # End of function
                        break
                    statement_c = "}"
                else:
                    # Process other statements
                    statement_c = self._process_statement_from_tokens()
                
                if statement_c is not None:
                    indent_level = self.current_indent_level
                    if statement_c == '}': 
                        indent_level = max(0, indent_level - 1) # Adjust indent before adding '}'
                    definition_lines.append(self._indent(indent_level) + statement_c)
                    if statement_c.endswith('{'): 
                        self.current_indent_level += 1
                    if statement_c == '}': 
                        self.current_indent_level = max(0, self.current_indent_level - 1)
            
            # Add closing brace for function
            self.current_indent_level = 0
            definition_lines.append("}")
            return "\n".join(definition_lines)
        
        except TranspilerError as e: 
            print(f"Error processing function '{func_name}': {e}")
            self.current_pos = start_pos
            try: self._consume('fnctn') 
            except: pass
            return None

    def _process_main_definition_from_tokens(self):
        """Processes main function definition from tokens."""
        start_pos = self.current_pos
        try:
            self._consume('mn'); self._consume('('); self._consume(')'); self._consume('{')
            definition_lines = ["int main(int argc, char *argv[]) {"]
            self.current_indent_level = 1
            while self._peek() != 'end':
                if self._peek() is None: raise TranspilerError("Unexpected end of stream inside main definition")
                statement_c = self._process_statement_from_tokens()
                if statement_c is not None:
                    indent_level = self.current_indent_level
                    if statement_c == '}': indent_level = max(0, indent_level - 1)
                    definition_lines.append(self._indent(indent_level) + statement_c)
                    if statement_c.endswith('{'): self.current_indent_level += 1
                    if statement_c == '}': self.current_indent_level = max(0, self.current_indent_level -1)
            self._consume('end'); self._consume(';')
            self.current_indent_level = 0
            definition_lines.append(self._indent(1) + "return 0; // Corresponds to Conso 'end;'")
            definition_lines.append("}")
            return "\n".join(definition_lines)
        except TranspilerError as e: print(f"Error processing main function: {e}"); self.current_pos = start_pos; 
        try: self._consume('mn') 
        except: pass; return None

    def _process_parameters_from_tokens(self):
        """Processes parameters from token stream until ')' is found."""
        params = []
        if self._peek() == ')': return "void"
        while self._peek() != ')':
            if self._peek() is None: raise TranspilerError("Unexpected end of stream in parameter list")
            type_token = self._consume()
            param_type_conso = type_token[0]
            if param_type_conso not in self.type_mapping:
                 if param_type_conso == 'id': c_type = type_token[1]
                 else: raise TranspilerError(f"Expected type token in parameter list, got '{param_type_conso}'")
            else: c_type = self.type_mapping.get(param_type_conso, param_type_conso)
            _, param_name, _ = self._consume('id')
            params.append(f"{c_type} {param_name}")
            if self._peek() == ',': self._consume(',')
            elif self._peek() == ')': break
            else: raise TranspilerError(f"Unexpected token '{self._peek()}' in parameter list")
        return ", ".join(params) if params else "void"

    # --- Statement Processing (Token-Based Dispatcher) ---
    def _process_statement_from_tokens(self, is_struct_member=False, is_global=False):
        """Processes a single statement from the current token position."""
        token_type = self._peek()
        if token_type is None: return ""

        start_pos = self.current_pos; line = '?'
        try: line = self._get_token_info(self.tokens[start_pos])[2]
        except: pass # Ignore errors getting line number for error reporting itself

        try:
            # --- Handle struct members first ---
            if is_struct_member:
                # Struct members cannot be const and must be standard types
                if token_type in self.type_mapping and token_type != 'dfstrct':
                     return self._process_declaration_from_tokens(assign_default=False, is_const=False) # Struct members are never const
                else:
                     # Skip unexpected tokens within struct def
                     print(f"Warning: Skipping non-declaration token '{token_type}' inside struct near line {line}");
                     self._consume();
                     return "" # Return empty string, effectively skipping

            # --- Processing for global, function, or main scope ---

            # Handle block delimiters first
            if token_type == '{': self._consume(); return "{"
            if token_type == '}': self._consume(); return "}"

            # --- Check for Constant Declaration ---
            is_const_decl = False
            if token_type == 'cnst':
                # Peek ahead to see if a valid type follows 'cnst'
                next_type_peek = self._peek(1)
                if next_type_peek in self.type_mapping and next_type_peek != 'dfstrct':
                    # It's a constant declaration, consume 'cnst'
                    self._consume('cnst')
                    is_const_decl = True
                    token_type = self._peek() # Update token_type to the actual data type (nt, dbl, etc.)
                else:
                    # 'cnst' not followed by a valid type - treat as error or unexpected token
                    # For simplicity, let it fall through to be handled as an 'other' statement or error later
                    pass # Or raise TranspilerError(f"Expected type after 'cnst', got '{next_type_peek}'", line)

            # --- Check for Regular or Constant Declaration ---
            # Now token_type is either the original peeked type or the type after 'cnst'
            if token_type in self.type_mapping and token_type != 'dfstrct':
                # Pass the is_const flag determined above
                # Global consts are assigned defaults if not initialized (handled inside)
                # Local consts require initialization (handled by semantic analysis)
                return self._process_declaration_from_tokens(assign_default=True, is_const=is_const_decl)

            # --- Check for Struct Instance Declaration ---
            elif token_type == 'dfstrct':
                # Struct instances cannot be const with 'cnst' keyword in this design
                return self._process_dfstrct_from_tokens()

            # --- Statements only valid inside functions/main ---
            if is_global:
                 # If we reach here in global scope with an unhandled token, it's an error
                 print(f"Error: Statement type '{token_type}' not allowed at global scope near line {line}")
                 # Skip until semicolon to attempt recovery
                 while self._peek() not in [';', None]: self._skip_token()
                 if self._peek() == ';': self._skip_token()
                 return f"// ERROR: Statement type '{token_type}' not allowed at global scope"

            # --- Function/Main Scope Statements ---
            # These should only be processed if not is_global
            if token_type == 'prnt': return self._process_print_from_tokens()
            elif token_type == 'id' and self._peek(1) == '=' and self._peek(2) == 'npt': return self._process_input_from_tokens()
            elif token_type == 'rtrn': return self._process_return_from_tokens()
            elif token_type == 'f': return self._process_if_from_tokens()
            elif token_type == 'lsf': return self._process_else_if_from_tokens()
            elif token_type == 'ls': return self._process_else_from_tokens()
            elif token_type == 'whl': return self._process_while_from_tokens()
            elif token_type == 'fr': return self._process_for_from_tokens()
            elif token_type == 'd': return self._process_do_from_tokens()
            elif token_type == 'swtch': return self._process_switch_from_tokens()
            elif token_type == 'cs': return self._process_case_from_tokens()
            elif token_type == 'dflt': return self._process_default_from_tokens()
            elif token_type == 'brk': self._consume('brk'); self._consume(';'); return "break;"
            elif token_type == 'cntn': self._consume('cntn'); self._consume(';'); return "continue;"
            else:
                # Handle assignments, function calls, etc.
                return self._process_other_statement_from_tokens()

        except TranspilerError as e:
             print(f"Error processing statement near line {e.line_num if e.line_num else line}: {e.message}")
             self.current_pos = start_pos # Try to reset position
             # Skip until semicolon or brace to attempt recovery
             while self._peek() not in [';', '}', None]: self._skip_token()
             if self._peek() == ';': self._skip_token()
             return f"// ERROR: {e.message}"
        except Exception as e:
             # Safely get line number for unexpected errors
             err_line = '?'
             try: err_line = self._get_token_info(self.tokens[start_pos])[2]
             except: pass
             print(f"Unexpected error processing statement near line {err_line}: {e}")
             # import traceback; traceback.print_exc() # Uncomment for debug
             if self.current_pos == start_pos: self._skip_token() # Advance at least one token
             return f"// UNEXPECTED ERROR processing statement: {e}"


    # --- Token-Based Specific Statement Processors ---
    def _process_declaration_from_tokens(self, assign_default=True, is_const=False): # Added is_const parameter
        """
        Processes declaration statement from tokens. Handles const.
        Handles array initializers. Assigns default values ONLY to non-array variables
        if assign_default is True and no explicit initializer is provided.
        Arrays are NOT initialized by default. Const requires initializer (semantic check).
        """
        # Consume the actual type token (e.g., nt, dbl) which follows 'cnst' if present
        type_token = self._consume()
        conso_type = type_token[0]

        # Map to base C type
        base_c_type = self.type_mapping.get(conso_type, conso_type)

        # Prepend "const " if this is a constant declaration
        c_type = f"const {base_c_type}" if is_const else base_c_type

        processed_decls = []

        while True: # Loop for comma-separated parts (e.g., nt x, y=1;)
            _, var_name, token_full = self._consume('id')
            array_suffix = ""
            initializer_tokens = None
            is_array = False
            line_num = self._get_token_info(token_full)[2]

            # Parse array dimensions
            dimensions = []
            if self._peek() == '[':
                is_array = True
                while self._peek() == '[':
                    self._consume('[')
                    size_tokens = []
                    while self._peek() != ']':
                        if self._peek() is None: raise TranspilerError("Unterminated array size", line_num)
                        size_tok_type, size_tok_val, _ = self._consume()
                        if size_tok_type == 'blnlit': size_tokens.append(self.bool_mapping.get(size_tok_val, '0'))
                        else: size_tokens.append(str(size_tok_val))
                    self._consume(']')
                    dimension_expr = "".join(size_tokens)
                    dimensions.append(dimension_expr)
                    array_suffix += f"[{dimension_expr}]"

            # Get default value based on type (only used for non-arrays, non-const without initializer)
            default_val = self.default_values.get(conso_type, "0")

            # Handle explicit initializer
            if self._peek() == '=':
                self._consume('=')
                initializer_tokens = []
                brace_level = 0; paren_level = 0
                while True:
                    next_token_type = self._peek()
                    if next_token_type is None: raise TranspilerError("Unterminated initializer", line_num)
                    if (next_token_type == ',' or next_token_type == ';') and brace_level == 0 and paren_level == 0: break
                    tok_type, tok_val, token_full = self._consume()
                    initializer_tokens.append((tok_type, tok_val))
                    if tok_type == '{': brace_level += 1
                    elif tok_type == '}': brace_level -= 1
                    elif tok_type == '(': paren_level += 1
                    elif tok_type == ')': paren_level -= 1
                    if brace_level < 0 or paren_level < 0: raise TranspilerError("Mismatched braces/parentheses in initializer", line_num)

                init_str = self._tokens_to_c_expression(initializer_tokens)
                # Use the potentially 'const' modified c_type here
                c_decl_part = f"{c_type} {var_name}{array_suffix} = {init_str}"

            else:
                # No explicit initializer provided
                # Semantic analysis should ensure 'const' variables ARE initialized.
                # If we reach here for a const variable, it's technically an error,
                # but we proceed assuming semantics handled it. We just won't assign default.
                if is_const:
                     # Const variables must be initialized. If no '=' found, generate declaration without value.
                     # Rely on C compiler to catch the missing initializer error.
                     c_decl_part = f"{c_type} {var_name}{array_suffix}"
                elif is_array:
                    # Regular arrays are NOT initialized by default.
                    c_decl_part = f"{c_type} {var_name}{array_suffix}"
                else:
                    # Regular (non-array, non-const) variable without initializer
                    if assign_default:
                        # Assign default value ONLY if assign_default is True
                        c_decl_part = f"{c_type} {var_name} = {default_val}"
                    else:
                        # Otherwise, just declare the variable
                        c_decl_part = f"{c_type} {var_name}"

            processed_decls.append(c_decl_part)

            # Check for end of declaration list (semicolon) or next declaration (comma)
            if self._peek() == ';':
                self._consume(';')
                break
            elif self._peek() == ',':
                self._consume(',')
                # Continue loop for the next variable in the list
            else:
                # Assume end of statement if unexpected token
                break

        # Join declarations if multiple were on one line (e.g., cnst nt x=1, y=2;)
        # Need careful joining if they were split by C compiler needs (like separate statements)
        # For now, join with "; " which might require C compiler fixups if types differ, but okay for same type.
        # A better approach might return a list of declarations.
        # Let's assume declarations on one line are typically the same base type.
        return "; ".join(processed_decls) + ";"
    
    def _count_array_elements(self, initializer_tokens):
        """Count the number of elements in a 1D array initializer."""
        if not initializer_tokens or initializer_tokens[0][0] != '{':
            return 0
        
        elements = 0
        brace_level = 0
        in_element = False
        
        for token_type, _ in initializer_tokens:
            if token_type == '{':
                brace_level += 1
                if brace_level == 1:
                    # Start of outermost array
                    continue
            elif token_type == '}':
                brace_level -= 1
                if brace_level == 0 and in_element:
                    # End of element
                    elements += 1
                    in_element = False
            elif brace_level == 1:
                if token_type == ',':
                    if in_element:
                        elements += 1
                    in_element = False
                elif token_type in ['ntlit', 'dbllit', 'blnlit', 'chrlit', 'strnglit', 'id', 'tr', 'fls']:
                    if not in_element:
                        in_element = True
        
        return elements


    # (Other _process_*_from_tokens methods remain largely the same as V6)
    def _process_dfstrct_from_tokens(self):
        self._consume('dfstrct'); _, struct_type, _ = self._consume('id'); var_names = []
        while self._peek() != ';':
            if self._peek() == 'id': var_names.append(self._consume('id')[1])
            elif self._peek() == ',': self._consume(',')
            else: raise TranspilerError(f"Unexpected token '{self._peek()}' in dfstrct")
        self._consume(';'); c_declarations = [f"{struct_type} {var_name}" for var_name in var_names]
        return "; ".join(c_declarations) + ";"

    def _process_print_from_tokens(self):
        """
        Processes a print statement (prnt(...)) from tokens, generating
        a C printf call with appropriate format specifiers based on argument types,
        including handling for array elements, literals, variables, struct members,
        function calls, and expressions (including arithmetic results).
        Requires access to the symbol_table to determine variable/member/return types.
        """
        self._consume('prnt')
        self._consume('(')
        arg_groups_tokens = [] # List to hold lists of tokens for each argument
        current_arg_tokens = [] # Temp list for tokens of the current argument
        paren_level = 0 # To handle nested parentheses within arguments

        # Handle empty print() case first
        if self._peek() == ')':
            self._consume(')')
            self._consume(';')
            # Return printf with an empty string and flush stdout
            return 'printf(""); fflush(stdout);'

        # Collect tokens for each argument, splitting by top-level commas
        while not (self._peek() == ')' and paren_level == 0):
            if self._peek() is None:
                # Get line number for error reporting if possible
                line = '?'
                if current_arg_tokens:
                    try: line = self._get_token_info(current_arg_tokens[-1])[2]
                    except: pass
                elif self.current_pos > 0:
                     try: line = self._get_token_info(self.tokens[self.current_pos-1])[2]
                     except: pass
                raise TranspilerError("Unexpected end of stream in print statement", line)

            # Consume the next token
            tok_type, tok_val, token_full = self._consume()

            # Track parenthesis level to correctly identify argument boundaries
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1

            # If we encounter a comma at the top level (paren_level == 0),
            # it signifies the end of the current argument.
            if tok_type == ',' and paren_level == 0:
                if current_arg_tokens: # Add the completed argument tokens to the main list
                    arg_groups_tokens.append(current_arg_tokens)
                current_arg_tokens = [] # Reset for the next argument
            else:
                # Otherwise, add the token to the current argument being built
                current_arg_tokens.append(token_full)

        # Add the last argument's tokens after the loop finishes
        if current_arg_tokens:
            arg_groups_tokens.append(current_arg_tokens)

        # Consume the closing parenthesis and semicolon of the prnt statement
        self._consume(')')
        self._consume(';')

        format_parts = [] # List to store the C format specifiers (e.g., "%d", "%.2f")
        c_args = []       # List to store the C expressions for each argument

        # Process each argument group to determine format specifier and C code
        for arg_tokens in arg_groups_tokens:
            if not arg_tokens: continue # Skip if an argument group is empty for some reason

            # Convert the argument's tokens into a C expression string
            # We need token pairs (type, value) for _tokens_to_c_expression
            token_pairs = [(self._get_token_info(t)[0], self._get_token_info(t)[1]) for t in arg_tokens]
            arg_c_expr = self._tokens_to_c_expression(token_pairs)

            fmt = None # Initialize format specifier for this argument

            # --- Logic to determine the format specifier ('fmt') ---

            # 1. Check for Array Element Access (e.g., myArr[index], myArr[i][j])
            #    Pattern: Starts with 'id', followed by '['
            if len(arg_tokens) >= 3 and \
               self._get_token_info(arg_tokens[0])[0] == 'id' and \
               self._get_token_info(arg_tokens[1])[0] == '[':
                base_var_name = self._get_token_info(arg_tokens[0])[1]
                # Look up the base array variable in the symbol table
                if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                    symbol_entry = self.symbol_table.lookup(base_var_name)
                    # Check if symbol exists and has a data type
                    if symbol_entry and hasattr(symbol_entry, 'data_type'):
                        var_type = symbol_entry.data_type # Get the type (nt, dbl, etc.)
                        # Assign format specifier based on the array's base type
                        if var_type == 'strng': fmt = "%s"
                        elif var_type == 'dbl': fmt = "%.2f" # Use .2f for doubles
                        elif var_type == 'chr': fmt = "%c"
                        elif var_type == 'nt': fmt = "%d"
                        elif var_type == 'bln': fmt = "%d" # Booleans printed as integers (0 or 1)
                        # Add other Conso types here if needed

            # 2. If not an array access, check for simple literals or single variables
            elif len(arg_tokens) == 1:
                arg_type, arg_val = self._get_token_info(arg_tokens[0])[:2]

                if arg_type == 'strnglit': fmt = "%s"
                elif arg_type == 'chrlit': fmt = "%c"
                elif arg_type == 'dbllit' or arg_type == 'NEGDOUBLELIT': fmt = "%.2f"
                elif arg_type == 'ntlit' or arg_type == 'NEGINTLIT': fmt = "%d"
                # Handle boolean literals tr/fls mapped to 1/0 in C expression, print as int
                elif arg_type == 'blnlit': fmt = "%d"
                elif arg_type == 'id':
                    # It's a single variable identifier (not array access)
                    if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                        symbol_entry = self.symbol_table.lookup(arg_val)
                        if symbol_entry:
                            # Check if it's NOT an array before assigning format here
                            # (Array elements handled above)
                            if not getattr(symbol_entry, 'is_array', False):
                                var_type = getattr(symbol_entry, 'data_type', None)
                                if var_type == 'strng': fmt = "%s"
                                elif var_type == 'dbl': fmt = "%.2f"
                                elif var_type == 'chr': fmt = "%c"
                                elif var_type == 'nt': fmt = "%d"
                                elif var_type == 'bln': fmt = "%d"

            # 3. If not handled above, check for complex expressions like
            #    struct access, function calls, or arithmetic/logical operations.
            else:
                # Initialize flags for expression type detection
                is_struct_access = False
                is_function_call = False
                fmt = None # Reset fmt for this block

                # --- Check if the expression is primarily a comparison ---
                # Comparisons should always result in an integer (0 or 1)
                is_comparison = any(self._get_token_info(t)[0] in ['==', '!=', '<', '>', '<=', '>='] for t in arg_tokens)
                if is_comparison:
                    fmt = "%d" # Force format to integer for comparison results
                else:
                    # --- If not a comparison, check for Struct Member Access ---
                    # Iterate through tokens looking for the id . id pattern
                    for i in range(len(arg_tokens) - 2):
                        if self._get_token_info(arg_tokens[i])[0] == 'id' and \
                           self._get_token_info(arg_tokens[i+1])[0] == '.' and \
                           self._get_token_info(arg_tokens[i+2])[0] == 'id':
                            # ... (struct lookup logic as before) ...
                            struct_var_name = self._get_token_info(arg_tokens[i])[1]
                            member_name = self._get_token_info(arg_tokens[i+2])[1]
                            if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                                struct_var_symbol = self.symbol_table.lookup(struct_var_name)
                                if struct_var_symbol and hasattr(struct_var_symbol, 'data_type'):
                                    struct_type_name = struct_var_symbol.data_type
                                    struct_def_symbol = self.symbol_table.lookup(struct_type_name)
                                    if struct_def_symbol and hasattr(struct_def_symbol, 'members') and hasattr(struct_def_symbol.members, 'get'):
                                        member_symbol = struct_def_symbol.members.get(member_name)
                                        if member_symbol and hasattr(member_symbol, 'data_type'):
                                            member_type = member_symbol.data_type
                                            if member_type == 'strng': fmt = "%s"
                                            elif member_type == 'dbl': fmt = "%.2f"
                                            elif member_type == 'chr': fmt = "%c"
                                            elif member_type == 'nt': fmt = "%d"
                                            elif member_type == 'bln': fmt = "%d"
                                            is_struct_access = True
                                            break # Found struct member type

                    # --- Check for Function Call (if not struct access) ---
                    if not is_struct_access and len(arg_tokens) >= 2 and \
                       self._get_token_info(arg_tokens[0])[0] == 'id' and \
                       self._get_token_info(arg_tokens[1])[0] == '(':
                        # ... (function lookup logic as before) ...
                        func_name = self._get_token_info(arg_tokens[0])[1]
                        if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                            func_symbol = self.symbol_table.lookup(func_name)
                            if func_symbol and hasattr(func_symbol, 'data_type'):
                                return_type = func_symbol.data_type
                                if return_type == 'strng': fmt = "%s"
                                elif return_type == 'dbl': fmt = "%.2f"
                                elif return_type == 'chr': fmt = "%c"
                                elif return_type == 'nt': fmt = "%d"
                                elif return_type == 'bln': fmt = "%d"
                                elif return_type == 'vd':
                                    print(f"Warning: Attempting to print result of void function '{func_name}' near line {self._get_token_info(arg_tokens[0])[2]}. Output may be unpredictable.")
                                    fmt = None # Let it default
                                is_function_call = True

                    # --- Fallback checks if not comparison/struct/function ---
                    if fmt is None:
                        # Check for logical operators (results in int)
                        has_logical_op = any(self._get_token_info(t)[0] in ['&&', '||'] for t in arg_tokens)
                        if has_logical_op:
                            fmt = "%d"
                        else:
                            # --- MODIFIED PART ---
                            # Check the overall expression type using the helper.
                            # This helps catch arithmetic operations resulting in double.
                            # Need token pairs (type, value) for get_expression_type
                            arg_token_pairs = [(self._get_token_info(t)[0], self._get_token_info(t)[1]) for t in arg_tokens]
                            expression_result_type = self.get_expression_type(arg_token_pairs)

                            if expression_result_type == 'dbl':
                                fmt = "%.2f"
                            # Add elif for other potential result types if needed
                            # elif expression_result_type == 'strng':
                            #    fmt = "%s" # e.g., for string concatenation if supported
                            # --- END MODIFIED PART ---


            # 4. Default format specifier if none of the above matched
            if fmt is None:
                # If the type is still unknown after all checks, default to integer.
                # This might happen for complex arithmetic resulting in int, or errors.
                fmt = "%d"

            # Add the determined format specifier and the C expression to our lists
            format_parts.append(fmt)
            c_args.append(arg_c_expr)

        # Construct the final printf statement
        format_str = " ".join(format_parts) # Join format specifiers with spaces
        # Join C arguments with commas
        args_str = ", ".join(c_args)

        # Ensure there's always a format string, even if empty
        if not format_str and not args_str:
             # Handle case like prnt(); -> printf("");
             return 'printf(""); fflush(stdout);'
        elif not args_str:
             # Handle case like prnt("Literal"); -> printf("Literal");
             # Assumes single literal was handled correctly by section #2.
             return f'printf("{format_str}"); fflush(stdout);' # format_str should be %s etc.
        else:
             # Normal case with format specifiers and arguments
             return f'printf("{format_str}", {args_str}); fflush(stdout);'

    # Helper method to check if a variable is a string
    def _is_string_var(self, token):
        """Check if a token represents a string variable"""
        token_type, token_value = self._get_token_info(token)[:2]
        if token_type != 'id':
            return False
        
        if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
            symbol = self.symbol_table.lookup(token_value)
            return symbol and getattr(symbol, 'data_type', None) == 'strng'
        
        return False

    def _process_input_from_tokens(self):
        """
        Processes an input statement (var = npt("prompt");) by generating
        a C assignment using pre-collected user input.
        Relies on self.user_inputs dictionary and self.symbol_table.
        """
        start_pos = self.current_pos
        line_num = '?'
        var_name = '<unknown>' # Initialize var_name for error reporting

        try:
            # Consume 'id', '=', 'npt', '('
            _, var_name, token_full = self._consume('id')
            line_num = self._get_token_info(token_full)[2]
            self._consume('=')
            self._consume('npt')
            self._consume('(')

            # Consume the prompt string literal if present, but we don't use it here
            # The prompt was already extracted in the pre-scan phase in server.py
            if self._peek() == 'strnglit':
                self._consume('strnglit')

            # Consume ')' and ';'
            self._consume(')')
            self._consume(';')

            # --- Get the pre-collected input value ---
            if var_name not in self.user_inputs:
                # This case should ideally be prevented by the pre-scan logic
                # ensuring all required inputs are collected.
                raise TranspilerError(f"Missing input value for variable '{var_name}' during transpilation", line_num)

            # Get the raw input string provided by the user
            input_value_str = self.user_inputs[var_name]

            # --- Determine variable type from symbol table ---
            var_type = None
            is_array = False # Check if it's an array type if needed
            if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                # Assuming 'lookup' searches the current scope appropriately.
                # You might need to pass the specific function scope's symbol table
                # to the transpiler or ensure lookup handles scopes correctly.
                symbol = self.symbol_table.lookup(var_name)
                if symbol:
                    var_type = getattr(symbol, 'data_type', None)
                    is_array = getattr(symbol, 'is_array', False)
                else:
                     # It's possible the variable is declared globally, try looking up there if applicable
                     # This depends heavily on your symbol table structure.
                     # For simplicity, we raise an error if not found in the provided table.
                     raise TranspilerError(f"Variable '{var_name}' not found in symbol table for input", line_num)
            else:
                 # This should not happen if semantic analysis passed, but check anyway.
                 raise TranspilerError("Symbol table not available for input processing", line_num)

            if var_type is None:
                 # Symbol found, but no type information? Semantic analysis should catch this.
                 raise TranspilerError(f"Could not determine type for variable '{var_name}' during input processing", line_num)

            # --- Format the input string into a C literal based on type ---
            c_literal = ""
            try:
                if var_type == 'nt':
                    # Convert to int, then back to string for C code
                    c_literal = str(int(input_value_str))
                elif var_type == 'dbl':
                     # Convert to float, format, then back to string
                     # Use a standard float representation, C compiler handles precision.
                     c_literal = str(float(input_value_str))
                elif var_type == 'chr':
                    # Take the first character, escape special chars if needed
                    if len(input_value_str) >= 1:
                        char_val = input_value_str[0]
                        # Basic escaping for single quote, double quote, and backslash
                        if char_val == "'": char_val = "\\'"
                        elif char_val == '"': char_val = '\\"' # Escape double quotes too
                        elif char_val == "\\": char_val = "\\\\"
                        # Add more escapes if needed (e.g., \n, \t) - though unlikely from simple input
                        c_literal = f"'{char_val}'"
                    else:
                        c_literal = "'\\0'" # Default to null char if input is empty
                elif var_type == 'bln':
                    # Map common truthy/falsy strings to 1/0
                    lowered_input = input_value_str.lower().strip()
                    if lowered_input in ['true', 'tr', '1', 'yes', 'y']:
                        c_literal = "1"
                    else:
                        c_literal = "0" # Default to false for unrecognized input
                elif var_type == 'strng':
                    # Escape double quotes and backslashes within the string for C literal
                    escaped_str = input_value_str.replace('\\', '\\\\').replace('"', '\\"')
                    # Assigning a string literal to char* is generally okay in C for initialization
                    # or if the pointer points to read-only memory. If the C code intends
                    # to modify the string later, this approach might need refinement
                    # (e.g., allocating memory and using strcpy in C).
                    # Based on your initial C code using `strdup`, assuming `char*` is used.
                    c_literal = f'"{escaped_str}"'
                else:
                    # Handle other types or raise error if a variable of an unsupported type
                    # is somehow used with npt (semantic analysis should prevent this).
                    raise TranspilerError(f"Unsupported type '{var_type}' for 'npt' assignment", line_num)

            except ValueError:
                 # Handle cases where the input string cannot be converted to the target type
                 # (e.g., user enters "abc" for an 'nt')
                 raise TranspilerError(f"Invalid input format for variable '{var_name}' (expected {var_type}, got '{input_value_str}')", line_num)


            # --- Generate the C assignment statement ---
            # Check if the variable is an array. Direct assignment might not be appropriate for arrays.
            # This example assumes non-array assignment based on your initial code.
            # Handling array input would require more complex logic (e.g., transpiling to strcpy or loops).
            if is_array:
                 # For now, raise an error if trying to assign input directly to an array base name
                 # A future enhancement could potentially use strcpy if var_type is 'strng' and it's a char array.
                 raise TranspilerError(f"Direct input assignment to array '{var_name}' using 'npt' is not supported in this version.", line_num)

            # Return the C assignment statement
            return f"{var_name} = {c_literal};"

        except TranspilerError as e:
            # Re-raise or handle specific transpiler errors
            print(f"Error processing input statement for '{var_name}' near line {e.line_num if e.line_num else line_num}: {e.message}")
            # Attempt to recover by skipping to the next statement delimiter
            self.current_pos = start_pos # Reset position
            while self._peek() not in [';', '}', '{', None]: # Skip until potential statement end/start
                self._skip_token()
            if self._peek() == ';':
                self._skip_token() # Consume the semicolon
            # Return an error comment in the generated code
            return f"// TRANSPILER ERROR (Input): {e.message}"
        except Exception as e:
             # Catch unexpected errors during input processing
             err_line = line_num # Use line_num obtained earlier
             print(f"Unexpected error processing input for '{var_name}' near line {err_line}: {e}")
             import traceback
             traceback.print_exc() # Print stack trace for debugging
             # Attempt recovery
             if self.current_pos == start_pos: self._skip_token() # Ensure progress
             # Return an error comment
             return f"// UNEXPECTED TRANSPILER ERROR (Input): {e}"

    def _process_return_from_tokens(self):
        self._consume('rtrn')
        if self._peek() == ';': self._consume(';'); return "return;"
        expr_tokens = []
        while self._peek() != ';': expr_tokens.append(self._consume()[:2])
        self._consume(';'); value_c = self._tokens_to_c_expression(expr_tokens)
        return f"return {value_c};"

    def _process_if_from_tokens(self):
        self._consume('f'); self._consume('('); condition_tokens = []; paren_level = 1
        while paren_level > 0:
             tt, tv, _ = self._consume();
             if tt == '(': paren_level += 1;
             elif tt == ')': paren_level -= 1
             if paren_level > 0: condition_tokens.append((tt, tv))
        condition_c = self._tokens_to_c_expression(condition_tokens)
        return f"if ({condition_c})"

    def _process_else_if_from_tokens(self):
        self._consume('lsf'); self._consume('('); condition_tokens = []; paren_level = 1
        while paren_level > 0:
             tt, tv, _ = self._consume();
             if tt == '(': paren_level += 1; 
             elif tt == ')': paren_level -= 1
             if paren_level > 0: condition_tokens.append((tt, tv))
        condition_c = self._tokens_to_c_expression(condition_tokens)
        return f"else if ({condition_c})"

    def _process_else_from_tokens(self): self._consume('ls'); return "else"
    def _process_while_from_tokens(self):
        self._consume('whl'); self._consume('('); condition_tokens = []; paren_level = 1
        while paren_level > 0:
             tt, tv, _ = self._consume();
             if tt == '(': paren_level += 1; 
             elif tt == ')': paren_level -= 1
             if paren_level > 0: condition_tokens.append((tt, tv))
        condition_c = self._tokens_to_c_expression(condition_tokens)
        return f"while ({condition_c})"

    def _process_for_from_tokens(self):
        self._consume('fr'); self._consume('('); it = []; ct = []; ut = []; p = 1; pl = 1
        while pl > 0:
             tt, tv, _ = self._consume();
             if tt == '(': pl += 1; 
             elif tt == ')': pl -= 1
             if pl == 0: break
             if tt == ';' and pl == 1: p += 1
             else: t = (tt, tv); (it if p == 1 else ct if p == 2 else ut).append(t)
        ic = self._tokens_to_c_expression(it) if it else ""; cc = self._tokens_to_c_expression(ct) if ct else ""; uc = self._tokens_to_c_expression(ut) if ut else ""
        return f"for ({ic}; {cc}; {uc})"

    def _process_do_from_tokens(self): self._consume('d'); return "do"
    def _process_switch_from_tokens(self):
        self._consume('swtch'); self._consume('('); expr_tokens = []; paren_level = 1
        while paren_level > 0:
             tt, tv, _ = self._consume();
             if tt == '(': paren_level += 1; 
             elif tt == ')': paren_level -= 1
             if paren_level > 0: expr_tokens.append((tt, tv))
        expr_c = self._tokens_to_c_expression(expr_tokens)
        return f"switch ({expr_c})"

    def _process_case_from_tokens(self):
        self._consume('cs'); value_tokens = []
        while self._peek() != ':': value_tokens.append(self._consume()[:2])
        self._consume(':'); value_c = self._tokens_to_c_expression(value_tokens)
        return f"case {value_c}:"

    def _process_default_from_tokens(self): self._consume('dflt'); self._consume(':'); return "default:"

    def _process_other_statement_from_tokens(self):
        """Processes assignments, function calls etc. from tokens until semicolon."""
        stmt_tokens = []; paren_level = 0; bracket_level = 0
        while not (self._peek() == ';' and paren_level == 0 and bracket_level == 0):
            if self._peek() is None: raise TranspilerError("Unexpected end of stream in statement")
            tok_type, tok_val, _ = self._consume()
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            elif tok_type == '[': bracket_level += 1
            elif tok_type == ']': bracket_level -= 1
            stmt_tokens.append((tok_type, tok_val))
        self._consume(';')
        return self._tokens_to_c_expression(stmt_tokens) + ";"

        # --- Helper Methods for Expression Processing (with Debugging) ---

    def format_token(self, tok_type, tok_val):
        """Formats a single token into its C string representation."""
        if tok_type == 'blnlit': return self.bool_mapping.get(tok_val, '0')
        elif tok_type == 'strnglit': return f'"{tok_val}"'
        elif tok_type == 'chrlit': return f"'{tok_val}'"
        else: return str(tok_val)

    def get_expression_type(self, expr_tokens):
        """
        Determines the resulting C type ('nt', 'dbl', 'strng', 'bln', 'chr', or None)
        of an expression represented by tokens.
        Prioritizes operator type over initial operand type.
        Relies on symbol table lookup.
        """
        # print(f"[DEBUG get_expression_type] Input tokens: {expr_tokens}") # Uncomment for deep debug
        if not expr_tokens:
            # print("[DEBUG get_expression_type] Returning: None (empty tokens)") # Uncomment for deep debug
            return None

        result_type = None # Initialize result type

        # --- Operator-based type determination FIRST ---
        # Check for comparison or logical operators first, as they dictate the result type (boolean -> int)
        is_comparison_or_logical = any(
            t[0] in ['==', '!=', '<', '>', '<=', '>=', '&&', '||']
            for t in expr_tokens
        )
        if is_comparison_or_logical:
            result_type = 'bln' # Result is always boolean (represented as int 0 or 1)
        else:
            # Check for arithmetic operations -> result type depends on operands
            has_arithmetic_op = any(t[0] in ['+', '-', '*', '/'] for t in expr_tokens)
            if has_arithmetic_op:
                promotes_to_double = False
                # Iterate through tokens to check operand types
                i = 0
                while i < len(expr_tokens):
                    tok_type, tok_val = expr_tokens[i]

                    # Check for double literals OR division operator (which often results in double)
                    if tok_type in ['dbllit', 'NEGDOUBLELIT', '/']:
                        promotes_to_double = True
                        break # Found a double source, no need to check further

                    # Check if an identifier is involved
                    if tok_type == 'id':
                        # --- MODIFICATION START: Check for struct access pattern (id . id) ---
                        # Look ahead for '.' followed by 'id'
                        if i + 2 < len(expr_tokens) and expr_tokens[i+1][0] == '.' and expr_tokens[i+2][0] == 'id':
                            struct_var_name = tok_val
                            member_name = expr_tokens[i+2][1]
                            # print(f"[DEBUG get_expression_type] Checking struct member: {struct_var_name}.{member_name}") # DEBUG
                            if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                                struct_var_symbol = self.symbol_table.lookup(struct_var_name)
                                if struct_var_symbol and hasattr(struct_var_symbol, 'data_type'):
                                    struct_type_name = struct_var_symbol.data_type
                                    # Look up the struct definition itself to find member types
                                    struct_def_symbol = self.symbol_table.lookup(struct_type_name)
                                    if struct_def_symbol and hasattr(struct_def_symbol, 'members') and hasattr(struct_def_symbol.members, 'get'):
                                        member_symbol = struct_def_symbol.members.get(member_name)
                                        # Check if the MEMBER's type is double
                                        if member_symbol and getattr(member_symbol, 'data_type', None) == 'dbl':
                                            # print(f"[DEBUG get_expression_type] Struct member {member_name} is dbl.") # DEBUG
                                            promotes_to_double = True
                                            break # Found a double source
                            # Skip the '.' and member 'id' tokens in the next iteration
                            i += 2
                        # --- MODIFICATION END ---
                        else:
                            # Regular ID lookup (not part of struct access pattern)
                            # print(f"[DEBUG get_expression_type] Checking identifier: {tok_val}") # DEBUG
                            if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                                symbol = self.symbol_table.lookup(tok_val)
                                # Check if the IDENTIFIER's type is double
                                if symbol and getattr(symbol, 'data_type', None) == 'dbl':
                                    # print(f"[DEBUG get_expression_type] Identifier {tok_val} is dbl.") # DEBUG
                                    promotes_to_double = True
                                    break # Found a double source

                    i += 1 # Move to the next token

                # Assign result type based on whether promotion occurred
                result_type = 'dbl' if promotes_to_double else 'nt'

        # --- If no operators determined the type, check structure (single token, array access, etc.) ---
        if result_type is None:
             # Check simple cases first: single literal or variable
             if len(expr_tokens) == 1:
                 tok_type, tok_val = expr_tokens[0]
                 if tok_type == 'strnglit': result_type = 'strng'
                 elif tok_type == 'chrlit': result_type = 'chr'
                 elif tok_type in ['dbllit', 'NEGDOUBLELIT']: result_type = 'dbl'
                 elif tok_type in ['ntlit', 'NEGINTLIT']: result_type = 'nt'
                 elif tok_type == 'blnlit': result_type = 'bln'
                 elif tok_type == 'id':
                     if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                         symbol = self.symbol_table.lookup(tok_val)
                         result_type = getattr(symbol, 'data_type', None) if symbol else None
             # Check complex structures - Array Element Access (e.g., arr[index])
             elif len(expr_tokens) >= 3 and expr_tokens[0][0] == 'id' and expr_tokens[1][0] == '[' and expr_tokens[-1][0] == ']':
                 base_var_name = expr_tokens[0][1]
                 if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                     symbol = self.symbol_table.lookup(base_var_name)
                     # Type of an array element is the base type of the array
                     result_type = getattr(symbol, 'data_type', None) if symbol else None
             # Check complex structures - Struct Member Access (e.g., struct.member)
             elif len(expr_tokens) >= 3 and expr_tokens[-1][0] == 'id' and expr_tokens[-2][0] == '.':
                 # This heuristic assumes simple id.id access. More complex chains might need recursion.
                 if len(expr_tokens) == 3 and expr_tokens[0][0] == 'id': # Simple id.id
                     struct_var_name = expr_tokens[0][1]
                     member_name = expr_tokens[-1][1]
                     if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                         struct_var_symbol = self.symbol_table.lookup(struct_var_name)
                         if struct_var_symbol and hasattr(struct_var_symbol, 'data_type'):
                             struct_type_name = struct_var_symbol.data_type
                             struct_def_symbol = self.symbol_table.lookup(struct_type_name)
                             if struct_def_symbol and hasattr(struct_def_symbol, 'members') and hasattr(struct_def_symbol.members, 'get'):
                                 member_symbol = struct_def_symbol.members.get(member_name)
                                 if member_symbol: result_type = getattr(member_symbol, 'data_type', None)
             # Check complex structures - Function Call (e.g., func(args))
             elif len(expr_tokens) >= 3 and expr_tokens[0][0] == 'id' and expr_tokens[1][0] == '(' and expr_tokens[-1][0] == ')':
                 func_name = expr_tokens[0][1]
                 if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                     symbol = self.symbol_table.lookup(func_name)
                     # Type of a function call is its return type
                     result_type = getattr(symbol, 'data_type', None) if symbol else None

        # print(f"[DEBUG get_expression_type] Returning type: {result_type}") # Uncomment for deep debug
        return result_type

    def _format_token_sequence(self, tokens_to_format):
        """Helper to format a sequence of tokens into C code with spacing."""
        parts = []
        if not tokens_to_format: return ""
        for i, (tok_type, tok_val) in enumerate(tokens_to_format):
             needs_space = False
             if parts:
                 last_part = parts[-1]
                 if tok_type not in [')', ']', '.', ';', ',', '(', '[', '++', '--'] and \
                    not last_part.endswith(('(', '[', '.')) and \
                    tok_type != '.':
                      if not ((last_part.isalnum() or last_part.endswith((')', ']'))) and tok_type in ['(', '[']):
                           if not (tok_type in ['++', '--'] and last_part.isalnum()):
                                needs_space = True
             if needs_space: parts.append(" ")
             parts.append(self.format_token(tok_type, tok_val))
        return "".join(parts)

    def _process_comparison_segment(self, segment_tokens):
        """
        Processes a segment of tokens (typically between logical operators)
        to handle comparisons, especially string comparisons using strcmp.
        """
        if not segment_tokens: return ""
        comparison_index = -1
        paren_level = 0
        bracket_level = 0
        comparison_ops = ['==', '!=', '<', '>', '<=', '>=']
        for idx, (tok_type, _) in enumerate(segment_tokens):
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            elif tok_type == '[': bracket_level += 1
            elif tok_type == ']': bracket_level -= 1
            elif paren_level == 0 and bracket_level == 0 and tok_type in comparison_ops:
                comparison_index = idx
                break
        if comparison_index != -1:
            op_tok_type = segment_tokens[comparison_index][0]
            left_operand_tokens = segment_tokens[:comparison_index]
            right_operand_tokens = segment_tokens[comparison_index + 1:]
            left_type = self.get_expression_type(left_operand_tokens)
            right_type = self.get_expression_type(right_operand_tokens)
            if left_type == 'strng' and right_type == 'strng' and op_tok_type in ['==', '!=']:
                left_c = self._tokens_to_c_expression(left_operand_tokens)
                right_c = self._tokens_to_c_expression(right_operand_tokens)
                op_str = "==" if op_tok_type == '==' else "!="
                return f"(strcmp({left_c}, {right_c}) {op_str} 0)"
            else:
                left_c = self._tokens_to_c_expression(left_operand_tokens)
                right_c = self._tokens_to_c_expression(right_operand_tokens)
                if left_c and right_c: return f"{left_c} {op_tok_type} {right_c}"
                elif left_c: return f"{left_c} {op_tok_type}"
                elif right_c: return f"{op_tok_type} {right_c}"
                else: return f"{op_tok_type}"
        else:
            return self._format_token_sequence(segment_tokens)

    def _tokens_to_c_expression(self, tokens):
        """
        Converts a list of (type, value) tokens into a C expression string.
        Handles operator precedence by splitting first by logical operators (&&, ||),
        then processing segments for comparisons (==, != with strcmp for strings),
        and finally formatting the remaining tokens.
        """
        if not tokens: return ""
        segments = []; operators = []; current_start = 0
        paren_level = 0; bracket_level = 0
        for i, (tok_type, _) in enumerate(tokens):
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            elif tok_type == '[': bracket_level += 1
            elif tok_type == ']': bracket_level -= 1
            elif paren_level == 0 and bracket_level == 0 and tok_type in ['&&', '||']:
                segments.append(tokens[current_start:i])
                operators.append(tok_type)
                current_start = i + 1
        segments.append(tokens[current_start:])
        processed_segments = [self._process_comparison_segment(segment) for segment in segments]
        result_parts = [processed_segments[0]]
        for i, op in enumerate(operators):
            result_parts.append(f" {op} ")
            result_parts.append(processed_segments[i+1])
        result = "".join(result_parts)
        result = self._replace_bool_literals(result)
        return result

    def _replace_bool_literals(self, text):
        """Replaces whole-word 'tr' and 'fls' with '1' and '0'."""
        import re
        text = re.sub(r'\btr\b', '1', text)
        text = re.sub(r'\bfls\b', '0', text)
        return text

    # --- Print Processing (with Debugging) ---

    def _process_print_from_tokens(self):
        """
        Processes a print statement (prnt(...)) from tokens, generating
        a C printf call with appropriate format specifiers based on argument types.
        Relies on get_expression_type to determine the resulting type for format selection.
        Includes DEBUG prints.
        """
        self._consume('prnt')
        self._consume('(')
        arg_groups_tokens = []
        current_arg_tokens = []
        paren_level = 0

        if self._peek() == ')':
            self._consume(')')
            self._consume(';')
            return 'printf(""); fflush(stdout);'

        while not (self._peek() == ')' and paren_level == 0):
            if self._peek() is None:
                line = '?'
                if current_arg_tokens: 
                    try: line = self._get_token_info(current_arg_tokens[-1])[2]
                    except: pass
                elif self.current_pos > 0: 
                    try: line = self._get_token_info(self.tokens[self.current_pos-1])[2]
                    except: pass
                raise TranspilerError("Unexpected end of stream in print statement", line)

            tok_type, tok_val, token_full = self._consume()
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1

            if tok_type == ',' and paren_level == 0:
                if current_arg_tokens: arg_groups_tokens.append(current_arg_tokens)
                current_arg_tokens = []
            else:
                current_arg_tokens.append(token_full)

        if current_arg_tokens: arg_groups_tokens.append(current_arg_tokens)
        self._consume(')')
        self._consume(';')

        format_parts = []
        c_args = []

        for arg_tokens in arg_groups_tokens:
            if not arg_tokens: continue

            print(f"\n[DEBUG _process_print] Processing arg tokens: {arg_tokens}") # DEBUG

            token_pairs = [(self._get_token_info(t)[0], self._get_token_info(t)[1]) for t in arg_tokens]
            arg_c_expr = self._tokens_to_c_expression(token_pairs)

            fmt = None

            # --- Universal Type Checking using get_expression_type ---
            expression_result_type = self.get_expression_type(token_pairs)
            print(f"[DEBUG _process_print] Determined type: {expression_result_type}") # DEBUG

            if expression_result_type == 'dbl':
                fmt = "%.2f"
            elif expression_result_type == 'strng':
                fmt = "%s"
            elif expression_result_type == 'chr':
                fmt = "%c"
            elif expression_result_type == 'nt':
                fmt = "%d"
            elif expression_result_type == 'bln':
                fmt = "%d" # Boolean results printed as integers

            # --- Default format specifier ---
            if fmt is None:
                line_num = self._get_token_info(arg_tokens[0])[2] if arg_tokens else '?'
                print(f"Warning: Could not determine print format for expression near line {line_num}. Defaulting to %d.")
                fmt = "%d"

            print(f"[DEBUG _process_print] Final format specifier: {fmt}") # DEBUG
            format_parts.append(fmt)
            c_args.append(arg_c_expr)

        # Construct the final printf statement
        format_str = " ".join(format_parts)
        args_str = ", ".join(c_args)

        if not format_str and not args_str: return 'printf(""); fflush(stdout);'
        elif not args_str: return f'printf("{format_str}"); fflush(stdout);'
        else: return f'printf("{format_str}", {args_str}); fflush(stdout);'

    # --- Helper Methods ---
    def _indent(self, level): return "    " * max(0, level)
    def _generate_headers(self):
        return ("#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <stdbool.h>\n#include <stddef.h>\n\n")
    def _generate_helper_functions(self): return """// Helper function for string input
char* conso_input(const char* prompt) { printf("%s", prompt); fflush(stdout); char buffer[1024]; char* line = NULL; size_t cl = 0; size_t bl = sizeof(buffer); if (fgets(buffer, bl, stdin) == NULL) { if (feof(stdin)) return NULL; fprintf(stderr, "Input Error\\n"); exit(1); } cl = strlen(buffer); if (cl > 0 && buffer[cl - 1] == '\\n') { buffer[cl - 1] = '\\0'; cl--; } line = malloc(cl + 1); if (line == NULL) { fprintf(stderr, "Malloc Error\\n"); exit(1); } strcpy(line, buffer); return line; }
// Helper function for string concatenation
char* conso_concat(const char* s1, const char* s2) { if (s1 == NULL) s1 = ""; if (s2 == NULL) s2 = ""; size_t l1 = strlen(s1); size_t l2 = strlen(s2); char* r = malloc(l1 + l2 + 1); if (r == NULL) { fprintf(stderr, "Malloc Error\\n"); exit(1); } strcpy(r, s1); strcat(r, s2); return r; }"""
    def _split_args(self, content): # Keep for legacy string processing if needed elsewhere
        if not content: return []
        args = []; current_arg = ""; pl = 0; bl = 0; brl = 0; isq = False; idq = False; en = False
        for char in content:
            if en: current_arg += char; en = False; continue
            if char == '\\': current_arg += char; en = True; continue
            if char == "'" and not idq: isq = not isq
            elif char == '"' and not isq: idq = not idq
            if isq or idq: current_arg += char; continue
            if char == '(': pl += 1; 
            elif char == ')': pl -= 1
            elif char == '[': bl += 1; 
            elif char == ']': bl -= 1
            elif char == '{': brl += 1; 
            elif char == '}': brl -= 1
            if char == ',' and pl == 0 and bl == 0 and brl == 0: args.append(current_arg); current_arg = ""
            else: current_arg += char
        args.append(current_arg); sa = [a.strip() for a in args]; return [a for a in sa if a]
    def _split_declaration_args(self, declaration_part): return self._split_args(declaration_part) # Keep using robust splitter
    def _replace_bool_literals(self, text): text = re.sub(r'\btr\b', '1', text); text = re.sub(r'\bfls\b', '0', text); return text


# --- Standalone Functions ---
def transpile(conso_code):
    """Standalone function to transpile Conso code string (legacy)."""
    print("Warning: Calling string-based transpile. Token-based is preferred.")
    return "// String-based transpile function needs lexer/parser integration."

def transpile_from_tokens(token_list, symbol_table=None, user_inputs=None): # Added user_inputs
    """
    Transpiles Conso code from a token list using the token-based transpiler,
    injecting provided user inputs for 'npt' statements.

    Args:
        token_list: List of tokens (type, value, line, col). EOF should be excluded.
        symbol_table: The symbol table (e.g., global scope or relevant function scope).
        user_inputs: Dictionary mapping variable names to user-provided input strings.

    Returns:
        The generated C code as a string, or an error comment string.
    """
    # Remove EOF token before passing to transpiler if present
    # Ensure token_list is not empty before checking the last element
    if token_list:
         last_token = token_list[-1]
         # Use a temporary instance just to access the helper method safely
         temp_transpiler = ConsoTranspilerTokenBased([])
         token_type, _, _ = temp_transpiler._get_token_info(last_token)
         if token_type == 'EOF':
              print("Info: Removing EOF token before transpilation.")
              token_list = token_list[:-1]

    # Pass user_inputs to the constructor
    transpiler = ConsoTranspilerTokenBased(token_list, symbol_table, user_inputs)
    try:
        # Perform the transpilation
        return transpiler.transpile()
    except TranspilerError as e:
        # Handle known transpilation errors
        print(f"Transpilation Error: {e}", file=sys.stderr)
        return f"// TRANSPILER ERROR: {e}"
    except Exception as e:
        # Handle unexpected errors during transpilation
        print(f"Unexpected Transpiler Error: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr) # Print full traceback
        return f"// UNEXPECTED TRANSPILER ERROR: {type(e).__name__}: {e}"

# --- Example Usage ---
if __name__ == "__main__":
    # Example token list simulating output from previous stages
    # --- Make sure these token types match your lexer ---
    # --- REMOVED EOF from this example list ---
    test_token_list = [
        # strng name = "hello";
        ('strng', 'strng', 1, 1), ('id', 'name', 1, 7), ('=', '=', 1, 12), ('strnglit', 'hello', 1, 14), (';', ';', 1, 21),
        # nt num[3];
        ('nt', 'nt', 2, 1), ('id', 'num', 2, 4), ('[', '[', 2, 7), ('ntlit', 3, 2, 8), (']', ']', 2, 9), (';', ';', 2, 10),
        # dbl frac[3];
        ('dbl', 'dbl', 3, 1), ('id', 'frac', 3, 5), ('[', '[', 3, 9), ('ntlit', 3, 3, 10), (']', ']', 3, 11), (';', ';', 3, 12),
        # bln flag[2];
        ('bln', 'bln', 4, 1), ('id', 'flag', 4, 5), ('[', '[', 4, 9), ('ntlit', 2, 4, 10), (']', ']', 4, 11), (';', ';', 4, 12),
        # chr letter[2];
        ('chr', 'chr', 5, 1), ('id', 'letter', 5, 5), ('[', '[', 5, 11), ('ntlit', 2, 5, 12), (']', ']', 5, 13), (';', ';', 5, 14),
        # strng nameArr;
        ('strng', 'strng', 6, 1), ('id', 'nameArr', 6, 7), (';', ';', 6, 14),
        # chr newLetter;
        ('chr', 'chr', 7, 1), ('id', 'newLetter', 7, 5), (';', ';', 7, 14),
        # dfstrct myStruct struct1, struct2; (Assuming myStruct is defined)
        # ('dfstrct', 'dfstrct', 8, 1), ('id', 'myStruct', 8, 9), ('id', 'struct1', 8, 18), (',', ',', 8, 25), ('id', 'struct2', 8, 27), (';', ';', 8, 34),

        # dbl fra3[2] = { 3.2 };
        ('dbl', 'dbl', 10, 1), ('id', 'fra3', 10, 5), ('[', '[', 10, 9), ('ntlit', 2, 10, 10), (']', ']', 10, 11), ('=', '=', 10, 13), ('{', '{', 10, 15), ('dbllit', 3.2, 10, 17), ('}', '}', 10, 21), (';', ';', 10, 22),
        # frac4[2][1] = {{3.3},{2.5}};
        ('id', 'frac4', 10, 24), ('[', '[', 10, 29), ('ntlit', 2, 10, 30), (']', ']', 10, 31), ('[', '[', 10, 32), ('ntlit', 1, 10, 33), (']', ']', 10, 34), ('=', '=', 10, 36), ('{', '{', 10, 38), ('{', '{', 10, 39), ('dbllit', 3.3, 10, 40), ('}', '}', 10, 43), (',', ',', 10, 44), ('{', '{', 10, 45), ('dbllit', 2.5, 10, 46), ('}', '}', 10, 49), ('}', '}', 10, 50), (';', ';', 10, 51),
        # bln flag2[2] = { tr, fls };
        ('bln', 'bln', 11, 1), ('id', 'flag2', 11, 5), ('[', '[', 11, 10), ('ntlit', 2, 11, 11), (']', ']', 11, 12), ('=', '=', 11, 14), ('{', '{', 11, 16), ('blnlit', 'tr', 11, 18), (',', ',', 11, 20), ('blnlit', 'fls', 11, 22), ('}', '}', 11, 26), (';', ';', 11, 27),
        # flag3[2][1] = {{tr},{tr}};
        ('id', 'flag3', 11, 29), ('[', '[', 11, 34), ('ntlit', 2, 11, 35), (']', ']', 11, 36), ('[', '[', 11, 37), ('ntlit', 1, 11, 38), (']', ']', 11, 39), ('=', '=', 11, 41), ('{', '{', 11, 43), ('{', '{', 11, 44), ('blnlit', 'tr', 11, 45), ('}', '}', 11, 47), (',', ',', 11, 48), ('{', '{', 11, 49), ('blnlit', 'tr', 11, 50), ('}', '}', 11, 52), ('}', '}', 11, 53), (';', ';', 11, 54),
        # chr letter2[2] = { 'c' };
        ('chr', 'chr', 12, 1), ('id', 'letter2', 12, 5), ('[', '[', 12, 12), ('ntlit', 2, 12, 13), (']', ']', 12, 14), ('=', '=', 12, 16), ('{', '{', 12, 18), ('chrlit', 'c', 12, 20), ('}', '}', 12, 24), (';', ';', 12, 25),
        # letter3[2][1] = {{'d'},{'c'}};
        ('id', 'letter3', 12, 27), ('[', '[', 12, 34), ('ntlit', 2, 12, 35), (']', ']', 12, 36), ('[', '[', 12, 37), ('ntlit', 1, 12, 38), (']', ']', 12, 39), ('=', '=', 12, 41), ('{', '{', 12, 43), ('{', '{', 12, 44), ('chrlit', 'd', 12, 45), ('}', '}', 12, 48), (',', ',', 12, 49), ('{', '{', 12, 50), ('chrlit', 'c', 12, 51), ('}', '}', 12, 54), ('}', '}', 12, 55), (';', ';', 12, 56),

        # mn(){ ... }
        ('mn', 'mn', 14, 1), ('(', '(', 14, 3), (')', ')', 14, 4), ('{', '{', 14, 5),
        ('end', 'end', 15, 7), (';', ';', 15, 10),
        # ('}', '}', 16, 1) # No closing brace for mn if using end;
    ]
      

    print("--- Transpiling User's Conso Code from Tokens ---")
    # Pass None for symbol_table for now
    generated_c_code = transpile_from_tokens(test_token_list, None) # Use token-based function
    print("\n--- Generated C Code ---")
    print(generated_c_code)
