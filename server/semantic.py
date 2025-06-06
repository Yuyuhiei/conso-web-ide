from lexer import Lexer

class SemanticError(Exception): 
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message 
        self.line = line
        self.column = column

    def __str__(self):
        if self.line is not None and self.column is not None:
            return f"Semantic Error at line {self.line}, column {self.column}: {self.message}"
        return f"Semantic Error: {self.message}"

class Symbol:
    def __init__(self, name, type, data_type=None, initialized=False, is_constant=False, 
                is_array=False, array_dimensions=None, array_sizes=None, line=None, column=None):
        self.name = name
        self.type = type  # 'variable', 'function', 'struct'
        self.data_type = data_type  # 'nt', 'dbl', 'bln', 'chr', 'strng'
        self.initialized = initialized
        self.is_constant = is_constant
        self.is_array = is_array
        self.array_dimensions = array_dimensions  # 1 for 1D, 2 for 2D
        self.array_sizes = array_sizes  # [size] for 1D, [size1, size2] for 2D
        self.line = line 
        self.column = column
        # New attribute to track initialized members of struct instances
        self.initialized_members = set() if type == 'struct_instance' else None

    def __str__(self):
        status = "initialized" if self.initialized else "uninitialized"
        constant = "constant " if self.is_constant else ""
        array_info = ""
        if self.is_array:
            if self.array_dimensions == 1:
                array_info = f"[{self.array_sizes[0]}]"
            elif self.array_dimensions == 2:
                array_info = f"[{self.array_sizes[0]}][{self.array_sizes[1]}]"
        
        location = f"(line {self.line}, col {self.column})" if self.line and self.column else ""
        return f"{self.name}: {constant}{self.type} {self.data_type}{array_info} ({status}) {location}"

class FunctionSymbol(Symbol):
    def __init__(self, name, return_type, parameters=None, line=None, column=None):
        super().__init__(name, 'function', return_type, True, False, False, None, None, line, column)
        self.parameters = parameters or []
        self.has_return_statement = False  # Track if function has a return statement
        # ADDED: To store start index of function body tokens (index AFTER '{')
        self.body_start_index = None

    def __str__(self):
        params = [f"{param.data_type} {param.name}" for param in self.parameters]
        params_str = ", ".join(params)
        location = f"(line {self.line}, col {self.column})" if self.line and self.column else ""
        # Indicate if body start index is set (for debugging)
        body_info = f" [Body Start Idx: {self.body_start_index}]" if self.body_start_index is not None else ""
        return f"{self.name}: {self.type} returns {self.data_type} ({params_str}) {location}{body_info}"

# Add this class after FunctionSymbol
class StructSymbol(Symbol):
    def __init__(self, name, members=None, line=None, column=None):
        super().__init__(name, 'struct', None, True, False, False, None, None, line, column)
        self.members = members or {}  # Dict of member name -> Symbol

    def __str__(self):
        member_str = ", ".join([f"{symbol.data_type} {name}" for name, symbol in self.members.items()])
        location = f"(line {self.line}, col {self.column})" if self.line and self.column else ""
        return f"{self.name}: {self.type} members: {{{member_str}}} {location}"

class SymbolTable:
    def __init__(self, parent=None, scope_name="global"):
        self.symbols = {}
        self.parent = parent
        self.scope_name = scope_name

    def insert(self, name, symbol):
        if name in self.symbols:
            return False
        self.symbols[name] = symbol
        return True

    def lookup(self, name):
        # First check in current scope
        if name in self.symbols:
            return self.symbols[name]
        
        # If not found in current scope and this is a function scope,
        # check directly in global scope (skip any intermediate scopes)
        if self.scope_name.startswith("function "):
            # We're in a function scope, check global scope directly
            global_scope = None
            
            # Find the global scope
            temp_scope = self
            while temp_scope.parent:
                temp_scope = temp_scope.parent
            global_scope = temp_scope
            
            # Check in global scope
            if name in global_scope.symbols:
                print(f"Found '{name}' in global scope from function scope '{self.scope_name}'")
                return global_scope.symbols[name]
        
        # Normal parent lookup
        if self.parent:
            return self.parent.lookup(name)
        
        return None

    def print_table(self, indent=0):
        """Print the contents of the symbol table"""
        indent_str = "  " * indent
        print(f"{indent_str}=== Symbol Table: {self.scope_name} ===")
        
        if not self.symbols:
            print(f"{indent_str}  (empty)")
            return

        # Print all symbols in current scope
        for name, symbol in sorted(self.symbols.items()):
            print(f"{indent_str}  {symbol}")

