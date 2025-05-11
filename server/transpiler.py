"""
Conso to C Transpiler (V7 - Token-Based Sequential - Input Brace Fix)
This module converts Conso code to C code using a token stream provided
by earlier compiler phases (Lexer, Parser, Semantic Analyzer).
Processes top-level blocks sequentially based on tokens.
Includes fixes for global declarations, array initializers, default values,
and removes extra braces around input statement code.
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
    def __init__(self, token_list, symbol_table=None, function_scopes=None): # Added function_scopes
        """
        Initializes the transpiler.
        
        Args:
            token_list: List of tokens from the lexer (EOF token should be removed).
            symbol_table: The global SymbolTable instance (used as default).
            function_scopes: A dictionary mapping function names to their SymbolTable instances.
        """
        self.tokens = token_list
        self.symbol_table = symbol_table # This will be the default (global) table
        self.function_scopes = function_scopes if function_scopes is not None else {} # Store function scopes
        self.current_pos = 0
        self.output_parts = []
        self.current_indent_level = 0
        self.input_buffer_declared_in_scope = set()

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
            "strng": "NULL", # Be cautious with NULL for char*, "" might be safer if not checking
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
        """Processes function definition from tokens, correctly handling nested braces."""
        start_pos = self.current_pos
        func_name = "<unknown>"
        # --- Store the current (likely global) table ---
        original_symbol_table = self.symbol_table
        func_body_tokens = []

        try:
            # Consume fnctn, return type, func_name, params
            self._consume('fnctn')
            type_token_type, type_token_value, _ = self._consume()
            if type_token_type == 'id': c_return_type = type_token_value
            elif type_token_type in self.type_mapping: c_return_type = self.type_mapping[type_token_type]
            else: raise TranspilerError(f"Invalid function return type token: {type_token_type}")
            _, func_name, _ = self._consume('id'); self._consume('(')
            params_c = self._process_parameters_from_tokens(); self._consume(')')
            self._consume('{'); # Consume function's opening brace

            # Find the end of the function block to get its tokens (for buffer check)
            # This part is okay, used only for the 'has_npt' check
            temp_pos = self.current_pos
            find_brace_level = 1
            while find_brace_level > 0:
                token_type = self._peek(temp_pos - self.current_pos)
                if token_type is None: raise TranspilerError(f"Unterminated function '{func_name}'")
                if token_type == '{': find_brace_level += 1
                elif token_type == '}': find_brace_level -= 1
                if find_brace_level == 0:
                    func_body_tokens = self.tokens[self.current_pos : temp_pos]
                    break
                temp_pos += 1
                if temp_pos >= len(self.tokens): raise TranspilerError(f"Cannot find closing brace for '{func_name}'")

            definition_lines = [f"{c_return_type} {func_name}({params_c}) {{"]
            self.current_indent_level = 1

            # Declare input buffer if needed (Keep this logic)
            has_npt = any(self._get_token_info(t)[0] == 'npt' for t in func_body_tokens)
            if has_npt:
                buffer_size = 1024
                definition_lines.append(self._indent(1) + f"char conso_input_buffer[{buffer_size}]; // Input buffer for this scope")
                self.input_buffer_declared_in_scope.add(func_name)

            # Temporarily switch symbol table context (Keep this logic)
            if self.function_scopes and func_name in self.function_scopes:
                print(f"[Transpiler] Switching symbol table to scope: {func_name}") # DEBUG
                self.symbol_table = self.function_scopes[func_name]
            else:
                print(f"[Transpiler Warning] Function scope '{func_name}' not found. Using previous table.")
                self.symbol_table = original_symbol_table # Fallback

            # --- MODIFIED LOOP: Track brace level ---
            body_lines = []
            body_brace_level = 1 # Start at 1 because we consumed the function's {
            while body_brace_level > 0:
                # Check for premature end of stream
                if self._peek() is None:
                    raise TranspilerError(f"Unexpected end of stream inside function '{func_name}' body")

                # Peek at the next token to see if it's the closing brace we expect
                next_token_type = self._peek()

                # Process the statement
                statement_start_pos = self.current_pos
                statement_c = self._process_statement_from_tokens(current_scope_name=func_name)

                if statement_c is not None:
                    # Adjust indent *before* adding the closing brace
                    indent_level = self.current_indent_level
                    if statement_c == "}": indent_level = max(0, indent_level - 1)

                    body_lines.append(self._indent(indent_level) + statement_c)

                    # Adjust indent *after* adding the opening brace
                    if statement_c.endswith("{"): self.current_indent_level += 1
                    # Adjust indent *after* adding the closing brace
                    if statement_c == "}": self.current_indent_level = max(0, self.current_indent_level - 1)

                    # --- Update brace level based on the processed statement ---
                    if statement_c.endswith("{"):
                        body_brace_level += 1
                    elif statement_c == "}":
                        body_brace_level -= 1
                    # --- End brace level update ---

                elif self.current_pos == statement_start_pos:
                     # Failsafe: If no statement was processed and position didn't change, skip token
                     skipped_token = self._consume()[0]
                     print(f"Warning: Skipping unhandled token '{skipped_token}' inside function '{func_name}'")

                # Check brace level after processing
                if body_brace_level == 0:
                    # We have just processed the function's closing brace
                    break
                elif body_brace_level < 0:
                     # Should not happen with balanced braces
                     raise TranspilerError(f"Mismatched braces detected inside function '{func_name}'")

            # --- REMOVED self._consume('}') ---
            # The loop now correctly consumes the function's closing brace.

            self.current_indent_level = 0 # Reset indent level

            definition_lines.extend(body_lines)
            # --- REMOVED definition_lines.append("}") ---
            # The closing brace is now part of the body_lines when processed by the loop.

            return "\n".join(definition_lines)

        except TranspilerError as e:
            print(f"Error processing function '{func_name}': {e}", file=sys.stderr)
            self.current_pos = start_pos # Attempt reset
            return f"// ERROR processing function '{func_name}': {e}"
        finally:
            # --- Restore original symbol table ---
            print(f"[Transpiler] Restoring symbol table after processing function: {func_name}") # DEBUG
            self.symbol_table = original_symbol_table
            # --- End restore ---
            # Cleanup buffer tracking
            if func_name != "<unknown>" and func_name in self.input_buffer_declared_in_scope:
                 self.input_buffer_declared_in_scope.remove(func_name)

    def _process_main_definition_from_tokens(self):
        """Processes main function definition from tokens, switching symbol table context."""
        start_pos = self.current_pos
        original_symbol_table = self.symbol_table # Store the current (global) table
        main_body_tokens = []
        try:
            self._consume('mn'); self._consume('('); self._consume(')'); self._consume('{')

            # Find the end of the main block to get its tokens (for buffer check)
            temp_pos = self.current_pos
            brace_level = 1
            while True:
                token_type = self._peek(temp_pos - self.current_pos)
                if token_type is None: raise TranspilerError("Unterminated 'mn' block")
                if token_type == '{': brace_level += 1
                elif token_type == '}': brace_level -= 1
                # Check for 'end' at the correct brace level
                elif token_type == 'end' and brace_level <= 1:
                    main_body_tokens = self.tokens[self.current_pos : temp_pos]
                    break
                temp_pos += 1
                if temp_pos >= len(self.tokens): raise TranspilerError("Cannot find 'end;' for 'mn' block")

            definition_lines = ["int main(int argc, char *argv[]) {"]
            self.current_indent_level = 1

            # Declare input buffer if needed
            has_npt = any(self._get_token_info(t)[0] == 'npt' for t in main_body_tokens)
            if has_npt:
                buffer_size = 1024
                definition_lines.append(self._indent(1) + f"char conso_input_buffer[{buffer_size}]; // Input buffer for this scope")
                self.input_buffer_declared_in_scope.add("main")

            # --- NEW: Switch to the 'main' specific symbol table (if exists) ---
            # Assuming semantic analyzer stores 'mn' scope in function_scopes['mn']
            main_scope_name = "mn" # Or whatever key your semantic analyzer uses for main
            if self.function_scopes and main_scope_name in self.function_scopes:
                print(f"[Transpiler] Switching symbol table to scope: {main_scope_name}") # DEBUG
                self.symbol_table = self.function_scopes[main_scope_name]
            else:
                # If no specific 'mn' scope found, maybe vars are global? Or error?
                # Let's assume for now it should exist if declared inside mn.
                # If it might fall back to global, keep original_symbol_table.
                print(f"[Transpiler Warning] Scope '{main_scope_name}' not found in function_scopes. Using previous table (likely global).")
                self.symbol_table = original_symbol_table # Fallback
            # --- END NEW ---

            # Process main body statements (will use the switched self.symbol_table)
            body_lines = []
            while self._peek() != 'end':
                if self._peek() is None: raise TranspilerError("Unexpected end of stream inside main definition, missing 'end;'?")
                statement_start_pos = self.current_pos
                # Pass scope name "main" for consistency if needed by other funcs
                statement_c = self._process_statement_from_tokens(current_scope_name="main")
                if statement_c is not None:
                    indent_level = self.current_indent_level
                    if statement_c == "}": indent_level = max(0, indent_level - 1)
                    body_lines.append(self._indent(indent_level) + statement_c)
                    if statement_c.endswith("{"): self.current_indent_level += 1
                    if statement_c == "}": self.current_indent_level = max(0, self.current_indent_level - 1)
                elif self.current_pos == statement_start_pos:
                     skipped_token = self._consume()[0]
                     print(f"Warning: Skipping unhandled token '{skipped_token}' inside 'mn' block")

            self._consume('end'); self._consume(';')
            self.current_indent_level = 0

            definition_lines.extend(body_lines)
            definition_lines.append(self._indent(1) + "return 0; // Corresponds to Conso 'end;'")
            definition_lines.append("}")
            return "\n".join(definition_lines)

        except TranspilerError as e:
            print(f"Error processing main function: {e}", file=sys.stderr)
            self.current_pos = start_pos
            return f"// ERROR processing 'mn' function: {e}"
        finally:
            # --- Restore original symbol table ---
            print(f"[Transpiler] Restoring symbol table after processing 'mn'.") # DEBUG
            self.symbol_table = original_symbol_table
            # --- End restore ---
            # Cleanup buffer tracking
            if "main" in self.input_buffer_declared_in_scope:
                self.input_buffer_declared_in_scope.remove("main")

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
    def _process_statement_from_tokens(self, is_struct_member=False, is_global=False, current_scope_name=None):
        """
        Processes a single statement from the current token position.
        This function dispatches to specific processing methods based on the
        initial token(s) of the statement.
        Modified to correctly identify input statements with complex targets
        and pass the current_scope_name to the input processor.
        """
        token_type = self._peek()
        if token_type is None:
            # Return empty string if there are no more tokens
            return ""

        start_pos = self.current_pos # Store the starting position for error recovery
        line_num = '?'
        try:
            # Attempt to get the line number from the first token
            line_num = self._get_token_info(self.tokens[start_pos])[2]
        except IndexError:
            # Handle case where there's no token at start_pos (should be caught by token_type is None check, but defensive)
            pass
        except Exception:
            # Ignore other errors getting line number for error reporting itself
            pass

        try:
            # --- Handle struct members first ---
            if is_struct_member:
                # Struct members can only be declarations (type followed by id, possibly array)
                if token_type in self.type_mapping and token_type != 'dfstrct':
                    # Process as a declaration. Struct members are not const and don't get default assignment here.
                    return self._process_declaration_from_tokens(assign_default=False, is_const=False)
                else:
                    # If an unexpected token is found within a struct definition, print a warning and skip it.
                    print(f"Warning: Skipping non-declaration token '{token_type}' inside struct near line {line_num}");
                    self._consume(); # Consume the unexpected token
                    return "" # Return empty string, effectively skipping this line in the output

            # --- Processing for global, function, or main scope ---

            # Handle block delimiters ({ and }) immediately
            if token_type == '{':
                self._consume(); # Consume the opening brace
                return "{" # Return the C equivalent
            if token_type == '}':
                self._consume(); # Consume the closing brace
                return "}" # Return the C equivalent

            # --- Check for Constant Declaration (cnst type id ...) ---
            is_const_decl = False
            if token_type == 'cnst':
                # Peek ahead to see if a valid type follows 'cnst'
                next_type_peek = self._peek(1)
                # Check if the next token is a recognized data type (excluding struct definition itself)
                if next_type_peek in self.type_mapping and next_type_peek != 'dfstrct':
                    # It's a constant declaration, consume the 'cnst' token
                    self._consume('cnst')
                    is_const_decl = True
                    # Update token_type to the actual data type token that follows 'cnst'
                    token_type = self._peek()
                else:
                    # 'cnst' not followed by a valid type - this might be an error or part of another expression.
                    # For now, let it fall through to be handled as an 'other' statement or error later.
                    pass # Semantic analysis should ideally catch this error earlier.

            # --- Check for Regular or Constant Declaration (type id ...) ---
            # Now token_type is either the original peeked type or the type after 'cnst'
            if token_type in self.type_mapping and token_type != 'dfstrct':
                # Process as a variable declaration (regular or constant)
                # Pass the is_const flag determined above.
                # assign_default=True means non-array, non-const variables without initializer get default values.
                return self._process_declaration_from_tokens(assign_default=True, is_const=is_const_decl)

            # --- Check for Struct Instance Declaration (dfstrct struct_name id ...) ---
            elif token_type == 'dfstrct':
                # Process as a struct instance declaration.
                # Struct instances cannot be declared 'const' using the 'cnst' keyword in this grammar.
                return self._process_dfstrct_from_tokens()

            # --- Statements only valid inside functions/main ---
            if is_global:
                 # If we reach here in global scope with an unhandled token type, it's an error
                 print(f"Error: Statement type '{token_type}' not allowed at global scope near line {line_num}", file=sys.stderr)
                 # Attempt to recover by skipping tokens until a potential statement boundary (semicolon, brace)
                 while self._peek() not in [';', '}', None] and self.current_pos < len(self.tokens):
                     self._skip_token()
                 # Consume the boundary token if it's a semicolon
                 if self._peek() == ';': self._skip_token()
                 # Return a C comment indicating the error
                 return f"// ERROR: Statement type '{token_type}' not allowed at global scope"

            # --- Function/Main Scope Statements ---
            # These should only be processed if we are NOT in the global scope

            # Check for specific keywords first
            if token_type == 'prnt': return self._process_print_from_tokens()
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
            elif token_type == 'brk':
                self._consume('brk'); self._consume(';'); # Consume 'brk' and ';'
                return "break;" # Return the C equivalent
            elif token_type == 'cntn':
                self._consume('cntn'); self._consume(';'); # Consume 'cntn' and ';'
                return "continue;" # Return the C equivalent
            # Add other specific statements here

            # --- NEW/MODIFIED: Handle Input Statement (target = npt(...)) ---
            # This requires looking ahead to find the '=' and 'npt' tokens.
            # We need to consume tokens until we find '=' at the top level (outside any parens/brackets).
            temp_pos = self.current_pos # Use a temporary position to peek ahead without consuming
            temp_paren_level = 0
            temp_bracket_level = 0
            found_assignment = False

            # Scan ahead to find the '=' token at the top level
            while temp_pos < len(self.tokens):
                peek_token_type = self._peek(temp_pos - self.current_pos)
                if peek_token_type is None: break # Reached end of stream

                if peek_token_type == '(': temp_paren_level += 1
                elif peek_token_type == ')': temp_paren_level -= 1
                elif peek_token_type == '[': temp_bracket_level += 1
                elif peek_token_type == ']': temp_bracket_level -= 1
                elif peek_token_type == '=' and temp_paren_level == 0 and temp_bracket_level == 0:
                    found_assignment = True
                    break # Found the top-level assignment operator

                temp_pos += 1 # Move to the next token

            # If an assignment was found, check if the RHS starts with 'npt'
            if found_assignment:
                # Peek at the token immediately after the '='
                token_after_assignment = self._peek(temp_pos - self.current_pos + 1)
                if token_after_assignment == 'npt':
                    # This is an input statement! Dispatch to the input processor.
                    # Pass the current_scope_name to the input processor.
                    return self._process_input_from_tokens(current_scope_name=current_scope_name)
                # If the token after '=' is not 'npt', it's a regular assignment or other expression.
                # Let it fall through to _process_other_statement_from_tokens.


            # --- Handle Other Statements (Assignments, Function Calls, Expressions) ---
            # If none of the specific statement types matched, process it as a general statement.
            # This includes assignments that are NOT input statements, function calls,
            # standalone expressions (though less common in C), etc.
            return self._process_other_statement_from_tokens()

        except TranspilerError as e:
             # Catch custom transpiler errors
             print(f"Error processing statement near line {e.line_num if e.line_num else line_num}: {e.message}", file=sys.stderr)
             # Attempt to reset the token position to the start of the statement for recovery
             self.current_pos = start_pos
             # Skip tokens until a potential statement boundary (semicolon, brace) to avoid infinite loops
             while self._peek() not in [';', '}', '{', None] and self.current_pos < len(self.tokens):
                 self._skip_token()
             # Consume the boundary token if it's a semicolon
             if self._peek() == ';': self._skip_token()
             # Return a C comment indicating the error
             return f"// TRANSPILER ERROR: {e.message}"
        except Exception as e:
             # Catch any unexpected Python exceptions
             # Safely get the line number if possible for the error report
             err_line = line_num
             print(f"Unexpected error processing statement near line {err_line}: {e}", file=sys.stderr)
             # Print a traceback for debugging unexpected errors
             import traceback
             traceback.print_exc(file=sys.stderr)
             # Advance at least one token if the position didn't change to prevent infinite loops
             if self.current_pos == start_pos: self._skip_token()
             # Return a C comment indicating the unexpected error
             return f"// UNEXPECTED TRANSPILER ERROR: {type(e).__name__}: {e}"


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

    def _process_input_from_tokens(self, current_scope_name=None):
        """
        Processes an input statement (target = npt("prompt");) by generating
        C code. Handles single variables, array elements, struct members,
        and array shortcut input.

        This function parses the left-hand side (LHS) of the
        assignment to correctly identify the target (simple variable,
        array index, struct member) and generate appropriate C input code.
        It distinguishes the array shortcut input (e.g., `arr = npt(...)`)
        which implies multiple values, from single-value assignments.
        Includes fix for string target C code generation structure.
        Only adds 'return 1;' on input failure if in the 'main' scope.
        """
        start_pos = self.current_pos
        line_num = '?'
        target_tokens = [] # Tokens for the LHS (the target variable/member/element)

        try:
            # 1. Consume the target tokens (LHS) until '='
            # This loop collects all tokens on the LHS, handling nested parentheses/brackets
            paren_level = 0
            bracket_level = 0
            # Consume tokens until we see '=' at the top level (outside any parens/brackets)
            while self._peek() != '=' or paren_level > 0 or bracket_level > 0:
                 if self._peek() is None:
                      raise TranspilerError("Unexpected end of token stream in input statement target", line_num)

                 # Consume the next token
                 tok_type, tok_val, token_full = self._consume()
                 # Update line number from the consumed token
                 line_num = self._get_token_info(token_full)[2]

                 # Track parenthesis and bracket levels
                 if tok_type == '(': paren_level += 1
                 elif tok_type == ')': paren_level -= 1
                 elif tok_type == '[': bracket_level += 1
                 elif tok_type == ']': bracket_level -= 1

                 # Add the consumed token (type and value) to the target tokens list
                 target_tokens.append((tok_type, tok_val))

            # Ensure we actually consumed some tokens for the target
            if not target_tokens:
                 raise TranspilerError("Missing target for input statement", line_num)

            # Convert target tokens into a C expression string.
            # This string will be used directly in the scanf/assignment C code.
            target_c_expression = self._tokens_to_c_expression(target_tokens)

            # 2. Consume '=' and the npt(...) call
            self._consume('=') # Consume the '=' token
            self._consume('npt') # Consume the 'npt' keyword
            self._consume('(') # Consume the opening parenthesis of the npt call

            # Consume the prompt string literal inside npt()
            prompt_text = ""
            if self._peek() == 'strnglit':
                _, prompt_text, _ = self._consume('strnglit')
            # Escape the prompt text for use in a C string literal (e.g., for printf)
            c_prompt = prompt_text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

            self._consume(')') # Consume the closing parenthesis of the npt call
            self._consume(';') # Consume the semicolon ending the statement

            # 3. Analyze Target Tokens to Determine Handling Method (Array Shortcut vs Single Value)
            is_array_shortcut = False
            array_type = None
            array_size_value = 0

            # Check if the target is a single identifier and that identifier is an array
            if len(target_tokens) == 1 and target_tokens[0][0] == 'id':
                var_name = target_tokens[0][1]
                # Look up the variable in the symbol table (current scope)
                symbol = self.symbol_table.lookup(var_name)

                # Check if the symbol exists and is marked as an array
                if symbol and getattr(symbol, 'is_array', False):
                    is_array_shortcut = True
                    # Retrieve array details needed for processing multiple inputs
                    array_type = getattr(symbol, 'data_type', None)
                    array_sizes_attr = getattr(symbol, 'array_sizes', None)

                    # Get the size of the first dimension for the loop
                    if isinstance(array_sizes_attr, list) and len(array_sizes_attr) > 0:
                         try:
                              # Attempt to convert the first dimension size to an integer
                              array_size_value = int(array_sizes_attr[0])
                         except (ValueError, TypeError):
                              # Handle cases where the size is not a simple integer literal
                              # (e.g., defined by a variable, which is not supported for input loops here)
                              raise TranspilerError(f"Array size for '{var_name}' must be a positive integer literal for shortcut input (found: {array_sizes_attr[0]})", line_num)
                    else:
                         # Handle cases where array_sizes attribute is missing or invalid
                         raise TranspilerError(f"Could not determine valid size for array '{var_name}' from 'array_sizes': {repr(array_sizes_attr)}", line_num)

                    # Ensure the array size is positive
                    if array_size_value <= 0:
                         raise TranspilerError(f"Array size must be positive for shortcut input '{var_name}' (found: {array_size_value})", line_num)

                    # Ensure the array type is supported for shortcut input
                    if array_type not in ['chr', 'strng', 'nt', 'dbl', 'bln']:
                         raise TranspilerError(f"Array shortcut input ('npt') not supported for array type '{array_type}' of variable '{var_name}'", line_num)


            # 4. Generate C Code based on Handling Method (Array Shortcut vs Single Value)
            c_input_code = []
            # Print the prompt before reading input
            c_input_code.append(f'printf("{c_prompt}"); fflush(stdout);')

            # Define the fixed size buffer name and size (assuming it's declared in the scope)
            fixed_buffer_name = "conso_input_buffer"
            buffer_size = 1024 # This size should match the buffer declaration

            if is_array_shortcut:
                # --- ARRAY SHORTCUT INPUT (Multiple values expected, e.g., comma/space separated) ---
                # This logic is adapted from your original code for handling array shortcut input.
                # It reads the entire line and then parses it.

                if array_type == 'chr':
                    # For char arrays, use scanf with a width specifier to read a fixed number of characters
                    # Note: scanf leaves the newline, so we need to consume it.
                    if array_size_value > 0:
                         c_input_code.append(f'scanf("%{array_size_value - 1}s", {var_name});')
                         # Consume the rest of the line including the newline
                         c_input_code.append('int c; while ((c = getchar()) != \'\\n\' && c != EOF);')
                    else:
                         # Handle zero-size char array (cannot use scanf)
                         raise TranspilerError(f"Cannot use scanf for zero-size char array '{var_name}'", line_num)

                elif array_type == 'strng':
                    # For string arrays (strng[]), read the line, then tokenize using strtok_r
                    # and duplicate each token using strdup.
                    c_input_code.append(f'int items_read_{var_name} = 0;')
                    # Before assigning new strings, free any existing strings in the array
                    c_input_code.append(f'for (int k_{var_name} = 0; k_{var_name} < {array_size_value}; ++k_{var_name}) {{')
                    c_input_code.append(f'    free({var_name}[k_{var_name}]); // Free existing string if any')
                    c_input_code.append(f'    {var_name}[k_{var_name}] = NULL; // Set pointer to NULL after freeing')
                    c_input_code.append(f'}}')

                    # Read the entire line into the buffer
                    c_input_code.append(f'if (fgets({fixed_buffer_name}, {buffer_size}, stdin) != NULL) {{')
                    # Remove the trailing newline from the buffer
                    c_input_code.append(f'    {fixed_buffer_name}[strcspn({fixed_buffer_name}, "\\n")] = 0;')

                    # Tokenize the buffer using space and tab as delimiters
                    c_input_code.append(f'    char *token_{var_name};')
                    c_input_code.append(f'    char *saveptr_{var_name}; // Pointer for strtok_r to maintain state')
                    c_input_code.append(f'    char *str_ptr_{var_name} = {fixed_buffer_name}; // Pointer to the current position in the buffer')

                    # Loop through the array size, tokenizing and assigning
                    c_input_code.append(f'    for (items_read_{var_name} = 0; items_read_{var_name} < {array_size_value}; ++items_read_{var_name}, str_ptr_{var_name} = NULL) {{')
                    # Get the next token (using strtok_r for thread safety/re-entrancy)
                    c_input_code.append(f'        token_{var_name} = strtok_r(str_ptr_{var_name}, " \\t", &saveptr_{var_name});')
                    # If no more tokens are found, break the loop
                    c_input_code.append(f'        if (token_{var_name} == NULL) {{')
                    c_input_code.append(f'            break; // Stop if fewer items were entered than array size')
                    c_input_code.append(f'        }}')
                    # Duplicate the token string and assign the new pointer to the array element
                    c_input_code.append(f'        // {var_name}[items_read_{var_name}] was freed or is NULL')
                    c_input_code.append(f'        {var_name}[items_read_{var_name}] = strdup(token_{var_name});')
                    # Check if strdup failed (memory allocation error)
                    c_input_code.append(f'        if ({var_name}[items_read_{var_name}] == NULL) {{')
                    c_input_code.append(f'            fprintf(stderr, "Memory allocation failed for string array input.\\n");')
                    # --- Conditional return 1 based on scope ---
                    if current_scope_name == "main":
                         c_input_code.append(f'            return 1; // Indicate failure')
                    # --- End Conditional return 1 ---
                    c_input_code.append(f'        }}')
                    c_input_code.append(f'    }}') # End for loop

                    # Handle the case where fgets failed
                    c_input_code.append(f'}} else {{ /* Handle fgets error */ items_read_{var_name} = 0; }}')


                elif array_type in ['nt', 'dbl', 'bln']:
                    # For numeric and boolean arrays, read the line, then parse values using sscanf in a loop
                    c_input_code.append(f'int items_read_{var_name} = 0;')
                    c_input_code.append(f'char* parse_ptr_{var_name}; // Pointer to the current parsing position in the buffer')
                    c_input_code.append(f'int offset_{var_name}; // To store the number of characters consumed by sscanf')

                    # Read the entire line into the buffer
                    c_input_code.append(f'if (fgets({fixed_buffer_name}, {buffer_size}, stdin) != NULL) {{')
                    # Remove the trailing newline
                    c_input_code.append(f'    {fixed_buffer_name}[strcspn({fixed_buffer_name}, "\\n")] = 0;')
                    c_input_code.append(f'    parse_ptr_{var_name} = {fixed_buffer_name}; // Start parsing from the beginning of the buffer')

                    # Determine the sscanf format specifier and assignment logic based on array element type
                    sscanf_fmt = ""; temp_var_decl = ""; assign_logic = f"{var_name}[items_read_{var_name}]"
                    if array_type == 'nt':   sscanf_fmt = "%d%n" # %n captures characters consumed
                    elif array_type == 'dbl':  sscanf_fmt = "%lf%n" # %lf for double
                    elif array_type == 'bln':
                        # Read boolean as int first, then convert
                        sscanf_fmt = "%d%n"; temp_var_decl = f"int temp_bln_{var_name};"; assign_logic = f"temp_bln_{var_name}"

                    # Declare a temporary variable if needed for boolean conversion
                    if temp_var_decl: c_input_code.append(f'    {temp_var_decl}')

                    # Loop to read multiple values using sscanf
                    c_input_code.append(f'    for (items_read_{var_name} = 0; items_read_{var_name} < {array_size_value}; ++items_read_{var_name}) {{')
                    # Attempt to scan the next value from the current parse_ptr position
                    c_input_code.append(f'        if (sscanf(parse_ptr_{var_name}, "{sscanf_fmt}", &{assign_logic}, &offset_{var_name}) == 1) {{')
                    # If scanning was successful:
                    if array_type == 'bln':
                        # Convert the temporary int to boolean (0 or non-zero)
                        c_input_code.append(f'            {var_name}[items_read_{var_name}] = (temp_bln_{var_name} != 0);')
                    # Advance the parse pointer by the number of characters consumed
                    c_input_code.append(f'            parse_ptr_{var_name} += offset_{var_name};')
                    # Skip any whitespace after the number
                    c_input_code.append(f'            while (*parse_ptr_{var_name} == \' \' || *parse_ptr_{var_name} == \'\\t\') parse_ptr_{var_name}++;')
                    # Check if the next character is a comma (if not the last item)
                    c_input_code.append(f'            if (items_read_{var_name} < {array_size_value} - 1 && *parse_ptr_{var_name} == \',\') {{ parse_ptr_{var_name}++; }}')
                    # Skip any whitespace after the comma
                    c_input_code.append(f'            while (*parse_ptr_{var_name} == \' \' || *parse_ptr_{var_name} == \'\\t\') parse_ptr_{var_name}++;')
                    c_input_code.append(f'        }} else {{')
                    # If sscanf failed, stop reading values
                    c_input_code.append(f'            break; // Stop if input doesn\'t match format or fewer items were entered')
                    c_input_code.append(f'        }}')
                    c_input_code.append(f'    }}') # End for loop

                    # Handle the case where fgets failed
                    c_input_code.append(f'}} else {{ /* Handle fgets error */ items_read_{var_name} = 0; }}')

                # No explicit 'return 1' on invalid input for array shortcut,
                # as it reads as many as possible. Error messages printed by sscanf/fprintf.

            else:
                # --- SINGLE VALUE INPUT (Simple var, array element like arr[0], struct member like person.age) ---
                # Determine the final type of the target expression (e.g., nt for arr[0], dbl for person.age)
                # This uses the helper function that analyzes the target tokens.
                target_type = self.get_expression_type(target_tokens)

                if target_type is None:
                     # This indicates an issue in get_expression_type or an unsupported target expression
                     raise TranspilerError(f"Could not determine type of input target '{target_c_expression}'", line_num)

                # Read the input line into the buffer
                c_input_code.append(f'if (fgets({fixed_buffer_name}, {buffer_size}, stdin) != NULL) {{')
                # Remove the trailing newline character from the buffer
                c_input_code.append(f'    {fixed_buffer_name}[strcspn({fixed_buffer_name}, "\\n")] = 0;')

                # Generate C code to parse the input based on the target type
                if target_type == 'strng':
                     # Handle char* targets (simple var, array element strng[], struct member char*)
                     # Use strdup to allocate memory and copy the string from the buffer
                     # Need to free any previously allocated string memory first, but NOT for string literals
                     c_input_code.append(f'    // Free existing string if it was dynamically allocated (not a literal)')
                     c_input_code.append(f'    if ({target_c_expression} != NULL && {target_c_expression} != "" && {target_c_expression} != " ") {{ // Basic check to avoid freeing literals')
                     c_input_code.append(f'        free({target_c_expression});')
                     c_input_code.append(f'    }}')
                     c_input_code.append(f'    {target_c_expression} = strdup({fixed_buffer_name});')
                     # Check if strdup failed (memory allocation error)
                     c_input_code.append(f'    if ({target_c_expression} == NULL) {{')
                     c_input_code.append(f'        fprintf(stderr, "Memory allocation failed for string input.\\n");')
                     # --- Conditional return 1 based on scope ---
                     if current_scope_name == "main":
                         c_input_code.append(f'        return 1; // Indicate failure and exit the current function')
                     # --- End Conditional return 1 ---
                     c_input_code.append(f'    }}')
                     # Add the closing brace for the fgets if block
                     # Corrected else block: Removed free, only set to NULL on fgets error
                     c_input_code.append(f'}} else {{ /* Handle fgets error or EOF */ {target_c_expression} = NULL; }}')

                elif target_type == 'chr' and '[' in target_c_expression:
                     # Handle char array targets (e.g., char_array[index] or struct member char array)
                     # Use strncpy to copy the string from the buffer to the char array element/member
                     # This requires knowing the size of the destination char array.
                     # A robust solution would look up the symbol for the target and get its size.
                     # For simplicity here, we'll use sizeof() on the target expression, which works
                     # if the target is a char array element or a struct member char array.
                     c_input_code.append(f'    // Assuming {target_c_expression} is a char array element or struct member char array')
                     c_input_code.append(f'    strncpy({target_c_expression}, {fixed_buffer_name}, sizeof({target_c_expression}) - 1);')
                     # Ensure null termination in case the input string is longer than the array capacity
                     c_input_code.append(f'    {target_c_expression}[sizeof({target_c_expression}) - 1] = \'\\0\'; // Ensure null termination')
                     # Add the closing brace for the fgets if block
                     c_input_code.append(f'}} else {{ /* Handle fgets error or EOF */ {target_c_expression}[0] = \'\\0\'; }}') # Added else block and closing brace

                elif target_type == 'nt':
                    # Use sscanf to parse an integer from the buffer and assign to the target
                    c_input_code.append(f'    if (sscanf({fixed_buffer_name}, "%d", &({target_c_expression})) != 1) {{')
                    # If sscanf fails (input is not a valid integer)
                    c_input_code.append(f'        fprintf(stderr, "\\nError: Invalid integer input for {target_c_expression}.\\n");')
                    # --- Conditional return 1 based on scope ---
                    if current_scope_name == "main":
                         c_input_code.append(f'        return 1; // Indicate failure and exit the current function')
                    # --- End Conditional return 1 ---
                    c_input_code.append(f'    }}')
                    # Add the closing brace for the fgets if block
                    c_input_code.append(f'}} else {{ /* Handle fgets error or EOF */ }}') # Added else block and closing brace

                elif target_type == 'dbl':
                     # Use sscanf to parse a double from the buffer and assign to the target
                     c_input_code.append(f'    if (sscanf({fixed_buffer_name}, "%lf", &({target_c_expression})) != 1) {{')
                     # If sscanf fails (input is not a valid double)
                     c_input_code.append(f'        fprintf(stderr, "\\nError: Invalid double input for {target_c_expression}.\\n");')
                     # --- Conditional return 1 based on scope ---
                     if current_scope_name == "main":
                         c_input_code.append(f'        return 1; // Indicate failure and exit the current function')
                     # --- End Conditional return 1 ---
                     c_input_code.append(f'    }}')
                     # Add the closing brace for the fgets if block
                     c_input_code.append(f'}} else {{ /* Handle fgets error or EOF */ }}') # Added else block and closing brace

                elif target_type == 'chr':
                     # Handle single character input: take the first character of the buffer
                     c_input_code.append(f'    if ({fixed_buffer_name}[0] != \'\\n\' && {fixed_buffer_name}[0] != \'\\0\') {{')
                     c_input_code.append(f'        {target_c_expression} = {fixed_buffer_name}[0];')
                     c_input_code.append(f'    }} else {{')
                     # If the buffer is empty or only contains a newline
                     c_input_code.append(f'        fprintf(stderr, "\\nError: Invalid character input for {target_c_expression}.\\n");')
                     # --- Conditional return 1 based on scope ---
                     if current_scope_name == "main":
                         c_input_code.append(f'        return 1; // Indicate failure and exit the current function')
                     # --- End Conditional return 1 ---
                     c_input_code.append(f'    }}')
                     # Add the closing brace for the fgets if block
                     c_input_code.append(f'}} else {{ /* Handle fgets error or EOF */ }}') # Added else block and closing brace

                elif target_type == 'bln':
                     # Handle boolean input: accept 0, 1, "tr", or "fls"
                     c_input_code.append(f'    int temp_bln_input;') # Temporary variable to read integer boolean
                     c_input_code.append(f'    if (sscanf({fixed_buffer_name}, "%d", &temp_bln_input) == 1) {{')
                     # If an integer (0 or 1) was successfully scanned, assign the boolean value
                     c_input_code.append(f'        {target_c_expression} = (temp_bln_input != 0);')
                     c_input_code.append(f'    }} else {{')
                     # If integer scan failed, check if the input string is "tr" or "fls"
                     c_input_code.append(f'        if (strcmp({fixed_buffer_name}, "tr") == 0) {{ {target_c_expression} = 1; }}')
                     c_input_code.append(f'        else if (strcmp({fixed_buffer_name}, "fls") == 0) {{ {target_c_expression} = 0; }}')
                     c_input_code.append(f'        else {{')
                     # If none of the expected formats match
                     c_input_code.append(f'            fprintf(stderr, "\\nError: Invalid boolean input for {target_c_expression} (expected 0, 1, tr, or fls).\\n");')
                     # --- Conditional return 1 based on scope ---
                     if current_scope_name == "main":
                         c_input_code.append(f'            return 1; // Indicate failure and exit the current function')
                     # --- End Conditional return 1 ---
                     c_input_code.append(f'        }}')
                     c_input_code.append(f'    }}')
                     # Add the closing brace for the fgets if block
                     c_input_code.append(f'}} else {{ /* Handle fgets error or EOF */ }}') # Added else block and closing brace

                else:
                    # This case should not be reached if get_expression_type is comprehensive
                    raise TranspilerError(f"Input ('npt') not supported for target type '{target_type}'", line_num)


            # Join all the generated C lines
            return "\n".join(c_input_code)

        # --- Error Handling (Keep existing blocks) ---
        except TranspilerError as e:
            # Print the custom transpiler error message
            print(f"Error processing input statement near line {e.line_num if e.line_num else line_num}: {e.message}", file=sys.stderr)
            # Attempt to reset the token position to the start of the statement for recovery
            self.current_pos = start_pos
            # Skip tokens until a potential statement boundary (semicolon, brace) to avoid infinite loops
            while self._peek() not in [';', '}', '{', None] and self.current_pos < len(self.tokens):
                self._skip_token()
            # Consume the boundary token if it's a semicolon
            if self._peek() == ';': self._skip_token()
            # Return a C comment indicating the error
            return f"// TRANSPILER ERROR (Input): {e.message}"
        except Exception as e:
            # Handle any unexpected Python exceptions during processing
            # Safely get the line number if possible for the error report
            err_line = line_num
            print(f"Unexpected error processing input for '{target_c_expression if 'target_c_expression' in locals() else 'unknown target'}' near line {err_line}: {e}", file=sys.stderr)
            # Print a traceback for debugging unexpected errors
            import traceback
            traceback.print_exc(file=sys.stderr)
            # Advance at least one token if the position didn't change to prevent infinite loops
            if self.current_pos == start_pos: self._skip_token()
            # Return a C comment indicating the unexpected error
            return f"// UNEXPECTED TRANSPILER ERROR (Input): {type(e).__name__}: {e}"
        
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
        """
        Formats a single token into its C string representation.
        Handles special cases for literals like strings, chars, and booleans.
        """
        if tok_type == 'blnlit':
             # Map boolean literals 'tr' and 'fls' to '1' and '0'
             return self.bool_mapping.get(tok_val, '0')
        elif tok_type == 'strnglit':
             # Enclose string literals in double quotes
             return f'"{tok_val}"'
        elif tok_type == 'chrlit':
             # Enclose character literals in single quotes
             return f"'{tok_val}'"
        else:
             # Default case: convert the token value to a string
             return str(tok_val)

    def get_expression_type(self, expr_tokens):
        """
        Determines the resulting C type ('nt', 'dbl', 'strng', 'bln', 'chr', or None)
        of an expression represented by a list of (type, value) tokens.
        Prioritizes operator type over initial operand type (e.g., division of ints
        might result in double in some contexts, though C integer division truncates).
        Relies on symbol table lookup to determine variable and member types.
        Handles simple literals, variables, array elements, struct members,
        function calls, and basic arithmetic/logical/comparison operations.
        """
        # print(f"[DEBUG get_expression_type] Input tokens: {expr_tokens}") # Uncomment for deep debug
        if not expr_tokens:
            # print("[DEBUG get_expression_type] Returning: None (empty tokens)") # Uncomment for deep debug
            return None # Return None for empty expressions

        result_type = None # Initialize the determined result type

        # --- Operator-based type determination FIRST ---
        # Check for comparison or logical operators, as they always result in a boolean (int in C)
        is_comparison_or_logical = any(
            t[0] in ['==', '!=', '<', '>', '<=', '>=', '&&', '||']
            for t in expr_tokens
        )
        if is_comparison_or_logical:
            result_type = 'bln' # The result of a comparison or logical operation is boolean (true/false)

        # If not a comparison/logical operation, check for arithmetic operations
        has_arithmetic_op = any(t[0] in ['+', '-', '*', '/'] for t in expr_tokens)
        if has_arithmetic_op and result_type is None: # Only check if type hasn't been determined yet
            promotes_to_double = False
            # Iterate through tokens to check operand types for potential double promotion
            i = 0
            while i < len(expr_tokens):
                tok_type, tok_val = expr_tokens[i]

                # If we find a double literal or a division operator '/', the result might be double
                if tok_type in ['dbllit', 'NEGDOUBLELIT', '/']:
                    promotes_to_double = True
                    break # Found a source that promotes to double, no need to check further

                # If an identifier is involved, check its type from the symbol table
                if tok_type == 'id':
                    # Check for struct member access pattern (id . id)
                    if i + 2 < len(expr_tokens) and expr_tokens[i+1][0] == '.' and expr_tokens[i+2][0] == 'id':
                        struct_var_name = tok_val
                        member_name = expr_tokens[i+2][1]
                        # print(f"[DEBUG get_expression_type] Checking struct member: {struct_var_name}.{member_name}") # DEBUG
                        if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                            # Look up the symbol for the struct variable
                            struct_var_symbol = self.symbol_table.lookup(struct_var_name)
                            if struct_var_symbol and hasattr(struct_var_symbol, 'data_type'):
                                struct_type_name = struct_var_symbol.data_type # Get the name of the struct type
                                # Look up the symbol for the struct definition itself
                                struct_def_symbol = self.symbol_table.lookup(struct_type_name)
                                # Check if the struct definition symbol exists and has members
                                if struct_def_symbol and hasattr(struct_def_symbol, 'members') and hasattr(struct_def_symbol.members, 'get'):
                                    # Get the symbol for the specific member
                                    member_symbol = struct_def_symbol.members.get(member_name)
                                    # Check if the MEMBER's data type is 'dbl'
                                    if member_symbol and getattr(member_symbol, 'data_type', None) == 'dbl':
                                        # print(f"[DEBUG get_expression_type] Struct member {member_name} is dbl.") # DEBUG
                                        promotes_to_double = True
                                        break # Found a double source, stop checking

                        # Skip the '.' and member 'id' tokens in the next iteration since they are part of this access
                        i += 2
                    else:
                        # Regular ID lookup (not part of struct access pattern)
                        # print(f"[DEBUG get_expression_type] Checking identifier: {tok_val}") # DEBUG
                        if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                            # Look up the symbol for the identifier
                            symbol = self.symbol_table.lookup(tok_val)
                            # Check if the IDENTIFIER's data type is 'dbl'
                            if symbol and getattr(symbol, 'data_type', None) == 'dbl':
                                # print(f"[DEBUG get_expression_type] Identifier {tok_val} is dbl.") # DEBUG
                                promotes_to_double = True
                                break # Found a double source, stop checking

                i += 1 # Move to the next token

            # Assign the result type based on whether any double source was found
            result_type = 'dbl' if promotes_to_double else 'nt'


        # --- If no operators determined the type, check the structure of the expression ---
        # This handles cases like single literals, variables, array elements, struct members, function calls.
        if result_type is None:
             # Check simple cases first: a single literal or a single variable identifier
             if len(expr_tokens) == 1:
                 tok_type, tok_val = expr_tokens[0]
                 if tok_type == 'strnglit': result_type = 'strng'
                 elif tok_type == 'chrlit': result_type = 'chr'
                 elif tok_type in ['dbllit', 'NEGDOUBLELIT']: result_type = 'dbl'
                 elif tok_type in ['ntlit', 'NEGINTLIT']: result_type = 'nt'
                 elif tok_type == 'blnlit': result_type = 'bln'
                 elif tok_type == 'id':
                     # Look up the identifier in the symbol table
                     if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                         symbol = self.symbol_table.lookup(tok_val)
                         # The type of a single variable is its data type from the symbol table
                         result_type = getattr(symbol, 'data_type', None) if symbol else None
             # Check complex structures - Array Element Access (e.g., arr[index])
             # Pattern: Starts with 'id', contains '[', ends with ']'
             elif len(expr_tokens) >= 3 and expr_tokens[0][0] == 'id' and expr_tokens[1][0] == '[' and expr_tokens[-1][0] == ']':
                 base_var_name = expr_tokens[0][1]
                 # Look up the base array variable in the symbol table
                 if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                     symbol = self.symbol_table.lookup(base_var_name)
                     # The type of an array element is the base data type of the array
                     result_type = getattr(symbol, 'data_type', None) if symbol else None
             # Check complex structures - Struct Member Access (e.g., struct.member)
             # Pattern: Ends with 'id', preceded by '.', preceded by something (often 'id')
             # This heuristic assumes simple id.id access. More complex chains might need recursive analysis.
             elif len(expr_tokens) >= 3 and expr_tokens[-1][0] == 'id' and expr_tokens[-2][0] == '.':
                 # Assuming a simple `id.id` structure for now
                 if len(expr_tokens) == 3 and expr_tokens[0][0] == 'id':
                     struct_var_name = expr_tokens[0][1]
                     member_name = expr_tokens[-1][1]
                     if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                         # Look up the symbol for the struct variable
                         struct_var_symbol = self.symbol_table.lookup(struct_var_name)
                         if struct_var_symbol and hasattr(struct_var_symbol, 'data_type'):
                             struct_type_name = struct_var_symbol.data_type # Get the name of the struct type
                             # Look up the symbol for the struct definition itself
                             struct_def_symbol = self.symbol_table.lookup(struct_type_name)
                             # Check if the struct definition symbol exists and has members
                             if struct_def_symbol and hasattr(struct_def_symbol, 'members') and hasattr(struct_def_symbol.members, 'get'):
                                 # Get the symbol for the specific member
                                 member_symbol = struct_def_symbol.members.get(member_name)
                                 # The type of a struct member is its data type from the struct definition
                                 if member_symbol: result_type = getattr(member_symbol, 'data_type', None)
             # Check complex structures - Function Call (e.g., func(args))
             # Pattern: Starts with 'id', followed by '(', ends with ')'
             elif len(expr_tokens) >= 3 and expr_tokens[0][0] == 'id' and expr_tokens[1][0] == '(' and expr_tokens[-1][0] == ')':
                 func_name = expr_tokens[0][1]
                 # Look up the function symbol in the symbol table
                 if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                     symbol = self.symbol_table.lookup(func_name)
                     # The type of a function call expression is the function's return type
                     result_type = getattr(symbol, 'data_type', None) if symbol else None

        # print(f"[DEBUG get_expression_type] Returning type: {result_type}") # Uncomment for deep debug
        return result_type

    def _format_token_sequence(self, tokens_to_format):
        """
        Helper to format a sequence of tokens into C code with basic spacing rules.
        Attempts to add spaces between tokens where appropriate (e.g., between
        identifiers and operators) but not around punctuation like '.', '(', '[', etc.
        """
        parts = []
        if not tokens_to_format: return ""

        for i, (tok_type, tok_val) in enumerate(tokens_to_format):
             needs_space = False
             # Check if a space is needed before the current token
             if parts:
                 last_part = parts[-1] # Get the last part added to the result

                 # Add a space if the current token is not punctuation that attaches to the previous token
                 # and the last part is not punctuation that attaches to the current token.
                 # Avoid space before ')', ']', '.', ';', ','
                 if tok_type not in [')', ']', '.', ';', ',']:
                      # Avoid space after '(', '[', '.'
                      if not last_part.endswith(('(', '[', '.')):
                           # Avoid space between alphanumeric/closing-paren/bracket and opening-paren/bracket (function calls, array access)
                           if not ((last_part.isalnum() or last_part.endswith((')', ']'))) and tok_type in ['(', '[']):
                                # Avoid space before '++' or '--' if preceded by alphanumeric
                                if not (tok_type in ['++', '--'] and last_part.isalnum()):
                                     # In most other cases, add a space
                                     needs_space = True

             # Add a space if needed
             if needs_space: parts.append(" ")

             # Add the formatted token value
             parts.append(self.format_token(tok_type, tok_val))

        # Join all parts into a single string
        return "".join(parts)

    def _process_comparison_segment(self, segment_tokens):
        """
        Processes a segment of tokens (typically between logical operators)
        to handle comparisons, especially string comparisons using strcmp.
        Finds the first top-level comparison operator and splits the segment.
        """
        if not segment_tokens: return ""

        comparison_index = -1
        paren_level = 0
        bracket_level = 0
        comparison_ops = ['==', '!=', '<', '>', '<=', '>='] # List of comparison operators

        # Iterate through the tokens to find a top-level comparison operator
        for idx, (tok_type, _) in enumerate(segment_tokens):
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            elif tok_type == '[': bracket_level += 1
            elif tok_type == ']': bracket_level -= 1
            # If the token is a comparison operator and we are at the top level (outside parens/brackets)
            elif paren_level == 0 and bracket_level == 0 and tok_type in comparison_ops:
                comparison_index = idx # Found the operator
                break # Stop at the first top-level comparison operator

        # If a comparison operator was found
        if comparison_index != -1:
            op_tok_type = segment_tokens[comparison_index][0] # Get the type of the operator
            left_operand_tokens = segment_tokens[:comparison_index] # Tokens before the operator
            right_operand_tokens = segment_tokens[comparison_index + 1:] # Tokens after the operator

            # Determine the types of the left and right operands
            left_type = self.get_expression_type(left_operand_tokens)
            right_type = self.get_expression_type(right_operand_tokens)

            # If both operands are strings and the operator is == or !=, use strcmp
            if left_type == 'strng' and right_type == 'strng' and op_tok_type in ['==', '!=']:
                # Convert operands to C expressions
                left_c = self._tokens_to_c_expression(left_operand_tokens)
                right_c = self._tokens_to_c_expression(right_operand_tokens)
                # Determine the C comparison operator based on the Conso operator
                op_str = "==" if op_tok_type == '==' else "!="
                # Generate the C code using strcmp
                return f"(strcmp({left_c}, {right_c}) {op_str} 0)"
            else:
                # For non-string or other comparison operators, generate standard C comparison
                left_c = self._tokens_to_c_expression(left_operand_tokens)
                right_c = self._tokens_to_c_expression(right_operand_tokens)
                # Combine the C expressions with the operator
                if left_c and right_c: return f"{left_c} {op_tok_type} {right_c}"
                elif left_c: return f"{left_c} {op_tok_type}" # Handle unary operators if needed (though not typical for comparison)
                elif right_c: return f"{op_tok_type} {right_c}" # Handle unary operators
                else: return f"{op_tok_type}" # Should not happen for binary operators

        else:
            # If no top-level comparison operator was found, format the segment as a simple sequence of tokens
            return self._format_token_sequence(segment_tokens)

    def _tokens_to_c_expression(self, tokens):
        """
        Converts a list of (type, value) tokens representing an expression
        into a C expression string.
        Handles operator precedence by splitting first by logical operators (&&, ||),
        then processing each segment for comparisons (using _process_comparison_segment),
        and finally formatting the remaining tokens within segments.
        Also replaces boolean literals 'tr' and 'fls' with '1' and '0'.
        """
        if not tokens: return ""

        segments = [] # List to hold token lists for segments separated by logical operators
        operators = [] # List to hold the logical operators (&&, ||)
        current_start = 0 # Index to track the start of the current segment

        paren_level = 0
        bracket_level = 0

        # Iterate through tokens to split by top-level logical operators (&&, ||)
        for i, (tok_type, _) in enumerate(tokens):
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            elif tok_type == '[': bracket_level += 1
            elif tok_type == ']': bracket_level -= 1
            # If a logical operator is found at the top level
            elif paren_level == 0 and bracket_level == 0 and tok_type in ['&&', '||']:
                # Add the tokens from the current segment to the segments list
                segments.append(tokens[current_start:i])
                # Add the operator to the operators list
                operators.append(tok_type)
                # Update the start index for the next segment
                current_start = i + 1

        # Add the last segment after the loop finishes
        segments.append(tokens[current_start:])

        # Process each segment to handle comparisons within it
        processed_segments = [self._process_comparison_segment(segment) for segment in segments]

        # Reconstruct the full C expression by joining the processed segments with the logical operators
        result_parts = []
        if processed_segments:
            result_parts.append(processed_segments[0]) # Add the first processed segment
            # Add the operators and the subsequent processed segments
            for i, op in enumerate(operators):
                result_parts.append(f" {op} ") # Add the operator with spacing
                result_parts.append(processed_segments[i+1]) # Add the next processed segment

        # Join all parts into a single string
        result = "".join(result_parts)

        # Replace Conso boolean literals ('tr', 'fls') with C equivalents ('1', '0')
        result = self._replace_bool_literals(result)

        return result

    def _replace_bool_literals(self, text):
        """
        Replaces whole-word occurrences of 'tr' and 'fls' with '1' and '0'
        using regular expressions to avoid replacing substrings.
        """
        # Replace 'tr' only when it's a whole word
        text = re.sub(r'\btr\b', '1', text)
        # Replace 'fls' only when it's a whole word
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

            # print(f"\n[DEBUG _process_print] Processing arg tokens: {arg_tokens}") # DEBUG

            token_pairs = [(self._get_token_info(t)[0], self._get_token_info(t)[1]) for t in arg_tokens]
            arg_c_expr = self._tokens_to_c_expression(token_pairs)

            fmt = None

            # --- Universal Type Checking using get_expression_type ---
            expression_result_type = self.get_expression_type(token_pairs)
            # print(f"[DEBUG _process_print] Determined type: {expression_result_type}") # DEBUG

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

            # print(f"[DEBUG _process_print] Final format specifier: {fmt}") # DEBUG
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

def transpile_from_tokens(token_list, symbol_table=None, function_scopes=None):
    # ... (implementation from previous step) ...
    if token_list:
         last_token = token_list[-1]
         temp_transpiler = ConsoTranspilerTokenBased([])
         token_type, _, _ = temp_transpiler._get_token_info(last_token)
         if token_type == 'EOF':
              token_list = token_list[:-1]
    transpiler = ConsoTranspilerTokenBased(token_list, symbol_table, function_scopes)
    try:
        return transpiler.transpile()
    except TranspilerError as e:
        print(f"Transpilation Error: {e}", file=sys.stderr)
        return f"// TRANSPILER ERROR: {e}"
    except Exception as e:
        print(f"Unexpected Transpiler Error: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
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
        # Example input statement inside main
        ('nt', 'nt', 15, 5), ('id', 'userInput', 15, 8), (';', ';', 15, 17), # Declare var
        ('id', 'userInput', 16, 5), ('=', '=', 16, 15), ('npt', 'npt', 16, 17), ('(', '(', 16, 20), ('strnglit', 'Enter value: ', 16, 21), (')', ')', 16, 36), (';', ';', 16, 37), # Input statement
        ('end', 'end', 17, 7), (';', ';', 17, 10),
        # ('}', '}', 18, 1) # No closing brace for mn if using end;
    ]


    print("--- Transpiling User's Conso Code from Tokens ---")
    # Pass None for symbol_table for now
    generated_c_code = transpile_from_tokens(test_token_list, None) # Use token-based function
    print("\n--- Generated C Code ---")
    print(generated_c_code)
