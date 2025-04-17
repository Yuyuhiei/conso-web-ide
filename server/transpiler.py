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
        """
        Processes declaration statement from tokens.
        Handles array initializers. Assigns default values ONLY to non-array variables
        if assign_default is True and no explicit initializer is provided.
        Arrays are NOT initialized by default.
        """
        type_token = self._consume()
        conso_type = type_token[0]
        c_type = self.type_mapping.get(conso_type, conso_type)
        processed_decls = []

        while True: # Loop for comma-separated parts (e.g., nt x, y=1;)
            _, var_name, token_full = self._consume('id')
            array_suffix = ""
            initializer_tokens = None
            is_array = False
            line_num = self._get_token_info(token_full)[2]

            # Parse array dimensions
            dimensions = [] # Store dimensions for potential later use if needed
            if self._peek() == '[':
                is_array = True
                # Process each dimension
                while self._peek() == '[':
                    self._consume('[')
                    size_tokens = []
                    while self._peek() != ']':
                        if self._peek() is None:
                            raise TranspilerError("Unterminated array size", line_num)
                        # Consume token and store its value
                        size_tok_type, size_tok_val, _ = self._consume()
                        # Convert boolean literals if necessary for size expression
                        if size_tok_type == 'blnlit':
                             size_tokens.append(self.bool_mapping.get(size_tok_val, '0'))
                        else:
                             size_tokens.append(str(size_tok_val)) # Ensure value is string

                    self._consume(']')
                    dimension_expr = "".join(size_tokens)
                    dimensions.append(dimension_expr) # Store the expression/value
                    array_suffix += f"[{dimension_expr}]"

            # Get default value based on type (only used for non-arrays now)
            default_val = self.default_values.get(conso_type, "0")

            # Handle explicit initializer
            if self._peek() == '=':
                self._consume('=')
                initializer_tokens = []
                brace_level = 0
                paren_level = 0 # Track parentheses within initializer if needed

                # Collect all tokens belonging to the initializer expression
                while True:
                    next_token_type = self._peek()
                    if next_token_type is None:
                        raise TranspilerError("Unterminated initializer", line_num)

                    # Stop if we hit the end of the declaration part (',' or ';')
                    # at the top level (outside braces/parentheses)
                    if (next_token_type == ',' or next_token_type == ';') and brace_level == 0 and paren_level == 0:
                        break

                    tok_type, tok_val, token_full = self._consume()
                    initializer_tokens.append((tok_type, tok_val)) # Store as (type, value)

                    # Track nesting level for braces and parentheses
                    if tok_type == '{': brace_level += 1
                    elif tok_type == '}': brace_level -= 1
                    elif tok_type == '(': paren_level += 1
                    elif tok_type == ')': paren_level -= 1

                    # Basic error check for mismatched braces/parentheses
                    if brace_level < 0 or paren_level < 0:
                         raise TranspilerError("Mismatched braces/parentheses in initializer", line_num)


                # Convert collected tokens to C expression string
                init_str = self._tokens_to_c_expression(initializer_tokens)
                c_decl_part = f"{c_type} {var_name}{array_suffix} = {init_str}"

            else:
                # No explicit initializer provided
                if is_array:
                    # *** MODIFIED PART ***
                    # Arrays are NOT initialized by default. Just declare them.
                    c_decl_part = f"{c_type} {var_name}{array_suffix}"
                else:
                    # Regular (non-array) variable without initializer
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
                break # End of the declaration statement
            elif self._peek() == ',':
                self._consume(',')
                # Continue loop for the next variable in the list
            else:
                # If neither ';' nor ',' follows, it might be an error or just the end
                # of the input in some contexts. We break assuming the statement ends.
                # A more robust parser might raise an error here if ';' is strictly required.
                # print(f"Warning: Missing ; or , after declaration part near line {line_num}?")
                break # Assume end of statement if unexpected token

        # Join all parts of the declaration (if multiple variables were declared)
        # and add the final semicolon.
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
        function calls, and expressions.
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
                        # Check for logical operators (also results in int)
                        has_logical_op = any(self._get_token_info(t)[0] in ['&&', '||'] for t in arg_tokens)
                        if has_logical_op:
                            fmt = "%d"
                        else:
                            # Check if expression contains a double literal
                            has_double_literal = any(self._get_token_info(t)[0] in ['dbllit', 'NEGDOUBLELIT'] for t in arg_tokens)
                            if has_double_literal:
                                fmt = "%.2f"
                            # Add more checks if needed (e.g., arithmetic operations)


            # 4. Default format specifier if none of the above matched
            if fmt is None:
                # If it's a known string variable/literal/return type somehow missed, default to %s? Risky.
                # Stick to defaulting to %d for unknown complex types or potential integers.
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

    # Helper method needed by _tokens_to_c_expression
    def format_token(self, tok_type, tok_val):
        """Formats a single token into its C string representation."""
        if tok_type == 'blnlit': return self.bool_mapping.get(tok_val, '0')
        elif tok_type == 'strnglit': return f'"{tok_val}"'
        elif tok_type == 'chrlit': return f"'{tok_val}'"
        else: return str(tok_val)

    # Helper method needed by _tokens_to_c_expression
    def get_expression_type(self, expr_tokens):
        """
        Determines the resulting C type of an expression represented by tokens.
        Relies on symbol table lookup. Simplified version.
        """
        if not expr_tokens: return None

        # Handle simple literals directly
        if len(expr_tokens) == 1:
            tok_type, tok_val = expr_tokens[0]
            if tok_type == 'strnglit': return 'strng'
            if tok_type == 'chrlit': return 'chr'
            if tok_type in ['dbllit', 'NEGDOUBLELIT']: return 'dbl'
            if tok_type in ['ntlit', 'NEGINTLIT']: return 'nt'
            if tok_type == 'blnlit': return 'bln' # Represents underlying int
            if tok_type == 'id':
                # Look up variable in symbol table
                if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                    symbol = self.symbol_table.lookup(tok_val)
                    return getattr(symbol, 'data_type', None) if symbol else None
                return None # Cannot determine type

        # Check for array access: id [ ... ] -> type is element type
        if len(expr_tokens) >= 3 and expr_tokens[0][0] == 'id' and expr_tokens[1][0] == '[':
             base_var_name = expr_tokens[0][1]
             if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                 symbol = self.symbol_table.lookup(base_var_name)
                 # data_type of the array symbol itself (e.g., 'nt' for 'nt num[3]')
                 return getattr(symbol, 'data_type', None) if symbol else None
             return None

        # Check for struct access: ... . id -> type is member type
        if len(expr_tokens) >= 3 and expr_tokens[-1][0] == 'id' and expr_tokens[-2][0] == '.':
             member_name = expr_tokens[-1][1]
             # Try simple id.id pattern first
             if len(expr_tokens) == 3 and expr_tokens[0][0] == 'id':
                 struct_var_name = expr_tokens[0][1]
                 if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                     struct_var_symbol = self.symbol_table.lookup(struct_var_name)
                     if struct_var_symbol and hasattr(struct_var_symbol, 'data_type'):
                         struct_type_name = struct_var_symbol.data_type
                         struct_def_symbol = self.symbol_table.lookup(struct_type_name)
                         if struct_def_symbol and hasattr(struct_def_symbol, 'members') and hasattr(struct_def_symbol.members, 'get'):
                             member_symbol = struct_def_symbol.members.get(member_name)
                             if member_symbol: return getattr(member_symbol, 'data_type', None)
             # Fallback: Cannot easily determine type for complex chains like expr.member
             return None

        # Check for function call: id ( ... ) -> type is return type
        if len(expr_tokens) >= 2 and expr_tokens[0][0] == 'id' and expr_tokens[1][0] == '(':
             func_name = expr_tokens[0][1]
             if self.symbol_table and hasattr(self.symbol_table, 'lookup'):
                 symbol = self.symbol_table.lookup(func_name)
                 # Return type is usually stored in data_type for function symbols
                 return getattr(symbol, 'data_type', None) if symbol else None
             return None

        # --- Default type determination based on operators/literals ---
        # If contains comparison/logical ops, result is boolean (int)
        if any(t[0] in ['==', '!=', '<', '>', '<=', '>=', '&&', '||'] for t in expr_tokens):
            return 'bln' # Representing int 0 or 1
        # If contains floating point literals or division, likely double
        if any(t[0] in ['dbllit', 'NEGDOUBLELIT', '/'] for t in expr_tokens):
             # Assume double for safety if division or float literal exists
             return 'dbl'

        # Default to integer if no other type indication
        return 'nt'

    # Helper method needed by _tokens_to_c_expression
    def _format_token_sequence(self, tokens_to_format):
        """Helper to format a sequence of tokens into C code with spacing."""
        parts = []
        if not tokens_to_format: return "" # Handle empty list

        for i, (tok_type, tok_val) in enumerate(tokens_to_format):
             needs_space = False
             if parts: # Check if not the first token
                 last_part = parts[-1]
                 # Basic heuristic: Add space unless current or previous token is punctuation/grouping
                 if tok_type not in [')', ']', '.', ';', ',', '(', '[', '++', '--'] and \
                    not last_part.endswith(('(', '[', '.')) and \
                    tok_type != '.': # Avoid space before dot
                      # Avoid space before '(' or '[' if preceded by identifier/')'/']' (func call/array index)
                      if not ((last_part.isalnum() or last_part.endswith((')', ']'))) and tok_type in ['(', '[']):
                           # Avoid space after unary operators like '!' if needed (more complex)
                           # Avoid space before postfix ++/--
                           if not (tok_type in ['++', '--'] and last_part.isalnum()):
                                needs_space = True

             if needs_space: parts.append(" ")
             # Use the helper method to format the token value correctly
             parts.append(self.format_token(tok_type, tok_val))
        return "".join(parts)

    # Helper method needed by _tokens_to_c_expression
    def _process_comparison_segment(self, segment_tokens):
        """
        Processes a segment of tokens (typically between logical operators)
        to handle comparisons, especially string comparisons using strcmp.
        """
        if not segment_tokens: return ""

        # Find the first top-level comparison operator (==, !=) in this segment
        comparison_index = -1
        paren_level = 0
        bracket_level = 0
        for idx, (tok_type, _) in enumerate(segment_tokens):
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            elif tok_type == '[': bracket_level += 1
            elif tok_type == ']': bracket_level -= 1
            # Found comparison at the top level of this segment
            elif paren_level == 0 and bracket_level == 0 and tok_type in ['==', '!=']:
                comparison_index = idx
                break # Process the first one found in the segment

        if comparison_index != -1:
            # Found a comparison operator (== or !=)
            op_tok_type = segment_tokens[comparison_index][0]
            # Split tokens into left and right operands relative to the operator
            left_operand_tokens = segment_tokens[:comparison_index]
            right_operand_tokens = segment_tokens[comparison_index + 1:]

            # Determine the types of the operands using the helper method
            left_type = self.get_expression_type(left_operand_tokens)
            right_type = self.get_expression_type(right_operand_tokens)

            # Check if both operands resolved to string type
            if left_type == 'strng' and right_type == 'strng':
                # Both are strings: Generate strcmp expression
                # Recursively call _tokens_to_c_expression to get C code for operands
                left_c = self._tokens_to_c_expression(left_operand_tokens)
                right_c = self._tokens_to_c_expression(right_operand_tokens)
                # Determine C comparison operator based on Conso operator
                op_str = "==" if op_tok_type == '==' else "!="
                # Construct the strcmp call
                return f"(strcmp({left_c}, {right_c}) {op_str} 0)"
            else:
                # Not a string comparison (or types couldn't be determined):
                # Process operands recursively and join with the original operator
                left_c = self._tokens_to_c_expression(left_operand_tokens)
                right_c = self._tokens_to_c_expression(right_operand_tokens)
                # Ensure space around the operator
                return f"{left_c} {op_tok_type} {right_c}"
        else:
            # No comparison operator (==, !=) found in this segment.
            # This segment might contain other operators (<, +, etc.) or be a single term.
            # Format the sequence of tokens directly into C code.
            # This part needs to handle other operators correctly if they exist.
            # For now, use the basic sequence formatter.
            # TODO: Enhance this part to handle other operators if needed.
            return self._format_token_sequence(segment_tokens)
        
    def _tokens_to_c_expression(self, tokens):
        """
        Converts a list of (type, value) tokens into a C expression string.
        Handles operator precedence by splitting first by logical operators (&&, ||),
        then processing segments for comparisons (==, != with strcmp for strings),
        and finally formatting the remaining tokens.
        """
        if not tokens: return ""

        # Split by lowest precedence operators first (&&, ||)
        segments = [] # Stores lists of tokens for each segment
        operators = [] # Stores the '&&' or '||' operators between segments
        current_start = 0
        paren_level = 0
        bracket_level = 0

        for i, (tok_type, _) in enumerate(tokens):
            # Track nesting levels for parentheses and brackets
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            elif tok_type == '[': bracket_level += 1
            elif tok_type == ']': bracket_level -= 1
            # Split only at top-level logical operators (&&, ||)
            elif paren_level == 0 and bracket_level == 0 and tok_type in ['&&', '||']:
                # Add the segment of tokens before the operator
                segments.append(tokens[current_start:i])
                # Store the operator
                operators.append(tok_type)
                # Update the start position for the next segment
                current_start = i + 1

        # Add the final segment of tokens after the last operator (or the only segment)
        segments.append(tokens[current_start:])

        # Process each segment using the helper function that handles comparisons
        processed_segments = [self._process_comparison_segment(segment) for segment in segments]

        # Join the processed C code segments back together with the logical operators
        result_parts = [processed_segments[0]] # Start with the first processed segment
        for i, op in enumerate(operators):
            # Add the logical operator with spaces
            result_parts.append(f" {op} ")
            # Add the next processed segment
            result_parts.append(processed_segments[i+1])

        # Combine all parts into the final C expression string
        result = "".join(result_parts)

        # Final replacement of boolean literals (tr -> 1, fls -> 0)
        # This should happen after the structure is built.
        result = self._replace_bool_literals(result)
        return result

    def _replace_bool_literals(self, text):
        """Replaces whole-word 'tr' and 'fls' with '1' and '0'."""
        # Use regex for whole word replacement to avoid partial matches (e.g., 'true_flag')
        # Import 're' module if not already imported at the top of the file
        import re
        text = re.sub(r'\btr\b', '1', text)
        text = re.sub(r'\bfls\b', '0', text)
        return text
    





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