class SemanticAnalyzer:
    def __init__(self):
        self.current_token_index = 0
        self.token_stream = []
        self.current_scope = None
        self.global_scope = SymbolTable(scope_name="global")
        self.function_scopes = {}  # Map function name to its SymbolTable
        
        # Define valid data types
        self.data_types = {'nt', 'dbl', 'bln', 'chr', 'strng'}
        
        # Define valid operators
        self.arithmetic_operators = {'+', '-', '*', '/', '%'}
        self.logical_operators = {'&&', '||'}
        self.relational_operators = {'<', '>', '<=', '>=', '==', '!='}
        self.equality_operators = {'==', '!='}  # Subset of relational that works for all types
        self.assignment_operators = {'='}
        self.unary_operators = {'!'}
        self.string_concat_operator = {'`'}
        
        # Define built-in functions
        self.built_in_functions = {'prnt', 'scan', 'len', 'npt'}
    
        # Add struct-related keywords
        self.struct_keywords = {'strct', 'dfstrct'}
    
        # Add these tracking flags
        self.in_loop = False
        self.in_switch = False
        self.in_case_block = False  # New flag to track if we're inside a case/default block

    def print_symbol_tables(self):
        """Print all symbol tables in the current scope hierarchy, including function scopes"""
        print("\nSymbol Table Contents:")
        print("=====================")
        
        # Print global scope hierarchy
        current = self.current_scope
        scopes = []
        while current:
            scopes.insert(0, current)
            current = current.parent
        for i, scope in enumerate(scopes):
            scope.print_table(indent=i)

        # Print all function scopes (including main)
        if hasattr(self, "function_scopes"):
            for func_name, func_scope in self.function_scopes.items():
                print(f"\n=== Symbol Table: {func_scope.scope_name} ===")
                func_scope.print_table(indent=1)
            
    # --- Modified collect_declarations ---
    def collect_declarations(self):
        """First pass: Collect struct definitions and function signatures (including main)."""
        print("Collecting declarations (Pass 1)...")
        original_index = self.current_token_index # Save entry index (usually 0)
        temp_index = 0 # Use a temporary index to scan the entire stream

        while temp_index < len(self.token_stream):
            # Set current_token_index temporarily for analysis functions
            self.current_token_index = temp_index
            token_type, token_value, line, column = self.get_current_token()

            if token_type == 'fnctn':
                func_name = "unknown"
                if temp_index + 2 < len(self.token_stream):
                     name_token = self.token_stream[temp_index + 2]
                     if name_token[0] == 'id': func_name = name_token[1]
                print(f"Pass 1: Found 'fnctn' for '{func_name}' at index {temp_index}.")
                self.analyze_function_declaration(is_first_pass=True)
                temp_index = self.current_token_index
                print(f"Pass 1: After skipping '{func_name}', temp_index is now {temp_index}.")
                continue

            elif token_type == 'strct':
                struct_name = "unknown"
                if temp_index + 1 < len(self.token_stream):
                     name_token = self.token_stream[temp_index + 1]
                     if name_token[0] == 'id': struct_name = name_token[1]
                print(f"Pass 1: Found 'strct' for '{struct_name}' at index {temp_index}.")
                self.analyze_struct_declaration()
                temp_index = self.current_token_index
                print(f"Pass 1: After processing '{struct_name}', temp_index is now {temp_index}.")
                continue

            # --- ADDED: Handle 'mn' signature collection in Pass 1 ---
            elif token_type == 'mn':
                print(f"Pass 1: Found 'mn' function declaration at index {temp_index}.")
                mn_line, mn_col = line, column
                # --- Start: Skipping mn() { signature ---
                # We need to advance self.current_token_index to find body start
                # and then update temp_index to after the skipped body
                saved_scan_index = self.current_token_index # Save index at 'mn'
                self.advance() # Past 'mn'

                # Check syntax: mn() {
                if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != '(':
                     raise SemanticError("Expected '(' after 'mn'", self.get_current_token()[2], self.get_current_token()[3])
                self.advance() # Past '('
                if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ')':
                     raise SemanticError("Expected ')' after '(' in 'mn'", self.get_current_token()[2], self.get_current_token()[3])
                self.advance() # Past ')'
                if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != '{':
                     raise SemanticError("Expected '{' after 'mn()'", self.get_current_token()[2], self.get_current_token()[3])
                body_start_index = self.current_token_index + 1 # Index after '{'
                # --- End: Skipping mn() { signature ---

                # Create symbol for mn
                main_symbol = FunctionSymbol(
                    name="mn",
                    return_type="vd",
                    parameters=[],
                    line=mn_line,
                    column=mn_col
                )
                main_symbol.body_start_index = body_start_index

                # Insert into global scope
                if not self.global_scope.insert("mn", main_symbol):
                     # Check if already declared (should only happen once)
                     existing = self.global_scope.lookup("mn")
                     if existing and existing.type == 'function':
                          raise SemanticError("'mn' function can only be declared once", mn_line, mn_col)
                     else: # If 'mn' exists but isn't a function (e.g., variable)
                          raise SemanticError("Symbol 'mn' already declared with a different type", mn_line, mn_col)
                print(f"Pass 1: Added 'mn' symbol to global scope.")

                # Create and store scope for mn
                if "mn" not in self.function_scopes:
                     main_scope = SymbolTable(parent=self.global_scope, scope_name="function mn")
                     self.function_scopes["mn"] = main_scope
                     print(f"Pass 1: Created scope for 'mn'.")
                else:
                     # This case should ideally not happen if mn can only be declared once
                     print(f"Warning: Scope for 'mn' already existed in self.function_scopes during Pass 1.")
                     pass # Or raise error?

                # Skip body (self.current_token_index is at '{')
                self.advance() # Past '{'
                brace_count = 1
                while brace_count > 0 and self.current_token_index < len(self.token_stream):
                    t_type = self.get_current_token()[0]
                    if t_type == '{': brace_count += 1
                    elif t_type == '}': brace_count -= 1
                    if brace_count > 0: self.advance() # Avoid advancing past the final '}'

                # Now at final '}' or end of stream
                if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '}':
                     self.advance() # Past '}'
                else: # Reached end of stream without closing brace
                     raise SemanticError("Unclosed body for 'mn'", line, column) # Use line/col of '{' maybe?

                # Update the main loop index (temp_index) to where we ended up
                temp_index = self.current_token_index
                print(f"Pass 1: After skipping 'mn' body, temp_index is now {temp_index}.")
                continue # Skip default temp_index increment
            # --- End 'mn' handling ---

            # If not a function or struct or main, just move to the next token
            temp_index += 1

        # Restore the original token index before starting pass 2
        self.current_token_index = original_index
        print("Finished collecting declarations (Pass 1).")
                
    def skip_function_declaration(self):
        """Skip past a function declaration and body"""
        self.advance()  # Skip 'fnctn'
        
        # Skip return type if present
        token_type, token_value, line, column = self.get_current_token()
        if token_type == 'vd' or token_type in self.data_types:
            self.advance()
            
        # Skip function name
        self.advance()
        
        # Skip opening parenthesis
        self.advance()
        
        # Skip parameters
        paren_count = 1
        while paren_count > 0 and self.current_token_index < len(self.token_stream):
            token_type = self.get_current_token()[0]
            if token_type == '(':
                paren_count += 1
            elif token_type == ')':
                paren_count -= 1
            self.advance()
        
        # Skip to opening brace of function body
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != '{':
            self.advance()
            
        self.advance()  # Skip opening brace
        
        # Skip function body
        brace_count = 1
        while brace_count > 0 and self.current_token_index < len(self.token_stream):
            token_type = self.get_current_token()[0]
            if token_type == '{':
                brace_count += 1
            elif token_type == '}':
                brace_count -= 1
            self.advance()
    
    def skip_struct_declaration(self):
        """Skip past a struct declaration"""
        self.advance()  # Skip 'strct'
        
        # Skip struct name
        self.advance()
        
        # Skip to opening brace
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != '{':
            self.advance()
        
        self.advance()  # Skip opening brace
        
        # Skip struct body
        brace_count = 1
        while brace_count > 0 and self.current_token_index < len(self.token_stream):
            token_type = self.get_current_token()[0]
            if token_type == '{':
                brace_count += 1
            elif token_type == '}':
                brace_count -= 1
            self.advance()
        
        # Skip semicolon after closing brace
        if self.get_current_token()[0] == ';':
            self.advance()
    
    # --- Modified analyze_function_declaration ---
    def analyze_function_declaration(self, is_first_pass=True):
        """
        Analyzes 'fnctn' declaration.
        Pass 1: Collects signature, creates scope, stores body start index, skips body.
        Pass 2: Retrieves symbol/scope, analyzes body.
        """
        # Ensure we're starting with 'fnctn' keyword
        token_type, _, line_fn, col_fn = self.get_current_token() # Line/col of 'fnctn'
        if token_type != 'fnctn':
             raise SemanticError(f"Expected 'fnctn' keyword, got '{token_type}'", line_fn, col_fn)

        self.advance()  # Move past 'fnctn'

        # Check for return type
        token_type, _, line_ret, col_ret = self.get_current_token()
        return_type = None
        if token_type == 'vd':
            return_type = 'vd'
            self.advance()
        elif token_type in self.data_types:
            return_type = token_type
            self.advance()
        else:
            raise SemanticError(f"Expected return type or 'vd', got '{token_type}'", line_ret, col_ret)

        # Get function name
        token_type, func_name, line_name, col_name = self.get_current_token()
        if token_type != 'id':
            raise SemanticError(f"Expected function name, got '{token_type}'", line_name, col_name)
        # --- CRITICAL: 'mn' should not be declared using 'fnctn' ---
        if func_name == 'mn':
            raise SemanticError(f"'mn' is a reserved keyword and cannot be used as a function name here. Use 'mn()' syntax.", line_name, col_name)
        # --- End Check ---

        self.advance()  # Move past function name

        # Process opening parenthesis for parameters
        token_type, _, line_paren1, col_paren1 = self.get_current_token()
        if token_type != '(':
            raise SemanticError(f"Expected '(' after function name, got '{token_type}'", line_paren1, col_paren1)
        self.advance()

        # Parse parameters
        parameters = []
        if self.get_current_token()[0] != ')':
            self.parse_parameter(parameters)
            while self.get_current_token()[0] == ',':
                self.advance()
                self.parse_parameter(parameters)

        # Check for closing parenthesis
        token_type, _, line_paren2, col_paren2 = self.get_current_token()
        if token_type != ')':
            raise SemanticError(f"Expected ')' after parameters, got '{token_type}'", line_paren2, col_paren2)
        self.advance()

        # --- Symbol and Scope Handling (Pass 1 vs Pass 2) ---
        func_symbol = None
        function_scope = None

        if is_first_pass:
            # Pass 1: Create symbol, add to global scope, create function scope
            func_symbol = FunctionSymbol(
                name=func_name,
                return_type=return_type,
                parameters=parameters,
                line=line_name, # Use line/col of function name for symbol
                column=col_name
            )
            if not self.global_scope.insert(func_name, func_symbol):
                 existing = self.global_scope.lookup(func_name)
                 if existing and existing.type == 'function':
                     raise SemanticError(f"Function '{func_name}' already declared", line_name, col_name)
                 else:
                     raise SemanticError(f"Symbol '{func_name}' already declared with a different type", line_name, col_name)
            else:
                 print(f"Pass 1: Added function '{func_name}' symbol to global scope.")

            # Create and store function scope
            function_scope = SymbolTable(parent=self.global_scope, scope_name=f"function {func_name}")
            for param in parameters:
                if not function_scope.insert(param.name, param):
                     param_line, param_col = param.line, param.column
                     raise SemanticError(f"Duplicate parameter name '{param.name}' in function '{func_name}'", param_line, param_col)
            self.function_scopes[func_name] = function_scope
            print(f"Pass 1: Created scope for function '{func_name}'.")

        else:
            # Pass 2: Retrieve existing symbol and scope
            func_symbol = self.global_scope.lookup(func_name)
            if not func_symbol or func_symbol.type != 'function':
                 raise SemanticError(f"Internal Error: Function symbol for '{func_name}' not found during pass 2", line_name, col_name)
            if func_name not in self.function_scopes:
                 raise SemanticError(f"Internal Error: Function scope for '{func_name}' not found during pass 2", line_name, col_name)
            function_scope = self.function_scopes[func_name]
            print(f"Pass 2: Retrieved symbol and scope for function '{func_name}'.")


        # Process opening brace for function body
        token_type, _, brace_line, brace_column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start function body, got '{token_type}'", brace_line, brace_column)

        if is_first_pass:
            # Pass 1: Store body start index and skip the body
            func_symbol.body_start_index = self.current_token_index + 1 # Store index AFTER '{'
            print(f"Pass 1: Stored body start index {func_symbol.body_start_index} for '{func_name}'. Skipping body.")
            self.advance() # Move past '{'
            brace_count = 1
            while brace_count > 0 and self.current_token_index < len(self.token_stream):
                token_type = self.get_current_token()[0]
                if token_type == '{': brace_count += 1
                elif token_type == '}': brace_count -= 1
                if brace_count > 0: self.advance()
            if self.get_current_token()[0] == '}': self.advance() # Move past the final '}'
            else: raise SemanticError(f"Unclosed function body for '{func_name}'", brace_line, brace_column)
            print(f"Pass 1: Finished skipping body for '{func_name}'. Current index: {self.current_token_index}")

        else:
            # Pass 2: Analyze the body now
            print(f"Pass 2: Analyzing body for '{func_name}' starting at index {self.current_token_index + 1}.")
            self.advance() # Move past '{'
            old_scope = self.current_scope
            self.current_scope = function_scope # Switch to function's scope
            has_return = self.analyze_function_body(return_type)
            if return_type != 'vd' and not has_return:
                 raise SemanticError(f"Function '{func_name}' with return type '{return_type}' must have a return statement",
                                     func_symbol.line, func_symbol.column)
            func_symbol.has_return_statement = has_return
            self.current_scope = old_scope
            print(f"Pass 2: Finished analyzing body for '{func_name}'. Current index: {self.current_token_index}")

    def parse_parameter(self, parameters):
        """Parse a single function parameter and add it to the parameters list"""
        # Get parameter type
        token_type, token_value, line, column = self.get_current_token()
        if token_type not in self.data_types:
            raise SemanticError(f"Expected parameter type, got '{token_type}'", line, column)
        
        param_type = token_type
        self.advance()  # Move past parameter type
        
        # Get parameter name
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'id':
            raise SemanticError(f"Expected parameter name, got '{token_type}'", line, column)
        
        param_name = token_value
        
        # Create parameter symbol
        param_symbol = Symbol(
            name=param_name,
            type='variable',
            data_type=param_type,
            initialized=True,  # Parameters are considered initialized
            line=line,
            column=column
        )
        
        parameters.append(param_symbol)
        self.advance()  # Move past parameter name

    def analyze_function_body(self, return_type):
        """Analyze the function body and check for return statements"""
        has_return = False
        
        # Save body start position for second pass if needed
        body_start = self.current_token_index
        
        # Save old context and ensure we're not in a loop or switch context
        old_in_loop = self.in_loop
        old_in_switch = self.in_switch
        self.in_loop = False
        self.in_switch = False
        
        # Process function body until we find closing brace
        while self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            
            # Debug output
            print(f"Function body token: {token_type} '{token_value}' at line {line}, column {column}")
            
            # Check for end of function
            if token_type == '}':
                self.advance()  # Move past '}'
                break
                
            # Check for direct break or continue at function level
            if token_type == 'brk':
                raise SemanticError("Break statement cannot be used directly in a function body", line, column)
                
            if token_type == 'cntn':
                raise SemanticError("Continue statement cannot be used directly in a function body", line, column)
            
            # Check for struct member access (identifier followed by dot)
            if token_type == 'id':
                next_token = self.peek_next_token()
                if next_token and next_token[0] == '.':
                    print(f"Found struct member access pattern, routing to analyze_struct_member_access for {token_value}.{next_token[1]}")
                    self.analyze_struct_member_access()
                    continue
                # Check for increment/decrement operators
                elif next_token and next_token[0] in ['++', '--']:
                    self.analyze_increment_operation()
                    continue
                # Check for shortcut assignments
                elif next_token and next_token[0] in ['+=', '-=', '*=', '/=', '%=']:
                    print(f"Found shortcut assignment {token_value} {next_token[0]}")
                    self.analyze_assignment()
                    continue
            
            # Check for return statement
            if token_type == 'rtrn':
                has_return = True
                self.analyze_return_statement(return_type, line, column)
                continue
                
            # Check for print statement
            if token_type == 'prnt':
                print("Found print statement in function body - calling analyze_print_statement()")  # Debug
                self.analyze_print_statement()
                continue
                
            # Handle conditional statements
            if token_type == 'f':
                self.analyze_if_statement()
                continue
                
            # Handle switch statements
            if token_type == 'swtch':
                self.analyze_switch_statement()
                continue
                
            # Handle for loops
            if token_type == 'fr':
                self.analyze_for_loop()
                continue
                
            # Handle while loops
            if token_type == 'whl':
                self.analyze_while_loop()
                continue
            
            # Handle do-while loops
            if token_type == 'd':
                self.analyze_do_while_loop()
                continue
            
            # Handle other statements using existing methods
            if token_type == 'cnst':
                self.analyze_constant_declaration()
            elif token_type == 'dfstrct':
                self.analyze_struct_instantiation()
            elif token_type in self.data_types:
                start_pos = self.current_token_index
                self.advance()
                if self.current_token_index >= len(self.token_stream) or self.token_stream[self.current_token_index][0] != 'id':
                    raise SemanticError(f"Expected an identifier after '{token_type}'", line, column)
                
                next_token = self.peek_next_token()
                if next_token and next_token[0] == '[':
                    self.current_token_index = start_pos
                    self.analyze_array_declaration()
                else:
                    self.current_token_index = start_pos
                    self.analyze_variable_declaration()
            elif token_type == 'id' and self.peek_next_token()[0] == '(':
                self.analyze_function_call()
            elif token_type == 'id' and self.peek_next_token()[0] == '[':
                self.analyze_array_access()
                
                # Skip to end of statement
                while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';':
                    self.advance()
                self.advance()  # Move past semicolon
            elif token_type == 'id':
                next_token = self.peek_next_token()
                if next_token and next_token[0] == '=':
                    self.analyze_assignment()
                else:
                    self.check_variable_usage(token_value, line, column)
                    self.advance()
            else:
                self.advance()
        
        # If we haven't found a return but need one (non-void function),
        # do a more thorough scan of the function body
        if not has_return and return_type != 'vd':
            print("No return found in first pass, performing second linear scan")
            # Save current position
            current_pos = self.current_token_index
            
            # Reset to start of function body
            self.current_token_index = body_start
            
            # Scan for any return statements in the function body
            brace_level = 1  # We start inside the function body
            while self.current_token_index < len(self.token_stream):
                token = self.token_stream[self.current_token_index]
                token_type, token_value, token_line, token_column = token
                
                # Track brace level to stay within function
                if token_type == '{':
                    brace_level += 1
                elif token_type == '}':
                    brace_level -= 1
                    if brace_level == 0:
                        # We've reached the end of the function
                        break
                
                # Check for any return statements
                if token_type == 'rtrn':
                    print(f"Found return statement in second pass at line {token_line}, column {token_column}")
                    has_return = True
                    break
                
                self.current_token_index += 1
            
            # Restore original position
            self.current_token_index = current_pos
        
        # Restore old context
        self.in_loop = old_in_loop
        self.in_switch = old_in_switch
        
        print(f"Function body analysis complete. Has return: {has_return}")
        return has_return

    def analyze_return_statement(self, function_return_type, line, column):
        """Analyze a return statement and ensure it matches the function's return type"""
        self.advance()  # Move past 'rtrn'

        # --- REMOVED CHECK FOR MAIN FUNCTION ---
        # # Check if we're in the main function
        # current_function = None
        # temp_scope = self.current_scope
        # while temp_scope:
        #     if temp_scope.scope_name.startswith("function "):
        #         current_function = temp_scope.scope_name[len("function "):]
        #         break
        #     temp_scope = temp_scope.parent
        #
        # # No return statements allowed in main function
        # if current_function == "mn":
        #     raise SemanticError("Return statements are not allowed in the main function", line, column)
        # --- END REMOVED CHECK ---

        # Get the next token to determine if there's a return expression
        token_type, token_value, token_line, token_column = self.get_current_token()

        # For void functions, return should not have a value
        if function_return_type == 'vd':
            # --- ADDED: Check if we are in 'mn' function, which now allows return 0 ---
            is_main_function = False
            temp_scope = self.current_scope
            while temp_scope:
                if temp_scope.scope_name == "function mn":
                    is_main_function = True
                    break
                temp_scope = temp_scope.parent

            if is_main_function:
                # Allow 'rtrn 0;' in main
                if token_type == 'ntlit' and token_value == '0':
                    self.advance() # Past 0
                    if self.get_current_token()[0] == ';':
                         self.advance() # Past ;
                         return # Valid return 0; in main
                    else:
                         raise SemanticError("Expected ';' after 'rtrn 0' in main function", self.get_current_token()[2], self.get_current_token()[3])
                elif token_type == ';':
                     # Allow 'rtrn;' in main (implicitly returns 0 later)
                     self.advance() # Past ;
                     return
                else:
                     raise SemanticError(f"Main function ('mn') can only return '0' or have no return value ('rtrn;'), got '{token_value}'", token_line, token_column)
            # --- END ADDED CHECK for 'mn' ---
            elif token_type != ';': # Original check for other void functions
                raise SemanticError(f"Void function cannot return a value", token_line, token_column)
            self.advance()  # Move past semicolon for non-main void functions
            return

        # For non-void functions (and potentially main now), there must be a return value
        if token_type == ';':
            raise SemanticError(f"Function with return type '{function_return_type}' must return a value", token_line, token_column)

        # Find the end of the return expression (semicolon)
        start_pos = self.current_token_index

        while self.current_token_index < len(self.token_stream) and self.token_stream[self.current_token_index][0] != ';':
            self.advance()

        if self.current_token_index >= len(self.token_stream):
            raise SemanticError("Unexpected end of file inside return statement", line, column)

        end_pos = self.current_token_index
        self.current_token_index = start_pos

        # Analyze the expression
        expr_type = self.analyze_expression(end_pos)

        # --- MODIFIED CHECK for 'mn' ---
        is_main_function = False
        temp_scope = self.current_scope
        while temp_scope:
            if temp_scope.scope_name == "function mn":
                is_main_function = True
                break
            temp_scope = temp_scope.parent

        if is_main_function:
             # In 'mn', only allow returning an integer literal 0
             if not (expr_type == 'nt' and self.token_stream[start_pos][0] == 'ntlit' and self.token_stream[start_pos][1] == '0' and start_pos + 1 == end_pos):
                  raise SemanticError(f"Main function ('mn') can only return the integer literal '0', got expression of type '{expr_type}'", token_line, token_column)
        # --- END MODIFIED CHECK ---
        # Check if return type matches function return type (for non-main functions)
        elif expr_type != function_return_type:
            raise SemanticError(f"Return type mismatch: expected '{function_return_type}', got '{expr_type}'", token_line, token_column)

        # Move past the semicolon
        if self.get_current_token()[0] == ';':
            self.advance()

    def analyze_function_call(self):
        """Analyze a function call and its arguments"""
        token_type, func_name, line, column = self.get_current_token()
        
        # Debug output
        print(f"Analyzing function call for '{func_name}' at line {line}, column {column}")
        
        # Check if this is a built-in function
        if func_name in self.built_in_functions:
            # Handle built-in functions
            print(f"  '{func_name}' is a built-in function")
            self.advance()  # Move past function name
            self.advance()  # Move past opening parenthesis
            
            # Process arguments and move past closing parenthesis
            arguments = self.parse_function_arguments()

            # For npt function, return appropriate data type
            if func_name == 'npt':
                print("  Processing 'npt' input function")
                # npt function with a string prompt returns a string by default
                # The actual type conversion happens at runtime
                result_type = 'strng'
                
                # Check if there's exactly one argument of type string
                if len(arguments) != 1 or arguments[0] != 'strng':
                    raise SemanticError(f"Input function 'npt' requires a single string prompt", line, column)
                
                # Check for semicolon after function call
                if self.get_current_token()[0] == ';':
                    self.advance()  # Move past semicolon
                
                return result_type
            
            # Check for semicolon after function call
            if self.get_current_token()[0] == ';':
                self.advance()  # Move past semicolon
            
            return None if func_name != 'len' else 'nt' # len() returns an integer
        else:
            # First look in the global scope directly for functions
            func_symbol = self.global_scope.symbols.get(func_name)
            
            # If not found, try the regular lookup which includes current scope and parent scopes
            if not func_symbol:
                func_symbol = self.current_scope.lookup(func_name)
            
            # Debug output - check what's in global scope
            print(f"  Global scope functions: {[name for name, sym in self.global_scope.symbols.items() if sym.type == 'function']}")
            
            if not func_symbol:
                raise SemanticError(f"Undefined function '{func_name}'", line, column)
            
            if func_symbol.type != 'function':
                raise SemanticError(f"'{func_name}' is not a function", line, column)
            
            print(f"  Found function '{func_name}' with return type '{func_symbol.data_type}'")
            
            self.advance()  # Move past function name
            self.advance()  # Move past opening parenthesis
            
            # Parse arguments
            arguments = self.parse_function_arguments()
            
            # Check number of arguments against parameters
            if len(arguments) != len(func_symbol.parameters):
                raise SemanticError(
                    f"Function '{func_symbol.name}' expects {len(func_symbol.parameters)} arguments, got {len(arguments)}",
                    line, column
                )
            
            # Check argument types against parameter types
            for i, (arg_type, param) in enumerate(zip(arguments, func_symbol.parameters)):
                if arg_type != param.data_type:
                    raise SemanticError(
                        f"Argument {i+1} type mismatch: expected '{param.data_type}', got '{arg_type}'",
                        line, column
                    )
            
            # Check for semicolon after function call
            if self.get_current_token()[0] == ';':
                self.advance()  # Move past semicolon
            
            return func_symbol.data_type  # Return the function's return type

    def parse_function_arguments(self):
        """Parse function arguments and return a list of their types"""
        argument_types = []
        
        # If no arguments (empty parentheses)
        if self.get_current_token()[0] == ')':
            self.advance()  # Move past closing parenthesis
            return argument_types
        
        # Process arguments
        while True:
            # Find the end of this argument
            arg_start = self.current_token_index
            paren_level = 0
            bracket_level = 0
            
            # Continue until we find a comma or closing parenthesis at the top level
            while self.current_token_index < len(self.token_stream):
                token_type = self.token_stream[self.current_token_index][0]
                
                if token_type == '(':
                    paren_level += 1
                elif token_type == ')':
                    if paren_level == 0:
                        # End of all arguments
                        break
                    paren_level -= 1
                elif token_type == '[':
                    bracket_level += 1
                elif token_type == ']':
                    bracket_level -= 1
                elif token_type == ',' and paren_level == 0 and bracket_level == 0:
                    # End of current argument
                    break
                    
                self.current_token_index += 1
            
            # Reset to the start of the argument
            arg_end = self.current_token_index
            self.current_token_index = arg_start
            
            # Parse the current argument expression
            arg_type = self.analyze_expression(arg_end)
            argument_types.append(arg_type)
            
            # Now at the end of the argument
            self.current_token_index = arg_end
            
            # Check for comma or closing parenthesis
            if self.get_current_token()[0] == ',':
                self.advance()  # Move past comma
            elif self.get_current_token()[0] == ')':
                self.advance()  # Move past closing parenthesis
                break
            else:
                raise SemanticError(
                    f"Expected ',' or ')' after function argument, got '{self.get_current_token()[0]}'",
                    self.get_current_token()[2], self.get_current_token()[3]
                )
        
        return argument_types

    def parse_function_argument(self):
        """Parse a single function argument and return its type"""
        arg_start = self.current_token_index
        
        # Handle special cases like literals, identifiers, etc.
        token_type, token_value, line, column = self.get_current_token()
        
        # Literal values
        if token_type in ['ntlit', '~ntlit']:
            self.advance()
            return 'nt'
        elif token_type in ['dbllit', '~dbllit']:
            self.advance()
            return 'dbl'
        elif token_type in ['true', 'false', 'blnlit']:
            self.advance()
            return 'bln'
        elif token_type == 'chrlit':
            self.advance()
            return 'chr'
        elif token_type == 'strnglit':
            self.advance()
            return 'strng'
        elif token_type == 'id':
            # Could be a variable or a function call
            symbol = self.current_scope.lookup(token_value)
            if not symbol:
                raise SemanticError(f"Undefined identifier '{token_value}'", line, column)
            
            # Check if it's a function call
            self.advance()
            if self.get_current_token()[0] == '(':
                # It's a function call within an argument
                self.current_token_index = arg_start  # Go back to the start
                return self.analyze_function_call()   # Process the function call and return its type
            else:
                # It's a variable reference
                return symbol.data_type
        elif token_type == '(':
            # Expression in parentheses
            self.advance()  # Skip opening parenthesis
            
            # Find the matching closing parenthesis
            paren_level = 1
            expr_start = self.current_token_index
            
            while paren_level > 0:
                self.advance()
                if self.current_token_index >= len(self.token_stream):
                    raise SemanticError("Unclosed parenthesis", line, column)
                
                current_token = self.get_current_token()[0]
                if current_token == '(':
                    paren_level += 1
                elif current_token == ')':
                    paren_level -= 1
            
            # Analyze the expression within the parentheses
            expr_end = self.current_token_index
            self.current_token_index = expr_start
            expr_type = self.analyze_expression(expr_end)
            
            self.advance()  # Skip closing parenthesis
            return expr_type
        else:
            # IMPROVED: Handle general expressions with proper nesting
            # Find the end of this argument considering nested parentheses/brackets
            paren_level = 0
            bracket_level = 0
            
            # Continue until we find a comma or closing parenthesis at the top level
            while self.current_token_index < len(self.token_stream):
                current_token = self.get_current_token()[0]
                
                if current_token == '(':
                    paren_level += 1
                elif current_token == ')':
                    if paren_level == 0:
                        # End of all arguments
                        break
                    paren_level -= 1
                elif current_token == '[':
                    bracket_level += 1
                elif current_token == ']':
                    bracket_level -= 1
                elif current_token == ',' and paren_level == 0 and bracket_level == 0:
                    # End of current argument
                    break
                    
                self.advance()
            
            # Analyze the expression
            expr_end = self.current_token_index
            self.current_token_index = arg_start
            return self.analyze_expression(expr_end)

    def analyze_struct_declaration(self):
        """Analyze a struct declaration"""
        # Ensure we're starting with 'strct' keyword
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'strct':
            raise SemanticError(f"Expected 'strct' keyword, got '{token_type}'", line, column)
        
        self.advance()  # Move past 'strct'
        
        # Get struct name
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'id':
            raise SemanticError(f"Expected struct name, got '{token_type}'", line, column)
        
        struct_name = token_value
        
        # Check for duplicate declaration
        if self.current_scope.lookup(struct_name):
            raise SemanticError(f"Struct '{struct_name}' already declared", line, column)
        
        self.advance()  # Move past struct name
        
        # Process opening brace
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' after struct name, got '{token_type}'", line, column)
        
        self.advance()  # Move past '{'
        
        # Process struct members
        members = {}
        
        while self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            
            # Check for end of struct
            if token_type == '}':
                break
            
            # Parse member data type
            if token_type not in self.data_types:
                raise SemanticError(f"Expected a data type for struct member, got '{token_type}'", line, column)
            
            member_type = token_type
            self.advance()  # Move past data type
            
            # Parse member name
            token_type, token_value, line, column = self.get_current_token()
            if token_type != 'id':
                raise SemanticError(f"Expected member name, got '{token_type}'", line, column)
            
            member_name = token_value
            
            # Check for duplicate member
            if member_name in members:
                raise SemanticError(f"Duplicate member '{member_name}' in struct '{struct_name}'", line, column)
            
            # Create member symbol
            member_symbol = Symbol(
                name=member_name,
                type='variable',
                data_type=member_type,
                initialized=False,  # Members start uninitialized
                line=line,
                column=column
            )
            
            members[member_name] = member_symbol
            
            self.advance()  # Move past member name
            
            # Check for semicolon
            token_type, token_value, line, column = self.get_current_token()
            if token_type != ';':
                raise SemanticError(f"Expected ';' after struct member, got '{token_type}'", line, column)
            
            self.advance()  # Move past semicolon
        
        # Check for closing brace
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '}':
            raise SemanticError(f"Expected '}}' at end of struct, got '{token_type}'", line, column)
        
        self.advance()  # Move past '}'
        
        # Check for semicolon after struct declaration
        token_type, token_value, line, column = self.get_current_token()
        if token_type != ';':
            raise SemanticError(f"Expected ';' after struct declaration, got '{token_type}'", line, column)
        
        self.advance()  # Move past semicolon
        
        # Create struct symbol
        struct_symbol = StructSymbol(
            name=struct_name,
            members=members,
            line=line,
            column=column
        )
        
        # Add to global scope (structs are global only)
        self.global_scope.insert(struct_name, struct_symbol)
        
        print(f"Added struct '{struct_name}' to global scope with {len(members)} members")

    def analyze_struct_instantiation(self):
        """Analyze a struct instance declaration with dfstrct"""
        # Ensure we're starting with 'dfstrct' keyword
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'dfstrct':
            raise SemanticError(f"Expected 'dfstrct' keyword, got '{token_type}'", line, column)
        
        self.advance()  # Move past 'dfstrct'
        
        # Get struct type name
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'id':
            raise SemanticError(f"Expected struct type name, got '{token_type}'", line, column)
        
        struct_type_name = token_value
        
        # Look up the struct type
        struct_symbol = self.global_scope.lookup(struct_type_name)
        if not struct_symbol or struct_symbol.type != 'struct':
            raise SemanticError(f"Undefined struct type '{struct_type_name}'", line, column)
        
        self.advance()  # Move past struct type name
        
        # Process one or more instance declarations
        while self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            
            # Check for end of declaration
            if token_type == ';':
                self.advance()  # Move past semicolon
                break
            
            # Parse instance name
            if token_type != 'id':
                raise SemanticError(f"Expected struct instance name, got '{token_type}'", line, column)
            
            instance_name = token_value
            
            # Check for duplicate declaration - FIXED to work in current scope
            if self.current_scope.lookup(instance_name):
                raise SemanticError(f"Variable '{instance_name}' already declared", line, column)
            
            instance_symbol = Symbol(
                name=instance_name,
                type='struct_instance',
                data_type=struct_type_name,
                initialized=True,
                line=line,
                column=column
            )
            instance_symbol.initialized_members = set()  # Initialize empty set for tracking initialized members
            
            # Add to current scope
            self.current_scope.insert(instance_name, instance_symbol)

            # Add this debug output:
            print(f"Added struct instance '{instance_name}' of type '{struct_type_name}' to scope '{self.current_scope.scope_name}'")
            
            self.advance()  # Move past instance name
            
            # Check for comma (for multiple declarations) or semicolon (end of declaration)
            token_type, token_value, line, column = self.get_current_token()
            if token_type == ',':
                self.advance()  # Move past comma
            elif token_type == ';':
                self.advance()  # Move past semicolon
                break
            else:
                raise SemanticError(f"Expected ',' or ';' after struct instance, got '{token_type}'", line, column)
        
    def analyze_struct_member_access(self):
        """
        Analyze a struct member access (reading or assignment LHS) and return the member type.
        This function only analyzes the `id.id` part, not the assignment or RHS.
        """
        # Get struct instance name
        token_type, instance_name, line, column = self.get_current_token()

        # Debug output
        print(f"Analyzing struct member access for '{instance_name}' at line {line}, column {column}")

        # Check if variable exists
        instance_symbol = self.current_scope.lookup(instance_name)
        print(f"Looking for struct instance '{instance_name}' in scope '{self.current_scope.scope_name}': {'Found' if instance_symbol else 'Not Found'}")
        if not instance_symbol:
            raise SemanticError(f"Undefined variable '{instance_name}'", line, column)

        # Check that it's a struct instance
        if instance_symbol.type != 'struct_instance':
            raise SemanticError(f"Variable '{instance_name}' is not a struct instance", line, column)

        # Get the struct type
        struct_type_name = instance_symbol.data_type

        # Look up the struct type in global scope (structs are only declared globally)
        struct_symbol = self.global_scope.lookup(struct_type_name)

        # Debug
        print(f"Looking for struct '{struct_type_name}' in global scope")
        print(f"Global scope contains: {[name for name in self.global_scope.symbols.keys()]}")

        if not struct_symbol:
            raise SemanticError(f"Undefined struct type '{struct_type_name}'", line, column)

        if struct_symbol.type != 'struct':
            raise SemanticError(f"Type '{struct_type_name}' is not a struct", line, column)

        self.advance()  # Move past instance name

        # Process dot operator
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '.':
            raise SemanticError(f"Expected '.' for struct member access, got '{token_type}'", line, column)

        self.advance()  # Move past '.'

        # Get member name
        token_type, member_name, line, column = self.get_current_token()
        if token_type != 'id':
            raise SemanticError(f"Expected member name, got '{token_type}'", line, column)

        # Check if member exists in the struct
        struct_symbol = self.global_scope.lookup(instance_symbol.data_type)
        if not hasattr(struct_symbol, 'members') or member_name not in struct_symbol.members:
            raise SemanticError(f"Struct '{instance_symbol.data_type}' has no member '{member_name}'", line, column)

        # --- REMOVED: Assignment handling logic from here ---
        # The assignment logic will be handled by analyze_assignment

        self.advance()  # Move past member name

        # Get the member type for expression typing
        member_symbol = struct_symbol.members[member_name]
        print(f"Finished analyzing struct member access for '{instance_name}.{member_name}', member type: {member_symbol.data_type}")
        return member_symbol.data_type # Return the type of the member
            
    # --- Modified analyze_main_function ---
    def analyze_main_function(self):
        """Analyze the main function BODY ('mn'). Assumes called during Pass 2."""
        # Assumes current token is 'mn'
        mn_line, mn_col = self.get_current_token()[2], self.get_current_token()[3]

        # --- Retrieve symbol and scope created in Pass 1 ---
        main_symbol = self.global_scope.lookup("mn")
        if not main_symbol or main_symbol.type != 'function':
             raise SemanticError("Internal Error: Main function 'mn' symbol not found or invalid during pass 2", mn_line, mn_col)

        if "mn" not in self.function_scopes:
            raise SemanticError("Internal Error: Main function scope for 'mn' not found during pass 2", mn_line, mn_col)
        main_scope = self.function_scopes["mn"]
        # --- End retrieval ---

        # --- Skip signature part mn() ---
        self.advance() # Past 'mn'
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != '(':
             raise SemanticError("Expected '(' after 'mn'", self.get_current_token()[2], self.get_current_token()[3])
        self.advance() # Past '('
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ')':
             raise SemanticError("Expected ')' after '(' in 'mn'", self.get_current_token()[2], self.get_current_token()[3])
        self.advance() # Past ')'
        # --- End skipping signature ---

        # --- Analyze Body ---
        old_scope = self.current_scope
        self.current_scope = main_scope # Switch to main's scope

        # Process opening brace
        token_type, _, brace_line, brace_column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start main function body, got '{token_type}'", brace_line, brace_column)
        self.advance()  # Move past '{'

        print(f"Pass 2: Starting to process main function body in scope '{self.current_scope.scope_name}'")

        # Save old context flags
        old_in_loop = self.in_loop
        old_in_switch = self.in_switch
        self.in_loop = False
        self.in_switch = False

        # Process main function body
        self.analyze_function_body("vd") # Pass "vd" as return type

        print(f"Pass 2: Finished processing main function body, returning to scope '{old_scope.scope_name}'")

        # Restore old context flags
        self.in_loop = old_in_loop
        self.in_switch = old_in_switch

        # Restore outer scope
        self.current_scope = old_scope
        # analyze_function_body should leave us positioned after '}'

    # --- Modified analyze method ---
    def analyze(self, tokens):
        """Main entry point for semantic analysis (Handles Pass 1 and Pass 2)."""
        self.token_stream = tokens
        self.current_scope = self.global_scope
        self.function_scopes = {} # Initialize/reset function scopes map
        errors = []

        try:
            # --- Pass 1: Collect Declarations ---
            self.current_token_index = 0
            self.collect_declarations() # Populates global scope with signatures, stores body indices

            # --- Debug Print Global Scope After Pass 1 ---
            print("\n--- Global Scope Contents After Pass 1 ---")
            if hasattr(self, 'global_scope') and self.global_scope:
                 for name, symbol in self.global_scope.symbols.items():
                      print(f"  {name}: {symbol}")
            else:
                 print("  Global scope not available.")
            print("----------------------------------------")
            # --- End Debug Print ---


            # --- Pass 2: Full Analysis ---
            self.current_token_index = 0
            self.current_scope = self.global_scope # Ensure we start in global scope for pass 2
            print("\nStarting full analysis (Pass 2)...")

            while self.current_token_index < len(self.token_stream):
                start_of_loop_index = self.current_token_index
                token_type, token_value, line, column = self.token_stream[self.current_token_index]
                scope_name = self.current_scope.scope_name if self.current_scope else "None"
                print(f"Pass 2 - Index: {self.current_token_index}, Token: {token_type} ('{token_value}'), Scope: {scope_name}")

                if token_type == 'strct':
                    print(f"Pass 2: Skipping struct definition '{self.peek_next_token()[1]}'.")
                    self.skip_struct_declaration()
                    print(f"Pass 2: After skipping struct, index is {self.current_token_index}")
                    continue

                # --- SIMPLIFIED 'fnctn' handling in Pass 2 ---
                # Handles ONLY user-defined functions declared with 'fnctn'
                elif token_type == 'fnctn':
                    func_name = "unknown"
                    name_token_idx = self.current_token_index + 2
                    if name_token_idx < len(self.token_stream):
                         func_name_token = self.token_stream[name_token_idx]
                         if func_name_token[0] == 'id': func_name = func_name_token[1]
                    print(f"Pass 2: Analyzing body of function '{func_name}'.")
                    self.analyze_function_declaration(is_first_pass=False)
                    print(f"Pass 2: After analyzing '{func_name}' body, index is {self.current_token_index}")
                    continue
                # --- End simplified 'fnctn' handling ---

                # Handle 'mn' function analysis trigger
                elif token_type == 'mn':
                    print(f"Pass 2: Analyzing 'mn' function.")
                    self.analyze_main_function() # Analyzes the body
                    print(f"Pass 2: After analyzing 'mn', index is {self.current_token_index}")
                    continue

                # Handle global declarations (struct instances, variables, constants)
                elif token_type == 'dfstrct':
                    print(f"Pass 2: Analyzing struct instantiation.")
                    self.analyze_struct_instantiation()
                    print(f"Pass 2: After dfstrct, index is {self.current_token_index}")
                    continue
                elif token_type == 'cnst':
                    print(f"Pass 2: Analyzing constant declaration.")
                    self.analyze_constant_declaration()
                    print(f"Pass 2: After cnst, index is {self.current_token_index}")
                    continue
                elif token_type in self.data_types:
                    print(f"Pass 2: Analyzing variable/array declaration starting with '{token_type}'.")
                    start_pos = self.current_token_index
                    # Look ahead logic to differentiate var/array
                    self.advance() # Past type
                    next_is_id = self.current_token_index < len(self.token_stream) and self.token_stream[self.current_token_index][0] == 'id'
                    if not next_is_id: raise SemanticError(f"Expected an identifier after '{token_type}'", line, column)
                    next_token_after_id = self.peek_next_token()
                    is_array = next_token_after_id and next_token_after_id[0] == '['
                    # Reset and analyze
                    self.current_token_index = start_pos
                    if is_array: self.analyze_array_declaration()
                    else: self.analyze_variable_declaration()
                    print(f"Pass 2: After var/array decl, index is {self.current_token_index}")
                    continue

                # Handle potential top-level statements
                elif token_type == 'id':
                    next_token = self.peek_next_token()
                    handled = False
                    if next_token:
                        if next_token[0] == '.':
                            print(f"Pass 2: Analyzing top-level struct member access/assignment.")
                            self.analyze_struct_member_access() # Returns type, ignore here
                            handled = True
                        # ... (other id handlers: '(', '[', '=', '++', '--', '+=', etc.) ...
                        elif next_token[0] == '(':
                            print(f"Pass 2: Analyzing top-level function call.")
                            self.analyze_function_call() # Returns type, ignore here
                            handled = True
                        elif next_token[0] == '[':
                            print(f"Pass 2: Analyzing top-level array access/assignment.")
                            self.analyze_array_access() # Returns type, ignore here
                            if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == ';': self.advance()
                            handled = True
                        elif next_token[0] == '=':
                            print(f"Pass 2: Analyzing top-level assignment.")
                            self.analyze_assignment()
                            handled = True
                        elif next_token[0] in ['++', '--']:
                            print(f"Pass 2: Analyzing top-level increment/decrement.")
                            self.analyze_increment_operation()
                            handled = True
                        elif next_token[0] in ['+=', '-=', '*=', '/=', '%=']:
                            print(f"Pass 2: Analyzing top-level shortcut assignment.")
                            self.analyze_assignment() # Handles shortcut ops too
                            handled = True

                    if handled:
                         print(f"Pass 2: After top-level ID statement, index is {self.current_token_index}")
                         continue
                    else:
                         print(f"Pass 2: Advancing past unhandled ID '{token_value}'.")
                         self.advance() # Advance if ID wasn't part of a handled statement

                elif token_type == 'prnt':
                     print(f"Pass 2: Analyzing top-level print statement.")
                     self.analyze_print_statement()
                     print(f"Pass 2: After top-level prnt, index is {self.current_token_index}")
                     continue

                # If the token wasn't handled by any case above, advance.
                if self.current_token_index == start_of_loop_index:
                     print(f"Pass 2: Advancing past unhandled token {token_type} ('{token_value}') to prevent loop.")
                     self.advance()

            # --- End of Pass 2 ---
            print("\nFinished full analysis (Pass 2).")
            self.print_symbol_tables()
            return True, errors

        except SemanticError as e:
            errors.append(str(e))
            print("\n--- Symbol Tables after Error ---")
            self.print_symbol_tables()
            print("-----------------------------")
            return False, errors
        except Exception as e:
             errors.append(f"Unexpected Internal Error during analysis: {e}")
             print("\n--- Symbol Tables after Internal Error ---")
             self.print_symbol_tables()
             print("-----------------------------")
             import traceback
             traceback.print_exc()
             return False, errors
    
    # --- Helper: skip_struct_declaration ---
    def skip_struct_declaration(self):
        """Advances the token index past a struct definition."""
        # Assumes current token is 'strct'
        if self.get_current_token()[0] != 'strct': return # Should not happen
        self.advance() # Skip 'strct'
        if self.get_current_token()[0] != 'id': return # Skip name (error if not ID)
        self.advance()
        if self.get_current_token()[0] != '{': return # Skip '{' (error if not '{')
        self.advance()
        brace_count = 1
        while brace_count > 0 and self.current_token_index < len(self.token_stream):
            token_type = self.get_current_token()[0]
            if token_type == '{':
                brace_count += 1
            elif token_type == '}':
                brace_count -= 1
            # Advance unconditionally inside the loop
            if brace_count > 0: # Avoid advancing past the final '}'
                 self.advance()

        # Now self.current_token_index is at the final '}'
        if self.get_current_token()[0] == '}':
            self.advance() # Move past '}'
        # Skip potential semicolon after '}'
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == ';':
            self.advance()


    # --- Helper: skip_function_declaration ---
    def skip_struct_declaration(self):
        """Advances the token index past a struct definition."""
        # Assumes current token is 'strct'
        if self.get_current_token()[0] != 'strct': return # Should not happen
        self.advance() # Skip 'strct'
        if self.get_current_token()[0] != 'id': return # Skip name (error if not ID)
        self.advance()
        if self.get_current_token()[0] != '{': return # Skip '{' (error if not '{')
        self.advance()
        brace_count = 1
        while brace_count > 0 and self.current_token_index < len(self.token_stream):
            token_type = self.get_current_token()[0]
            if token_type == '{':
                brace_count += 1
            elif token_type == '}':
                brace_count -= 1
            # Advance unconditionally inside the loop
            if brace_count > 0: # Avoid advancing past the final '}'
                 self.advance()

        # Now self.current_token_index is at the final '}'
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '}':
            self.advance() # Move past '}'
        # Skip potential semicolon after '}'
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == ';':
            self.advance()

    def is_in_function_body(self):
        """Check if current position is inside a function body"""
        # Start from current position and look backward for function keyword
        pos = self.current_token_index
        
        # Go backwards until we find a function start or beginning of file
        while pos > 0:
            token_type = self.token_stream[pos][0]
            
            # If we find a function, we're inside it
            if token_type in ['fnctn', 'mn']:
                # Check if we've passed the opening brace
                brace_pos = pos
                while brace_pos < self.current_token_index:
                    if self.token_stream[brace_pos][0] == '{':
                        return True
                    brace_pos += 1
                return False
            
            # If we find the end of a previous function, we're not in a function
            if token_type == '}':
                # Check if it's the end of a function
                # This is simplified and might need refinement
                return False
            
            pos -= 1
        
        return False

    def skip_function_declaration(self):
        """Advances the token index past a 'fnctn' definition (signature and body)."""
        # Assumes current token is 'fnctn'
        if self.get_current_token()[0] != 'fnctn': return
        self.advance() # Skip 'fnctn'
        # Skip return type/vd
        if self.get_current_token()[0] in self.data_types or self.get_current_token()[0] == 'vd':
             self.advance()
        else: return # Error in syntax
        # Skip function name
        if self.get_current_token()[0] == 'id':
             self.advance()
        else: return # Error in syntax
        # Skip parameters (...)
        if self.get_current_token()[0] != '(': return
        self.advance() # Skip '('
        paren_count = 1
        while paren_count > 0 and self.current_token_index < len(self.token_stream):
            token_type = self.get_current_token()[0]
            if token_type == '(': paren_count += 1
            elif token_type == ')': paren_count -= 1
            if paren_count > 0: self.advance()
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == ')':
             self.advance() # Move past ')'
        else: return # Error in syntax

        # Skip body {...}
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != '{': return
        self.advance() # Skip '{'
        brace_count = 1
        while brace_count > 0 and self.current_token_index < len(self.token_stream):
            token_type = self.get_current_token()[0]
            if token_type == '{': brace_count += 1
            elif token_type == '}': brace_count -= 1
            if brace_count > 0: self.advance()
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '}':
             self.advance() # Move past '}'
        
    def analyze_constant_declaration(self):
        """Analyze a constant declaration"""
        # At this point, the current token should be 'cnst'
        self.advance()  # Move past 'cnst'
        
        # Get the data type
        data_type_token, data_type_value, data_line, data_column = self.get_current_token()
        if data_type_token not in self.data_types:
            raise SemanticError(f"Expected data type after 'cnst', got {data_type_token}", data_line, data_column)
        
        self.advance()  # Move past data type
        
        # Get the variable name
        var_token_type, var_name, name_line, name_column = self.get_current_token()
        if var_token_type != 'id':
            raise SemanticError(f"Expected an identifier, got {var_token_type}", name_line, name_column)
        
        # Check for duplicate declaration
        if self.current_scope.lookup(var_name) and self.current_scope.symbols.get(var_name):
            raise SemanticError(f"Variable '{var_name}' already declared", name_line, name_column)
        
        # Look ahead to see if this is an array declaration
        next_token = self.peek_next_token()
        if next_token and next_token[0] == '[':
            # Go back to the cnst token
            self.current_token_index -= 2  # Back to cnst
            self.analyze_array_declaration()
            return
        
        # Otherwise, handle as a regular constant
        self.advance()  # Move past variable name
        
        # Constants must be initialized
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '=':
            raise SemanticError(f"Constants must be initialized", line, column)
        
        self.advance()  # Move past '='
        
        # Save starting position for expression analysis
        start_pos = self.current_token_index
        
        # Skip ahead to find the end of the expression (semicolon or comma)
        while (self.current_token_index < len(self.token_stream) and 
            self.token_stream[self.current_token_index][0] not in [';', ',']):
            self.advance()
        
        # Reset position to start of expression
        end_pos = self.current_token_index
        self.current_token_index = start_pos
        
        # Analyze the expression
        expr_type = self.analyze_expression(end_pos)
        
        # Check if the expression type matches the variable type
        if data_type_token != expr_type:
            raise SemanticError(
                f"Type mismatch: Cannot initialize constant '{data_type_token}' with {expr_type}",
                line, column
            )
        
        # Create and add the constant symbol
        symbol = Symbol(
            name=var_name,
            type='variable',
            data_type=data_type_token,
            initialized=True,
            is_constant=True,
            line=name_line,
            column=name_column
        )
        self.current_scope.insert(var_name, symbol)
        
        # Current position is now at the end of the expression
        token_type, token_value, line, column = self.get_current_token()
        
        # Handle multiple declarations
        if token_type == ',':
            self.advance()  # Move past comma
            self.analyze_constant_declaration_continuation(data_type_token)
        elif token_type == ';':
            self.advance()  # Move past semicolon

    def analyze_constant_declaration_continuation(self, data_type):
        """Handle the continuation of a constant declaration (after a comma)"""
        # Get the next variable name
        var_token_type, var_name, name_line, name_column = self.get_current_token()
        if var_token_type != 'id':
            raise SemanticError(f"Expected an identifier, got {var_token_type}", name_line, name_column)
        
        # Check for duplicate declaration
        if self.current_scope.lookup(var_name) and self.current_scope.symbols.get(var_name):
            raise SemanticError(f"Variable '{var_name}' already declared", name_line, name_column)
        
        # Look ahead to see if this is an array declaration
        next_token = self.peek_next_token()
        if next_token and next_token[0] == '[':
            # Cannot handle array declaration in the middle of a constant declaration list
            raise SemanticError(f"Array declarations must be separate from variable declarations", name_line, name_column)
        
        self.advance()  # Move past variable name
        
        # Constants must be initialized
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '=':
            raise SemanticError(f"Constants must be initialized", line, column)
        
        self.advance()  # Move past '='
        
        # Save starting position for expression analysis
        start_pos = self.current_token_index
        
        # Skip ahead to find the end of the expression (semicolon or comma)
        while (self.current_token_index < len(self.token_stream) and 
            self.token_stream[self.current_token_index][0] not in [';', ',']):
            self.advance()
        
        # Reset position to start of expression
        end_pos = self.current_token_index
        self.current_token_index = start_pos
        
        # Analyze the expression
        expr_type = self.analyze_expression(end_pos)
        
        # Check if the expression type matches the variable type
        if data_type != expr_type:
            raise SemanticError(
                f"Type mismatch: Cannot initialize constant '{data_type}' with {expr_type}",
                line, column
            )
        
        # Create and add the constant symbol
        symbol = Symbol(
            name=var_name,
            type='variable',
            data_type=data_type,
            initialized=True,
            is_constant=True,
            line=name_line,
            column=name_column
        )
        self.current_scope.insert(var_name, symbol)
        
        # Current position is now at the end of the expression
        token_type, token_value, line, column = self.get_current_token()
        
        # Handle multiple declarations
        if token_type == ',':
            self.advance()  # Move past comma
            self.analyze_constant_declaration_continuation(data_type)
        elif token_type == ';':
            self.advance()  # Move past semicolon
        

    def analyze_variable_declaration(self):
        """Analyze a variable declaration and possible initialization for multiple variables"""
        data_type, type_value, type_line, type_column = self.token_stream[self.current_token_index]
        self.advance()  # Move past the data type
        
        # Continue parsing declarations until we hit a semicolon or end of statement
        while self.current_token_index < len(self.token_stream):
            # Get variable name
            var_token_type, var_name, name_line, name_column = self.get_current_token()
            
            if var_token_type != 'id':
                raise SemanticError(f"Expected an identifier, got {var_token_type}", name_line, name_column)
            
            # Check for duplicate declaration in current scope
            if self.current_scope.lookup(var_name) and self.current_scope.symbols.get(var_name):
                raise SemanticError(f"Variable '{var_name}' already declared", name_line, name_column)
            
            # Create symbol
            symbol = Symbol(
                name=var_name,
                type='variable',
                data_type=data_type,
                initialized=False,
                line=name_line,
                column=name_column
            )
            
            self.advance()  # Move past variable name
            
            # Check for initialization
            token_type, token_value, line, column = self.get_current_token()
            
            if token_type == '=':
                self.advance()  # Move past '='
                
                # Save starting position for expression analysis
                start_pos = self.current_token_index
                
                # Skip ahead to find the end of the expression (semicolon or comma)
                while (self.current_token_index < len(self.token_stream) and 
                       self.token_stream[self.current_token_index][0] not in [';', ',']):
                    self.advance()
                
                # Reset position to start of expression
                end_pos = self.current_token_index
                self.current_token_index = start_pos
                
                # Analyze the expression
                expr_type = self.analyze_expression(end_pos)
                
                # Check if the expression type matches the variable type
                if data_type != expr_type:
                    # Special case for boolean variables being assigned relational expressions
                    if data_type == 'bln' and expr_type == 'bln':
                        # This is fine, expression results in boolean and variable is boolean
                        pass
                    else:
                        raise SemanticError(
                            f"Type mismatch: Cannot initialize '{data_type}' with {expr_type}",
                            line, column
                        )
                
                symbol.initialized = True
                
                # Current position is now at the end of the expression
            
            # Add the symbol to the symbol table
            self.current_scope.insert(var_name, symbol)
            
            # Check for comma or end of declaration
            token_type, token_value, line, column = self.get_current_token()
            
            if token_type == ',':
                self.advance()  # Move past the comma
                continue
            elif token_type == ';':
                self.advance()  # Move past the semicolon
                break
            else:
                # For languages that don't require semicolons, or end of line tokens
                # You might want additional logic here
                break
    def analyze_array_declaration(self):
        """Analyze an array declaration and possible initialization"""
        is_constant = False
        
        # Check if this is a constant array
        token_type, token_value, line, column = self.get_current_token()
        if token_type == 'cnst':
            is_constant = True
            self.advance()  # Move past 'cnst'
        
        data_type, type_value, type_line, type_column = self.get_current_token()
        self.advance()  # Move past the data type
        
        # Process all array declarations and variables in this declaration
        self.process_array_or_variable(data_type, is_constant)

    def process_array_or_variable(self, data_type, is_constant=False):
        """Process an array or variable declaration, possibly followed by more declarations"""
        # Get variable name
        var_token_type, var_name, name_line, name_column = self.get_current_token()
        
        if var_token_type != 'id':
            raise SemanticError(f"Expected an identifier, got {var_token_type}", name_line, name_column)
        
        # Check for duplicate declaration in current scope
        if self.current_scope.lookup(var_name) and self.current_scope.symbols.get(var_name):
            raise SemanticError(f"Variable '{var_name}' already declared", name_line, name_column)
        
        self.advance()  # Move past variable name
        
        # Check if this is an array declaration (followed by '[')
        if self.get_current_token()[0] == '[':
            # Process array dimensions and sizes
            array_dimensions = 0
            array_sizes = []
            
            # First dimension
            array_dimensions += 1
            self.advance()  # Move past '['
            
            # Parse size expression
            size1_token_type, size1_value, size1_line, size1_column = self.get_current_token()
            
            if size1_token_type not in ['ntlit', 'id']:
                raise SemanticError(f"Array size must be an integer constant or variable", size1_line, size1_column)
            
            # If the size is a variable, check that it's declared and of type 'nt'
            if size1_token_type == 'id':
                size_symbol = self.current_scope.lookup(size1_value)
                if not size_symbol:
                    raise SemanticError(f"Undefined variable '{size1_value}' used as array size", size1_line, size1_column)
                if size_symbol.data_type != 'nt':
                    raise SemanticError(f"Array size must be of type 'nt', got '{size_symbol.data_type}'", size1_line, size1_column)
                if not size_symbol.initialized:
                    raise SemanticError(f"Uninitialized variable '{size1_value}' used as array size", size1_line, size1_column)
                array_sizes.append(size1_value)  # Store the variable name
            else:
                # It's a literal, make sure it's positive
                size1 = int(size1_value)
                if size1 <= 0:
                    raise SemanticError(f"Array size must be positive, got {size1}", size1_line, size1_column)
                array_sizes.append(size1)
            
            self.advance()  # Move past size
            
            if self.get_current_token()[0] != ']':
                raise SemanticError(f"Expected ']', got {self.get_current_token()[0]}", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            self.advance()  # Move past ']'
            
            # Check for second dimension [size2]
            if self.get_current_token()[0] == '[':
                array_dimensions += 1
                self.advance()  # Move past '['
                
                # Parse size expression
                size2_token_type, size2_value, size2_line, size2_column = self.get_current_token()
                
                if size2_token_type not in ['ntlit', 'id']:
                    raise SemanticError(f"Array size must be an integer constant or variable", size2_line, size2_column)
                
                # If the size is a variable, check that it's declared and of type 'nt'
                if size2_token_type == 'id':
                    size_symbol = self.current_scope.lookup(size2_value)
                    if not size_symbol:
                        raise SemanticError(f"Undefined variable '{size2_value}' used as array size", size2_line, size2_column)
                    if size_symbol.data_type != 'nt':
                        raise SemanticError(f"Array size must be of type 'nt', got '{size_symbol.data_type}'", size2_line, size2_column)
                    if not size_symbol.initialized:
                        raise SemanticError(f"Uninitialized variable '{size2_value}' used as array size", size2_line, size2_column)
                    array_sizes.append(size2_value)  # Store the variable name
                else:
                    # It's a literal, make sure it's positive
                    size2 = int(size2_value)
                    if size2 <= 0:
                        raise SemanticError(f"Array size must be positive, got {size2}", size2_line, size2_column)
                    array_sizes.append(size2)
                
                self.advance()  # Move past size
                
                if self.get_current_token()[0] != ']':
                    raise SemanticError(f"Expected ']', got {self.get_current_token()[0]}", 
                                    self.get_current_token()[2], self.get_current_token()[3])
                
                self.advance()  # Move past ']'
            
            # Create array symbol
            symbol = Symbol(
                name=var_name,
                type='variable',
                data_type=data_type,
                initialized=False,
                is_constant=is_constant,
                is_array=True,
                array_dimensions=array_dimensions,
                array_sizes=array_sizes,
                line=name_line,
                column=name_column
            )
            
            # Check for initialization
            if self.get_current_token()[0] == '=':
                self.advance()  # Move past '='
                
                # Handle array initialization
                if self.get_current_token()[0] != '{':
                    raise SemanticError(f"Expected '{{' for array initialization, got {self.get_current_token()[0]}", 
                                    self.get_current_token()[2], self.get_current_token()[3])
                
                # Process array initialization
                if array_dimensions == 1:
                    self.validate_1d_array_init(symbol, data_type, array_sizes[0])
                elif array_dimensions == 2:
                    self.validate_2d_array_init(symbol, data_type, array_sizes[0], array_sizes[1])
                
                symbol.initialized = True
            elif is_constant:
                # Constants must be initialized
                raise SemanticError(f"Constant array '{var_name}' must be initialized", name_line, name_column)
            
            # Add the array symbol to the symbol table
            self.current_scope.insert(var_name, symbol)
            print(f"Added array '{var_name}' of type '{data_type}' with dimensions {array_dimensions} to scope '{self.current_scope.scope_name}'")
            
        else:
            # This is a regular variable, not an array
            # Create symbol
            symbol = Symbol(
                name=var_name,
                type='variable',
                data_type=data_type,
                initialized=False,
                is_constant=is_constant,
                line=name_line,
                column=name_column
            )
            
            # Check for initialization
            if self.get_current_token()[0] == '=':
                self.advance()  # Move past '='
                
                # Save starting position for expression analysis
                start_pos = self.current_token_index
                
                # Skip ahead to find the end of the expression (semicolon or comma)
                while (self.current_token_index < len(self.token_stream) and 
                    self.token_stream[self.current_token_index][0] not in [';', ',']):
                    self.advance()
                
                # Reset position to start of expression
                end_pos = self.current_token_index
                self.current_token_index = start_pos
                
                # Analyze the expression
                expr_type = self.analyze_expression(end_pos)
                
                # Check if the expression type matches the variable type
                if data_type != expr_type:
                    # Special case for boolean variables being assigned relational expressions
                    if data_type == 'bln' and expr_type == 'bln':
                        # This is fine, expression results in boolean and variable is boolean
                        pass
                    else:
                        raise SemanticError(
                            f"Type mismatch: Cannot initialize '{data_type}' with {expr_type}",
                            name_line, name_column
                        )
                
                symbol.initialized = True
                
                # Move to end of expression
                self.current_token_index = end_pos
            
            # Add the variable symbol to the symbol table
            self.current_scope.insert(var_name, symbol)
            print(f"Added variable '{var_name}' of type '{data_type}' to scope '{self.current_scope.scope_name}'")
        
        # Check for comma or semicolon
        if self.get_current_token()[0] == ',':
            self.advance()  # Move past comma
            self.process_array_or_variable(data_type, is_constant)  # Process next variable or array
        elif self.get_current_token()[0] == ';':
            self.advance()  # Move past semicolon
        else:
            raise SemanticError(f"Expected ',' or ';', got {self.get_current_token()[0]}", 
                            self.get_current_token()[2], self.get_current_token()[3])

    def validate_1d_array_init(self, symbol, data_type, size):
        """Validate 1D array initialization"""
        self.advance()  # Move past '{'
        
        element_count = 0
        
        # Process elements until we see '}'
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != '}':
            # Get element
            elem_type, elem_value, elem_line, elem_column = self.get_current_token()
            
            # Validate element type
            if data_type == 'nt' and elem_type not in ['ntlit', '~ntlit', 'id']:
                raise SemanticError(f"Type mismatch: Array element must be 'nt', got '{elem_type}'", 
                                elem_line, elem_column)
            elif data_type == 'dbl' and elem_type not in ['dbllit', '~dbllit', 'ntlit', '~ntlit', 'id']:
                raise SemanticError(f"Type mismatch: Array element must be 'dbl', got '{elem_type}'", 
                                elem_line, elem_column)
            elif data_type == 'bln' and elem_type not in ['true', 'false', 'blnlit', 'id']:
                raise SemanticError(f"Type mismatch: Array element must be 'bln', got '{elem_type}'", 
                                elem_line, elem_column)
            elif data_type == 'chr' and elem_type not in ['chrlit', 'id']:
                raise SemanticError(f"Type mismatch: Array element must be 'chr', got '{elem_type}'", 
                                elem_line, elem_column)
            elif data_type == 'strng' and elem_type not in ['strnglit', 'id']:
                raise SemanticError(f"Type mismatch: Array element must be 'strng', got '{elem_type}'", 
                                elem_line, elem_column)
            
            # If element is an identifier, check if it's declared and of the right type
            if elem_type == 'id':
                elem_symbol = self.current_scope.lookup(elem_value)
                if not elem_symbol:
                    raise SemanticError(f"Undefined variable '{elem_value}' used as array element", 
                                    elem_line, elem_column)
                if elem_symbol.data_type != data_type:
                    raise SemanticError(f"Type mismatch: Array element must be '{data_type}', got '{elem_symbol.data_type}'", 
                                    elem_line, elem_column)
                if not elem_symbol.initialized:
                    raise SemanticError(f"Uninitialized variable '{elem_value}' used as array element", 
                                    elem_line, elem_column)
            
            element_count += 1
            self.advance()  # Move past element
            
            # Skip comma if present
            if self.get_current_token()[0] == ',':
                self.advance()
        
        # Check if we've gone over the array size
        if isinstance(size, int) and element_count > size:
            raise SemanticError(f"Array initialization has {element_count} elements, but array size is {size}", 
                            self.get_current_token()[2], self.get_current_token()[3])
        
        # For constant arrays, ensure all elements are initialized
        if symbol.is_constant and isinstance(size, int) and element_count < size:
            raise SemanticError(f"Constant array must initialize all {size} elements, but only {element_count} provided", 
                            self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Move past '}'

    def validate_2d_array_init(self, symbol, data_type, rows, cols):
        """Validate 2D array initialization"""
        self.advance()  # Move past '{'
        
        row_count = 0
        
        # Process rows until we see '}'
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != '}':
            if self.get_current_token()[0] != '{':
                raise SemanticError(f"Expected '{{' for 2D array row, got {self.get_current_token()[0]}", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            self.advance()  # Move past '{'
            
            col_count = 0
            
            # Process elements in this row
            while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != '}':
                # Get element
                elem_type, elem_value, elem_line, elem_column = self.get_current_token()
                
                # Validate element type (same as 1D array validation)
                if data_type == 'nt' and elem_type not in ['ntlit', '~ntlit', 'id']:
                    raise SemanticError(f"Type mismatch: Array element must be 'nt', got '{elem_type}'", 
                                    elem_line, elem_column)
                elif data_type == 'dbl' and elem_type not in ['dbllit', '~dbllit', 'ntlit', '~ntlit', 'id']:
                    raise SemanticError(f"Type mismatch: Array element must be 'dbl', got '{elem_type}'", 
                                    elem_line, elem_column)
                elif data_type == 'bln' and elem_type not in ['true', 'false', 'blnlit', 'id']:
                    raise SemanticError(f"Type mismatch: Array element must be 'bln', got '{elem_type}'", 
                                    elem_line, elem_column)
                elif data_type == 'chr' and elem_type not in ['chrlit', 'id']:
                    raise SemanticError(f"Type mismatch: Array element must be 'chr', got '{elem_type}'", 
                                    elem_line, elem_column)
                elif data_type == 'strng' and elem_type not in ['strnglit', 'id']:
                    raise SemanticError(f"Type mismatch: Array element must be 'strng', got '{elem_type}'", 
                                    elem_line, elem_column)
                
                # If element is an identifier, check its type
                if elem_type == 'id':
                    elem_symbol = self.current_scope.lookup(elem_value)
                    if not elem_symbol:
                        raise SemanticError(f"Undefined variable '{elem_value}' used as array element", 
                                        elem_line, elem_column)
                    if elem_symbol.data_type != data_type:
                        raise SemanticError(f"Type mismatch: Array element must be '{data_type}', got '{elem_symbol.data_type}'", 
                                        elem_line, elem_column)
                    if not elem_symbol.initialized:
                        raise SemanticError(f"Uninitialized variable '{elem_value}' used as array element", 
                                        elem_line, elem_column)
                
                col_count += 1
                self.advance()  # Move past element
                
                # Skip comma if present
                if self.get_current_token()[0] == ',':
                    self.advance()
            
            # Check if we've gone over the columns size
            if isinstance(cols, int) and col_count > cols:
                raise SemanticError(f"Row {row_count} has {col_count} elements, but array column size is {cols}", 
                                self.get_current_token()[2], self.get_current_token()[3])
                                
            # For constant arrays, ensure all elements in each row are initialized
            if symbol.is_constant and isinstance(cols, int) and col_count < cols:
                raise SemanticError(f"Constant array row must initialize all {cols} elements, but only {col_count} provided", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            self.advance()  # Move past '}' for this row
            row_count += 1
            
            # Skip comma if present
            if self.get_current_token()[0] == ',':
                self.advance()
        
        # Check if we've gone over the rows size
        if isinstance(rows, int) and row_count > rows:
            raise SemanticError(f"Array initialization has {row_count} rows, but array row size is {rows}", 
                            self.get_current_token()[2], self.get_current_token()[3])
        
        # For constant arrays, ensure all rows are initialized
        if symbol.is_constant and isinstance(rows, int) and row_count < rows:
            raise SemanticError(f"Constant array must initialize all {rows} rows, but only {row_count} provided", 
                            self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Move past '}'

    def analyze_array_access(self):
        """
        Analyze array element access (reading or assignment LHS) and return the element type.
        This function only analyzes the `id[...]` part, not the assignment or RHS.
        """
        var_token_type, var_name, line, column = self.get_current_token()

        # Check if variable exists
        symbol = self.current_scope.lookup(var_name)
        if not symbol:
            raise SemanticError(f"Undefined variable '{var_name}'", line, column)

        # Check that it's an array
        if not symbol.is_array:
            raise SemanticError(f"Variable '{var_name}' is not an array", line, column)

        self.advance()  # Move past array name

        # Process array index(es)
        # First dimension
        if self.get_current_token()[0] != '[':
            raise SemanticError(f"Expected '[', got {self.get_current_token()[0]}",
                            self.get_current_token()[2], self.get_current_token()[3])

        self.advance()  # Move past '['

        # Save the current index token for bounds checking
        index1_token_type, index1_value, index1_line, index1_column = self.get_current_token()

        # Find the end of this index expression (should be the closing bracket)
        start_pos = self.current_token_index
        bracket_level = 1

        while bracket_level > 0 and self.current_token_index < len(self.token_stream):
            # Need to check for nested brackets within the index expression
            current_token = self.token_stream[self.current_token_index][0]
            if current_token == '[':
                bracket_level += 1
            elif current_token == ']':
                bracket_level -= 1

            if bracket_level > 0: # Advance only if still inside brackets
                self.current_token_index += 1

            if self.current_token_index >= len(self.token_stream):
                raise SemanticError("Unclosed bracket in array access", line, column)


        # Now self.current_token_index is at the closing ']'
        end_pos = self.current_token_index
        self.current_token_index = start_pos # Reset position to analyze the expression

        # Analyze the index expression - it must evaluate to type nt
        index1_type = self.analyze_expression(end_pos)
        if index1_type != 'nt':
            raise SemanticError(f"Array index must be of type 'nt', got '{index1_type}'",
                            index1_line, index1_column)

        # Check bounds if index is a literal and size is known
        if index1_token_type == 'ntlit' and isinstance(symbol.array_sizes[0], int):
            index1 = int(index1_value)
            if index1 < 0 or index1 >= symbol.array_sizes[0]:
                raise SemanticError(f"Array index {index1} out of bounds (size {symbol.array_sizes[0]})",
                                index1_line, index1_column)

        # Move past the closing bracket
        if self.get_current_token()[0] != ']':
             # This should not happen if the loop above worked correctly, but as a safeguard
             raise SemanticError(f"Expected ']', got {self.get_current_token()[0]} after index expression",
                             self.get_current_token()[2], self.get_current_token()[3])
        self.advance()  # Move past ']'

        # Check for second dimension if this is a 2D array
        if symbol.array_dimensions == 2:
            if self.get_current_token()[0] != '[':
                raise SemanticError(f"Expected second dimension '[' for 2D array, got {self.get_current_token()[0]}",
                                self.get_current_token()[2], self.get_current_token()[3])

            self.advance()  # Move past '['

            # Save the current index token for bounds checking
            index2_token_type, index2_value, index2_line, index2_column = self.get_current_token()

            # Find the end of this index expression (should be the closing bracket)
            start_pos = self.current_token_index
            bracket_level = 1

            while bracket_level > 0 and self.current_token_index < len(self.token_stream):
                # Need to check for nested brackets within the index expression
                current_token = self.token_stream[self.current_token_index][0]
                if current_token == '[':
                    bracket_level += 1
                elif current_token == ']':
                    bracket_level -= 1

                if bracket_level > 0: # Advance only if still inside brackets
                     self.current_token_index += 1

                if self.current_token_index >= len(self.token_stream):
                    raise SemanticError("Unclosed bracket in 2D array access", line, column)

            # Now self.current_token_index is at the closing ']'
            end_pos = self.current_token_index
            self.current_token_index = start_pos # Reset position to analyze the expression

            # Validate index expression is of type nt
            index2_type = self.analyze_expression(end_pos)
            if index2_type != 'nt':
                raise SemanticError(f"Array index must be of type 'nt', got '{index2_type}'",
                                index2_line, index2_column)

            # Check bounds if index is a literal and size is known
            if index2_token_type == 'ntlit' and isinstance(symbol.array_sizes[1], int):
                index2 = int(index2_value)
                if index2 < 0 or index2 >= symbol.array_sizes[1]:
                    raise SemanticError(f"Array index {index2} out of bounds (size {symbol.array_sizes[1]})",
                                    index2_line, index2_column)

            # Move past the closing bracket
            if self.get_current_token()[0] != ']':
                 # This should not happen if the loop above worked correctly, but as a safeguard
                 raise SemanticError(f"Expected ']', got {self.get_current_token()[0]} after 2nd index expression",
                             self.get_current_token()[2], self.get_current_token()[3])
            self.advance()  # Move past ']'

        # Return the data type of the array element
        # The caller (analyze_assignment) will handle the '=' and the RHS
        print(f"Finished analyzing array access for '{var_name}[...]', element type: {symbol.data_type}")
        return symbol.data_type # Return the type of the element

    
    def analyze_expression(self, end_pos):
        """Analyze an expression and determine its resulting type using strict type rules"""
        # Add debug output
        print(f"Analyzing expression from position {self.current_token_index} to {end_pos}")
        
        # Save current position
        original_pos = self.current_token_index
        
        # Debug - show the tokens being analyzed
        expr_tokens = self.token_stream[original_pos:end_pos]
        expr_str = " ".join([f"{t[0]}('{t[1]}')" for t in expr_tokens])
        print(f"Expression tokens: {expr_str}")
        
        # Check if this is a simple function call expression
        if (self.current_token_index < len(self.token_stream) and 
                self.token_stream[self.current_token_index][0] == 'id'):
            
            func_name = self.token_stream[self.current_token_index][1]
            next_pos = self.current_token_index + 1
            
            # Check if next token is opening parenthesis (function call)
            if (next_pos < len(self.token_stream) and 
                    self.token_stream[next_pos][0] == '('):
                
                # This might be a function call - use our specialized function call parser
                return_type = self.analyze_function_call()
                
                # If we're at or beyond the end_pos, we're done
                if self.current_token_index >= end_pos:
                    return return_type
                
                # Otherwise reset position and fall back to regular expression parsing
                self.current_token_index = original_pos
            
            # Check if next token is dot (struct member access)
            elif (next_pos < len(self.token_stream) and 
                self.token_stream[next_pos][0] == '.'):
                print(f"Found potential struct member access: {func_name}.{self.token_stream[next_pos+1][1]}")
                
                # This is a struct member access - use our specialized struct member access parser
                member_type = self.analyze_struct_member_access()
                
                # If we're at or beyond the end_pos, we're done
                if self.current_token_index >= end_pos:
                    return member_type
                
                # Otherwise reset position and fall back to regular expression parsing
                self.current_token_index = original_pos
                
            # NEW: Check if next token is square bracket (array access)
            elif (next_pos < len(self.token_stream) and 
                self.token_stream[next_pos][0] == '['):
                print(f"Found potential array access: {func_name}[...]")
                
                # This is an array access - we need to handle it specially
                element_type = self.analyze_array_element()
                
                # If we're at or beyond the end_pos, we're done
                if self.current_token_index >= end_pos:
                    return element_type
                
                # Otherwise reset position and fall back to regular expression parsing
                self.current_token_index = original_pos
        
        # Regular expression parsing
        result_type, has_relational = self._parse_expression(end_pos)
        print(f"Expression result type: {result_type}, has relational: {has_relational}")
        return result_type
    
    def _parse_expression(self, end_pos):
        """
        Parse an expression and return its type and if it contains relational operators.
        Returns a tuple (type, has_relational_op)
        
        UPDATED to handle nested parentheses correctly.
        """
        # For complex expressions, we need to track:
        # 1. The current operand type we're working with
        # 2. The current operator (if any)
        # 3. Whether we're expecting an operand or operator
        
        current_type = None
        current_operator = None
        expecting_operand = True
        
        # If this is a relational expression, the result is boolean
        contains_relational_op = False
        
        # Debug output
        print(f"Parsing expression from position {self.current_token_index} to {end_pos}")
        # Print tokens being parsed
        expr_tokens = self.token_stream[self.current_token_index:end_pos]
        expr_str = " ".join([f"{t[0]}('{t[1]}')" for t in expr_tokens])
        print(f"Expression tokens: {expr_str}")
        
        while self.current_token_index < end_pos:
            token_type, token_value, line, column = self.get_current_token()
            print(f"Processing token: {token_type} '{token_value}'")
            
            # Handle opening parenthesis - parse subexpression
            if token_type == '(':
                self.advance()  # Skip over the opening parenthesis
                
                # Parse the subexpression - find matching closing parenthesis first
                subexpr_start = self.current_token_index
                paren_level = 1
                subexpr_end = None
                
                # Find matching closing parenthesis
                temp_pos = self.current_token_index
                while paren_level > 0 and temp_pos < end_pos:
                    temp_token_type = self.token_stream[temp_pos][0]
                    if temp_token_type == '(':
                        paren_level += 1
                    elif temp_token_type == ')':
                        paren_level -= 1
                        if paren_level == 0:
                            subexpr_end = temp_pos
                    temp_pos += 1
                
                if subexpr_end is None:
                    raise SemanticError("Unclosed parenthesis", line, column)
                
                # Recursively parse the subexpression
                subexpr_type, subexpr_relational = self._parse_expression(subexpr_end)
                print(f"Subexpression type: {subexpr_type}, relational: {subexpr_relational}")
                
                # Move to position after the closing parenthesis
                self.current_token_index = subexpr_end + 1
                
                # Update current state
                if current_operator:
                    # Check compatibility with operator
                    if current_operator in self.arithmetic_operators:
                        # Arithmetic operators require numeric operands, allow mixing nt and dbl
                        if current_type not in ['nt', 'dbl'] or subexpr_type not in ['nt', 'dbl']:
                            print(f"ERROR: Cannot apply '{current_operator}' to '{current_type}' and '{subexpr_type}'")
                            raise SemanticError(
                                f"Type mismatch: Cannot apply '{current_operator}' to '{current_type}' and '{subexpr_type}'",
                                line, column
                            )
                        
                        # If we mix nt and dbl, the result is dbl
                        if current_type == 'dbl' or subexpr_type == 'dbl':
                            current_type = 'dbl'
                        else:
                            # Both are nt, result remains nt
                            current_type = 'nt'
                            
                    elif current_operator in self.logical_operators:
                        # Logical operators require boolean operands
                        if current_type != 'bln' or subexpr_type != 'bln':
                            print(f"ERROR: Cannot apply '{current_operator}' to '{current_type}' and '{subexpr_type}'")
                            raise SemanticError(
                                f"Type mismatch: Cannot apply '{current_operator}' to '{current_type}' and '{subexpr_type}'",
                                line, column
                            )
                        # Result is boolean
                        current_type = 'bln'
                    elif current_operator in self.relational_operators:
                        # Relational operators behavior depends on specific operator
                        if current_operator in self.equality_operators:
                            # == and != work for all types, but both operands must be same type
                            # However, we'll allow comparing nt with dbl
                            if current_type != subexpr_type:
                                # Allow comparing nt with dbl
                                if not ((current_type == 'nt' and subexpr_type == 'dbl') or 
                                    (current_type == 'dbl' and subexpr_type == 'nt')):
                                    print(f"ERROR: Cannot compare '{current_type}' with '{subexpr_type}'")
                                    raise SemanticError(
                                        f"Type mismatch: Cannot compare '{current_type}' with '{subexpr_type}'",
                                        line, column
                                    )
                        else:
                            # <, >, <=, >= only work for numeric types - now allow mixing nt and dbl
                            if current_type not in ['nt', 'dbl'] or subexpr_type not in ['nt', 'dbl']:
                                print(f"ERROR: Cannot apply '{current_operator}' to '{current_type}' and '{subexpr_type}'")
                                raise SemanticError(
                                    f"Type mismatch: Cannot apply '{current_operator}' to '{current_type}' and '{subexpr_type}'",
                                    line, column
                                )
                        
                        # Result is boolean
                        current_type = 'bln'
                        contains_relational_op = True
                    elif current_operator in self.string_concat_operator:
                        # String concatenation requires string operands
                        if current_type != 'strng' or subexpr_type != 'strng':
                            print(f"ERROR: Cannot concatenate '{current_type}' with '{subexpr_type}'")
                            raise SemanticError(
                                f"Type mismatch: Cannot concatenate '{current_type}' with '{subexpr_type}'",
                                line, column
                            )
                        # Result is string
                        current_type = 'strng'
                    
                    # Reset operator after applying it
                    current_operator = None
                    expecting_operand = False
                else:
                    # This is the first operand
                    current_type = subexpr_type
                    contains_relational_op = contains_relational_op or subexpr_relational
                    expecting_operand = False
                
                # Update relational operator flag
                contains_relational_op = contains_relational_op or subexpr_relational
                
                continue
            
            # Handle operands (values, variables, function calls, struct member access)
            if expecting_operand:
                operand_type = None

                 # Handle pre-increment/decrement operators
                if token_type in ['++', '--']:
                    print(f"Found pre-{token_type} operator")
                    pre_op = token_type
                    self.advance()  # Move past the operator
                    
                    # Must be followed by an identifier
                    if self.get_current_token()[0] != 'id':
                        print(f"ERROR: {pre_op} must be followed by an identifier")
                        raise SemanticError(f"{pre_op} operator must be followed by an identifier", line, column)
                    
                    var_name = self.get_current_token()[1]
                    var_line, var_column = self.get_current_token()[2], self.get_current_token()[3]
                    
                    # Check if variable exists
                    symbol = self.current_scope.lookup(var_name)
                    if not symbol:
                        print(f"ERROR: Undefined variable '{var_name}'")
                        raise SemanticError(f"Undefined variable '{var_name}'", var_line, var_column)
                    
                    # Check if variable is of type 'nt'
                    if symbol.data_type != 'nt':
                        print(f"ERROR: {pre_op} operator can only be applied to 'nt' variables, not '{symbol.data_type}'")
                        raise SemanticError(f"{pre_op} operator can only be applied to 'nt' variables, not '{symbol.data_type}'", 
                                        var_line, var_column)
                    
                    # Pre-increment/decrement returns the modified value
                    operand_type = 'nt'
                    self.advance()  # Move past the variable name
                
                # Determine the type of the current operand
                elif token_type in ['ntlit', '~ntlit']:
                    operand_type = 'nt'
                    if current_operator == '/' and token_value == '0':
                        raise SemanticError(f"Division by zero detected", line, column)
                    self.advance()
                elif token_type in ['dbllit', '~dbllit']:
                    operand_type = 'dbl'
                    if current_operator == '/' and token_value == '0':
                        raise SemanticError(f"Division by zero detected", line, column)
                    self.advance()
                elif token_type in ['true', 'false', 'blnlit']:
                    operand_type = 'bln'
                    self.advance()
                elif token_type == 'chrlit':
                    operand_type = 'chr'
                    self.advance()
                elif token_type == 'strnglit':
                    operand_type = 'strng'
                    self.advance()
                elif token_type == 'id':
                    # Save position for lookahead
                    save_pos = self.current_token_index
                    var_name = token_value
                    
                    # Look ahead to see what follows the identifier
                    self.advance()
                    if self.current_token_index < end_pos:
                        next_token = self.get_current_token()[0]

                        # Check for array access: id[...]
                        if next_token == '[':
                            print(f"Found array access in expression: {var_name}[...]")
                            # Go back to array name
                            self.current_token_index = save_pos
                            
                            # Get array element type
                            operand_type = self.analyze_array_element()
                            print(f"Array element type in expression: {operand_type}")
                        
                        # Check for post-increment or post-decrement
                        elif next_token in ['++', '--']:
                            # These operators can only be applied to 'nt' variables
                            symbol = self.current_scope.lookup(var_name)
                            if not symbol:
                                raise SemanticError(f"Undefined variable '{var_name}'", line, column)
                            
                            if symbol.data_type != 'nt':
                                print(f"ERROR: Increment/decrement only applies to 'nt' variables, not '{symbol.data_type}'")
                                raise SemanticError(f"Increment/decrement operators can only be applied to 'nt' variables, not '{symbol.data_type}'", 
                                                line, column)
                            
                            operand_type = 'nt'
                            self.advance()  # Move past the operator
                        
                        # Check for function call: id(...)
                        elif next_token == '(':
                            # This is a function call within an expression
                            # Go back to function name
                            self.current_token_index = save_pos
                            
                            # Process function call and get its return type
                            operand_type = self.analyze_function_call()
                            
                            # If the function is void, it can't be used in an expression
                            if operand_type == 'vd':
                                print(f"ERROR: Void function '{var_name}' cannot be used in expression")
                                raise SemanticError(f"Void function '{var_name}' cannot be used in an expression", line, column)
                        
                        # Check for struct member access: id.member
                        elif next_token == '.':
                            print(f"Processing struct member access in _parse_expression: {var_name}.{self.token_stream[self.current_token_index+1][1]}")
                            # This is a struct member access
                            # Go back to struct instance name
                            self.current_token_index = save_pos
                            
                            # Process struct member access and get its type
                            operand_type = self.analyze_struct_member_access()
                        
                        else:
                            # Not a function call or struct member access, just a variable reference
                            self.current_token_index = save_pos
                            
                            # Get type from symbol table
                            symbol = self.current_scope.lookup(var_name)
                            if not symbol:
                                print(f"ERROR: Undefined variable '{var_name}'")
                                raise SemanticError(f"Undefined variable '{var_name}'", line, column)
                            
                            # Check if it's a function being used without parentheses
                            if symbol.type == 'function':
                                print(f"ERROR: Function '{var_name}' used without parentheses")
                                raise SemanticError(f"Function '{var_name}' used without parentheses", line, column)
                            
                            # Check if variable is initialized
                            if not symbol.initialized:
                                print(f"Warning: Variable '{var_name}' may be used before initialization at line {line}, column {column}")
                            
                            operand_type = symbol.data_type
                            self.advance()
                    else:
                        # We're at the end - treat as variable reference
                        self.current_token_index = save_pos
                        
                        # Get type from symbol table
                        symbol = self.current_scope.lookup(var_name)
                        if not symbol:
                            print(f"ERROR: Undefined variable '{var_name}'")
                            raise SemanticError(f"Undefined variable '{var_name}'", line, column)
                        
                        operand_type = symbol.data_type
                        self.advance()
                elif token_type == '!':
                    # Logical NOT operator
                    self.advance()  # Skip !
                    
                    # Track number of consecutive NOT operators
                    not_count = 1
                    while self.current_token_index < end_pos and self.token_stream[self.current_token_index][0] == '!':
                        not_count += 1
                        self.advance()  # Skip additional ! operators
                    
                    # Handle subexpression after the series of ! operators
                    if self.current_token_index < end_pos:
                        next_token_type = self.token_stream[self.current_token_index][0]
                        next_token_value = self.token_stream[self.current_token_index][1]
                        next_line = self.token_stream[self.current_token_index][2]
                        next_column = self.token_stream[self.current_token_index][3]
                        
                        if next_token_type == '(':
                            # Process parenthesized expression after !
                            self.advance()  # Skip (
                            
                            # Find closing parenthesis
                            start_pos = self.current_token_index
                            paren_level = 1
                            while paren_level > 0 and self.current_token_index < end_pos:
                                self.advance()
                                if self.current_token_index >= len(self.token_stream):
                                    raise SemanticError("Unclosed parenthesis after '!'", line, column)
                                
                                current_token = self.token_stream[self.current_token_index][0]
                                if current_token == '(':
                                    paren_level += 1
                                elif current_token == ')':
                                    paren_level -= 1
                            
                            # Current token is now at the closing parenthesis
                            subexpr_end = self.current_token_index
                            self.current_token_index = start_pos
                            
                            # Parse the subexpression
                            subexpr_type, _ = self._parse_expression(subexpr_end)
                            
                            # Skip the closing parenthesis
                            self.advance()
                            
                            if subexpr_type != 'bln':
                                print(f"ERROR: Cannot apply '!' to non-boolean type '{subexpr_type}'")
                                raise SemanticError(f"Type mismatch: Cannot apply '!' to non-boolean type '{subexpr_type}'", line, column)
                            
                            # The result is always boolean, regardless of how many ! operators
                            # If there's an odd number of ! operators, the value is negated
                            # If there's an even number, it's equivalent to the original value
                            current_type = 'bln'
                        else:
                            # Not a parenthesized expression - check the identifier or literal
                            if next_token_type == 'id':
                                # Variable reference
                                symbol = self.current_scope.lookup(next_token_value)
                                if not symbol:
                                    print(f"ERROR: Undefined variable '{next_token_value}'")
                                    raise SemanticError(f"Undefined variable '{next_token_value}'", next_line, next_column)
                                
                                subexpr_type = symbol.data_type
                            elif next_token_type in ['true', 'false', 'blnlit']:
                                subexpr_type = 'bln'
                            else:
                                # For other token types, get their corresponding type
                                subexpr_type = self.get_token_type(next_token_type)
                            
                            if subexpr_type != 'bln':
                                print(f"ERROR: Cannot apply '!' to non-boolean type '{subexpr_type}'")
                                raise SemanticError(f"Type mismatch: Cannot apply '!' to non-boolean type '{subexpr_type}'", next_line, next_column)
                            
                            self.advance()  # Skip the operand
                            current_type = 'bln'
                        
                        expecting_operand = False
                        
                    else:
                        # No operand after ! operator
                        raise SemanticError("Unexpected end of expression after '!'", line, column)
                    
                    operand_type = 'bln'
                    current_type = operand_type 
                    expecting_operand = False
                    continue
                elif token_type == 'npt':
                    print(f"Found npt function in expression")
                    # This is a built-in function for input
                    # Use our function call analyzer which now handles npt
                    operand_type = self.analyze_function_call()
                else:
                    # Unknown token in expression
                    print(f"ERROR: Unexpected token '{token_type}' in expression")
                    raise SemanticError(f"Unexpected token '{token_type}' in expression", line, column)
                
                # Handle the operand in context
                if current_type is None:
                    # This is the first operand
                    current_type = operand_type
                elif current_operator:
                    # This is a right operand - check compatibility with operator and left operand
                    if current_operator in self.arithmetic_operators:
                        # Arithmetic operators require numeric operands - now allow mixing nt and dbl
                        if current_type not in ['nt', 'dbl'] or operand_type not in ['nt', 'dbl']:
                            print(f"ERROR: Cannot apply '{current_operator}' to '{current_type}' and '{operand_type}'")
                            raise SemanticError(
                                f"Type mismatch: Cannot apply '{current_operator}' to '{current_type}' and '{operand_type}'",
                                line, column
                            )
                        
                        # If we mix nt and dbl, the result is dbl
                        if current_type == 'dbl' or operand_type == 'dbl':
                            current_type = 'dbl'
                        else:
                            # Both are nt, result remains nt
                            current_type = 'nt'
                            
                    elif current_operator in self.logical_operators:
                        # Logical operators require boolean operands
                        if current_type != 'bln' or operand_type != 'bln':
                            print(f"ERROR: Cannot apply '{current_operator}' to '{current_type}' and '{operand_type}'")
                            raise SemanticError(
                                f"Type mismatch: Cannot apply '{current_operator}' to '{current_type}' and '{operand_type}'",
                                line, column
                            )
                        # Result is boolean
                        current_type = 'bln'
                    elif current_operator in self.relational_operators:
                        # Relational operators behavior depends on specific operator
                        if current_operator in self.equality_operators:
                            # == and != work for all types, but operands must match
                            # However, we'll allow comparing nt with dbl
                            if current_type != operand_type:
                                # Allow comparing nt with dbl
                                if not ((current_type == 'nt' and operand_type == 'dbl') or 
                                    (current_type == 'dbl' and operand_type == 'nt')):
                                    print(f"ERROR: Cannot compare '{current_type}' with '{operand_type}'")
                                    raise SemanticError(
                                        f"Type mismatch: Cannot compare '{current_type}' with '{operand_type}'",
                                        line, column
                                    )
                        else:
                            # <, >, <=, >= only work for numeric types - now allow mixing nt and dbl
                            if current_type not in ['nt', 'dbl'] or operand_type not in ['nt', 'dbl']:
                                print(f"ERROR: Cannot apply '{current_operator}' to '{current_type}' and '{operand_type}'")
                                raise SemanticError(
                                    f"Type mismatch: Cannot apply '{current_operator}' to '{current_type}' and '{operand_type}'",
                                    line, column
                                )
                        
                        # Result is always boolean
                        current_type = 'bln'
                        contains_relational_op = True
                    elif current_operator in self.string_concat_operator:
                        # String concatenation requires string operands
                        if current_type != 'strng' or operand_type != 'strng':
                            print(f"ERROR: Cannot concatenate '{current_type}' with '{operand_type}'")
                            raise SemanticError(
                                f"Type mismatch: Cannot concatenate '{current_type}' with '{operand_type}'",
                                line, column
                            )
                        # Result is string
                        current_type = 'strng'
                    
                    # Clear the operator now that it's been applied
                    current_operator = None
                
                expecting_operand = False
            
            # Handle operators
            else:
                if token_type in self.arithmetic_operators:
                    # Verify current type supports arithmetic
                    if current_type not in ['nt', 'dbl']:
                        print(f"ERROR: Cannot apply arithmetic operator '{token_type}' to '{current_type}'")
                        raise SemanticError(
                            f"Type mismatch: Cannot apply '{token_type}' to '{current_type}'",
                            line, column
                        )
                    current_operator = token_type
                    expecting_operand = True
                    self.advance()
                elif token_type in self.logical_operators:
                    # Verify current type is boolean
                    if current_type != 'bln':
                        print(f"ERROR: Cannot apply logical operator '{token_type}' to '{current_type}'")
                        raise SemanticError(
                            f"Type mismatch: Cannot apply '{token_type}' to '{current_type}'",
                            line, column
                        )
                    current_operator = token_type
                    expecting_operand = True
                    self.advance()
                elif token_type in self.relational_operators:
                    # For relational operators, verify based on specific operator
                    if token_type in self.equality_operators:
                        # == and != work for all types
                        # No additional checks needed here, will check type match with right operand
                        pass
                    else:
                        # <, >, <=, >= only work with numeric types
                        if current_type not in ['nt', 'dbl']:
                            print(f"ERROR: Cannot apply relational operator '{token_type}' to '{current_type}'")
                            raise SemanticError(
                                f"Type mismatch: Cannot apply '{token_type}' to '{current_type}'",
                                line, column
                            )
                    
                    # Store the relational operator
                    current_operator = token_type
                    contains_relational_op = True
                    expecting_operand = True
                    self.advance()
                elif token_type == '`':
                    # String concatenation operator
                    if current_type != 'strng':
                        print(f"ERROR: Cannot apply string concatenation to non-string type '{current_type}'")
                        raise SemanticError(
                            f"Type mismatch: Cannot apply '`' to non-string type '{current_type}'",
                            line, column
                        )
                    current_operator = token_type
                    expecting_operand = True
                    self.advance()
                elif token_type == ')':
                    # This should be handled by the parenthesis processing logic
                    # If we encounter a closing parenthesis here, it means it's not balanced properly
                    print(f"ERROR: Unexpected closing parenthesis")
                    raise SemanticError(f"Unexpected closing parenthesis", line, column)
                else:
                    # Unknown operator
                    print(f"ERROR: Unexpected token '{token_type}' in expression")
                    raise SemanticError(f"Unexpected token '{token_type}' in expression", line, column)
        
        if expecting_operand:
            print(f"ERROR: Incomplete expression: expecting operand")
            raise SemanticError("Incomplete expression: expecting operand", line, column)
        
        # If we have a pending operator, that's an error
        if current_operator:
            print(f"ERROR: Incomplete expression: missing right operand for '{current_operator}'")
            raise SemanticError(f"Incomplete expression: missing right operand for '{current_operator}'", line, column)
        
        # Print final result for debugging
        print(f"Expression final type: {current_type}, contains relational: {contains_relational_op}")
        
        # If expression contains a relational operator, result is boolean
        if contains_relational_op:
            return 'bln', True
        
        return current_type, contains_relational_op

    def analyze_array_element(self):
        """
        Analyze an array element access expression and return the element type.
        Used for expressions like arr[1] when they appear on right side of assignments.
        """
        # Get array name
        token_type, var_name, line, column = self.get_current_token()
        if token_type != 'id':
            raise SemanticError(f"Expected array identifier, got {token_type}", line, column)
        
        print(f"Analyzing array element access for '{var_name}' at line {line}, column {column}")
        
        # Check if variable exists
        symbol = self.current_scope.lookup(var_name)
        if not symbol:
            raise SemanticError(f"Undefined variable '{var_name}'", line, column)
        
        # Check that it's an array
        if not symbol.is_array:
            raise SemanticError(f"Variable '{var_name}' is not an array", line, column)
        
        self.advance()  # Move past array name
        
        # Process opening bracket
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '[':
            raise SemanticError(f"Expected '[', got {token_type}", line, column)
        
        self.advance()  # Move past '['
        
        # Save the current index token for bounds checking
        index1_token_type, index1_value, index1_line, index1_column = self.get_current_token()
        
        # Find the end of this index expression (should be the closing bracket)
        start_pos = self.current_token_index
        bracket_level = 1
        
        while bracket_level > 0 and self.current_token_index < len(self.token_stream):
            self.current_token_index += 1
            if self.current_token_index >= len(self.token_stream):
                raise SemanticError("Unclosed bracket", line, column)
            
            current_token = self.token_stream[self.current_token_index][0]
            if current_token == '[':
                bracket_level += 1
            elif current_token == ']':
                bracket_level -= 1
        
        end_pos = self.current_token_index
        self.current_token_index = start_pos
        
        # Validate index expression is of type nt
        index1_type = self.analyze_expression(end_pos)
        if index1_type != 'nt':
            raise SemanticError(f"Array index must be of type 'nt', got '{index1_type}'", 
                            index1_line, index1_column)
        
        # Check bounds if index is a literal
        if index1_token_type == 'ntlit' and isinstance(symbol.array_sizes[0], int):
            index1 = int(index1_value)
            if index1 < 0 or index1 >= symbol.array_sizes[0]:
                raise SemanticError(f"Array index {index1} out of bounds (size {symbol.array_sizes[0]})",
                            index1_line, index1_column)
        
        if self.get_current_token()[0] != ']':
            raise SemanticError(f"Expected ']', got {self.get_current_token()[0]}", 
                            self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Move past ']'
        
        # Check for second dimension if this is a 2D array
        if symbol.array_dimensions == 2:
            if self.get_current_token()[0] != '[':
                raise SemanticError(f"Expected second dimension '[' for 2D array, got {self.get_current_token()[0]}", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            self.advance()  # Move past '['
            
            # Save the current index token for bounds checking
            index2_token_type, index2_value, index2_line, index2_column = self.get_current_token()
            
            # Find the end of this index expression (should be the closing bracket)
            start_pos = self.current_token_index
            bracket_level = 1
            
            while bracket_level > 0 and self.current_token_index < len(self.token_stream):
                self.current_token_index += 1
                if self.current_token_index >= len(self.token_stream):
                    raise SemanticError("Unclosed bracket", line, column)
                
                current_token = self.token_stream[self.current_token_index][0]
                if current_token == '[':
                    bracket_level += 1
                elif current_token == ']':
                    bracket_level -= 1
            
            end_pos = self.current_token_index
            self.current_token_index = start_pos
            
            # Validate index expression is of type nt
            index2_type = self.analyze_expression(end_pos)
            if index2_type != 'nt':
                raise SemanticError(f"Array index must be of type 'nt', got '{index2_type}'", 
                                index2_line, index2_column)
            
            # Check bounds if index is a literal
            if index2_token_type == 'ntlit' and isinstance(symbol.array_sizes[1], int):
                index2 = int(index2_value)
                if index2 < 0 or index2 >= symbol.array_sizes[1]:
                    raise SemanticError(f"Array index {index2} out of bounds (size {symbol.array_sizes[1]})",
                                    index2_line, index2_column)
            
            if self.get_current_token()[0] != ']':
                raise SemanticError(f"Expected ']', got {self.get_current_token()[0]}", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            self.advance()  # Move past ']'
        
        # Return the data type of the array element
        print(f"Array element type: {symbol.data_type}")
        return symbol.data_type
    
    def is_compatible_type(self, declared_type, value_type):
        """Check if value type is compatible with declared type"""
        # Map literal types to their corresponding data types
        if value_type in ('ntlit', '~ntlit'):
            return declared_type == 'nt'
        elif value_type in ('dbllit', '~dbllit'):
            return declared_type == 'dbl'
        elif value_type in ('true', 'false', 'blnlit'):
            return declared_type == 'bln'
        elif value_type == 'chrlit':
            return declared_type == 'chr'
        elif value_type == 'strnglit':
            return declared_type == 'strng'
        
        # Handle exact type matching (no type conversion)
        return declared_type == value_type

    def analyze_assignment(self):
        """Analyze variable assignment including shortcut assignment operators"""
        var_token_type, var_name, line, column = self.get_current_token()
        
        # Debug output
        print(f"Analyzing assignment for variable '{var_name}' at line {line}, column {column}")
        
        # Check if variable exists
        symbol = self.current_scope.lookup(var_name)
        if not symbol:
            raise SemanticError(f"Variable '{var_name}' not declared", line, column)
        
        var_type = symbol.data_type
        print(f"Variable '{var_name}' has type '{var_type}'")
        
        # Check if this is a constant
        if symbol.is_constant:
            raise SemanticError(f"Cannot reassign constant '{var_name}'", line, column)
        
        # Move past variable name
        self.advance()
        
        # Check which assignment operator is being used
        token_type, token_value, op_line, op_column = self.get_current_token()
        print(f"Assignment operator: {token_type}")
        
        # Handle increment/decrement operators (++, --)
        if token_type in ['++', '--']:
            # These operators can only be applied to 'nt' variables
            if var_type != 'nt':
                raise SemanticError(f"Increment/decrement operators can only be applied to 'nt' variables, not '{var_type}'", 
                                op_line, op_column)
            
            self.advance()  # Move past the operator
            
            # Check for semicolon
            if self.get_current_token()[0] != ';':
                raise SemanticError(f"Expected ';' after increment/decrement operation", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            self.advance()  # Move past semicolon
            symbol.initialized = True
            return
        
        # Handle compound assignment operators (+=, -=, *=, /=, %=)
        if token_type in ['+=', '-=', '*=', '/=', '%=']:
            print(f"Processing shortcut assignment operator '{token_type}'")
            
            # These operators require numeric operands for variable
            if var_type not in ['nt', 'dbl']:
                raise SemanticError(f"Shortcut assignment operator '{token_type}' can only be applied to numeric types, not '{var_type}'", 
                                op_line, op_column)
            
            self.advance()  # Move past the operator
            
            # Save starting position for expression analysis
            start_pos = self.current_token_index
            
            # Skip ahead to find the end of the expression (semicolon)
            while (self.current_token_index < len(self.token_stream) and 
                self.token_stream[self.current_token_index][0] != ';'):
                self.advance()
            
            # Reset position to start of expression
            end_pos = self.current_token_index
            self.current_token_index = start_pos
            
            # Get the tokens being analyzed for debug
            expr_tokens = self.token_stream[start_pos:end_pos]
            expr_str = " ".join([f"{t[0]}('{t[1]}')" for t in expr_tokens])
            print(f"Expression tokens: {expr_str}")
            
            # Analyze the expression on the right side of the shortcut assignment
            expr_type = self.analyze_expression(end_pos)
            print(f"Expression type: {expr_type}")
            
            # For shortcut assignments, the right operand must be a compatible numeric type
            if expr_type not in ['nt', 'dbl']:
                raise SemanticError(
                    f"Type mismatch: Cannot use '{token_type}' with non-numeric type '{expr_type}'",
                    op_line, op_column
                )
            
            # Mark variable as initialized
            symbol.initialized = True
            
            # Move past the semicolon
            if self.get_current_token()[0] == ';':
                self.advance()  # Move past the semicolon
            return
        
        # Regular assignment (=)
        elif token_type == '=':
            # ... (rest of your existing regular assignment code)
            self.advance()  # Move past the = operator

            # Check if this is an npt input statement directly    
            next_token = self.get_current_token()
            if next_token and next_token[0] == 'npt':
                print(f"Found direct npt function call in assignment for variable '{var_name}'")
                # Use our function call analyzer to process the npt function
                expr_type = self.analyze_function_call()
                
                # npt function returns strng by default, but we'll allow type coercion
                # Type conversion happens at runtime, so we'll just mark the variable as initialized
                symbol.initialized = True
                
                # Current position is now at the semicolon
                if self.get_current_token()[0] == ';':
                    self.advance()  # Move past the semicolon
                
                return
        
            # Save starting position for expression analysis
            start_pos = self.current_token_index
            
            # Skip ahead to find the end of the expression (semicolon)
            while (self.current_token_index < len(self.token_stream) and 
                self.token_stream[self.current_token_index][0] != ';'):
                self.advance()
            
            # Reset position to start of expression
            end_pos = self.current_token_index
            self.current_token_index = start_pos
            
            # Analyze the expression
            expr_type = self.analyze_expression(end_pos)
            
            # Validate assignment compatibility - no implicit conversions in Conso
            if var_type != expr_type:
                # Special case: Boolean variable can be assigned result of relational expression
                if var_type == 'bln' and expr_type == 'bln':
                    # This is valid - a boolean variable can hold the result of a relational expression
                    pass
                else:
                    raise SemanticError(
                        f"Type mismatch: Cannot assign {expr_type} to {var_type}",
                        op_line, op_column
                    )
            
            symbol.initialized = True
            
            # Current position is now at the semicolon
            if self.get_current_token()[0] == ';':
                self.advance()  # Move past the semicolon
        else:
            raise SemanticError(f"Expected assignment operator, got '{token_type}'", op_line, op_column)

    def check_variable_usage(self, var_name, line, column):
        """Check if a variable used in an expression or function call is declared"""
        # Skip check for built-in symbols if applicable
        if var_name in self.built_in_functions:
            return True
            
        # Look up the variable in the current scope and parent scopes
        symbol = self.current_scope.lookup(var_name)
        if not symbol:
            raise SemanticError(f"Undefined variable '{var_name}'", line, column)
            
        # Optionally: Check if variable is initialized before use
        if not symbol.initialized:
            # This could be a warning instead of an error
            print(f"Warning: Variable '{var_name}' may be used before initialization at line {line}, column {column}")
            
        return symbol.data_type
    
    def analyze_if_statement(self):
        """Analyze an if statement (f statement in Conso)"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'f':
            raise SemanticError(f"Expected 'f' keyword, got '{token_type}'", line, column)

        self.advance()  # Move past 'f'

        # Process opening parenthesis for condition
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '(':
            raise SemanticError(f"Expected '(' after 'f', got '{token_type}'", line, column)

        # Keep track of the outermost parentheses level
        outer_paren_start = self.current_token_index
        self.advance()  # Move past opening parenthesis

        # Need to find the matching closing parenthesis for the outermost level
        paren_level = 1

        while paren_level > 0 and self.current_token_index < len(self.token_stream):
            current_token = self.get_current_token()[0]
            if current_token == '(':
                paren_level += 1
            elif current_token == ')':
                paren_level -= 1

            if paren_level > 0:
                self.advance()

        # Now we should be at the closing parenthesis of the condition
        if paren_level > 0:
            raise SemanticError("Unclosed parenthesis in 'f' statement condition", line, column)

        # Now at the closing parenthesis
        outer_paren_end = self.current_token_index

        # Reset to just after the opening parenthesis
        self.current_token_index = outer_paren_start + 1

        # Analyze the condition using your expression analyzer
        # The condition is everything between the parentheses
        expr_type = self.analyze_expression(outer_paren_end)

        # --- MODIFIED CHECK: Allow 'nt' or 'bln' ---
        if expr_type not in ['bln', 'nt']:
            raise SemanticError(f"Condition in 'f' statement must be of type 'bln' or 'nt', got '{expr_type}'", line, column)
        # --- END MODIFIED CHECK ---

        # Move to the closing parenthesis and advance past it
        self.current_token_index = outer_paren_end
        self.advance()  # Move past the closing parenthesis

        # Process opening brace for if-body
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start 'f' body, got '{token_type}'", line, column)

        self.advance()  # Move past '{'

        # Create a new scope for the if-body
        if_scope = SymbolTable(parent=self.current_scope, scope_name="if block")
        original_scope = self.current_scope  # Store the original scope
        self.current_scope = if_scope

        # Process if-body statements
        self.analyze_block_statements()

        # Restore original scope
        self.current_scope = original_scope

        # Check for elseif (lsf) or else (ls) statements
        if self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            if token_type == 'lsf':
                self.analyze_elseif_statement(original_scope)  # Pass the original scope
            elif token_type == 'ls':
                self.analyze_else_statement(original_scope)  # Pass the original scope
    
    def analyze_elseif_statement(self, parent_scope):
        """Analyze an else-if statement (lsf statement in Conso)"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'lsf':
            raise SemanticError(f"Expected 'lsf' keyword, got '{token_type}'", line, column)

        self.advance()  # Move past 'lsf'

        # Process opening parenthesis for condition
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '(':
            raise SemanticError(f"Expected '(' after 'lsf', got '{token_type}'", line, column)

        # Keep track of the outermost parentheses level
        outer_paren_start = self.current_token_index
        self.advance()  # Move past opening parenthesis

        # Need to find the matching closing parenthesis for the outermost level
        paren_level = 1

        while paren_level > 0 and self.current_token_index < len(self.token_stream):
            current_token = self.get_current_token()[0]
            if current_token == '(':
                paren_level += 1
            elif current_token == ')':
                paren_level -= 1

            if paren_level > 0:
                self.advance()

        # Now we should be at the closing parenthesis of the condition
        if paren_level > 0:
            raise SemanticError("Unclosed parenthesis in 'lsf' statement condition", line, column)

        # Now at the closing parenthesis
        outer_paren_end = self.current_token_index

        # Reset to just after the opening parenthesis
        self.current_token_index = outer_paren_start + 1

        # Analyze the condition using your expression analyzer
        # The condition is everything between the parentheses
        expr_type = self.analyze_expression(outer_paren_end)

        # --- MODIFIED CHECK: Allow 'nt' or 'bln' ---
        if expr_type not in ['bln', 'nt']:
            raise SemanticError(f"Condition in 'lsf' statement must be of type 'bln' or 'nt', got '{expr_type}'", line, column)
        # --- END MODIFIED CHECK ---

        # Move to the closing parenthesis and advance past it
        self.current_token_index = outer_paren_end
        self.advance()  # Move past the closing parenthesis

        # Process opening brace for elseif-body
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start 'lsf' body, got '{token_type}'", line, column)

        self.advance()  # Move past '{'

        # Create a new scope for the elseif-body, using the passed parent scope
        elseif_scope = SymbolTable(parent=parent_scope, scope_name="elseif block")
        self.current_scope = elseif_scope

        # Process elseif-body statements
        self.analyze_block_statements()

        # Restore original scope
        self.current_scope = parent_scope

        # Check for another elseif (lsf) or else (ls) statement
        if self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            if token_type == 'lsf':
                self.analyze_elseif_statement(parent_scope)  # Pass the original scope
            elif token_type == 'ls':
                self.analyze_else_statement(parent_scope)  # Pass the original scope

    def analyze_else_statement(self, parent_scope):
        """Analyze an else statement (ls statement in Conso)"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'ls':
            raise SemanticError(f"Expected 'ls' keyword, got '{token_type}'", line, column)
        
        self.advance()  # Move past 'ls'
        
        # Process opening brace for else-body
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start 'ls' body, got '{token_type}'", line, column)
        
        self.advance()  # Move past '{'
        
        # Create a new scope for the else-body, using the passed parent scope
        else_scope = SymbolTable(parent=parent_scope, scope_name="else block")
        self.current_scope = else_scope
        
        # Process else-body statements
        self.analyze_block_statements()
        
        # Restore original scope
        self.current_scope = parent_scope

    def analyze_switch_statement(self):
        """Analyze a switch statement (swtch statement in Conso)"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'swtch':
            raise SemanticError(f"Expected 'swtch' keyword, got '{token_type}'", line, column)
        
        self.advance()  # Move past 'swtch'
        
        # Process opening parenthesis for switch expression
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '(':
            raise SemanticError(f"Expected '(' after 'swtch', got '{token_type}'", line, column)
        
        self.advance()  # Move past '('
        
        # Now get the switch expression token
        token_type, token_value, line, column = self.get_current_token()
        switch_expr_line, switch_expr_column = line, column
        
        # If it's a struct member access (e.g., student.id)
        if token_type == 'id' and self.peek_next_token()[0] == '.':
            switch_expr_type = self.analyze_struct_member_access()
        elif token_type == 'id':
            # Get the variable type from symbol table
            var_name = token_value
            symbol = self.current_scope.lookup(var_name)
            if not symbol:
                raise SemanticError(f"Undefined variable '{var_name}'", line, column)
            
            switch_expr_type = symbol.data_type
            self.advance()  # Move past identifier
        else:
            # Not an identifier or struct member access
            raise SemanticError(f"Switch expression must be an identifier", line, column)
        
        # Verify switch expression type is nt or chr
        if switch_expr_type not in ['nt', 'chr']:
            raise SemanticError(f"Switch expression must be of type 'nt' or 'chr', got '{switch_expr_type}'", 
                            switch_expr_line, switch_expr_column)
        
        # Process closing parenthesis
        token_type, token_value, line, column = self.get_current_token()
        if token_type != ')':
            raise SemanticError(f"Expected ')' after switch expression, got '{token_type}'", line, column)
        
        self.advance()  # Move past ')'
        
        # Process opening brace for switch body
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start switch body, got '{token_type}'", line, column)
        
        self.advance()  # Move past '{'

        # Save old switch and case block state
        old_in_switch = self.in_switch
        old_in_case_block = self.in_case_block
        
        # Set new state - we're now in a switch but not yet in a case block
        self.in_switch = True
        self.in_case_block = False
        
        # Create a new scope for the switch body
        switch_scope = SymbolTable(parent=self.current_scope, scope_name="switch block")
        original_scope = self.current_scope
        self.current_scope = switch_scope
        
        # Track case labels to ensure no duplicates
        case_labels = set()
        
        # Process case statements
        has_default = False
        found_break = True  # Initially true to allow the first case
        
        while self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            
            # Check for end of switch
            if token_type == '}':
                self.advance()  # Move past '}'
                break
            
            # Handle case statement
            if token_type == 'cs':
                self.in_case_block = True
                if not found_break:
                    raise SemanticError(f"Missing 'brk' statement before new case", line, column)
                
                self.advance()  # Move past 'cs'
                
                # Get case label
                token_type, token_value, line, column = self.get_current_token()
                
                # Ensure case label type matches switch expression type
                if switch_expr_type == 'nt':
                    if token_type != 'ntlit':
                        raise SemanticError(f"Case label must be of type 'nt', got '{token_type}'", line, column)
                    
                    # Check for duplicate case label
                    if token_value in case_labels:
                        raise SemanticError(f"Duplicate case label '{token_value}'", line, column)
                    
                    case_labels.add(token_value)
                elif switch_expr_type == 'chr':
                    if token_type != 'chrlit':
                        raise SemanticError(f"Case label must be of type 'chr', got '{token_type}'", line, column)
                    
                    # Check for duplicate case label
                    if token_value in case_labels:
                        raise SemanticError(f"Duplicate case label '{token_value}'", line, column)
                    
                    case_labels.add(token_value)
                
                self.advance()  # Move past case label
                
                # Check for colon
                token_type, token_value, line, column = self.get_current_token()
                if token_type != ':':
                    raise SemanticError(f"Expected ':' after case label, got '{token_type}'", line, column)
                
                self.advance()  # Move past ':'
                
                # Reset break flag
                found_break = False
                
                # Process statements until break or next case/default
                while self.current_token_index < len(self.token_stream):
                    current_token = self.get_current_token()[0]
                    
                    # Check for continue statement
                    if current_token == 'cntn':
                        raise SemanticError("Continue statement cannot be used directly in a switch case", 
                                        self.get_current_token()[2], self.get_current_token()[3])
                    
                    # Found break - set flag and process it
                    if current_token == 'brk':
                        found_break = True
                        self.analyze_break_statement()
                        break
                    
                    # Reached another case or end of switch without finding break
                    if current_token in ['cs', 'dflt', '}']:
                        raise SemanticError(f"Missing 'brk' statement at end of case", line, column)
                    
                    # Now we'll properly handle statements in the case block
                    # Handle various statement types (including loops and nested switches)
                    if current_token == 'f':
                        self.analyze_if_statement()
                    elif current_token == 'whl':
                        # Allow loops inside switch cases
                        self.analyze_while_loop()
                    elif current_token == 'fr':
                        # Allow for loops inside switch cases
                        self.analyze_for_loop()
                    elif current_token == 'd':
                        # Allow do-while loops inside switch cases
                        self.analyze_do_while_loop()
                    elif current_token == 'swtch':
                        # Allow nested switch statements - REMOVED the restriction
                        self.analyze_switch_statement()
                    elif current_token == 'cnst':
                        self.analyze_constant_declaration()
                    elif current_token == 'dfstrct':
                        self.analyze_struct_instantiation()
                    elif current_token in self.data_types:
                        start_pos = self.current_token_index
                        self.advance()
                        if self.current_token_index >= len(self.token_stream) or self.token_stream[self.current_token_index][0] != 'id':
                            raise SemanticError(f"Expected an identifier after '{current_token}'", 
                                            self.get_current_token()[2], self.get_current_token()[3])
                        
                        next_token = self.peek_next_token()
                        if next_token and next_token[0] == '[':
                            self.current_token_index = start_pos
                            self.analyze_array_declaration()
                        else:
                            self.current_token_index = start_pos
                            self.analyze_variable_declaration()
                    elif current_token == 'id':
                        id_token_value = self.get_current_token()[1]
                        next_token = self.peek_next_token()
                        if next_token and next_token[0] == '.':
                            self.analyze_struct_member_access()
                        elif next_token and next_token[0] == '(':
                            self.analyze_function_call()
                        elif next_token and next_token[0] == '[':
                            self.analyze_array_access()
                            
                            # Skip to end of statement
                            while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';':
                                self.advance()
                            self.advance()  # Move past semicolon
                        elif next_token and next_token[0] == '=':
                            self.analyze_assignment()
                        else:
                            self.check_variable_usage(id_token_value, 
                                                self.get_current_token()[2], self.get_current_token()[3])
                            self.advance()
                    elif current_token == 'prnt':
                        self.analyze_print_statement()
                    elif current_token == 'rtrn':
                        self.analyze_return_in_conditional()
                    else:
                        self.advance()
            
            # Handle default case
            elif token_type == 'dflt':
                self.in_case_block = True
                if not found_break:
                    raise SemanticError(f"Missing 'brk' statement before default case", line, column)
                
                if has_default:
                    raise SemanticError(f"Multiple default cases are not allowed", line, column)
                
                has_default = True
                self.advance()  # Move past 'dflt'
                
                # Check for colon
                token_type, token_value, line, column = self.get_current_token()
                if token_type != ':':
                    raise SemanticError(f"Expected ':' after 'dflt', got '{token_type}'", line, column)
                
                self.advance()  # Move past ':'
                
                # Reset break flag
                found_break = False
                
                # Process statements until break or next case/default (similar logic to case)
                while self.current_token_index < len(self.token_stream):
                    current_token = self.get_current_token()[0]
                    
                    # Check for continue statement
                    if current_token == 'cntn':
                        raise SemanticError("Continue statement cannot be used directly in a switch default block", 
                                        self.get_current_token()[2], self.get_current_token()[3])
                    
                    # Found break
                    if current_token == 'brk':
                        found_break = True
                        self.analyze_break_statement()
                        break
                    
                    # Reached another case or end of switch without finding break
                    if current_token in ['cs', 'dflt', '}']:
                        raise SemanticError(f"Missing 'brk' statement at end of default case", line, column)
                    
                    # Now handle all possible statements in the default block
                    # Process statements (same as case block)
                    if current_token == 'f':
                        self.analyze_if_statement()
                    elif current_token == 'whl':
                        self.analyze_while_loop()
                    elif current_token == 'fr':
                        self.analyze_for_loop()
                    elif current_token == 'd':
                        self.analyze_do_while_loop()
                    elif current_token == 'swtch':
                        # Allow nested switch
                        self.analyze_switch_statement()
                    elif current_token == 'cnst':
                        self.analyze_constant_declaration()
                    elif current_token == 'dfstrct':
                        self.analyze_struct_instantiation()
                    elif current_token in self.data_types:
                        start_pos = self.current_token_index
                        self.advance()
                        if self.current_token_index >= len(self.token_stream) or self.token_stream[self.current_token_index][0] != 'id':
                            raise SemanticError(f"Expected an identifier after '{current_token}'", 
                                            self.get_current_token()[2], self.get_current_token()[3])
                        
                        next_token = self.peek_next_token()
                        if next_token and next_token[0] == '[':
                            self.current_token_index = start_pos
                            self.analyze_array_declaration()
                        else:
                            self.current_token_index = start_pos
                            self.analyze_variable_declaration()
                    elif current_token == 'id':
                        id_token_value = self.get_current_token()[1]
                        next_token = self.peek_next_token()
                        if next_token and next_token[0] == '.':
                            self.analyze_struct_member_access()
                        elif next_token and next_token[0] == '(':
                            self.analyze_function_call()
                        elif next_token and next_token[0] == '[':
                            self.analyze_array_access()
                            
                            # Skip to end of statement
                            while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';':
                                self.advance()
                            self.advance()  # Move past semicolon
                        elif next_token and next_token[0] == '=':
                            self.analyze_assignment()
                        else:
                            self.check_variable_usage(id_token_value, 
                                                self.get_current_token()[2], self.get_current_token()[3])
                            self.advance()
                    elif current_token == 'prnt':
                        self.analyze_print_statement()
                    elif current_token == 'rtrn':
                        self.analyze_return_in_conditional()
                    else:
                        self.advance()
            
            elif token_type == 'brk' and not self.in_case_block:
                raise SemanticError("Break statement in switch must appear within a case or default block", 
                                line, column)
            else:
                # Unexpected token in switch statement
                self.advance()  # Skip unexpected tokens to avoid infinite loops
        
        # Restore original flags and scope
        self.in_switch = old_in_switch
        self.in_case_block = old_in_case_block
        self.current_scope = original_scope

    def analyze_case_body(self):
        """Analyze statements inside a case body until break statement"""
        # Keep track of whether we found a nested switch or break
        found_break = False
        
        while self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            
            # Check for break statement
            if token_type == 'brk':
                return True  # Return True to indicate a break was found
            
            # Check for nested switch statement (not allowed)
            if token_type == 'swtch':
                raise SemanticError(f"Nested switch statements are not allowed", line, column)
            
            # Check for end of switch (missing break)
            if token_type == '}':
                return False  # Return False to indicate no break was found
            
            # Handle other case statements (missing break)
            if token_type in ['cs', 'dflt']:
                return False  # Return False to indicate no break was found
            
            # Handle if statements
            if token_type == 'f':
                self.analyze_if_statement_in_switch()
                continue
            
            # Handle other statements
            if token_type == 'cnst':
                self.analyze_constant_declaration()
            elif token_type == 'dfstrct':
                self.analyze_struct_instantiation()
            elif token_type in self.data_types:
                start_pos = self.current_token_index
                self.advance()
                if self.current_token_index >= len(self.token_stream) or self.token_stream[self.current_token_index][0] != 'id':
                    raise SemanticError(f"Expected an identifier after '{token_type}'", line, column)
                
                next_token = self.peek_next_token()
                if next_token and next_token[0] == '[':
                    self.current_token_index = start_pos
                    self.analyze_array_declaration()
                else:
                    self.current_token_index = start_pos
                    self.analyze_variable_declaration()
            elif token_type == 'id':
                next_token = self.peek_next_token()
                if next_token and next_token[0] == '.':
                    self.analyze_struct_member_access()
                elif next_token and next_token[0] == '(':
                    self.analyze_function_call()
                elif next_token and next_token[0] == '[':
                    self.analyze_array_access()
                    
                    # Skip to end of statement
                    while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';':
                        self.advance()
                    self.advance()  # Move past semicolon
                elif next_token and next_token[0] == '=':
                    self.analyze_assignment()
                else:
                    self.check_variable_usage(token_value, line, column)
                    self.advance()
            else:
                self.advance()
        
        return False  # No break found if we reach end of tokens

    def analyze_if_statement_in_switch(self):
        """Analyze an if statement inside a switch case (special handling to prevent nested switch)"""
        # Create a flag to track that we're inside a switch case
        old_in_switch = getattr(self, 'in_switch_case', False)
        self.in_switch_case = True
        
        try:
            # Use regular if statement analysis
            self.analyze_if_statement()
        finally:
            # Restore the flag
            self.in_switch_case = old_in_switch

    def analyze_block_statements(self):
        """Analyze statements inside a block until closing brace"""
        # Process block statements until we find closing brace
        while self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            
            # Add debug output
            print(f"Processing token in block: {token_type} '{token_value}' at line {line}, column {column}")
            
            # Check for end of block
            if token_type == '}':
                self.advance()  # Move past '}'
                break

            # Add special handling for break and continue
            if token_type == 'brk':
                if self.in_loop:
                    # Break in a loop is always fine
                    self.analyze_break_statement()
                    continue
                elif self.in_switch and self.in_case_block:
                    # Break in a switch is only fine if inside a case/default block
                    self.analyze_break_statement()
                    continue
                elif self.in_switch:
                    # Break in a switch but not in a case block
                    raise SemanticError("Break statement in switch must appear within a case or default block", 
                                    line, column)
                else:
                    # Not in a loop or switch
                    raise SemanticError("Break statement can only be used inside a loop or switch statement", 
                                    line, column)
                
            if token_type == 'cntn':
                if self.in_switch and not self.in_loop:
                    # Continue inside switch but not inside a loop
                    raise SemanticError("Continue statement cannot be used in a switch statement", 
                                    line, column)
                elif not self.in_loop:
                    # Not in a loop
                    raise SemanticError("Continue statement can only be used inside a loop", 
                                    line, column)
                else:
                    # Inside a loop, continue is fine
                    self.analyze_continue_statement()
                    continue
            
            # Handle all statement types
            if token_type == 'f':
                self.analyze_if_statement()
            elif token_type == 'whl':
                self.analyze_while_loop()
            elif token_type == 'd':
                self.analyze_do_while_loop()
            elif token_type == 'fr':
                self.analyze_for_loop()
            elif token_type == 'swtch':
                self.analyze_switch_statement()
            elif token_type == 'prnt':
                # Explicitly call analyze_print_statement when 'prnt' token is found
                print("Found print statement - calling analyze_print_statement()")  # Debug
                self.analyze_print_statement()
            elif token_type == 'rtrn':
                # Handle return inside blocks
                self.analyze_return_in_conditional()
            elif token_type == 'cnst':
                self.analyze_constant_declaration()
            elif token_type == 'dfstrct':
                self.analyze_struct_instantiation()
            elif token_type in self.data_types:
                start_pos = self.current_token_index
                self.advance()
                if self.current_token_index >= len(self.token_stream) or self.token_stream[self.current_token_index][0] != 'id':
                    raise SemanticError(f"Expected an identifier after '{token_type}'", line, column)
                
                next_token = self.peek_next_token()
                if next_token and next_token[0] == '[':
                    self.current_token_index = start_pos
                    self.analyze_array_declaration()
                else:
                    self.current_token_index = start_pos
                    self.analyze_variable_declaration()
            elif token_type == 'id':
                next_token = self.peek_next_token()
                
                # Check for increment/decrement operations
                if next_token and next_token[0] in ['++', '--']:
                    self.analyze_increment_operation()
                # Check for shortcut assignments
                elif next_token and next_token[0] in ['+=', '-=', '*=', '/=', '%=']:
                    print(f"Found shortcut assignment {token_value} {next_token[0]}")
                    self.analyze_assignment()
                elif next_token and next_token[0] == '.':
                    self.analyze_struct_member_access()
                elif next_token and next_token[0] == '(':
                    self.analyze_function_call()
                elif next_token and next_token[0] == '[':
                    self.analyze_array_access()
                    
                    # Skip to end of statement
                    while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';':
                        self.advance()
                    self.advance()  # Move past semicolon
                elif next_token and next_token[0] == '=':
                    self.analyze_assignment()
                else:
                    self.check_variable_usage(token_value, line, column)
                    self.advance()
            else:
                self.advance()  # Skip other tokens

    def analyze_return_in_conditional(self):
        """Analyze a return statement inside a conditional block"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'rtrn':
            raise SemanticError(f"Expected 'rtrn' keyword, got '{token_type}'", line, column)

        self.advance()  # Move past 'rtrn'

        # Check if we're in the main function
        is_main_function = False
        current_function_name = None
        temp_scope = self.current_scope
        while temp_scope:
            if temp_scope.scope_name.startswith("function "):
                current_function_name = temp_scope.scope_name[len("function "):]
                if current_function_name == "mn":
                    is_main_function = True
                break
            temp_scope = temp_scope.parent

        # --- REMOVED CHECK THAT DISALLOWED RETURN IN MAIN ---
        # # No return statements allowed in main function
        # if current_function == "mn":
        #     raise SemanticError("Return statements are not allowed in the main function", line, column)
        # --- END REMOVED CHECK ---

        # For other functions (or main), we need to check against the function's return type
        if current_function_name: # Should always be true if we are in a function scope
            func_symbol = self.global_scope.lookup(current_function_name)
            if func_symbol and func_symbol.type == 'function':
                return_type = func_symbol.data_type

                # For void functions (excluding main), there should be no return value
                if return_type == 'vd' and not is_main_function:
                    token_type, token_value, line, column = self.get_current_token()
                    if token_type != ';':
                        raise SemanticError(f"Void function cannot return a value", line, column)
                    self.advance()  # Move past ';'
                # For main or non-void functions
                else:
                    # --- ADDED: Handle return in main ---
                    if is_main_function:
                        # Allow 'rtrn 0;' or 'rtrn;'
                        next_token_type, next_token_value, next_line, next_col = self.get_current_token()
                        if next_token_type == 'ntlit' and next_token_value == '0':
                             self.advance() # Past 0
                             if self.get_current_token()[0] == ';':
                                 self.advance() # Past ;
                                 return # Valid rtrn 0;
                             else:
                                 raise SemanticError("Expected ';' after 'rtrn 0' in main function", self.get_current_token()[2], self.get_current_token()[3])
                        elif next_token_type == ';':
                             # Allow 'rtrn;'
                             self.advance() # Past ;
                             return # Valid rtrn;
                        else:
                             # Invalid return value for main
                             raise SemanticError(f"Main function ('mn') can only return '0' or have no return value ('rtrn;'), got '{next_token_value}'", next_line, next_col)
                    # --- END ADDED check for main ---
                    # For non-void, non-main functions, analyze the return expression
                    else:
                        start_pos = self.current_token_index

                        # Find the end of the return expression (semicolon)
                        while self.current_token_index < len(self.token_stream) and self.token_stream[self.current_token_index][0] != ';':
                            self.advance()

                        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ';':
                             raise SemanticError("Expected ';' after return value", line, column)


                        end_pos = self.current_token_index
                        self.current_token_index = start_pos

                        # Analyze the expression
                        expr_type = self.analyze_expression(end_pos)

                        # Check if return type matches function return type
                        if expr_type != return_type:
                            raise SemanticError(f"Return type mismatch: expected '{return_type}', got '{expr_type}'", line, column)

                        # Move past the semicolon
                        # self.advance() # Move to semicolon (analyze_expression leaves us here)
                        if self.get_current_token()[0] == ';':
                            self.advance()  # Move past semicolon
                        else: # Should not happen if semicolon check above worked
                            raise SemanticError("Internal Error: Expected semicolon after analyzed return expression", line, column)

    def analyze_for_loop(self):
        """Analyze a for loop (fr statement in Conso)"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'fr':
            raise SemanticError(f"Expected 'fr' keyword, got '{token_type}'", line, column)
        
        self.advance()  # Move past 'fr'
        
        # Process opening parenthesis
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '(':
            raise SemanticError(f"Expected '(' after 'fr', got '{token_type}'", line, column)
        
        self.advance()  # Move past '('
        
        # Process initialization part
        # Note: You mentioned initialization is already validated in syntax
        # We'll just skip past it to the first semicolon
        init_start = self.current_token_index
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';':
            self.advance()
        
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ';':
            raise SemanticError(f"Expected ';' after for loop initialization", line, column)
        
        # Go back to analyze the initialization
        self.current_token_index = init_start
        
        # Process the initialization (typically an assignment)
        # In your language, this should only be an 'nt' variable initialized with an 'nt' value
        if self.get_current_token()[0] == 'id':
            var_name = self.get_current_token()[1]
            init_line, init_column = self.get_current_token()[2], self.get_current_token()[3]
            
            # Check if variable exists
            var_symbol = self.current_scope.lookup(var_name)
            if not var_symbol:
                raise SemanticError(f"Undefined variable '{var_name}' in for loop initialization", init_line, init_column)
            
            # Check if variable is of type 'nt'
            if var_symbol.data_type != 'nt':
                raise SemanticError(f"Variable in for loop initialization must be of type 'nt', got '{var_symbol.data_type}'", init_line, init_column)
            
            # Skip past variable name and = sign
            self.advance()  # Move past variable name
            
            # Expect = sign
            if self.get_current_token()[0] != '=':
                raise SemanticError(f"Expected '=' in for loop initialization, got '{self.get_current_token()[0]}'", init_line, init_column)
            
            self.advance()  # Move past =
            
            # Check the value being assigned
            init_value_type = self.get_current_token()[0]
            if init_value_type == 'ntlit':
                # Integer literal is OK
                self.advance()  # Move past literal
            elif init_value_type == 'id':
                # Check if the identifier is of type 'nt'
                init_id = self.get_current_token()[1]
                init_id_symbol = self.current_scope.lookup(init_id)
                if not init_id_symbol:
                    raise SemanticError(f"Undefined variable '{init_id}' in for loop initialization", init_line, init_column)
                
                if init_id_symbol.data_type != 'nt':
                    raise SemanticError(f"Variable in for loop initialization value must be of type 'nt', got '{init_id_symbol.data_type}'", init_line, init_column)
                
                self.advance()  # Move past identifier
            else:
                raise SemanticError(f"For loop initialization value must be an 'nt' literal or identifier, got '{init_value_type}'", init_line, init_column)
        
        # Now we should be at the first semicolon
        if self.get_current_token()[0] != ';':
            raise SemanticError(f"Expected ';' after for loop initialization, got '{self.get_current_token()[0]}'", 
                            self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Move past the first semicolon
        
        # Process the condition
        condition_start = self.current_token_index
        condition_line, condition_column = self.get_current_token()[2], self.get_current_token()[3]
        
        # Find the end of the condition (should be the second semicolon)
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';':
            self.advance()
        
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ';':
            raise SemanticError(f"Expected ';' after for loop condition", condition_line, condition_column)
        
        condition_end = self.current_token_index
        self.current_token_index = condition_start
        
        # Analyze the condition expression - it must evaluate to a boolean
        # and must only involve 'nt' values in the comparison
        condition_expr_type = self.analyze_expression(condition_end)
        if condition_expr_type != 'bln':
            raise SemanticError(f"For loop condition must evaluate to a boolean, got '{condition_expr_type}'", 
                            condition_line, condition_column)
        
        # Now we should be at the second semicolon
        if self.get_current_token()[0] != ';':
            raise SemanticError(f"Expected ';' after for loop condition, got '{self.get_current_token()[0]}'", 
                            self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Move past the second semicolon
        
        # Process the increment/decrement
        increment_start = self.current_token_index
        increment_line, increment_column = self.get_current_token()[2], self.get_current_token()[3]
        
        # Find the end of the increment (should be the closing parenthesis)
        paren_level = 1  # Start at 1 because we're already inside a parenthesis
        while self.current_token_index < len(self.token_stream):
            if self.get_current_token()[0] == '(':
                paren_level += 1
            elif self.get_current_token()[0] == ')':
                paren_level -= 1
                if paren_level == 0:
                    break
            
            self.advance()
        
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ')':
            raise SemanticError(f"Expected ')' after for loop increment", increment_line, increment_column)
        
        increment_end = self.current_token_index
        self.current_token_index = increment_start
        
        # Analyze the increment expression - it must involve an 'nt' identifier
        # Check for pre-increment/decrement: ++id or --id
        if self.get_current_token()[0] in ['++', '--']:
            incr_op = self.get_current_token()[0]
            self.advance()  # Move past operator
            
            if self.get_current_token()[0] != 'id':
                raise SemanticError(f"Expected an identifier after '{incr_op}' in for loop increment", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            incr_var_name = self.get_current_token()[1]
            incr_var_symbol = self.current_scope.lookup(incr_var_name)
            
            if not incr_var_symbol:
                raise SemanticError(f"Undefined variable '{incr_var_name}' in for loop increment", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            # Check if variable is of type 'nt'
            if incr_var_symbol.data_type != 'nt':
                raise SemanticError(f"Variable in for loop increment must be of type 'nt', got '{incr_var_symbol.data_type}'", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            self.advance()  # Move past identifier
        
        # Check for post-increment/decrement or other forms: id++ or id-- or other assignments
        elif self.get_current_token()[0] == 'id':
            incr_var_name = self.get_current_token()[1]
            incr_var_symbol = self.current_scope.lookup(incr_var_name)
            
            if not incr_var_symbol:
                raise SemanticError(f"Undefined variable '{incr_var_name}' in for loop increment", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            # Check if variable is of type 'nt'
            if incr_var_symbol.data_type != 'nt':
                raise SemanticError(f"Variable in for loop increment must be of type 'nt', got '{incr_var_symbol.data_type}'", 
                                self.get_current_token()[2], self.get_current_token()[3])
            
            self.advance()  # Move past identifier
            
            # Check for operator: ++, --, +=, -=, *=, /=
            if self.get_current_token()[0] in ['++', '--']:
                # Simple increment/decrement is fine
                self.advance()  # Move past operator
            elif self.get_current_token()[0] in ['+=', '-=', '*=', '/=']:
                operator = self.get_current_token()[0]
                self.advance()  # Move past operator
                
                # Check the value - should be 'nt' literal or identifier
                if self.get_current_token()[0] == 'ntlit':
                    # Integer literal is OK
                    self.advance()  # Move past literal
                elif self.get_current_token()[0] == 'id':
                    # Check if the identifier is of type 'nt'
                    right_id = self.get_current_token()[1]
                    right_id_symbol = self.current_scope.lookup(right_id)
                    
                    if not right_id_symbol:
                        raise SemanticError(f"Undefined variable '{right_id}' in for loop increment", 
                                        increment_line, increment_column)
                    
                    if right_id_symbol.data_type != 'nt':
                        raise SemanticError(f"Variable in for loop increment must be of type 'nt', got '{right_id_symbol.data_type}'", 
                                        increment_line, increment_column)
                    
                    self.advance()  # Move past identifier
                else:
                    raise SemanticError(f"For loop increment value must be an 'nt' literal or identifier, got '{self.get_current_token()[0]}'", 
                                    increment_line, increment_column)
            else:
                raise SemanticError(f"Expected increment/decrement operator in for loop increment, got '{self.get_current_token()[0]}'", 
                                increment_line, increment_column)
        
        # Skip to the end of the increment (should be the closing parenthesis)
        while self.current_token_index < increment_end:
            self.advance()
        
        # Now we should be at the closing parenthesis
        if self.get_current_token()[0] != ')':
            raise SemanticError(f"Expected ')' after for loop increment, got '{self.get_current_token()[0]}'", 
                            self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Move past the closing parenthesis
        
        # Process opening brace for loop body
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start for loop body, got '{token_type}'", line, column)
        
        self.advance()  # Move past '{'

         # ADD THE LOOP FLAG CODE HERE, just before creating the new scope:
        old_in_loop = self.in_loop
        self.in_loop = True
        
        # Create a new scope for the loop body
        loop_scope = SymbolTable(parent=self.current_scope, scope_name="for loop block")
        original_scope = self.current_scope
        self.current_scope = loop_scope
        
        # Process loop body statements
        self.analyze_block_statements()
        
        # Restore original flags and scope
        self.in_loop = old_in_loop
        self.current_scope = original_scope
        
        # Create a new scope for the loop body
        loop_scope = SymbolTable(parent=self.current_scope, scope_name="for loop block")
        original_scope = self.current_scope
        self.current_scope = loop_scope
        
        # Process loop body statements
        self.analyze_block_statements()
        
        # Restore original scope
        self.current_scope = original_scope

    def analyze_while_loop(self):
        """Analyze a while loop (whl statement in Conso)"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'whl':
            raise SemanticError(f"Expected 'whl' keyword, got '{token_type}'", line, column)

        self.advance()  # Move past 'whl'

        # Process opening parenthesis for condition
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '(':
            raise SemanticError(f"Expected '(' after 'whl', got '{token_type}'", line, column)

        # Keep track of the outermost parentheses level
        outer_paren_start = self.current_token_index
        self.advance()  # Move past opening parenthesis

        # Find the matching closing parenthesis for the outermost level
        paren_level = 1

        while paren_level > 0 and self.current_token_index < len(self.token_stream):
            current_token = self.get_current_token()[0]
            if current_token == '(':
                paren_level += 1
            elif current_token == ')':
                paren_level -= 1

            if paren_level > 0:
                self.advance()

        # Now we should be at the closing parenthesis of the condition
        if paren_level > 0:
            raise SemanticError("Unclosed parenthesis in 'whl' condition", line, column)

        # Now at the closing parenthesis
        outer_paren_end = self.current_token_index

        # Reset to just after the opening parenthesis
        self.current_token_index = outer_paren_start + 1

        # Analyze the condition using your expression analyzer
        # The condition is everything between the parentheses
        expr_type = self.analyze_expression(outer_paren_end)

        # --- MODIFIED CHECK: Allow 'nt' or 'bln' ---
        if expr_type not in ['bln', 'nt']:
            raise SemanticError(f"Condition in 'whl' statement must be of type 'bln' or 'nt', got '{expr_type}'", line, column)
        # --- END MODIFIED CHECK ---

        # Move to the closing parenthesis and advance past it
        self.current_token_index = outer_paren_end
        self.advance()  # Move past the closing parenthesis

        # Process opening brace for while-body
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start 'whl' body, got '{token_type}'", line, column)

        self.advance()  # Move past '{'

        old_in_loop = self.in_loop
        self.in_loop = True

        # Existing code for creating a new scope
        while_scope = SymbolTable(parent=self.current_scope, scope_name="while block")
        original_scope = self.current_scope
        self.current_scope = while_scope

        # Process while-body statements
        self.analyze_block_statements()

        # Just before you restore the original scope, add this:
        self.in_loop = old_in_loop

        # Existing code to restore scope
        self.current_scope = original_scope

    def analyze_do_while_loop(self):
        """Analyze a do-while loop (d-whl statement in Conso)"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'd':
            raise SemanticError(f"Expected 'd' keyword, got '{token_type}'", line, column)

        self.advance()  # Move past 'd'

        # Process opening brace for do-body
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '{':
            raise SemanticError(f"Expected '{{' to start 'd' body, got '{token_type}'", line, column)

        self.advance()  # Move past '{'

        old_in_loop = self.in_loop
        self.in_loop = True

        # Create a new scope for the do-body
        do_scope = SymbolTable(parent=self.current_scope, scope_name="do-while block")
        original_scope = self.current_scope
        self.current_scope = do_scope

        # Process do-body statements
        self.analyze_block_statements()

        # Restore original scope (parent scope, not the do-while scope itself)
        self.current_scope = original_scope

        # Process 'whl' keyword
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'whl':
             # If analyze_block_statements finished correctly, current token should be 'whl'
             # This error might indicate an unclosed block or other issue inside the loop body
             # Find the line/col of the closing brace '}' if possible
             loop_end_line, loop_end_col = line, column # Fallback to current token's pos
             temp_idx = self.current_token_index -1
             if temp_idx >= 0 and self.token_stream[temp_idx][0] == '}':
                  loop_end_line, loop_end_col = self.token_stream[temp_idx][2], self.token_stream[temp_idx][3]

             raise SemanticError(f"Expected 'whl' after do block body", loop_end_line, loop_end_col)


        self.advance()  # Move past 'whl'

        # Process opening parenthesis for condition
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '(':
            raise SemanticError(f"Expected '(' after 'whl' in do-while, got '{token_type}'", line, column)

        # Keep track of the outermost parentheses level
        outer_paren_start = self.current_token_index
        self.advance()  # Move past opening parenthesis

        # Find the matching closing parenthesis for the outermost level
        paren_level = 1

        while paren_level > 0 and self.current_token_index < len(self.token_stream):
            current_token = self.get_current_token()[0]
            if current_token == '(':
                paren_level += 1
            elif current_token == ')':
                paren_level -= 1

            if paren_level > 0:
                self.advance()

        # Now we should be at the closing parenthesis of the condition
        if paren_level > 0:
            raise SemanticError("Unclosed parenthesis in 'd-whl' condition", line, column)

        # Now at the closing parenthesis
        outer_paren_end = self.current_token_index

        # Reset to just after the opening parenthesis
        self.current_token_index = outer_paren_start + 1

        # Analyze the condition using your expression analyzer
        # The condition is everything between the parentheses
        expr_type = self.analyze_expression(outer_paren_end)

        # --- MODIFIED CHECK: Allow 'nt' or 'bln' ---
        if expr_type not in ['bln', 'nt']:
            raise SemanticError(f"Condition in 'd-whl' statement must be of type 'bln' or 'nt', got '{expr_type}'", line, column)
        # --- END MODIFIED CHECK ---

        # Move to the closing parenthesis and advance past it
        self.current_token_index = outer_paren_end
        self.advance()  # Move past the closing parenthesis

        # FOR DO-WHILE: Look for semicolon, not opening brace
        token_type, token_value, line, column = self.get_current_token()
        if token_type != ';':
            raise SemanticError(f"Expected ';' after 'd-whl' condition, got '{token_type}'", line, column)

        self.advance()  # Move past ';'

        # Restore the loop flag
        self.in_loop = old_in_loop

    def analyze_increment_operation(self):
        """Analyze increment or decrement operation (++, --)"""
        # Get the variable name
        token_type, var_name, line, column = self.get_current_token()
        
        # Look up the variable
        symbol = self.current_scope.lookup(var_name)
        if not symbol:
            raise SemanticError(f"Undefined variable '{var_name}'", line, column)
        
        # Check if variable is of type 'nt'
        if symbol.data_type != 'nt':
            raise SemanticError(f"Increment/decrement operators can only be applied to 'nt' variables, not '{symbol.data_type}'", 
                            line, column)
        
        self.advance()  # Move past identifier
        
        # Check if it's an increment or decrement operator
        token_type, token_value, line, column = self.get_current_token()
        if token_type not in ['++', '--']:
            raise SemanticError(f"Expected increment/decrement operator, got '{token_type}'", line, column)
        
        self.advance()  # Move past ++ or --
        
        # Check for semicolon
        token_type, token_value, line, column = self.get_current_token()
        if token_type != ';':
            raise SemanticError(f"Expected ';' after increment/decrement operation", line, column)
        
        self.advance()  # Move past semicolon

    def analyze_print_statement(self):
        """
        Analyze a print statement with proper type checking.
        This function enforces the same strict type constraints
        as regular expressions in the Conso language.
        """
        # Current token should be 'prnt'
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'prnt':
            raise SemanticError(f"Expected 'prnt' keyword, got '{token_type}'", line, column)
        
        print(f"Analyzing print statement at line {line}, column {column}")  # Debug output
        
        self.advance()  # Move past 'prnt'
        
        # Check for opening parenthesis
        token_type, token_value, line, column = self.get_current_token()
        if token_type != '(':
            raise SemanticError(f"Expected '(' after 'prnt', got '{token_type}'", line, column)
        
        self.advance()  # Move past '('
        
        # Handle empty print statement: prnt();
        if self.get_current_token()[0] == ')':
            self.advance()  # Skip ')'
            
            # Check for semicolon
            token_type, token_value, line, column = self.get_current_token()
            if token_type != ';':
                raise SemanticError(f"Expected ';' after print statement", line, column)
            
            self.advance()  # Skip ';'
            return
        
        # Process expressions until closing parenthesis
        while True:
            # Mark the start of the current print argument
            expr_start = self.current_token_index
            
            # Find the end of this expression (comma or closing parenthesis)
            paren_level = 0
            while self.current_token_index < len(self.token_stream):
                token_type = self.get_current_token()[0]
                
                if token_type == '(':
                    paren_level += 1
                elif token_type == ')':
                    if paren_level == 0:
                        # This is the closing parenthesis of the print statement
                        break
                    paren_level -= 1
                elif token_type == ',' and paren_level == 0:
                    # This is a comma separating expressions
                    break
                
                self.advance()
            
            # Save the end position
            expr_end = self.current_token_index
            
            # Reset to start of expression for analysis
            self.current_token_index = expr_start
            
            # Get the tokens being analyzed for debug
            expr_tokens = self.token_stream[expr_start:expr_end]
            expr_str = " ".join([f"{t[0]}('{t[1]}')" for t in expr_tokens])
            print(f"Print expression tokens: {expr_str}")  # Debug output
            
            # Analyze the expression using our standard expression analyzer
            try:
                # The standard analyze_expression will properly enforce all type constraints
                # including arithmetic, relational, logical, and string operations
                expr_type = self.analyze_expression(expr_end)
                print(f"Print expression type result: {expr_type}")  # Debug output
            except SemanticError as e:
                print(f"Semantic error in print expression: {e}")  # Debug output
                # Re-raise the error
                raise e
            
            # Move to the end of this expression
            self.current_token_index = expr_end
            
            # Check if we're at a comma or closing parenthesis
            if self.get_current_token()[0] == ',':
                self.advance()  # Move past comma to the next expression
            else:
                # We should be at the closing parenthesis
                break
        
        # We should now be at the closing parenthesis
        token_type, token_value, line, column = self.get_current_token()
        if token_type != ')':
            raise SemanticError(f"Expected ')' at end of print statement", line, column)
        
        self.advance()  # Skip ')'
        
        # Check for semicolon
        token_type, token_value, line, column = self.get_current_token()
        if token_type != ';':
            raise SemanticError(f"Expected ';' after print statement", line, column)
        
        self.advance()  # Skip ';'
        print("Print statement analysis completed successfully")  # Debug output

    def analyze_break_statement(self):
        """Analyze a break statement"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'brk':
            raise SemanticError(f"Expected 'brk' keyword, got '{token_type}'", line, column)
        
        self.advance()  # Move past 'brk'
        
        # Check for semicolon
        token_type, token_value, line, column = self.get_current_token()
        if token_type != ';':
            raise SemanticError(f"Expected ';' after 'brk', got '{token_type}'", line, column)
        
        self.advance()  # Move past ';'

    def analyze_continue_statement(self):
        """Analyze a continue statement"""
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'cntn':
            raise SemanticError(f"Expected 'cntn' keyword, got '{token_type}'", line, column)
        
        self.advance()  # Move past 'cntn'
        
        # Check for semicolon
        token_type, token_value, line, column = self.get_current_token()
        if token_type != ';':
            raise SemanticError(f"Expected ';' after 'cntn', got '{token_type}'", line, column)
        
        self.advance()  # Move past ';'

    def advance(self):
        """Move to the next token"""
        self.current_token_index += 1

    def peek_next_token(self):
        """Peek at the next token without advancing"""
        if self.current_token_index + 1 < len(self.token_stream):
            return self.token_stream[self.current_token_index + 1]
        return None, None, None, None

    def get_current_token(self):
        """Get the current token tuple (type, value, line, column)"""
        if self.current_token_index < len(self.token_stream):
            return self.token_stream[self.current_token_index]
        return None, None, None, None
    
    def debug_print_scope_hierarchy(self, scope=None, indent=0):
        if scope is None:
            scope = self.current_scope
        print(" " * indent + f"Scope: {scope.scope_name}")
        print(" " * indent + "Symbols: " + ", ".join(scope.symbols.keys()))
        if scope.parent:
            self.debug_print_scope_hierarchy(scope.parent, indent + 2)