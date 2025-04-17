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
    def __init__(self, token_list, symbol_table=None):
        self.tokens = token_list # Assumes NO EOF token is present in this list
        self.symbol_table = symbol_table
        self.current_pos = 0
        self.output_parts = []
        self.current_indent_level = 0

        # Mappings
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
        # --- UPDATED Default values ---
        self.default_values = {
            "nt": "0",
            "dbl": "0.00",
            "strng": "NULL", # Changed from "\"\"" to NULL
            "bln": "0",
            "chr": "'\\0'" # Changed from "'/'" to the null terminator character
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
            if is_struct_member:
                if token_type in self.type_mapping and token_type != 'dfstrct': return self._process_declaration_from_tokens(assign_default=False)
                else: print(f"Warning: Skipping non-declaration token '{token_type}' inside struct near line {line}"); self._consume(); return ""
            # --- Processing for global, function, or main scope ---
            if token_type == '{': self._consume(); return "{"
            if token_type == '}': self._consume(); return "}"
            if token_type in self.type_mapping and token_type != 'dfstrct': return self._process_declaration_from_tokens(assign_default=True)
            elif token_type == 'dfstrct': return self._process_dfstrct_from_tokens()
            # --- Statements only valid inside functions/main ---
            if is_global:
                 print(f"Error: Statement type '{token_type}' not allowed at global scope near line {line}")
                 while self._peek() not in [';', None]: self._skip_token()
                 if self._peek() == ';': self._skip_token()
                 return f"// ERROR: Statement type '{token_type}' not allowed at global scope"
            # --- Function/Main Scope Statements ---
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
            else: return self._process_other_statement_from_tokens()
        except TranspilerError as e:
             print(f"Error processing statement near line {e.line_num if e.line_num else line}: {e.message}")
             self.current_pos = start_pos # Try to reset position
             while self._peek() not in [';', '}', None]: self._skip_token() # Skip to likely end
             if self._peek() == ';': self._skip_token()
             return f"// ERROR: {e.message}"
        except Exception as e:
             # Safely get line number for unexpected errors
             err_line = '?'
             try: err_line = self._get_token_info(self.tokens[start_pos])[2]
             except: pass
             print(f"Unexpected error processing statement near line {err_line}: {e}")
             # import traceback; traceback.print_exc() # Uncomment for debug
             # Simple recovery: advance past current token if possible
             if self.current_pos == start_pos: self._skip_token()
             # More robust recovery might skip to next semicolon or brace
             # while self._peek() not in [';', '}', None]: self._skip_token()
             # if self._peek() == ';': self._skip_token()
             return f"// UNEXPECTED ERROR processing statement: {e}"


    # --- Token-Based Specific Statement Processors ---
    def _process_declaration_from_tokens(self, assign_default=True):
        """Processes declaration statement from tokens. Handles array initializers with default values."""
        type_token = self._consume(); conso_type = type_token[0]; c_type = self.type_mapping.get(conso_type, conso_type)
        processed_decls = []
        while True: # Loop for comma-separated parts (e.g., nt x, y=1;)
            _, var_name, token_full = self._consume('id'); array_suffix = ""; initializer_tokens = None; is_array = False
            line_num = self._get_token_info(token_full)[2]
            
            # Parse array dimensions
            dimensions = []
            if self._peek() == '[':
                is_array = True
                # Process each dimension
                while self._peek() == '[':
                    self._consume('[')
                    size_tokens = []
                    while self._peek() != ']':
                        if self._peek() is None: raise TranspilerError("Unterminated array size", line_num)
                        size_tok = self._consume()
                        size_tokens.append(size_tok[1])
                    self._consume(']')
                    
                    # Attempt to parse the size as an integer
                    try:
                        if isinstance(size_tokens[0], int):
                            dimensions.append(int(size_tokens[0]))
                        else:
                            # If it's not a simple integer (could be a variable name), just use it as is
                            dimensions.append(size_tokens[0])
                    except (ValueError, IndexError):
                        dimensions.append(''.join(map(str, size_tokens)))
                    
                    array_suffix += f"[{''.join(map(str, size_tokens))}]"
            
            # Get default value based on type
            default_val = self.default_values.get(conso_type, "0")
            
            # Handle initializer
            if self._peek() == '=':
                self._consume('=')
                
                # DEBUG: print statement to check token positions
                print(f"Processing initializer for {var_name} with dimensions {dimensions}")
                
                # Collect initializer tokens
                initializer_tokens = []
                brace_level = 0
                
                while True:
                    if self._peek() is None: 
                        raise TranspilerError("Unterminated initializer", line_num)
                    
                    # Check for end of initializer (comma or semicolon at top level)
                    if (self._peek() == ',' or self._peek() == ';') and brace_level == 0:
                        break
                    
                    # Get next token
                    tok_type, tok_val, _ = self._consume()
                    initializer_tokens.append((tok_type, tok_val))
                    
                    # Track nesting level
                    if tok_type == '{': brace_level += 1
                    elif tok_type == '}': brace_level -= 1
                
                # For 1D arrays with initializers, we need to ensure all elements have values
                if is_array and len(dimensions) == 1 and isinstance(dimensions[0], int) and assign_default:
                    # First convert tokens to C string to see what we have
                    init_str = self._tokens_to_c_expression(initializer_tokens)
                    
                    # DEBUG: print initializer string
                    print(f"Initial value for {var_name}: {init_str}")
                    
                    # Count the elements in the initializer
                    element_count = 0
                    current_level = 0
                    in_element = False
                    
                    # Basic parse of the initializer - this is a simplified approach
                    for tok_type, _ in initializer_tokens:
                        if tok_type == '{':
                            current_level += 1
                        elif tok_type == '}':
                            current_level -= 1
                            # When we reach the end of the outer array, add last element if needed
                            if current_level == 0 and in_element:
                                element_count += 1
                                in_element = False
                        elif tok_type == ',':
                            if current_level == 1:  # Only count commas at the first nesting level
                                if in_element:
                                    element_count += 1
                                    in_element = False
                        elif tok_type in ['ntlit', 'dbllit', 'chrlit', 'strnglit', 'blnlit', 'tr', 'fls', 'id'] and current_level == 1:
                            if not in_element:
                                in_element = True
                    
                    # DEBUG: print element count
                    print(f"Found {element_count} elements in initializer for {var_name}[{dimensions[0]}]")
                    
                    # If we have fewer elements than the array size, add default values
                    if element_count < dimensions[0]:
                        # Create array of default values
                        default_values = [default_val] * dimensions[0]
                        
                        # Extract actual values from initializer
                        actual_values = []
                        current_level = 0
                        current_element = ""
                        
                        for i, (tok_type, tok_val) in enumerate(initializer_tokens):
                            if tok_type == '{':
                                if current_level == 0:
                                    # Skip outer opening brace
                                    current_level += 1
                                    continue
                                else:
                                    current_level += 1
                                    current_element += '{'
                            elif tok_type == '}':
                                if current_level == 1:
                                    # End of outer array
                                    if current_element:
                                        actual_values.append(current_element)
                                    current_level -= 1
                                else:
                                    current_level -= 1
                                    current_element += '}'
                            elif tok_type == ',':
                                if current_level == 1:
                                    # Separator between elements
                                    if current_element:
                                        actual_values.append(current_element)
                                        current_element = ""
                                else:
                                    current_element += ','
                            else:
                                # Handle the actual value
                                if tok_type == 'blnlit':
                                    val = self.bool_mapping.get(tok_val, '0')
                                elif tok_type == 'chrlit':
                                    val = f"'{tok_val}'"
                                elif tok_type == 'strnglit':
                                    val = f'"{tok_val}"'
                                else:
                                    val = str(tok_val)
                                
                                if current_level >= 1:
                                    if not current_element:
                                        current_element = val
                                    else:
                                        current_element += val
                        
                        # Replace as many default values as we have actual values
                        for i, val in enumerate(actual_values):
                            if i < len(default_values):
                                default_values[i] = val
                        
                        # Create new initializer with all values
                        init_str = "{ " + ", ".join(default_values) + " }"
                    
                    c_decl_part = f"{c_type} {var_name}{array_suffix} = {init_str}"
                else:
                    # For non-arrays or multidimensional arrays, use the original initializer
                    init_str = self._tokens_to_c_expression(initializer_tokens)
                    c_decl_part = f"{c_type} {var_name}{array_suffix} = {init_str}"
            else:
                # No initializer - generate default values
                if is_array:
                    if assign_default:
                        # For 1D arrays, generate initializer with default values for all elements
                        if len(dimensions) == 1 and isinstance(dimensions[0], int):
                            init_values = ", ".join([default_val] * dimensions[0])
                            c_decl_part = f"{c_type} {var_name}{array_suffix} = {{{init_values}}}"
                        # For 2D arrays, generate nested initializers
                        elif len(dimensions) == 2 and all(isinstance(d, int) for d in dimensions):
                            row_init = ", ".join([default_val] * dimensions[1])
                            all_rows = ", ".join(["{" + row_init + "}"] * dimensions[0])
                            c_decl_part = f"{c_type} {var_name}{array_suffix} = {{{all_rows}}}"
                        else:
                            # For variable sized or higher dimension arrays, use simple initializer
                            c_decl_part = f"{c_type} {var_name}{array_suffix} = {{0}}"
                    else:
                        c_decl_part = f"{c_type} {var_name}{array_suffix}"
                else:
                    # Regular variable without initializer
                    if assign_default:
                        c_decl_part = f"{c_type} {var_name} = {default_val}"
                    else:
                        c_decl_part = f"{c_type} {var_name}"
            
            processed_decls.append(c_decl_part)
            
            # Check for end of declaration list
            if self._peek() == ';': self._consume(';'); break
            elif self._peek() == ',': self._consume(',')
            else:
                print(f"Warning: Missing ; or , after declaration near line {line_num}?"); break
        
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
        self._consume('prnt'); self._consume('('); arg_groups_tokens = []; current_arg_tokens = []; paren_level = 0
        
        # Handle empty print
        if self._peek() == ')':
            self._consume(')'); self._consume(';')
            return 'printf(""); fflush(stdout);'
        
        # Process arguments
        while not (self._peek() == ')' and paren_level == 0):
            if self._peek() is None: raise TranspilerError("Unexpected end of stream in print statement")
            tok_type, tok_val, token_full = self._consume()
            
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            
            if tok_type == ',' and paren_level == 0:
                if current_arg_tokens: arg_groups_tokens.append(current_arg_tokens)
                current_arg_tokens = []
            else: 
                current_arg_tokens.append(token_full)
        
        if current_arg_tokens: arg_groups_tokens.append(current_arg_tokens)
        self._consume(')'); self._consume(';')
        
        format_parts = []; c_args = []
        
        for arg_tokens in arg_groups_tokens:
            # Convert to C expression
            token_pairs = [(self._get_token_info(t)[0], self._get_token_info(t)[1]) for t in arg_tokens]
            arg_c_expr = self._tokens_to_c_expression(token_pairs)
            
            # Default format
            fmt = "%d"
            
            # Simple case: single token
            if len(arg_tokens) == 1:
                arg_type, arg_val = self._get_token_info(arg_tokens[0])[:2]
                
                if arg_type == 'strnglit': 
                    fmt = "%s"
                elif arg_type == 'chrlit': 
                    fmt = "%c"
                elif arg_type == 'dbllit' or arg_type == 'NEGDOUBLELIT': 
                    fmt = "%.2f"
                elif arg_type == 'ntlit' or arg_type == 'NEGINTLIT': 
                    fmt = "%d"
                elif arg_type == 'blnlit': 
                    fmt = "%d"  # Boolean as int
                elif arg_type == 'id':
                    # Variables
                    if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                        symbol_entry = self.symbol_table.lookup(arg_val)
                        if symbol_entry:
                            var_type = getattr(symbol_entry, 'data_type', None)
                            if var_type == 'strng': fmt = "%s"
                            elif var_type == 'dbl': fmt = "%.2f"
                            elif var_type == 'chr': fmt = "%c"
                            elif var_type == 'nt': fmt = "%d"
                            elif var_type == 'bln': fmt = "%d"
                            else: fmt = "%d"  # Default
            else:
                # Check for struct member access (id.id)
                has_struct_member = False
                for i in range(len(arg_tokens) - 2):
                    tok_type1 = self._get_token_info(arg_tokens[i])[0]
                    tok_type2 = self._get_token_info(arg_tokens[i+1])[0]
                    tok_type3 = self._get_token_info(arg_tokens[i+2])[0]
                    
                    if tok_type1 == 'id' and tok_type2 == '.' and tok_type3 == 'id':
                        has_struct_member = True
                        
                        # Get the struct instance and member names
                        struct_name = self._get_token_info(arg_tokens[i])[1]
                        member_name = self._get_token_info(arg_tokens[i+2])[1]
                        
                        # Try to get the type from symbol table
                        if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                            struct_symbol = self.symbol_table.lookup(struct_name)
                            if struct_symbol and hasattr(struct_symbol, 'data_type'):
                                struct_type = struct_symbol.data_type
                                struct_def = self.symbol_table.lookup(struct_type)
                                
                                if struct_def and hasattr(struct_def, 'members') and member_name in struct_def.members:
                                    member_type = struct_def.members[member_name].data_type
                                    
                                    if member_type == 'strng': fmt = "%s"
                                    elif member_type == 'dbl': fmt = "%.2f"
                                    elif member_type == 'chr': fmt = "%c"
                                    elif member_type == 'nt': fmt = "%d"
                                    elif member_type == 'bln': fmt = "%d"
                        
                        break
                
                # Check for function call (id followed by parenthesis)
                if not has_struct_member:
                    has_function_call = False
                    for i in range(len(arg_tokens) - 1):
                        if self._get_token_info(arg_tokens[i])[0] == 'id' and self._get_token_info(arg_tokens[i+1])[0] == '(':
                            has_function_call = True
                            
                            # Get function name
                            func_name = self._get_token_info(arg_tokens[i])[1]
                            
                            # Try to get return type from symbol table
                            if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                                func_symbol = self.symbol_table.lookup(func_name)
                                if func_symbol and hasattr(func_symbol, 'data_type'):
                                    return_type = func_symbol.data_type
                                    
                                    if return_type == 'strng': fmt = "%s"
                                    elif return_type == 'dbl': fmt = "%.2f"
                                    elif return_type == 'chr': fmt = "%c"
                                    elif return_type == 'nt': fmt = "%d"
                                    elif return_type == 'bln': fmt = "%d"
                            
                            break
                
                # If not struct member or function call, look for logical operators and comparisons
                if not has_struct_member and not has_function_call:
                    if any(self._get_token_info(t)[0] in ['&&', '||'] for t in arg_tokens):
                        # Logical expressions result in boolean (int)
                        fmt = "%d"
                    elif any(self._get_token_info(t)[0] in ['==', '!='] for t in arg_tokens):
                        # Equality checks result in boolean (int)
                        fmt = "%d"
                    elif 'dbl' in [self._get_token_info(t)[0] for t in arg_tokens] or '.' in arg_c_expr:
                        fmt = "%.2f"
            
            # Add format and argument
            format_parts.append(fmt)
            c_args.append(arg_c_expr)
        
        # Generate printf statement
        format_str = " ".join(format_parts)
        return f'printf("{format_str}", {", ".join(c_args)}); fflush(stdout);'
    
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
        """Process input statement (varname = npt("prompt");) with type-based handling"""
        # Get the variable name being assigned
        _, var_name, _ = self._consume('id')
        self._consume('=')
        self._consume('npt')
        self._consume('(')
        
        # Get the prompt string if present
        prompt = ""
        if self._peek() == 'strnglit':
            prompt = self._consume('strnglit')[1]
        
        self._consume(')')
        self._consume(';')
        
        # Determine variable type using symbol table
        var_type = 'strng'  # Default to string if type can't be determined
        array_size = 100    # Default size for string buffers
        is_array = False
        
        if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
            symbol = self.symbol_table.lookup(var_name)
            if symbol:
                var_type = getattr(symbol, 'data_type', 'strng')
                is_array = getattr(symbol, 'is_array', False)
                # If it's an array, try to get the size
                if is_array and hasattr(symbol, 'array_sizes') and symbol.array_sizes:
                    if isinstance(symbol.array_sizes[0], int):
                        array_size = symbol.array_sizes[0]
        
        # Generate appropriate input code based on type
        c_code = []
        
        # Always print the prompt
        if prompt:
            c_code.append(f'printf("{prompt}");')
        
        # Generate type-specific input code
        if var_type == 'nt':
            # Integer input
            c_code.append(f'scanf("%d", &{var_name});')
            c_code.append('getchar(); // Consume newline')
        elif var_type == 'dbl':
            # Double input
            c_code.append(f'scanf("%lf", &{var_name});')
            c_code.append('getchar(); // Consume newline')
        elif var_type == 'chr':
            # Character input
            c_code.append(f'{var_name} = getchar();')
            c_code.append('getchar(); // Consume newline if present')
        elif var_type == 'bln':
            # Boolean input - read as int
            c_code.append(f'{{ int temp; scanf("%d", &temp); {var_name} = temp != 0; }}')
            c_code.append('getchar(); // Consume newline')
        else:
            # String input (default)
            if is_array:
                # For array variables, use fgets directly
                c_code.append(f'fgets({var_name}, sizeof({var_name}), stdin);')
                # Remove trailing newline if present
                c_code.append(f'{{ char *p = strchr({var_name}, \'\\n\'); if(p) *p = 0; }}')
            else:
                # For regular char* variables, allocate buffer, read, and assign
                c_code.append(f'{{ char buffer[{array_size}]; fgets(buffer, {array_size}, stdin);')
                c_code.append('char *p = strchr(buffer, \'\\n\'); if(p) *p = 0;')
                c_code.append(f'{var_name} = strdup(buffer); }}')
        
        return ' '.join(c_code)

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

    def _tokens_to_c_expression(self, tokens):
        """Converts a list of (type, value) tokens into a C expression string."""
        # We need a recursive approach to handle complex expressions
        
        # Extract potential string comparison subexpressions first
        def process_subexpression(start, end):
            """Process a subexpression, handling string comparisons."""
            # Look for string comparison expressions
            for i in range(start, end-1):
                if tokens[i][0] in ['==', '!=']:
                    # Check if both sides are strings
                    if i > start and i < end-1:
                        left_idx = i-1
                        right_idx = i+1
                        left_type, left_val = tokens[left_idx]
                        right_type, right_val = tokens[right_idx]
                        
                        # Determine if both operands are strings
                        left_is_string = left_type == 'strnglit'
                        right_is_string = right_type == 'strnglit'
                        
                        # Check variables in symbol table
                        if left_type == 'id' and self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                            symbol = self.symbol_table.lookup(left_val)
                            if symbol and getattr(symbol, 'data_type', None) == 'strng':
                                left_is_string = True
                        
                        if right_type == 'id' and self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                            symbol = self.symbol_table.lookup(right_val)
                            if symbol and getattr(symbol, 'data_type', None) == 'strng':
                                right_is_string = True
                        
                        # If both are strings, replace with strcmp
                        if left_is_string and right_is_string:
                            # Format the operands
                            left_expr = format_token(left_type, left_val)
                            right_expr = format_token(right_type, right_val)
                            
                            # Create the strcmp expression
                            op = tokens[i][0]
                            if op == '==':
                                return f"(strcmp({left_expr}, {right_expr}) == 0)"
                            else:  # !=
                                return f"(strcmp({left_expr}, {right_expr}) != 0)"
            
            # If no string comparison, format normally
            parts = []
            for i in range(start, end):
                tok_type, tok_val = tokens[i]
                
                # Add spacing between tokens if needed
                if parts and tok_type not in [')', ']', '.', ';', ',', '++', '--'] and parts[-1][-1] not in ['(', '[', '.']:
                    if not (parts[-1].endswith('id') and tok_type == '('):  # No space for function calls
                        parts.append(" ")
                
                # Format the token
                parts.append(format_token(tok_type, tok_val))
            
            return "".join(parts)
        
        def format_token(tok_type, tok_val):
            """Format a single token based on its type."""
            if tok_type == 'blnlit':
                return self.bool_mapping.get(tok_val, '0')
            elif tok_type == 'strnglit':
                return f'"{tok_val}"'
            elif tok_type == 'chrlit':
                return f"'{tok_val}'"
            elif tok_val in self.keyword_mapping:
                return self.keyword_mapping[tok_val]
            else:
                return str(tok_val)
        
        # Split the expression into logical segments (&&, ||)
        segments = []
        current_start = 0
        paren_level = 0
        
        for i, (tok_type, tok_val) in enumerate(tokens):
            if tok_type == '(':
                paren_level += 1
            elif tok_type == ')':
                paren_level -= 1
            
            # Only split at top-level logical operators
            if paren_level == 0 and tok_type in ['&&', '||']:
                # Process the segment before the operator
                segments.append(process_subexpression(current_start, i))
                segments.append(tok_type)  # Add the operator
                current_start = i + 1
        
        # Add the final segment
        if current_start < len(tokens):
            segments.append(process_subexpression(current_start, len(tokens)))
        
        # Join segments
        result = "".join(segments)
        
        # Replace boolean literals again as whole words
        result = self._replace_bool_literals(result)
        return result


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

def transpile_from_tokens(token_list, symbol_table=None):
    """
    Transpiles Conso code from a token list using the token-based transpiler.
    """
    # Remove EOF token before passing to transpiler if present
    if token_list:
         last_token = token_list[-1]
         token_type, _, _ = ConsoTranspilerTokenBased(token_list)._get_token_info(last_token) # Use helper to get type
         if token_type == 'EOF':
              print("Info: Removing EOF token before transpilation.")
              token_list = token_list[:-1]

    transpiler = ConsoTranspilerTokenBased(token_list, symbol_table)
    try:
        return transpiler.transpile()
    except TranspilerError as e:
        print(f"Transpilation Error: {e}", file=sys.stderr)
        return f"// TRANSPILER ERROR: {e}"
    except Exception as e:
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
