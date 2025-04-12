import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lexer import Lexer
from parser import parse
import definitions

class CodeGenError(Exception):
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message
        self.line = line if line is not None else None
        self.column = column

    def __str__(self):
        if self.line is not None and self.column is not None:
            return f"Code Generation Error at line {self.line}, column {self.column}: {self.message}"
        return f"Code Generation Error: {self.message}"

class CodeGenerator:
    def __init__(self, symbol_table, tokens):
        self.symbol_table = symbol_table
        self.token_stream = tokens
        self.current_token_index = 0
        self.output_code = []
        self.temp_counter = 0
        self.label_counter = 0
        self.current_scope = symbol_table  # Start with global scope
        
        # Track function information
        self.current_function = None
        self.functions = {}
        
        # Stack to track temporary registers
        self.temp_stack = []
        
        # Maps for storing variables
        self.var_map = {}
        self.array_map = {}
        
        # Used to track the output of expressions
        self.result_register = None
        
        # Track indentation level
        self.indent_level = 0
        
        # Maximum token iterations to prevent infinite loops
        self.max_iterations = 100000
        self.iteration_count = 0
        
        # Add last position tracking to detect if we're not advancing
        self.last_position = -1
        self.stuck_count = 0
    
    def generate_code(self):
        """Main entry point for code generation"""
        self.output_code.append("# Conso Compiler Generated Python Code")
        self.output_code.append("")
        self.output_code.append("import math")  # For math functions like sqrt
        self.output_code.append("")
        
        try:
            # First pass to collect function declarations
            self.collect_functions()
            
            # Reset position for main code generation
            self.current_token_index = 0
            self.iteration_count = 0
            
            # Add built-in functions
            self.add_builtin_functions()
            
            # Process global declarations and the main function
            while self.current_token_index < len(self.token_stream) and self.iteration_count < self.max_iterations:
                token_type, token_value, line, column = self.get_current_token()
                
                # Check if we're stuck
                if self.current_token_index == self.last_position:
                    self.stuck_count += 1
                    if self.stuck_count > 10:
                        raise CodeGenError(f"Stuck at token '{token_type}' at line {line}, column {column}")
                else:
                    self.last_position = self.current_token_index
                    self.stuck_count = 0
                
                self.iteration_count += 1
                
                if token_type == 'fnctn':
                    # Process function declarations
                    self.generate_function_declaration()
                elif token_type in ['nt', 'dbl', 'bln', 'chr', 'strng']:
                    # Handle global variable declarations
                    self.generate_global_var_declaration()
                elif token_type == 'cnst':
                    # Handle global constant declarations
                    self.generate_global_const_declaration()
                elif token_type == 'strct':
                    # Skip struct definitions - simplified for now
                    self.skip_struct_definition()
                elif token_type == 'mn':
                    # Generate code for main function
                    self.generate_main_function()
                else:
                    self.advance()  # Skip other tokens
            
            if self.iteration_count >= self.max_iterations:
                raise CodeGenError("Code generation exceeded maximum iterations, likely stuck in an infinite loop")
            
            # Add main function call at the end
            self.output_code.append("")
            self.output_code.append("# Call main function if file is run directly")
            self.output_code.append("if __name__ == \"__main__\":")
            self.output_code.append("    main()")
            
            return "\n".join(self.output_code)
        
        except CodeGenError as e:
            return f"Code generation failed: {str(e)}"
        except Exception as e:
            return f"Unexpected error during code generation: {str(e)}"
    
    def collect_functions(self):
        """First pass to collect all function declarations"""
        while self.current_token_index < len(self.token_stream) and self.iteration_count < self.max_iterations:
            token_type, token_value, line, column = self.get_current_token()
            
            # Check if we're stuck
            if self.current_token_index == self.last_position:
                self.stuck_count += 1
                if self.stuck_count > 10:
                    raise CodeGenError(f"Stuck at token '{token_type}' at line {line}, column {column} during function collection")
            else:
                self.last_position = self.current_token_index
                self.stuck_count = 0
            
            self.iteration_count += 1
            
            if token_type == 'fnctn':
                self.register_function()
            else:
                self.advance()
        
        if self.iteration_count >= self.max_iterations:
            raise CodeGenError("Function collection exceeded maximum iterations, likely stuck in an infinite loop")
    
    def register_function(self):
        """Register a function during the first pass"""
        self.advance()  # Skip 'fnctn'
        
        # Get the return type
        token_type, token_value, line, column = self.get_current_token()
        return_type = token_type
        self.advance()
        
        # Get the function name
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'id':
            raise CodeGenError(f"Expected function name, got {token_type}", line, column)
        
        func_name = token_value
        self.advance()
        
        # Record function for later code generation
        self.functions[func_name] = {
            'return_type': return_type,
            'params': [],
            'start_index': self.current_token_index
        }
        
        # Skip to end of function to continue registration
        self.skip_function_body()
    
    def skip_function_body(self):
        """Skip over a function body"""
        start_pos = self.current_token_index
        iteration_count = 0
        max_iterations = 5000  # Lower threshold for skipping a single function
        
        # Skip to opening brace of function body
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            if self.get_current_token()[0] == '{':
                break
            self.advance()
            iteration_count += 1
        
        if self.current_token_index >= len(self.token_stream):
            raise CodeGenError("Unexpected end of file while looking for function body")
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Failed to find function body opening brace, started at position {start_pos}")
        
        # Skip the function body
        brace_count = 1
        self.advance()  # Skip opening brace
        
        iteration_count = 0
        while brace_count > 0 and self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            token_type = self.get_current_token()[0]
            if token_type == '{':
                brace_count += 1
            elif token_type == '}':
                brace_count -= 1
            self.advance()
            iteration_count += 1
        
        if iteration_count >= max_iterations:
            token_type, token_value, line, column = self.get_current_token()
            raise CodeGenError(f"Failed to find function body closing brace within iteration limit. Current token: {token_type} at line {line}")
    
    def skip_struct_definition(self):
        """Skip over a struct definition"""
        start_pos = self.current_token_index
        iteration_count = 0
        max_iterations = 5000  # Lower threshold for skipping a struct
        
        self.advance()  # Skip 'strct'
        
        # Skip struct name
        self.advance()
        
        # Skip to opening brace
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != '{' and iteration_count < max_iterations:
            self.advance()
            iteration_count += 1
        
        if self.current_token_index >= len(self.token_stream) or iteration_count >= max_iterations:
            raise CodeGenError(f"Failed to find struct body opening brace, started at position {start_pos}")
        
        # Skip the struct body
        brace_count = 1
        self.advance()  # Skip opening brace
        
        iteration_count = 0
        while brace_count > 0 and self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            token_type = self.get_current_token()[0]
            if token_type == '{':
                brace_count += 1
            elif token_type == '}':
                brace_count -= 1
            self.advance()
            iteration_count += 1
        
        if iteration_count >= max_iterations:
            token_type, token_value, line, column = self.get_current_token()
            raise CodeGenError(f"Failed to find struct body closing brace within iteration limit. Current token: {token_type} at line {line}")
        
        # Skip semicolon after struct definition
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == ';':
            self.advance()
    
    def generate_global_var_declaration(self):
        """Generate code for global variable declarations"""
        # Get the data type
        data_type, type_value, line, column = self.get_current_token()
        self.advance()
        
        # Process variables until semicolon
        while self.current_token_index < len(self.token_stream):
            token_type, var_name, line, column = self.get_current_token()
            
            if token_type != 'id':
                raise CodeGenError(f"Expected variable name, got {token_type}", line, column)
            
            self.advance()
            
            # Check if this is an array declaration or normal variable
            if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '[':
                self.generate_global_array_declaration(var_name, data_type)
            else:
                # Regular variable
                self.output_code.append(f"# Global variable: {var_name} of type {data_type}")
                self.var_map[var_name] = {
                    'type': data_type,
                    'is_global': True
                }
                
                # Check for initialization
                if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '=':
                    self.advance()  # Skip '='
                    
                    # Generate initialization code
                    self.output_code.append(f"{var_name} = ", end='')
                    self.generate_expression_code()
                    self.output_code.append("")
                else:
                    # Default initialization based on type
                    if data_type == 'nt':
                        self.output_code.append(f"{var_name} = 0")
                    elif data_type == 'dbl':
                        self.output_code.append(f"{var_name} = 0.0")
                    elif data_type == 'bln':
                        self.output_code.append(f"{var_name} = False")
                    elif data_type == 'chr':
                        self.output_code.append(f"{var_name} = ' '")
                    elif data_type == 'strng':
                        self.output_code.append(f"{var_name} = \"\"")
                
            # Check for comma or semicolon
            if self.current_token_index < len(self.token_stream):
                if self.get_current_token()[0] == ',':
                    self.advance()  # Skip comma
                    continue
                elif self.get_current_token()[0] == ';':
                    self.advance()  # Skip semicolon
                    break
    
    def generate_global_array_declaration(self, array_name, data_type):
        """Generate code for global array declarations"""
        # We need to parse array dimensions and size
        dimensions = 0
        sizes = []
        
        # Process opening bracket
        self.advance()  # Skip '['
        
        # Get first dimension size
        token_type, size_value, line, column = self.get_current_token()
        if token_type not in ['ntlit', 'id']:
            raise CodeGenError(f"Expected integer or identifier for array size, got {token_type}", line, column)
        
        sizes.append(size_value)
        dimensions += 1
        self.advance()  # Skip size value
        
        # Process closing bracket
        if self.get_current_token()[0] != ']':
            raise CodeGenError(f"Expected ']', got {self.get_current_token()[0]}", line, column)
        
        self.advance()  # Skip ']'
        
        # Check for second dimension
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '[':
            dimensions += 1
            self.advance()  # Skip '['
            
            # Get second dimension size
            token_type, size_value, line, column = self.get_current_token()
            if token_type not in ['ntlit', 'id']:
                raise CodeGenError(f"Expected integer or identifier for array size, got {token_type}", line, column)
            
            sizes.append(size_value)
            self.advance()  # Skip size value
            
            # Process closing bracket
            if self.get_current_token()[0] != ']':
                raise CodeGenError(f"Expected ']', got {self.get_current_token()[0]}", line, column)
            
            self.advance()  # Skip ']'
        
        # Register the array
        self.array_map[array_name] = {
            'type': data_type,
            'dimensions': dimensions,
            'sizes': sizes,
            'is_global': True
        }
        
        # Generate array code
        if dimensions == 1:
            self.output_code.append(f"# Global array: {array_name}[{sizes[0]}] of type {data_type}")
            # Default initialization
            if data_type == 'nt':
                self.output_code.append(f"{array_name} = [0] * {sizes[0]}")
            elif data_type == 'dbl':
                self.output_code.append(f"{array_name} = [0.0] * {sizes[0]}")
            elif data_type == 'bln':
                self.output_code.append(f"{array_name} = [False] * {sizes[0]}")
            elif data_type == 'chr':
                self.output_code.append(f"{array_name} = [' '] * {sizes[0]}")
            elif data_type == 'strng':
                self.output_code.append(f"{array_name} = [\"\"] * {sizes[0]}")
        else:
            self.output_code.append(f"# Global array: {array_name}[{sizes[0]}][{sizes[1]}] of type {data_type}")
            # Default initialization for 2D array
            if data_type == 'nt':
                self.output_code.append(f"{array_name} = [[0 for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
            elif data_type == 'dbl':
                self.output_code.append(f"{array_name} = [[0.0 for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
            elif data_type == 'bln':
                self.output_code.append(f"{array_name} = [[False for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
            elif data_type == 'chr':
                self.output_code.append(f"{array_name} = [[' ' for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
            elif data_type == 'strng':
                self.output_code.append(f"{array_name} = [[\"\" for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
        
        # Check for initialization
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '=':
            self.advance()  # Skip '='
            
            # Process array initialization
            if self.get_current_token()[0] != '{':
                raise CodeGenError(f"Expected '{{' for array initialization, got {self.get_current_token()[0]}", line, column)
            
            # Process the array initialization - simplified for now
            self.output_code.append(f"# Initializing array {array_name}")
            self.skip_array_initialization(dimensions)
    
    def skip_array_initialization(self, dimensions):
        """Skip past array initialization code"""
        brace_count = 1
        self.advance()  # Skip opening brace
        
        iteration_count = 0
        max_iterations = 1000  # Lower threshold for array initialization
        
        while brace_count > 0 and self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            token_type = self.get_current_token()[0]
            if token_type == '{':
                brace_count += 1
            elif token_type == '}':
                brace_count -= 1
            self.advance()
            iteration_count += 1
        
        if iteration_count >= max_iterations:
            token_type, token_value, line, column = self.get_current_token()
            raise CodeGenError(f"Failed to find array initialization closing brace within iteration limit. Current token: {token_type} at line {line}")
    
    def generate_global_const_declaration(self):
        """Generate code for global constant declarations"""
        self.advance()  # Skip 'cnst'
        
        # Get the data type
        data_type, type_value, line, column = self.get_current_token()
        self.advance()
        
        # Process constant declarations
        while self.current_token_index < len(self.token_stream):
            token_type, const_name, line, column = self.get_current_token()
            
            if token_type != 'id':
                raise CodeGenError(f"Expected constant name, got {token_type}", line, column)
            
            self.advance()
            
            # Expect initialization (constants must be initialized)
            if self.get_current_token()[0] != '=':
                raise CodeGenError(f"Expected '=' for constant initialization", line, column)
            
            self.advance()  # Skip '='
            
            # Register the constant
            self.var_map[const_name] = {
                'type': data_type,
                'is_global': True,
                'is_constant': True
            }
            
            # Generate initialization code
            self.output_code.append(f"# Global constant: {const_name} of type {data_type}")
            self.output_code.append(f"{const_name} = ", end='')
            
            # Generate expression code
            self.generate_expression_code()
            self.output_code.append("")
            
            # Check for comma or semicolon
            if self.current_token_index < len(self.token_stream):
                if self.get_current_token()[0] == ',':
                    self.advance()  # Skip comma
                    continue
                elif self.get_current_token()[0] == ';':
                    self.advance()  # Skip semicolon
                    break
    
    def generate_expression_code(self):
        """Generate code for an expression - fixed to prevent infinite loops"""
        # Find the end of the expression (semicolon, comma, or closing symbol)
        expr_start = self.current_token_index
        
        # Simplified for now: Just copy the expression tokens
        expr_tokens = []
        paren_level = 0
        bracket_level = 0
        
        iteration_count = 0
        max_iterations = 200  # Lower limit for parsing a single expression
        
        # Track our position to detect if we're stuck
        last_pos = -1
        stuck_count = 0
        
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            # Check if we're stuck
            if self.current_token_index == last_pos:
                stuck_count += 1
                if stuck_count > 5:
                    line, column = None, None
                    if self.current_token_index < len(self.token_stream):
                        _, _, line, column = self.get_current_token()
                    raise CodeGenError(f"Stuck parsing expression at position {self.current_token_index}", line, column)
            else:
                last_pos = self.current_token_index
                stuck_count = 0
            
            iteration_count += 1
            token_type, token_value, line, column = self.get_current_token()
            
            if token_type == '(':
                paren_level += 1
                expr_tokens.append('(')
            elif token_type == ')':
                paren_level -= 1
                if paren_level < 0:
                    break
                expr_tokens.append(')')
            elif token_type == '[':
                bracket_level += 1
                expr_tokens.append('[')
            elif token_type == ']':
                bracket_level -= 1
                if bracket_level < 0:
                    break
                expr_tokens.append(']')
            elif paren_level == 0 and bracket_level == 0:
                if token_type in [';', ',', ')', ']']:
                    break
                
                # Convert tokens as needed
                if token_type == '&&':
                    expr_tokens.append('and')
                elif token_type == '||':
                    expr_tokens.append('or')
                elif token_type == '!':
                    expr_tokens.append('not')
                elif token_type == 'blnlit':
                    if token_value.lower() in ['tr', 'true']:
                        expr_tokens.append('True')
                    else:
                        expr_tokens.append('False')
                else:
                    expr_tokens.append(token_value)
            else:
                # Inside parentheses or brackets
                if token_type == '&&':
                    expr_tokens.append('and')
                elif token_type == '||':
                    expr_tokens.append('or')
                elif token_type == '!':
                    expr_tokens.append('not')
                elif token_type == 'blnlit':
                    if token_value.lower() in ['tr', 'true']:
                        expr_tokens.append('True')
                    else:
                        expr_tokens.append('False')
                else:
                    expr_tokens.append(token_value)
            
            self.advance()
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Expression parsing exceeded maximum iterations, likely stuck in an infinite loop. Started at token position {expr_start}")
        
        # Simple approach: just create a string of the expression
        expr_str = " ".join(expr_tokens)
        self.output_code.append(expr_str)
    
    def generate_expression_until(self, end_token):
        """Generate code for an expression until a specific token is encountered"""
        expr_tokens = []
        paren_level = 0
        bracket_level = 0
        
        iteration_count = 0
        max_iterations = 200  # Lower limit for parsing a single expression
        
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            iteration_count += 1
            token_type, token_value, line, column = self.get_current_token()
            
            if token_type == '(':
                paren_level += 1
                expr_tokens.append('(')
            elif token_type == ')':
                paren_level -= 1
                if paren_level < 0 and end_token == ')':
                    break
                expr_tokens.append(')')
            elif token_type == '[':
                bracket_level += 1
                expr_tokens.append('[')
            elif token_type == ']':
                bracket_level -= 1
                if bracket_level < 0 and end_token == ']':
                    break
                expr_tokens.append(']')
            elif token_type == end_token and paren_level == 0 and bracket_level == 0:
                break
            
            # Special handling for logical operators
            elif token_type == '&&':
                expr_tokens.append('and')
            elif token_type == '||':
                expr_tokens.append('or')
            elif token_type == '!':
                expr_tokens.append('not')
            # Handle identifiers and literals
            elif token_type == 'id':
                expr_tokens.append(token_value)
            elif token_type in ['ntlit', '~ntlit', 'dbllit', '~dbllit']:
                expr_tokens.append(token_value)
            elif token_type == 'blnlit':
                # Convert to Python boolean
                if token_value.lower() in ['tr', 'true']:
                    expr_tokens.append('True')
                else:
                    expr_tokens.append('False')
            elif token_type == 'chrlit':
                expr_tokens.append(f"'{token_value}'")
            elif token_type == 'strnglit':
                expr_tokens.append(f'"{token_value}"')
            # Handle operators
            elif token_type in ['+', '-', '*', '/', '%']:
                expr_tokens.append(token_type)
            # Handle relational operators
            elif token_type in ['==', '!=', '<', '>', '<=', '>=']:
                expr_tokens.append(token_type)
            # Handle other tokens
            else:
                expr_tokens.append(token_value)
            
            self.advance()
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Expression parsing exceeded maximum iterations, likely stuck in an infinite loop")
        
        # Join the tokens to form the expression string
        self.output_code.append(' '.join(expr_tokens))
    
    def generate_function_declaration(self):
        """Generate code for a function declaration"""
        self.advance()  # Skip 'fnctn'
        
        # Get return type
        token_type, token_value, line, column = self.get_current_token()
        return_type = token_type
        self.advance()
        
        # Get function name
        token_type, token_value, line, column = self.get_current_token()
        if token_type != 'id':
            raise CodeGenError(f"Expected function name, got {token_type}", line, column)
        
        func_name = token_value
        self.current_function = func_name
        self.advance()
        
        # Generate function header
        self.output_code.append(f"def {func_name}(", end='')
        
        # Skip opening parenthesis
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after function name", line, column)
        
        self.advance()  # Skip '('
        
        # Process parameters
        params = []
        if self.get_current_token()[0] != ')':
            while True:
                # Get parameter type
                token_type, token_value, line, column = self.get_current_token()
                if token_type not in ['nt', 'dbl', 'bln', 'chr', 'strng']:
                    raise CodeGenError(f"Expected parameter type, got {token_type}", line, column)
                
                param_type = token_type
                self.advance()
                
                # Get parameter name
                token_type, token_value, line, column = self.get_current_token()
                if token_type != 'id':
                    raise CodeGenError(f"Expected parameter name, got {token_type}", line, column)
                
                param_name = token_value
                params.append(param_name)
                self.advance()
                
                # Check for comma or closing parenthesis
                if self.get_current_token()[0] == ',':
                    self.advance()  # Skip comma
                else:
                    break
        
        # Complete parameter list
        self.output_code.append(", ".join(params))
        self.output_code.append("):")
        
        # Skip closing parenthesis
        if self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after parameters", line, column)
        
        self.advance()  # Skip ')'
        
        # Skip opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start function body", line, column)
        
        self.advance()  # Skip '{'
        
        # Increase indentation level
        self.indent_level += 1
        
        # Process function body
        if return_type == 'vd':
            # For void functions, no return value needed
            self.generate_function_body_code(func_name)
        else:
            # For functions with return type, add return annotation
            self.output_code.append(f"    # Returns {return_type}")
            self.generate_function_body_code(func_name)
        
        # Decrease indentation level
        self.indent_level -= 1
        
        # Reset current function
        self.current_function = None
    
    def generate_main_function(self):
        """Generate code for the main function"""
        self.output_code.append("\n# Main function")
        token_type, token_value, line, column = self.get_current_token()
        
        if token_type != 'mn':
            raise CodeGenError(f"Expected 'mn', got {token_type}", line, column)
        
        self.advance()  # Skip 'mn'
        
        # Skip past opening/closing parentheses
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after 'mn'", line, column)
        
        self.advance()  # Skip '('
        
        if self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after '('", line, column)
        
        self.advance()  # Skip ')'
        
        # Generate function header
        self.current_function = "main"
        self.output_code.append("def main():")
        
        # Skip past opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start main function", line, column)
        
        self.advance()  # Skip '{'
        
        # Increase indentation level
        self.indent_level += 1
        
        # Generate code for the function body statements
        self.generate_function_body_code('main')
        
        # Decrease indentation level
        self.indent_level -= 1
        
        # Reset current function
        self.current_function = None
    
    def generate_function_body_code(self, function_name):
        """Generate code for a function body"""
        # Process statements until closing brace
        empty_body = True  # Track if the function body is empty
        
        # Add counter to prevent infinite loops
        iteration_count = 0
        max_iterations = 5000  # Reasonable limit for a function body
        
        # Track position to detect if we're stuck
        last_position = -1
        stuck_count = 0
        
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            token_type, token_value, line, column = self.get_current_token()

             # Skip EOF tokens
            if token_type == 'EOF':
                self.advance()  # Skip EOF tokens
                continue
            
            # Check if we're stuck
            if self.current_token_index == last_position:
                stuck_count += 1
                if stuck_count > 10:
                    raise CodeGenError(f"Stuck at token '{token_type}' at line {line}, column {column} in function {function_name}")
            else:
                last_position = self.current_token_index
                stuck_count = 0
            
            iteration_count += 1
            
            # Check for end of function
            if token_type == '}':
                self.advance()  # Skip closing brace
                break
            
            empty_body = False  # Found a statement, body is not empty
            
            # Handle various statement types
            if token_type in ['nt', 'dbl', 'bln', 'chr', 'strng']:
                # Variable declaration
                self.generate_local_var_declaration(function_name)
            elif token_type == 'cnst':
                # Constant declaration
                self.generate_local_const_declaration(function_name)
            elif token_type == 'f':
                # If statement
                self.generate_if_statement_code(function_name)
            elif token_type == 'whl':
                # While loop
                self.generate_while_loop_code(function_name)
            elif token_type == 'd':
                # Do-while loop
                self.generate_do_while_loop_code(function_name)
            elif token_type == 'fr':
                # For loop
                self.generate_for_loop_code(function_name)
            elif token_type == 'swtch':
                # Switch statement
                self.generate_switch_statement_code(function_name)
            elif token_type == 'brk':
                # Break statement
                self.output_code.append(self.get_indent() + "break")
                self.advance()  # Skip 'brk'
                
                # Skip semicolon
                if self.get_current_token()[0] == ';':
                    self.advance()
            elif token_type == 'cntn':
                # Continue statement
                self.output_code.append(self.get_indent() + "continue")
                self.advance()  # Skip 'cntn'
                
                # Skip semicolon
                if self.get_current_token()[0] == ';':
                    self.advance()
            elif token_type == 'rtrn':
                # Return statement
                self.generate_return_statement_code(function_name)
            elif token_type == 'prnt':
                # Print statement
                self.generate_print_statement_code()
            elif token_type == 'id':
                # Could be function call, assignment, etc.
                self.generate_identifier_code(function_name)
            elif token_type == 'end':
                # In Conso, 'end' appears before the closing brace of main
                # Just skip it and its semicolon
                self.advance()  # Skip 'end'
                
                # Skip semicolon if present
                if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == ';':
                    self.advance()
            else:
                # Skip unknown tokens
                self.advance()
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Function body generation exceeded maximum iterations in function {function_name}, likely stuck in an infinite loop")
        
        # Add 'pass' if function body is empty (needed in Python)
        if empty_body:
            self.output_code.append(self.get_indent() + "pass")
    
    def generate_local_var_declaration(self, function_name):
        """Generate code for local variable declarations"""
        # Get the data type
        data_type, type_value, line, column = self.get_current_token()
        self.advance()
        
        # Process variables until semicolon
        iteration_count = 0
        max_iterations = 100  # Reasonable limit for processing variables
        
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            iteration_count += 1
            token_type, var_name, line, column = self.get_current_token()
            
            if token_type != 'id':
                raise CodeGenError(f"Expected variable name, got {token_type}", line, column)
            
            self.advance()
            
            # Check if this is an array declaration or normal variable
            if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '[':
                self.generate_local_array_declaration(var_name, data_type, function_name)
            else:
                # Regular variable
                var_key = f"{function_name}_{var_name}"
                self.var_map[var_key] = {
                    'type': data_type,
                    'is_global': False,
                    'function': function_name
                }
                
                # Check for initialization
                if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '=':
                    self.advance()  # Skip '='
                    
                    # Generate initialization code
                    self.output_code.append(f"{self.get_indent()}{var_name} = ", end='')
                    self.generate_expression_code()
                else:
                    # Default initialization based on type
                    if data_type == 'nt':
                        self.output_code.append(f"{self.get_indent()}{var_name} = 0")
                    elif data_type == 'dbl':
                        self.output_code.append(f"{self.get_indent()}{var_name} = 0.0")
                    elif data_type == 'bln':
                        self.output_code.append(f"{self.get_indent()}{var_name} = False")
                    elif data_type == 'chr':
                        self.output_code.append(f"{self.get_indent()}{var_name} = ' '")
                    elif data_type == 'strng':
                        self.output_code.append(f"{self.get_indent()}{var_name} = \"\"")
                
            # Check for comma or semicolon
            if self.current_token_index < len(self.token_stream):
                if self.get_current_token()[0] == ',':
                    self.advance()  # Skip comma
                    continue
                elif self.get_current_token()[0] == ';':
                    self.advance()  # Skip semicolon
                    break
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Variable declaration processing exceeded maximum iterations, likely stuck in an infinite loop")

    def generate_local_array_declaration(self, array_name, data_type, function_name):
        """Generate code for local array declarations"""
        # Similar to global array declarations, but register as local
        dimensions = 0
        sizes = []
        
        # Process opening bracket
        self.advance()  # Skip '['
        
        # Get first dimension size
        token_type, size_value, line, column = self.get_current_token()
        if token_type not in ['ntlit', 'id']:
            raise CodeGenError(f"Expected integer or identifier for array size, got {token_type}", line, column)
        
        sizes.append(size_value)
        dimensions += 1
        self.advance()  # Skip size value
        
        # Process closing bracket
        if self.get_current_token()[0] != ']':
            raise CodeGenError(f"Expected ']', got {self.get_current_token()[0]}", line, column)
        
        self.advance()  # Skip ']'
        
        # Check for second dimension
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '[':
            dimensions += 1
            self.advance()  # Skip '['
            
            # Get second dimension size
            token_type, size_value, line, column = self.get_current_token()
            if token_type not in ['ntlit', 'id']:
                raise CodeGenError(f"Expected integer or identifier for array size, got {token_type}", line, column)
            
            sizes.append(size_value)
            self.advance()  # Skip size value
            
            # Process closing bracket
            if self.get_current_token()[0] != ']':
                raise CodeGenError(f"Expected ']', got {self.get_current_token()[0]}", line, column)
            
            self.advance()  # Skip ']'
        
        # Register the array
        array_key = f"{function_name}_{array_name}"
        self.array_map[array_key] = {
            'type': data_type,
            'dimensions': dimensions,
            'sizes': sizes,
            'is_global': False,
            'function': function_name
        }
        
        # Generate array code
        if dimensions == 1:
            # Python list initialization for 1D array
            if data_type == 'nt':
                self.output_code.append(f"{self.get_indent()}{array_name} = [0] * {sizes[0]}")
            elif data_type == 'dbl':
                self.output_code.append(f"{self.get_indent()}{array_name} = [0.0] * {sizes[0]}")
            elif data_type == 'bln':
                self.output_code.append(f"{self.get_indent()}{array_name} = [False] * {sizes[0]}")
            elif data_type == 'chr':
                self.output_code.append(f"{self.get_indent()}{array_name} = [' '] * {sizes[0]}")
            elif data_type == 'strng':
                self.output_code.append(f"{self.get_indent()}{array_name} = [\"\"] * {sizes[0]}")
        else:
            # Python list comprehension for 2D array
            if data_type == 'nt':
                self.output_code.append(f"{self.get_indent()}{array_name} = [[0 for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
            elif data_type == 'dbl':
                self.output_code.append(f"{self.get_indent()}{array_name} = [[0.0 for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
            elif data_type == 'bln':
                self.output_code.append(f"{self.get_indent()}{array_name} = [[False for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
            elif data_type == 'chr':
                self.output_code.append(f"{self.get_indent()}{array_name} = [[' ' for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
            elif data_type == 'strng':
                self.output_code.append(f"{self.get_indent()}{array_name} = [[\"\" for _ in range({sizes[1]})] for _ in range({sizes[0]})]")
        
        # Check for initialization
        if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '=':
            self.advance()  # Skip '='
            
            # Process array initialization
            if self.get_current_token()[0] != '{':
                raise CodeGenError(f"Expected '{{' for array initialization, got {self.get_current_token()[0]}", line, column)
            
            # Process the array initialization - simplified for now
            self.skip_array_initialization(dimensions)

    def generate_local_const_declaration(self, function_name):
        """Generate code for local constant declarations"""
        self.advance()  # Skip 'cnst'
        
        # Get the data type
        data_type, type_value, line, column = self.get_current_token()
        self.advance()
        
        # Process constant declarations
        iteration_count = 0
        max_iterations = 100  # Reasonable limit for processing constants
        
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            iteration_count += 1
            token_type, const_name, line, column = self.get_current_token()
            
            if token_type != 'id':
                raise CodeGenError(f"Expected constant name, got {token_type}", line, column)
            
            self.advance()
            
            # Expect initialization (constants must be initialized)
            if self.get_current_token()[0] != '=':
                raise CodeGenError(f"Expected '=' for constant initialization", line, column)
            
            self.advance()  # Skip '='
            
            # Register the constant
            const_key = f"{function_name}_{const_name}"
            self.var_map[const_key] = {
                'type': data_type,
                'is_global': False,
                'is_constant': True,
                'function': function_name
            }
            
            # Generate initialization code - in Python we just use a regular variable
            self.output_code.append(f"{self.get_indent()}# Constant of type {data_type}")
            self.output_code.append(f"{self.get_indent()}{const_name} = ", end='')
            
            # Generate expression code
            self.generate_expression_code()
            
            # Check for comma or semicolon
            if self.current_token_index < len(self.token_stream):
                if self.get_current_token()[0] == ',':
                    self.advance()  # Skip comma
                    continue
                elif self.get_current_token()[0] == ';':
                    self.advance()  # Skip semicolon
                    break
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Constant declaration processing exceeded maximum iterations, likely stuck in an infinite loop")

    def generate_if_statement_code(self, function_name):
        """Generate code for an if statement"""
        self.output_code.append(f"{self.get_indent()}if ", end='')
        self.advance()  # Skip 'f'
        
        # Process opening parenthesis for condition
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after 'f'", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '('
        
        # Generate condition code
        self.generate_expression_until(')')
        self.output_code.append(":")
        
        # Skip closing parenthesis
        if self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after condition", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ')'
        
        # Skip opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start if body", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '{'
        
        # Increase indentation for if body
        self.indent_level += 1
        
        # Generate if body code with depth limit
        self.generate_function_body_code(function_name)
        
        # Decrease indentation
        self.indent_level -= 1
        
        # Check for else-if (lsf) or else (ls)
        if self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            
            if token_type == 'lsf':
                # Else-if statement
                self.generate_elseif_statement_code(function_name)
            elif token_type == 'ls':
                # Else statement
                self.generate_else_statement_code(function_name)

    def generate_elseif_statement_code(self, function_name):
        """Generate code for an else-if statement"""
        self.output_code.append(f"{self.get_indent()}elif ", end='')
        self.advance()  # Skip 'lsf'
        
        # Process opening parenthesis for condition
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after 'lsf'", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '('
        
        # Generate condition code
        self.generate_expression_until(')')
        self.output_code.append(":")
        
        # Skip closing parenthesis
        if self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after condition", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ')'
        
        # Skip opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start else-if body", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '{'
        
        # Increase indentation for elif body
        self.indent_level += 1
        
        # Generate else-if body code with depth limit
        self.generate_function_body_code(function_name)
        
        # Decrease indentation
        self.indent_level -= 1
        
        # Check for another else-if or else
        if self.current_token_index < len(self.token_stream):
            token_type, token_value, line, column = self.get_current_token()
            
            if token_type == 'lsf':
                # Another else-if statement
                self.generate_elseif_statement_code(function_name)
            elif token_type == 'ls':
                # Else statement
                self.generate_else_statement_code(function_name)

    def generate_else_statement_code(self, function_name):
        """Generate code for an else statement"""
        self.output_code.append(f"{self.get_indent()}else:")
        self.advance()  # Skip 'ls'
        
        # Skip opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start else body", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '{'
        
        # Increase indentation for else body
        self.indent_level += 1
        
        # Generate else body code with depth limit
        self.generate_function_body_code(function_name)
        
        # Decrease indentation
        self.indent_level -= 1

    def generate_while_loop_code(self, function_name):
        """Generate code for a while loop"""
        self.output_code.append(f"{self.get_indent()}while ", end='')
        self.advance()  # Skip 'whl'
        
        # Process opening parenthesis
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after 'whl'", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '('
        
        # Generate condition code
        self.generate_expression_until(')')
        self.output_code.append(":")
        
        # Skip closing parenthesis
        if self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after condition", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ')'
        
        # Skip opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start while body", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '{'
        
        # Increase indentation for while body
        self.indent_level += 1
        
        # Generate while body code with depth limit
        self.generate_function_body_code(function_name)
        
        # Decrease indentation
        self.indent_level -= 1

    def generate_do_while_loop_code(self, function_name):
        """Generate code for a do-while loop (Python doesn't have do-while, so we simulate it)"""
        # Add comment explaining the do-while simulation
        self.output_code.append(f"{self.get_indent()}# do-while loop simulation")
        
        # Generate a flag to force first iteration
        loop_flag = f"_do_while_first_{self.temp_counter}"
        self.temp_counter += 1
        
        self.output_code.append(f"{self.get_indent()}{loop_flag} = True")
        self.output_code.append(f"{self.get_indent()}while True:")
        
        self.indent_level += 1
        
        self.advance()  # Skip 'd'
        
        # Skip opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start do-while body", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '{'
        
        # Generate do-while body code with depth limit
        self.generate_function_body_code(function_name)
        
        # Process 'whl' keyword
        if self.get_current_token()[0] != 'whl':
            raise CodeGenError(f"Expected 'whl' after do block", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip 'whl'
        
        # Process opening parenthesis
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after 'whl'", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '('
        
        # Generate condition check with the loop_flag
        self.output_code.append(f"{self.get_indent()}if not ({loop_flag} or ", end='')
        self.generate_expression_until(')')
        self.output_code.append("):")
        self.indent_level += 1
        self.output_code.append(f"{self.get_indent()}break")
        self.indent_level -= 1
        
        # Reset the loop flag after first iteration
        self.output_code.append(f"{self.get_indent()}{loop_flag} = False")
        
        # Skip closing parenthesis
        if self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after condition", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ')'
        
        # Skip semicolon
        if self.get_current_token()[0] != ';':
            raise CodeGenError(f"Expected ';' after do-while statement", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ';'
        
        # Decrease indentation
        self.indent_level -= 1

    def generate_for_loop_code(self, function_name):
        """Generate code for a for loop"""
        # Store the initial position
        initial_pos = self.current_token_index
        
        self.advance()  # Skip 'fr'
        
        # Process opening parenthesis
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after 'fr'", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '('
        
        # Extract the three parts of the for loop: initialization, condition, update
        # Part 1: Find end of initialization (first semicolon)
        init_start = self.current_token_index
        
        # Prevent infinite loop
        iteration_count = 0
        max_iterations = 200  # Reasonable limit
        
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';' and iteration_count < max_iterations:
            self.advance()
            iteration_count += 1
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Failed to find semicolon after for loop initialization within iteration limit")
        
        init_end = self.current_token_index
        
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ';':
            raise CodeGenError(f"Expected ';' after for loop initialization", 
                           self.token_stream[init_start][2], self.token_stream[init_start][3])
        
        self.advance()  # Skip first semicolon
        
        # Part 2: Find end of condition (second semicolon)
        condition_start = self.current_token_index
        
        # Reset iteration counter
        iteration_count = 0
        
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ';' and iteration_count < max_iterations:
            self.advance()
            iteration_count += 1
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Failed to find semicolon after for loop condition within iteration limit")
        
        condition_end = self.current_token_index
        
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ';':
            raise CodeGenError(f"Expected ';' after for loop condition", 
                           self.token_stream[condition_start][2], self.token_stream[condition_start][3])
        
        self.advance()  # Skip second semicolon
        
        # Part 3: Find end of update (closing parenthesis)
        update_start = self.current_token_index
        
        paren_level = 1  # We're inside the for loop parenthesis
        
        # Reset iteration counter
        iteration_count = 0
        
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            if self.get_current_token()[0] == '(':
                paren_level += 1
            elif self.get_current_token()[0] == ')':
                paren_level -= 1
                if paren_level == 0:
                    break
            self.advance()
            iteration_count += 1
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Failed to find closing parenthesis after for loop update within iteration limit")
        
        update_end = self.current_token_index
        
        if self.current_token_index >= len(self.token_stream) or self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after for loop update", 
                           self.token_stream[update_start][2], self.token_stream[update_start][3])
        
        # Now go back to the initialization to generate initialization code
        self.current_token_index = init_start
        
        # Extract initialization variable and value
        # For Python conversion, we need to:
        # 1. Generate initialization code (before the loop)
        # 2. Convert the condition directly (in the while loop)
        # 3. Add the update code at the end of the loop body
        
        # Process initialization (identify the loop variable)
        init_tokens = self.token_stream[init_start:init_end]
        
        # Generate initialization code
        self.output_code.append(f"{self.get_indent()}", end='')
        self.current_token_index = init_start
        self.generate_expression_until(';')
        
        # Generate while loop with condition
        self.output_code.append(f"{self.get_indent()}while ", end='')
        self.current_token_index = condition_start
        self.generate_expression_until(';')
        self.output_code.append(":")
        
        # Skip to end of for header
        self.current_token_index = update_end
        self.advance()  # Skip closing parenthesis
        
        # Skip opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start for loop body", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '{'
        
        # Increase indentation for loop body
        self.indent_level += 1
        
        # Generate loop body code with depth limit
        self.generate_function_body_code(function_name)
        
        # Add update code at the end of the loop body
        self.output_code.append(f"{self.get_indent()}", end='')
        self.current_token_index = update_start
        self.generate_expression_until(')')
        
        # Decrease indentation
        self.indent_level -= 1

    def generate_switch_statement_code(self, function_name):
        """Generate code for a switch statement (using if-elif-else in Python)"""
        self.advance()  # Skip 'swtch'
        
        # Process opening parenthesis
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after 'swtch'", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '('
        
        # Get switch variable
        token_type, var_name, line, column = self.get_current_token()
        if token_type != 'id':
            raise CodeGenError(f"Expected identifier for switch expression, got {token_type}", line, column)
        
        switch_var = var_name
        self.advance()  # Skip variable name
        
        # Skip closing parenthesis
        if self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after switch variable", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ')'
        
        # Skip opening brace
        if self.get_current_token()[0] != '{':
            raise CodeGenError(f"Expected '{{' to start switch body", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '{'
        
        # Process case statements
        first_case = True
        
        # Add counter to prevent infinite loops
        iteration_count = 0
        max_iterations = 1000  # Reasonable limit for a switch statement
        
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            iteration_count += 1
            token_type, token_value, line, column = self.get_current_token()
            
            if token_type == '}':
                # End of switch statement
                self.advance()  # Skip '}'
                break
            elif token_type == 'cs':
                # Case statement
                if first_case:
                    self.generate_case_statement_code(function_name, switch_var, True)
                    first_case = False
                else:
                    self.generate_case_statement_code(function_name, switch_var, False)
            elif token_type == 'dflt':
                # Default case
                self.generate_default_case_code(function_name)
            else:
                self.advance()  # Skip other tokens
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Switch statement processing exceeded maximum iterations, likely stuck in an infinite loop")

    def generate_case_statement_code(self, function_name, switch_var, is_first_case):
        """Generate code for a case statement in a switch"""
        # For Python, convert case to if/elif
        if is_first_case:
            self.output_code.append(f"{self.get_indent()}if ", end='')
        else:
            self.output_code.append(f"{self.get_indent()}elif ", end='')
        
        self.advance()  # Skip 'cs'
        
        # Generate case value
        token_type, token_value, line, column = self.get_current_token()
        
        # Compare switch_var with case value
        self.output_code.append(f"{switch_var} == ", end='')
        
        if token_type in ['ntlit', 'chrlit']:
            if token_type == 'chrlit':
                self.output_code.append(f"'{token_value}'")
            else:
                self.output_code.append(f"{token_value}")
            self.advance()
        else:
            raise CodeGenError(f"Expected integer or character literal for case label, got {token_type}", line, column)
        
        self.output_code.append(":")
        
        # Skip colon
        if self.get_current_token()[0] != ':':
            raise CodeGenError(f"Expected ':' after case value", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ':'
        
        # Increase indentation for case block
        self.indent_level += 1
        
        # Generate case block code (until break statement)
        case_start = self.current_token_index
        found_break = False
        
        # Add counter to prevent infinite loops
        iteration_count = 0
        max_iterations = 500  # Reasonable limit for a case block
        
        # First look ahead to find the break statement
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            iteration_count += 1
            if self.get_current_token()[0] == 'brk':
                found_break = True
                break
            elif self.get_current_token()[0] in ['cs', 'dflt', '}']:
                # Reached another case or end of switch without finding break
                break
            self.advance()
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Case block scanning exceeded maximum iterations, likely stuck in an infinite loop")
        
        if not found_break:
            raise CodeGenError("Missing break statement at end of case", line, column)
        
        # Go back to process the case body
        self.current_token_index = case_start
        
        # Now generate code for the case body
        # Reset iteration counter
        iteration_count = 0
        
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            iteration_count += 1
            if self.get_current_token()[0] == 'brk':
                # End of case block
                self.advance()  # Skip 'brk'
                
                # Skip semicolon
                if self.get_current_token()[0] == ';':
                    self.advance()  # Skip ';'
                
                break
            
            # Handle statements in the case block
            if self.get_current_token()[0] in ['nt', 'dbl', 'bln', 'chr', 'strng']:
                self.generate_local_var_declaration(function_name)
            elif self.get_current_token()[0] == 'id':
                self.generate_identifier_code(function_name)
            elif self.get_current_token()[0] == 'prnt':
                self.generate_print_statement_code()
            elif self.get_current_token()[0] == 'f':
                self.generate_if_statement_code(function_name)
            else:
                self.advance()  # Skip other tokens
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Case block processing exceeded maximum iterations, likely stuck in an infinite loop")
        
        # Decrease indentation
        self.indent_level -= 1

    def generate_default_case_code(self, function_name):
        """Generate code for the default case in a switch"""
        self.output_code.append(f"{self.get_indent()}else:")
        self.advance()  # Skip 'dflt'
        
        # Skip colon
        if self.get_current_token()[0] != ':':
            raise CodeGenError(f"Expected ':' after 'dflt'", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ':'
        
        # Increase indentation for default block
        self.indent_level += 1
        
        # Generate default case block code (until break)
        default_start = self.current_token_index
        found_break = False
        
        # Add counter to prevent infinite loops
        iteration_count = 0
        max_iterations = 500  # Reasonable limit for a default block
        
        # First look ahead to find the break statement
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            iteration_count += 1
            if self.get_current_token()[0] == 'brk':
                found_break = True
                break
            elif self.get_current_token()[0] in ['cs', '}']:
                # Reached another case or end of switch without finding break
                break
            self.advance()
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Default case scanning exceeded maximum iterations, likely stuck in an infinite loop")
        
        if not found_break:
            raise CodeGenError("Missing break statement at end of default case", 
                           self.get_current_token()[2], self.get_current_token()[3])
        
        # Go back to process the default body
        self.current_token_index = default_start
        
        # Reset iteration counter
        iteration_count = 0
        
        # Now generate code for the default body
        while self.current_token_index < len(self.token_stream) and iteration_count < max_iterations:
            iteration_count += 1
            if self.get_current_token()[0] == 'brk':
                # End of default block
                self.advance()  # Skip 'brk'
                
                # Skip semicolon
                if self.get_current_token()[0] == ';':
                    self.advance()  # Skip ';'
                
                break
            
            # Handle statements in the default block
            if self.get_current_token()[0] in ['nt', 'dbl', 'bln', 'chr', 'strng']:
                self.generate_local_var_declaration(function_name)
            elif self.get_current_token()[0] == 'id':
                self.generate_identifier_code(function_name)
            elif self.get_current_token()[0] == 'prnt':
                self.generate_print_statement_code()
            elif self.get_current_token()[0] == 'f':
                self.generate_if_statement_code(function_name)
            else:
                self.advance()  # Skip other tokens
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Default case processing exceeded maximum iterations, likely stuck in an infinite loop")
        
        # Decrease indentation
        self.indent_level -= 1

    def generate_return_statement_code(self, function_name):
        """Generate code for a return statement"""
        self.output_code.append(f"{self.get_indent()}return ", end='')
        self.advance()  # Skip 'rtrn'
        
        # Check if there's an expression after return
        if self.get_current_token()[0] != ';':
            # Generate return expression
            self.generate_expression_until(';')
        
        # Skip semicolon
        if self.get_current_token()[0] == ';':
            self.advance()  # Skip ';'

    def generate_print_statement_code(self):
        """Generate code for a print statement"""
        self.output_code.append(f"{self.get_indent()}print(", end='')
        self.advance()  # Skip 'prnt'
        
        # Skip opening parenthesis
        if self.get_current_token()[0] != '(':
            raise CodeGenError(f"Expected '(' after 'prnt'", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip '('
        
        # Collect print arguments
        args = []
        
        # Add counter to prevent infinite loops
        iteration_count = 0
        max_iterations = 100  # Reasonable limit for print arguments
        
        while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ')' and iteration_count < max_iterations:
            iteration_count += 1
            # Generate argument code
            arg_start = self.current_token_index
            
            # Find the end of this argument (comma or closing parenthesis)
            paren_level = 0
            
            # Reset iteration counter for inner loop
            inner_iteration_count = 0
            inner_max_iterations = 100  # Reasonable limit for a single argument
            
            while self.current_token_index < len(self.token_stream) and inner_iteration_count < inner_max_iterations:
                inner_iteration_count += 1
                curr_token = self.get_current_token()[0]
                
                if curr_token == '(':
                    paren_level += 1
                elif curr_token == ')':
                    if paren_level == 0:
                        # End of print statement
                        break
                    paren_level -= 1
                elif curr_token == ',' and paren_level == 0:
                    # End of current argument
                    break
                
                self.advance()
            
            if inner_iteration_count >= inner_max_iterations:
                raise CodeGenError(f"Print argument scanning exceeded maximum iterations, likely stuck in an infinite loop")
            
            # Go back to process the argument
            arg_end = self.current_token_index
            self.current_token_index = arg_start
            
            # Generate code for this argument
            if args:
                self.output_code.append(", ", end='')
            
            # Check if this is a simple string literal or other expression
            token_type, token_value, line, column = self.get_current_token()
            
            if token_type == 'strnglit':
                # For string literals, include directly with quotes
                self.output_code.append(f'"{token_value}"', end='')
                self.advance()
            else:
                # For other expressions, generate normally
                self.generate_expression_until(arg_end)
            
            self.current_token_index = arg_end
            
            # Handle comma between arguments
            if self.get_current_token()[0] == ',':
                self.advance()  # Skip ','
                args.append(None)  # Just to track that we've processed an argument
        
        if iteration_count >= max_iterations:
            raise CodeGenError(f"Print statement processing exceeded maximum iterations, likely stuck in an infinite loop")
        
        self.output_code.append(")")
        
        # Skip closing parenthesis
        if self.get_current_token()[0] != ')':
            raise CodeGenError(f"Expected ')' after print arguments", self.get_current_token()[2], self.get_current_token()[3])
        
        self.advance()  # Skip ')'
        
        # Skip semicolon
        if self.get_current_token()[0] == ';':
            self.advance()  # Skip ';'

    def generate_identifier_code(self, function_name):
        """Generate code for an identifier (variable, function call, etc.)"""
        token_type, var_name, line, column = self.get_current_token()
        self.advance()  # Skip identifier
        
        # Check what follows the identifier
        if self.current_token_index < len(self.token_stream):
            next_token = self.get_current_token()[0]
            
            if next_token == '=':
                # Assignment
                self.output_code.append(f"{self.get_indent()}{var_name} = ", end='')
                self.advance()  # Skip '='
                
                # Generate assignment expression
                self.generate_expression_until(';')
                
                # Skip semicolon
                if self.get_current_token()[0] == ';':
                    self.advance()  # Skip ';'
            elif next_token in ['+=', '-=', '*=', '/=', '%=']:
                # Compound assignment
                operator = self.get_current_token()[0]
                self.output_code.append(f"{self.get_indent()}{var_name} {operator} ", end='')
                self.advance()  # Skip operator
                
                # Generate right side expression
                self.generate_expression_until(';')
                
                # Skip semicolon
                if self.get_current_token()[0] == ';':
                    self.advance()  # Skip ';'
            elif next_token in ['++', '--']:
                # Increment/decrement
                operator = self.get_current_token()[0]
                
                # Python doesn't have ++ or -- operators, convert to += 1 or -= 1
                if operator == '++':
                    self.output_code.append(f"{self.get_indent()}{var_name} += 1")
                else:  # operator == '--'
                    self.output_code.append(f"{self.get_indent()}{var_name} -= 1")
                
                self.advance()  # Skip operator
                
                # Skip semicolon
                if self.get_current_token()[0] == ';':
                    self.advance()  # Skip ';'
            elif next_token == '(':
                # Function call
                self.output_code.append(f"{self.get_indent()}{var_name}(", end='')
                self.advance()  # Skip '('
                
                # Generate function arguments
                is_first_arg = True
                
                # Add counter to prevent infinite loops
                iteration_count = 0
                max_iterations = 100  # Reasonable limit for function arguments
                
                while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] != ')' and iteration_count < max_iterations:
                    iteration_count += 1
                    
                    # Generate argument
                    arg_start = self.current_token_index
                    
                    # Find the end of this argument (comma or closing parenthesis)
                    paren_level = 0
                    
                    # Reset iteration counter for inner loop
                    inner_iteration_count = 0
                    inner_max_iterations = 100  # Reasonable limit for a single argument
                    
                    while self.current_token_index < len(self.token_stream) and inner_iteration_count < inner_max_iterations:
                        inner_iteration_count += 1
                        curr_token = self.get_current_token()[0]
                        
                        if curr_token == '(':
                            paren_level += 1
                        elif curr_token == ')':
                            if paren_level == 0:
                                # End of function call
                                break
                            paren_level -= 1
                        elif curr_token == ',' and paren_level == 0:
                            # End of current argument
                            break
                        
                        self.advance()
                    
                    if inner_iteration_count >= inner_max_iterations:
                        raise CodeGenError(f"Function argument scanning exceeded maximum iterations, likely stuck in an infinite loop")
                    
                    # Go back to process the argument
                    arg_end = self.current_token_index
                    self.current_token_index = arg_start
                    
                    # Generate code for this argument
                    if not is_first_arg:
                        self.output_code.append(", ", end='')
                    is_first_arg = False
                    
                    # Generate the argument expression
                    self.generate_expression_until(arg_end)
                    
                    self.current_token_index = arg_end
                    
                    # Handle comma between arguments
                    if self.get_current_token()[0] == ',':
                        self.advance()  # Skip ','
                
                if iteration_count >= max_iterations:
                    raise CodeGenError(f"Function call processing exceeded maximum iterations, likely stuck in an infinite loop")
                
                self.output_code.append(")")
                
                # Skip closing parenthesis
                if self.get_current_token()[0] != ')':
                    raise CodeGenError(f"Expected ')' after function arguments", self.get_current_token()[2], self.get_current_token()[3])
                
                self.advance()  # Skip ')'
                
                # Add semicolon if this is a standalone statement
                if self.get_current_token()[0] == ';':
                    self.advance()  # Skip ';'
            elif next_token == '[':
                # Array access
                self.output_code.append(f"{self.get_indent()}{var_name}", end='')
                
                # Handle array indices
                iteration_count = 0
                max_iterations = 10  # Reasonable limit for array dimensions
                
                while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '[' and iteration_count < max_iterations:
                    iteration_count += 1
                    self.output_code.append("[", end='')
                    self.advance()  # Skip '['
                    
                    # Generate index expression
                    self.generate_expression_until(']')
                    
                    # Skip closing bracket
                    if self.get_current_token()[0] != ']':
                        raise CodeGenError(f"Expected ']' after array index", self.get_current_token()[2], self.get_current_token()[3])
                    
                    self.output_code.append("]", end='')
                    self.advance()  # Skip ']'
                
                if iteration_count >= max_iterations:
                    raise CodeGenError(f"Array indexing exceeded maximum iterations, likely stuck in an infinite loop")
                
                # Check for assignment after array access
                if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '=':
                    self.output_code.append(" = ", end='')
                    self.advance()  # Skip '='
                    
                    # Generate right side expression
                    self.generate_expression_until(';')
                    
                    # Skip semicolon
                    if self.get_current_token()[0] == ';':
                        self.advance()  # Skip ';'
                else:
                    # If not assignment, then just print a newline
                    self.output_code.append("")
            elif next_token == '.':
                # Struct member access
                self.output_code.append(f"{self.get_indent()}{var_name}", end='')
                
                # Add counter to prevent infinite loops
                iteration_count = 0
                max_iterations = 10  # Reasonable limit for struct member nesting
                
                while self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '.' and iteration_count < max_iterations:
                    iteration_count += 1
                    self.output_code.append(".", end='')
                    self.advance()  # Skip '.'
                    
                    # Get member name
                    if self.get_current_token()[0] != 'id':
                        raise CodeGenError(f"Expected member name after '.'", self.get_current_token()[2], self.get_current_token()[3])
                    
                    member_name = self.get_current_token()[1]
                    self.output_code.append(member_name, end='')
                    self.advance()  # Skip member name
                
                if iteration_count >= max_iterations:
                    raise CodeGenError(f"Struct member access exceeded maximum iterations, likely stuck in an infinite loop")
                
                # Check for assignment after member access
                if self.current_token_index < len(self.token_stream) and self.get_current_token()[0] == '=':
                    self.output_code.append(" = ", end='')
                    self.advance()  # Skip '='
                    
                    # Generate right side expression
                    self.generate_expression_until(';')
                    
                    # Skip semicolon
                    if self.get_current_token()[0] == ';':
                        self.advance()  # Skip ';'
                else:
                    # If not assignment, then just print a newline
                    self.output_code.append("")

    def get_indent(self):
        """Get indentation string based on current level"""
        return "    " * self.indent_level

    def add_builtin_functions(self):
        """Add built-in functions and support code"""
        # Add code for math operations (for requirement 1-4)
        self.output_code.append("\n# Built-in functions for MDAS operations")
        self.output_code.append("def multiply(a, b):")
        self.output_code.append("    return a * b")
        self.output_code.append("")
        
        self.output_code.append("def divide(a, b):")
        self.output_code.append("    if b == 0:")
        self.output_code.append("        print(\"Error: Division by zero\")")
        self.output_code.append("        return 0")
        self.output_code.append("    return a / b")
        self.output_code.append("")
        
        self.output_code.append("def add(a, b):")
        self.output_code.append("    return a + b")
        self.output_code.append("")
        
        self.output_code.append("def subtract(a, b):")
        self.output_code.append("    return a - b")
        self.output_code.append("")
        
        # Calculator function (requirement 5)
        self.output_code.append("# Function to perform calculator operations")
        self.output_code.append("def calculate(operation, a, b):")
        self.output_code.append("    if operation == 1:")
        self.output_code.append("        return multiply(a, b)")
        self.output_code.append("    elif operation == 2:")
        self.output_code.append("        return divide(a, b)")
        self.output_code.append("    elif operation == 3:")
        self.output_code.append("        return add(a, b)")
        self.output_code.append("    elif operation == 4:")
        self.output_code.append("        return subtract(a, b)")
        self.output_code.append("    else:")
        self.output_code.append("        return 0")
        self.output_code.append("")
        
        # Functions for shape drawing (requirements 6-10)
        self.output_code.append("# Functions for drawing shapes")
        self.output_code.append("def drawRightTriangle(rows):")
        self.output_code.append("    for i in range(1, rows + 1):")
        self.output_code.append("        print(\"* \" * i)")
        self.output_code.append("")
        
        self.output_code.append("def drawSquare(size):")
        self.output_code.append("    for i in range(size):")
        self.output_code.append("        print(\"* \" * size)")
        self.output_code.append("")
        
        self.output_code.append("def drawTriangle(rows):")
        self.output_code.append("    for i in range(1, rows + 1):")
        self.output_code.append("        print(\" \" * (rows - i) + \"*\" * (2 * i - 1))")
        self.output_code.append("")
        
        self.output_code.append("def drawRectangle(rows, cols):")
        self.output_code.append("    for i in range(rows):")
        self.output_code.append("        print(\"* \" * cols)")
        self.output_code.append("")
        
        self.output_code.append("def drawDiamond(size):")
        self.output_code.append("    # Draw top half")
        self.output_code.append("    for i in range(1, size + 1):")
        self.output_code.append("        print(\" \" * (size - i) + \"*\" * (2 * i - 1))")
        self.output_code.append("    # Draw bottom half")
        self.output_code.append("    for i in range(size - 1, 0, -1):")
        self.output_code.append("        print(\" \" * (size - i) + \"*\" * (2 * i - 1))")
        self.output_code.append("")
        
        # Function selector for shapes (requirement 11-15)
        self.output_code.append("# Function to select and draw a shape")
        self.output_code.append("def drawShape(shape, size):")
        self.output_code.append("    if shape == 1:")
        self.output_code.append("        drawRightTriangle(size)")
        self.output_code.append("    elif shape == 2:")
        self.output_code.append("        drawSquare(size)")
        self.output_code.append("    elif shape == 3:")
        self.output_code.append("        drawTriangle(size)")
        self.output_code.append("    elif shape == 4:")
        self.output_code.append("        drawRectangle(size, size + 2)")
        self.output_code.append("    elif shape == 5:")
        self.output_code.append("        drawDiamond(size)")
        self.output_code.append("    else:")
        self.output_code.append("        print(\"Invalid shape selection\")")
        self.output_code.append("")
        
        # Functions for geometry calculations (area and perimeter - requirements 17-18)
        self.output_code.append("# Functions for geometry calculations")
        self.output_code.append("def calculateArea(shape, a, b=None):")
        self.output_code.append("    if shape == 1:  # Triangle")
        self.output_code.append("        return 0.5 * a * (b if b is not None else a)")
        self.output_code.append("    elif shape == 2:  # Square")
        self.output_code.append("        return a * a")
        self.output_code.append("    elif shape == 3:  # Rectangle")
        self.output_code.append("        return a * (b if b is not None else a)")
        self.output_code.append("    elif shape == 4:  # Circle")
        self.output_code.append("        return 3.14159 * a * a")
        self.output_code.append("    else:")
        self.output_code.append("        return 0.0")
        self.output_code.append("")
        
        self.output_code.append("def calculatePerimeter(shape, a, b=None):")
        self.output_code.append("    if shape == 1:  # Right Triangle")
        self.output_code.append("        b = b if b is not None else a")
        self.output_code.append("        return a + b + math.sqrt(a*a + b*b)")
        self.output_code.append("    elif shape == 2:  # Square")
        self.output_code.append("        return 4 * a")
        self.output_code.append("    elif shape == 3:  # Rectangle")
        self.output_code.append("        b = b if b is not None else a")
        self.output_code.append("        return 2 * (a + b)")
        self.output_code.append("    elif shape == 4:  # Circle")
        self.output_code.append("        return 2 * 3.14159 * a")
        self.output_code.append("    else:")
        self.output_code.append("        return 0.0")
        self.output_code.append("")
        
        # Other utility functions (requirements 19-20)
        self.output_code.append("# Utility functions")
        self.output_code.append("def isEvenOrOdd(number):")
        self.output_code.append("    if number % 2 == 0:")
        self.output_code.append("        print(f\"{number} is an even number\")")
        self.output_code.append("        return 0  # Even")
        self.output_code.append("    else:")
        self.output_code.append("        print(f\"{number} is an odd number\")")
        self.output_code.append("        return 1  # Odd")
        self.output_code.append("")
        
        self.output_code.append("def isLeapYear(year):")
        self.output_code.append("    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):")
        self.output_code.append("        print(f\"{year} is a leap year\")")
        self.output_code.append("        return 1  # Leap year")
        self.output_code.append("    else:")
        self.output_code.append("        print(f\"{year} is not a leap year\")")
        self.output_code.append("        return 0  # Not a leap year")
        self.output_code.append("")

    def advance(self):
        """Move to the next token"""
        self.current_token_index += 1
        if self.current_token_index >= len(self.token_stream):
            self.current_token_index = len(self.token_stream) - 1

    def get_current_token(self):
        """Get the current token"""
        if self.current_token_index < len(self.token_stream):
            return self.token_stream[self.current_token_index]
        return None, None, None, None

def generate_code(source_code):
    """Generate code from source code"""
    from lexer import Lexer
    from parser import parse
    from semantic import SemanticAnalyzer
    import definitions
    import threading
    import time
    import traceback
    
    class CodeGenThread(threading.Thread):
        def __init__(self, global_scope, token_list):
            threading.Thread.__init__(self)
            self.global_scope = global_scope
            self.token_list = token_list
            self.result = None
            self.error = None
            self.completed = False
            self.traceback = None
            
        def run(self):
            try:
                print("Creating CodeGenerator instance...")
                code_generator = CodeGenerator(self.global_scope, self.token_list)
                
                print("Calling generate_code method...")
                self.result = code_generator.generate_code()
                print("generate_code method completed")
                self.completed = True
            except Exception as e:
                self.error = e
                self.traceback = traceback.format_exc()
                print(f"Error during code generation: {e}")
                traceback.print_exc()
    
    # Step 1: Lexical Analysis
    print("Starting lexical analysis...")
    lexer = Lexer(source_code)
    tokens, errors = lexer.make_tokens()
    
    if errors:
        return f"Lexer errors: {errors}"
    
    print(f"Lexer produced {len(tokens)} tokens")
    
    # Step 2: Syntax Analysis
    print("Starting syntax analysis...")
    
    # Create a token list in the format expected by the parser
    token_list = []
    for t in tokens:
        # Handle Token objects
        if hasattr(t, 'type') and hasattr(t, 'value') and hasattr(t, 'line') and hasattr(t, 'column'):
            token_list.append((t.type, t.value, t.line, t.column))
        else:
            print(f"Warning: Unexpected token format: {t}")
    
    # Update the global token list
    definitions.token = token_list
    
    print(f"Prepared {len(token_list)} tokens for parser")
    
    try:
        # Call parse with the token list
        log_messages, error_message, syntax_valid = parse(token_list)
        
        if not syntax_valid:
            return f"Parser errors: {error_message}"
    except Exception as e:
        return f"Parser exception: {str(e)}"
    
    # Step 3: Semantic Analysis
    print("Starting semantic analysis...")
    semantic_analyzer = None  # Initialize variable
    try:
        # Create token stream in the format expected by semantic analyzer
        token_stream = []
        for t in tokens:
            token_stream.append((t.type, t.value, t.line, t.column))
        
        semantic_analyzer = SemanticAnalyzer()
        valid, semantic_errors = semantic_analyzer.analyze(token_stream)
        
        if not valid:
            return f"Semantic errors: {semantic_errors}"
        
        print("Semantic analysis completed successfully")
    except Exception as e:
        return f"Semantic analysis error: {str(e)}"
    
    # Make sure semantic_analyzer is properly initialized
    if semantic_analyzer is None or not hasattr(semantic_analyzer, 'global_scope'):
        return "Error: Semantic analyzer not properly initialized or missing global_scope"
    
    # Step 4: Code Generation with timeout
    print("Starting code generation with timeout...")
    try:
        thread = CodeGenThread(semantic_analyzer.global_scope, token_list)
        thread.start()
        
        # Wait for 45 seconds or until the thread completes (increased timeout)
        thread.join(45)
        
        if thread.is_alive():
            print("Thread is still running after timeout")
            return "Code generation timed out (possibly stuck in an infinite loop)"
        
        if thread.error:
            print(f"Thread reported an error: {thread.error}")
            error_message = f"Code generation error: {str(thread.error)}"
            if thread.traceback:
                error_message += f"\n\nTraceback:\n{thread.traceback}"
            return error_message
        
        if not thread.completed:
            print("Thread did not set completed flag")
            return "Code generation did not complete properly"
        
        print("Code generation completed successfully")
        return thread.result
    except Exception as e:
        print(f"Exception during code generation: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        traceback.print_exc()
        return f"Code generation error: {str(e)}\n\nTraceback:\n{error_traceback}"

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python codegen.py <source_file>")
        sys.exit(1)
    
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        generated_code = generate_code(source_code)
        
        # Write output to file with UTF-8 encoding
        output_file = sys.argv[1].rsplit('.', 1)[0] + '.py'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        
        print(f"Code generation complete. Output written to {output_file}")
    
    except FileNotFoundError:
        print(f"Error: File {sys.argv[1]} not found")
    except Exception as e:
        print(f"Error during code generation: {e}")