"""
Conso to C Transpiler
This module converts Conso code to C code, assuming the input has already passed
lexical, syntax and semantic analysis.
"""
import re
import sys

class ConsoTranspiler:
    def __init__(self):
        # Mapping of Conso types to C types
        self.type_mapping = {
            "nt": "int",
            "dbl": "double",
            "strng": "char*",
            "bln": "int",  # boolean values in C are integers
            "chr": "char",
            "vd": "void",
            "dfstrct": "struct"  # struct instantiation
        }
        
        # Mapping of Conso keywords to C equivalents
        self.keyword_mapping = {
            "f": "if",
            "ls": "else",
            "lsf": "else if",
            "whl": "while",
            "fr": "for",
            "d": "do",
            "swtch": "switch",
            "cs": "case",
            "dflt": "default",
            "brk": "break",
            "rtrn": "return",
            "cntn": "continue"
        }
        
        # Boolean literals
        self.bool_mapping = {
            "tr": "1",
            "fls": "0"
        }

        # Default values for uninitialized variables
        self.default_values = {
            "nt": "0",
            "dbl": "0.0",
            "strng": "\"\"",
            "bln": "0",  # false
            "chr": "' '"
        }

    def transpile(self, conso_code):
        """
        Transpile Conso code to C code.
        Handles function declarations/definitions, structs, and main function separately.
        """
        # Add standard headers and helper functions
        c_code = self._generate_headers() + self._generate_helper_functions()
        
        # Parse and process the code
        function_prototypes = []  # Store function prototypes
        function_definitions = []  # Store function definitions
        struct_definitions = []   # Store struct definitions
        main_function = None      # Store main function
        
        # Split into lines and process
        lines = conso_code.split('\n')
        i = 0
        
        # First pass - extract all declarations and blocks
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:  # Skip empty lines
                i += 1
                continue
                
            # Extract function declarations and definitions
            if line.startswith('fnctn '):
                # Extract the function block
                function_block, skip_lines = self._extract_block(lines, i)
                if function_block:
                    # Process the function
                    proto, definition = self._process_function(function_block)
                    if proto:
                        function_prototypes.append(proto)
                    if definition:
                        function_definitions.append(definition)
                i += skip_lines
                continue
                
            # Extract struct definitions
            elif line.startswith('strct '):
                # Extract the struct block
                struct_block, skip_lines = self._extract_block(lines, i)
                if struct_block:
                    # Process the struct
                    struct_def = self._process_struct(struct_block)
                    if struct_def:
                        struct_definitions.append(struct_def)
                i += skip_lines
                continue
                
            # Extract main function
            elif line.startswith('mn('):
                # Extract the main function block
                main_block, skip_lines = self._extract_main_block(lines, i)
                if main_block:
                    # Process the main function
                    main_function = self._process_main(main_block)
                i += skip_lines
                continue
                
            i += 1
        
        # Construct the final C code
        output = []
        
        # Add struct definitions
        if struct_definitions:
            output.append("// Struct definitions")
            output.extend(struct_definitions)
            output.append("")
        
        # Add function prototypes
        if function_prototypes:
            output.append("// Function prototypes")
            output.extend(function_prototypes)
            output.append("")
        
        # Add main function
        if main_function:
            output.append(main_function)
            output.append("")
        
        # Add function definitions
        if function_definitions:
            output.append("// Function definitions")
            output.extend(function_definitions)
        
        # Join and return the final C code
        c_code += "\n".join(output)
        return c_code

    def _extract_block(self, lines, start_idx):
        """
        Extract a code block from lines starting at start_idx.
        Returns the block and the number of lines to skip.
        """
        result = []
        i = start_idx
        brace_count = 0
        in_block = False
        
        # Process until we find the end of the block
        while i < len(lines):
            current_line = lines[i].strip()
            if not in_block:
                # First time encountering the block
                in_block = True
                if '{' in current_line:
                    brace_count = 1  # Count the opening brace
                else:
                    brace_count = 0
                
                result.append(lines[i])  # Add the line with original indentation
                i += 1
                continue
            
            # Already inside the block, count braces
            result.append(lines[i])  # Add the line with original indentation
            
            if '{' in current_line:
                brace_count += current_line.count('{')
            if '}' in current_line:
                brace_count -= current_line.count('}')
                
            # If brace count reaches 0, we've found the end
            if brace_count == 0:
                break
                
            i += 1
        
        return '\n'.join(result), (i - start_idx + 1)

    def _extract_main_block(self, lines, start_idx):
        """
        Special extraction for main function, which ends with 'end;'
        """
        result = []
        i = start_idx
        
        # Process until we find the 'end;' statement
        while i < len(lines):
            current_line = lines[i].strip()
            result.append(lines[i])  # Add the line with original indentation
            
            if current_line == 'end;':
                break
                
            i += 1
        
        return '\n'.join(result), (i - start_idx + 1)

    def _process_function(self, function_block):
        """
        Process a function block into prototype and definition.
        Returns (prototype, definition)
        """
        lines = function_block.split('\n')
        
        # Extract function details from the first line
        first_line = lines[0].strip()
        match = re.match(r'fnctn\s+(\w+)\s+(\w+)\s*\((.*?)\)\s*\{?', first_line)
        if not match:
            return None, None
            
        return_type, func_name, params = match.groups()
        
        # Process return type
        c_return_type = self.type_mapping.get(return_type, return_type)
        
        # Process parameters
        c_params = self._process_parameters(params)
        
        # Create prototype
        prototype = f"{c_return_type} {func_name}({c_params});"
        
        # Create definition start
        definition = f"{c_return_type} {func_name}({c_params}) {{"
        
        # Process function body (skip first and last lines)
        for i in range(1, len(lines) - 1):
            line = lines[i].strip()
            if not line or line == '{' or line == '}':  # Skip empty lines and lone braces
                continue
                
            processed_line = self._process_line(line)
            if processed_line:
                definition += f"\n    {processed_line}"
        
        # Close function definition
        definition += "\n}"
        
        return prototype, definition

    def _process_parameters(self, params):
        """Process function parameters"""
        if not params.strip():
            return ""
            
        param_list = []
        
        # Split parameters by commas
        for param in params.split(','):
            param = param.strip()
            if not param:
                continue
                
            # Split parameter into type and name
            parts = param.split()
            if len(parts) != 2:
                # If cannot parse, keep as is
                param_list.append(param)
                continue
                
            param_type, param_name = parts
            
            # Convert parameter type if needed
            if param_type in self.type_mapping:
                c_type = self.type_mapping[param_type]
                param_list.append(f"{c_type} {param_name}")
            else:
                param_list.append(param)
        
        return ", ".join(param_list)

    def _process_struct(self, struct_block):
        """Process a struct block into C struct definition"""
        lines = struct_block.split('\n')
        
        # Extract struct name from the first line
        first_line = lines[0].strip()
        match = re.match(r'strct\s+(\w+)\s*\{?', first_line)
        if not match:
            return None
            
        struct_name = match.group(1)
        
        # Create struct definition
        definition = f"typedef struct {struct_name} {{"
        
        # Process struct members (skip first and last lines)
        for i in range(1, len(lines) - 1):
            line = lines[i].strip()
            if not line or line == '{' or line == '}':  # Skip empty lines and lone braces
                continue
                
            # Process member declarations
            if any(line.startswith(t + " ") for t in self.type_mapping):
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    member_type = parts[0]
                    member_rest = parts[1]
                    
                    # Convert member type
                    if member_type in self.type_mapping:
                        c_type = self.type_mapping[member_type]
                        definition += f"\n    {c_type} {member_rest}"
                    else:
                        definition += f"\n    {line}"
            else:
                definition += f"\n    {line}"
        
        # Close the struct definition
        definition += f"\n}} {struct_name};"
        
        return definition

    def _process_main(self, main_block):
        """Process the main function block"""
        lines = main_block.split('\n')
        
        # Create main function definition
        definition = "int main(int argc, char *argv[]) {"
        
        # Process main function body (skip first and last lines)
        for i in range(1, len(lines) - 1):
            line = lines[i].strip()
            
            # Skip empty lines, lone braces, and end statement
            if not line or line == '{' or line == '}' or line == 'end;':
                continue
            
            processed_line = self._process_line(line)
            if processed_line:
                definition += f"\n    {processed_line}"
        
        # Add return statement and close the function
        definition += "\n    return 0;\n}"
        
        return definition

    def _process_line(self, line):
        """Process a single line of code"""
        if not line:
            return ""
            
        # Skip lines that are just braces
        if line in ['{', '}']:
            return line
            
        # Handle variable declarations
        if any(line.startswith(t + " ") for t in self.type_mapping):
            return self._process_declaration(line)
            
        # Handle print statements
        if line.startswith('prnt('):
            return self._process_print(line)
            
        # Handle input statements
        if '=' in line and 'npt(' in line:
            return self._process_input(line)
            
        # Handle return statements
        if line.startswith('rtrn '):
            return self._process_return(line)
            
        # Handle struct instantiation
        if line.startswith('dfstrct '):
            return self._process_dfstrct(line)
            
        # Handle end statement
        if line == 'end;':
            return "return 0;"
            
        # Handle other statements
        return self._process_other_statement(line)

    def _process_declaration(self, line):
        """Process a variable declaration"""
        # Remove trailing semicolon first for processing
        semicolon = ";" if line.endswith(';') else ""
        if semicolon:
            line = line[:-1]
        
        # Extract type and declaration part
        parts = line.split(' ', 1)
        if len(parts) < 2:
            return line + semicolon
            
        conso_type = parts[0]
        declaration = parts[1]
        
        # Convert type if needed
        if conso_type in self.type_mapping:
            c_type = self.type_mapping[conso_type]
            
            # Handle comma-separated declarations
            decls = [d.strip() for d in declaration.split(',')]
            processed_decls = []
            
            for decl in decls:
                # Check if it's an array declaration
                if '[' in decl and ']' in decl:
                    # Handle array initialization
                    if '=' in decl:
                        var_name, init_part = decl.split('=', 1)
                        var_name = var_name.strip()
                        init_part = init_part.strip()
                        processed_decls.append(f"{c_type} {var_name} = {init_part}")
                    else:
                        processed_decls.append(f"{c_type} {decl} = {{0}}")
                else:
                    # Handle regular variables
                    if '=' in decl:
                        var_name, init_part = decl.split('=', 1)
                        var_name = var_name.strip()
                        init_part = init_part.strip()
                        
                        # Handle string literals
                        if conso_type == "strng" and not (init_part.startswith('"') and init_part.endswith('"')):
                            if init_part not in ["0", "NULL"]:  # Don't add quotes to null values
                                init_part = f'"{init_part}"'
                        
                        # Handle character literals
                        if conso_type == "chr" and not (init_part.startswith("'") and init_part.endswith("'")):
                            if len(init_part) == 1:  # Only for single characters
                                init_part = f"'{init_part}'"
                        
                        # Handle boolean literals
                        if conso_type == "bln":
                            init_part = self._replace_bool_literals(init_part)
                        
                        processed_decls.append(f"{c_type} {var_name} = {init_part}")
                    else:
                        # Add default initialization
                        processed_decls.append(f"{c_type} {decl} = {self.default_values[conso_type]}")
            
            # Join declarations with semicolons
            if len(processed_decls) > 1:
                # Multiple declarations get their own lines
                return "; ".join(processed_decls) + semicolon
            else:
                # Single declaration
                return processed_decls[0] + semicolon
        
        return line + semicolon

    def _process_print(self, line):
        """Process a print statement"""
        # Remove trailing semicolon if present
        semicolon = ";" if line.endswith(';') else ""
        if semicolon:
            line = line[:-1]
        
        # Skip if it doesn't look like a print statement
        if not line.startswith('prnt('):
            return line + semicolon
            
        # Remove prnt( and trailing )
        content = line[5:-1]
        
        # If empty, return newline print
        if not content:
            return 'printf("\\n"); fflush(stdout);'
            
        # Split by commas, respecting quotes and parentheses
        args = self._split_args(content)
        
        # Process each argument
        format_parts = []
        c_args = []
        
        for arg in args:
            arg = arg.strip()
            
            # String literal - use as format string
            if arg.startswith('"') and arg.endswith('"'):
                format_parts.append("%s")
                c_args.append(arg)
            
            # Boolean literals
            elif arg == "tr":
                format_parts.append("%d")
                c_args.append("1")
            elif arg == "fls":
                format_parts.append("%d")
                c_args.append("0")
            
            # Number or expression (default to %d)
            else:
                # Try to guess the type
                if any(c in arg for c in ['.', 'dbl', 'float']):
                    format_parts.append("%.2f")
                elif any(c in arg for c in ['chr', "'"]):
                    format_parts.append("%c")
                else:
                    format_parts.append("%d")
                
                # Process any boolean literals in expressions
                arg = self._replace_bool_literals(arg)
                c_args.append(arg)
        
        # Build the printf statement
        if format_parts:
            format_str = " ".join(format_parts) + "\\n"
            return f'printf("{format_str}", {", ".join(c_args)}); fflush(stdout);'
        else:
            return 'printf("\\n"); fflush(stdout);'

    def _process_input(self, line):
        """Process an input statement"""
        # Remove trailing semicolon if present
        semicolon = ";" if line.endswith(';') else ""
        if semicolon:
            line = line[:-1]
            
        # Format: var = npt("prompt");
        if '=' not in line or 'npt(' not in line:
            return line + semicolon
            
        # Split into variable and input part
        var_name, input_part = line.split('=', 1)
        var_name = var_name.strip()
        input_part = input_part.strip()
        
        # Extract prompt from npt(...)
        if input_part.startswith('npt(') and input_part.endswith(')'):
            prompt = input_part[4:-1]
            return f"{var_name} = conso_input({prompt});"
        
        return line + semicolon

    def _process_return(self, line):
        """Process a return statement"""
        # Remove trailing semicolon if present
        semicolon = ";" if line.endswith(';') else ""
        if semicolon:
            line = line[:-1]
        
        if not line.startswith('rtrn '):
            return line + semicolon
            
        # Extract the return value
        return_value = line[5:].strip()
        
        # Replace boolean literals
        return_value = self._replace_bool_literals(return_value)
        
        return f"return {return_value};"

    def _process_dfstrct(self, line):
        """Process a struct instantiation"""
        # Remove trailing semicolon if present
        semicolon = ";" if line.endswith(';') else ""
        if semicolon:
            line = line[:-1]
        
        if not line.startswith('dfstrct '):
            return line + semicolon
            
        # Remove dfstrct keyword
        rest = line[8:].strip()
            
        # Split into struct type and variable list
        parts = rest.split(' ', 1)
        if len(parts) != 2:
            return line + semicolon
            
        struct_type, var_list = parts
        
        return f"{struct_type} {var_list};"

    def _process_other_statement(self, line):
        """Process other types of statements"""
        # Remove trailing semicolon if present
        semicolon = ";" if line.endswith(';') else ""
        if semicolon:
            line = line[:-1]
        
        # Replace boolean literals
        line = self._replace_bool_literals(line)
        
        # Replace Conso keywords with C equivalents
        for conso_key, c_key in self.keyword_mapping.items():
            if conso_key + " " in line or conso_key + "(" in line:
                line = line.replace(conso_key + " ", c_key + " ")
                line = line.replace(conso_key + "(", c_key + "(")
        
        # Add trailing semicolon if needed
        if not (line.endswith('{') or line.endswith('}')):
            return line + ";"
        else:
            return line

    def _split_args(self, content):
        """Split comma-separated arguments, respecting quotes and parentheses"""
        args = []
        current_arg = ""
        in_quotes = False
        paren_level = 0
        bracket_level = 0
        
        for char in content:
            if char == '"':
                in_quotes = not in_quotes
                current_arg += char
            elif char == '(' and not in_quotes:
                paren_level += 1
                current_arg += char
            elif char == ')' and not in_quotes:
                paren_level -= 1
                current_arg += char
            elif char == '[' and not in_quotes:
                bracket_level += 1
                current_arg += char
            elif char == ']' and not in_quotes:
                bracket_level -= 1
                current_arg += char
            elif char == ',' and not in_quotes and paren_level == 0 and bracket_level == 0:
                args.append(current_arg)
                current_arg = ""
            else:
                current_arg += char
                
        if current_arg:
            args.append(current_arg)
            
        return args

    def _replace_bool_literals(self, text):
        """Replace boolean literals in text"""
        for conso_bool, c_bool in self.bool_mapping.items():
            # Use word boundaries to avoid partial matches
            text = re.sub(r'\b' + conso_bool + r'\b', c_bool, text)
        return text

    def _generate_headers(self):
        """Generate standard C headers"""
        return (
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n"
            "#include <string.h>\n"
            "\n"
        )

    def _generate_helper_functions(self):
        """Generate helper functions for Conso-specific operations"""
        return """// Helper function for string input
char* conso_input(const char* prompt) {
    printf("%s", prompt);
    char* buffer = malloc(1024);
    if (buffer == NULL) {
        fprintf(stderr, "Memory allocation failed\\n");
        exit(1);
    }
    fgets(buffer, 1024, stdin);
    // Remove newline character if present
    size_t len = strlen(buffer);
    if (len > 0 && buffer[len-1] == '\\n') {
        buffer[len-1] = '\\0';
    }
    return buffer;
}

// Helper function for string concatenation
char* conso_concat(const char* str1, const char* str2) {
    if (str1 == NULL) str1 = "";
    if (str2 == NULL) str2 = "";
    size_t len1 = strlen(str1);
    size_t len2 = strlen(str2);
    char* result = malloc(len1 + len2 + 1);
    if (result == NULL) {
        fprintf(stderr, "Memory allocation failed\\n");
        exit(1);
    }
    strcpy(result, str1);
    strcat(result, str2);
    return result;
}

"""

class TranspilerError(Exception):
    """Exception for transpiler errors"""
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self):
        if self.line is not None and self.column is not None:
            return f"Transpiler Error at line {self.line}, column {self.column}: {self.message}"
        return f"Transpiler Error: {self.message}"

def transpile(conso_code):
    """
    Transpile Conso code to C code.
    
    Args:
        conso_code (str): Conso code to transpile
        
    Returns:
        str: Transpiled C code
    """
    transpiler = ConsoTranspiler()
    return transpiler.transpile(conso_code)

def transpile_from_tokens(token_list, symbol_table=None):
    """
    Transpile Conso code to C code using a token stream.
    Args:
        token_list (list): List of Token objects or (type, value, line, column) tuples.
        symbol_table (SymbolTable): The symbol table from semantic analysis.
    Returns:
        str: Transpiled C code
    """
    # Convert token list to a string representation of the code
    conso_code = _tokens_to_code(token_list)
    
    # Use the regular transpiler on the reconstructed code
    return transpile(conso_code)

def _tokens_to_code(token_list):
    """
    Convert a list of tokens back to code text.
    This is a simple implementation - you may need to adjust it based on your token format.
    """
    code_lines = []
    current_line = ""
    
    for token in token_list:
        # Extract token type and value based on token format
        if hasattr(token, 'type') and hasattr(token, 'value'):
            token_type = token.type
            token_value = token.value
        elif isinstance(token, tuple):
            if len(token) >= 2:
                token_type = token[0]
                token_value = token[1]
            else:
                continue  # Skip invalid tokens
        else:
            continue  # Skip unknown token formats
        
        # Skip EOF token
        if token_type == "EOF":
            continue
        
        # Handle different token types
        if token_type in ["id", "ntlit", "dbllit", "strnglit", "chrlit", "blnlit"]:
            current_line += str(token_value) + " "
        elif token_type in ["+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">="]:
            current_line += token_type + " "
        elif token_type == ";":
            current_line += ";"
            code_lines.append(current_line)
            current_line = ""
        elif token_type == "{":
            current_line += " {"
            code_lines.append(current_line)
            current_line = ""
        elif token_type == "}":
            code_lines.append("}")
            current_line = ""
        elif token_type in ["fnctn", "mn", "nt", "dbl", "strng", "bln", "chr", "vd"]:
            current_line += token_type + " "
        elif token_type == "end":
            current_line += "end;"
            code_lines.append(current_line)
            current_line = ""
        else:
            # Default: just add the token value
            current_line += str(token_value) + " "
            # Add any remaining line
    if current_line.strip():
        code_lines.append(current_line)
    
    # Join all lines
    return "\n".join(code_lines)

if __name__ == "__main__":
    # Example code - comprehensive test case
    test_code = """
    strct myStruct {                                                           
         nt age; 
         dbl grade;    
         bln flag; 
         chr letter;        
         strng name;       
    };   
       
    fnctn vd Test(){
         nt sum;
         sum = 3;         
    }     
                 
    mn(){       
         dfstrct myStruct s1; 
         nt num, num2 = 3;
         dbl frac; 
         dbl frac2 = 5.28;
         bln flag = tr, flag2 = fls;   
         chr letter = 'c';  
         strng name = "John";                
         prnt("Hi", name, 1+1);        
         end;       
    }
    """
    
    # Transpile and print the result
    c_code = transpile(test_code)
    print(c_code)