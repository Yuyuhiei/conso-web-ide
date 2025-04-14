"""
Conso to C Transpiler
This module converts Conso code to C code, assuming the input has already passed
lexical, syntax and semantic analysis.
"""
import sys
import re

class ConsoTranspiler:
    def __init__(self):
        # Mapping of Conso types to C types
        self.type_mapping = {
            "nt": "int",
            "dbl": "double",
            "strng": "char*",
            "bln": "int",  # boolean values in C are integers
            "chr": "char",
            "vd": "void"
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
            "dbl": "0.00",
            "strng": "\"\"",
            "bln": "0",  # false
            "chr": "'/'"
        }


    def transpile(self, conso_code):
        """
        Transpile Conso code to C code.
        Assumes the input code has already passed lexical, syntax, and semantic validation.
        """
        # Add standard headers
        c_code = self._generate_headers()
        
        # Add helper functions
        c_code += self._generate_helper_functions()
        
        # Process each line and convert to C
        processed_lines = []
        in_function = False
        indent_level = 0
        
        lines = conso_code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Handle main function
            if line.lstrip().startswith('mn('):
                in_function = True
                processed_line = "int main(int argc, char *argv[]) {"
                indent_level = 1

            # Handle end statement (return from main)
            elif line.lstrip().startswith('end;'):
                processed_line = self._indent(indent_level) + "return 0;"
                indent_level = 0
                in_function = False

            # Handle variable declarations
            elif any(line.lstrip().startswith(t + " ") for t in self.type_mapping):
                processed_line = self._process_declaration(line)

            # Handle print statements
            elif line.lstrip().startswith('prnt('):
                processed_line = self._process_print(line)

            # Handle input statements
            elif line.lstrip().startswith('npt(') or 'npt(' in line:
                processed_line = self._process_input(line)

            # Handle if statements
            elif line.lstrip().startswith('f ('):
                processed_line = self._process_if_statement(line)
                indent_level += 1

            # Handle else if statements
            elif line.lstrip().startswith('lsf ('):
                indent_level -= 1  # Reduce indent for else if
                processed_line = self._process_else_if_statement(line)
                indent_level += 1  # Increase indent after else if

            # Handle else statements
            elif line.lstrip().startswith('ls {'):
                indent_level -= 1  # Reduce indent for else
                processed_line = self._indent(indent_level) + "else {"
                indent_level += 1  # Increase indent after else

            # Handle while loops
            elif line.lstrip().startswith('whl ('):
                processed_line = self._process_while_loop(line)
                indent_level += 1

            # Handle for loops
            elif line.lstrip().startswith('fr ('):
                processed_line = self._process_for_loop(line)
                indent_level += 1

            # Handle do-while loops
            elif line.lstrip().startswith('d {'):
                processed_line = self._indent(indent_level) + "do {"
                indent_level += 1

            # Handle the "while" part of do-while
            elif line.lstrip().startswith('whl (') and i > 0 and lines[i-1].strip() == '}':
                # This is part of a do-while loop
                indent_level -= 1  # Reduce indent for the while condition
                processed_line = self._process_do_while_condition(line)

            # Handle switch statements
            elif line.lstrip().startswith('swtch ('):
                processed_line = self._process_switch(line)
                indent_level += 1

            # Handle case statements
            elif line.lstrip().startswith('cs '):
                processed_line = self._process_case(line)

            # Handle default case
            elif line.lstrip().startswith('dflt:'):
                processed_line = self._indent(indent_level) + "default:"

            # Handle functions
            elif line.lstrip().startswith('fnctn '):
                processed_line = self._process_function(line)
                in_function = True
                indent_level = 1

            # Handle return statements
            elif line.lstrip().startswith('rtrn '):
                processed_line = self._process_return(line)

            # Handle struct declarations
            elif line.lstrip().startswith('strct '):
                processed_line, struct_lines = self._process_struct(lines, i)
                i += struct_lines  # Skip the processed struct lines

            # Handle closing braces - decrease indent level
            elif line.strip() == '}':
                indent_level -= 1
                processed_line = self._indent(indent_level) + "}"
                if indent_level == 0:
                    in_function = False

            # Handle other statements (assignments, expressions, etc.)
            else:
                processed_line = self._process_other_statement(line)

            # Debug: print the original and processed line
            print(f"Transpiler: original='{line}' processed='{processed_line}'")

            # Add proper indentation to the processed line
            if processed_line and not processed_line.startswith(' ') and not processed_line.startswith('\t'):
                processed_line = self._indent(indent_level) + processed_line

            # Add the processed line to our result
            if processed_line:
                processed_lines.append(processed_line)

            i += 1
        
        # Join all processed lines and return the C code
        c_code += '\n'.join(processed_lines)
        
        return c_code

    def _indent(self, level):
        """Helper function to add proper indentation"""
        return "    " * level

    def _generate_headers(self):
        """Generate the necessary C headers"""
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

    def _process_declaration(self, line):
        """
        Process a variable declaration statement.
        Supports multiple inline declarations for nt, dbl, chr, strng, bln.
        Maps tr/fls to 1/0 for bln.
        Provides default initialization for variables without explicit values.
        """
        parts = line.split(' ', 1)
        if len(parts) < 2:
            return line  # Not enough parts, return unchanged

        conso_type = parts[0]
        rest = parts[1].rstrip(';')  # Remove trailing semicolon for processing

        if conso_type in self.type_mapping:
            c_type = self.type_mapping[conso_type]
            # Split by commas for multiple declarations
            decls = [d.strip() for d in rest.split(',')]
            
            # For string and char types, we need to declare each variable separately
            if conso_type == "strng":
                separate_declarations = []
                for decl in decls:
                    if '=' in decl:
                        var, val = [x.strip() for x in decl.split('=', 1)]
                        # Handle string literals
                        if not (val.startswith('"') and val.endswith('"')):
                            if not val.startswith('"'):
                                val = f'"{val}'
                            if not val.endswith('"'):
                                val = f'{val}"'
                        separate_declarations.append(f"{c_type} {var} = {val};")
                    else:
                        # Add default initialization for strings
                        separate_declarations.append(f"{c_type} {decl} = {self.default_values[conso_type]};")
                
                return "\n".join(separate_declarations)
            
            # Process all other types with normal comma-separated declarations
            processed_decls = []
            for decl in decls:
                if '=' in decl:
                    var, val = [x.strip() for x in decl.split('=', 1)]
                    
                    # Handle char literals
                    if conso_type == "chr" and not (val.startswith("'") and val.endswith("'")):
                        if not val.startswith("'"):
                            val = f"'{val}"
                        if not val.endswith("'"):
                            val = f"{val}'"
                    
                    # For bln, map tr/fls to 1/0 using regex for whole word replacement
                    elif conso_type == "bln":
                        val = re.sub(r'\btr\b', self.bool_mapping['tr'], val)
                        val = re.sub(r'\bfls\b', self.bool_mapping['fls'], val)
                    
                    processed_decls.append(f"{var} = {val}")
                else:
                    # Add default initialization
                    processed_decls.append(f"{decl} = {self.default_values[conso_type]}")
            
            return f"{c_type} {', '.join(processed_decls)};"
        
        return line  # Type not found, return unchanged

    def _process_print(self, line):
        """Process a print statement with a more robust approach"""
        # Remove trailing semicolon if present for parsing
        if line.endswith(';'):
            line = line[:-1]
        # Extract the content inside the parentheses
        content = line[line.find('(')+1:line.rfind(')')].strip()

        # If empty print statement
        if not content:
            return 'printf("\\n"); fflush(stdout);'

        # Split the arguments by commas, handling string literals with commas
        args = []
        current_arg = ""
        in_string = False
        in_char = False
        
        for char in content:
            if char == '"' and not in_char:
                in_string = not in_string
                current_arg += char
            elif char == "'" and not in_string:
                in_char = not in_char
                current_arg += char
            elif char == ',' and not in_string and not in_char:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        
        if current_arg:
            args.append(current_arg.strip())

        # Process each argument
        format_parts = []
        c_args = []
        
        for arg in args:
            # String literal
            if arg.startswith('"') and arg.endswith('"'):
                format_parts.append("%s")
                c_args.append(arg)
            # Char literal
            elif arg.startswith("'") and arg.endswith("'"):
                format_parts.append("%c")
                c_args.append(arg)
            # Boolean literals
            elif arg == "tr":
                format_parts.append("%d")
                c_args.append("1")
            elif arg == "fls":
                format_parts.append("%d")
                c_args.append("0")
            # Variable or expression - assume int by default
            else:
                # Check if it might be a variable name only (simple heuristic)
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', arg):
                    # Simple variable name, we could check if it's in a symbol table
                    format_parts.append("%s")  # Default to string
                else:
                    # Expression, default to %d (int)
                    format_parts.append("%d")
                c_args.append(arg)

        # Build the printf statement
        if format_parts:
            format_str = " ".join(format_parts) + "\\n"
            return f'printf("{format_str}", {", ".join(c_args)}); fflush(stdout);'
        else:
            return 'printf("\\n"); fflush(stdout);'

    def _process_input(self, line):
        """Process an input statement"""
        # Handle input statements
        if line.startswith('npt('):
            # Standalone input function call: npt("Enter value: ");
            content = line[line.find('(')+1:line.rfind(')')]
            return f"conso_input({content});"
        elif '=' in line and 'npt(' in line:
            # Assignment with input: var = npt("Enter value: ");
            var_name, input_call = line.split('=', 1)
            var_name = var_name.strip()
            input_call = input_call.strip()
            if input_call.startswith('npt('):
                content = input_call[input_call.find('(')+1:input_call.rfind(')')]
                return f"{var_name} = conso_input({content});"
        
        return line  # Not recognized, return unchanged

    def _process_if_statement(self, line):
        """Process an if statement"""
        # "f (condition) {" -> "if (condition) {"
        if line.startswith('f ('):
            condition = line[line.find('(')+1:line.rfind(')')]
            # Convert boolean literals in the condition
            condition = re.sub(r'\btr\b', '1', condition)
            condition = re.sub(r'\bfls\b', '0', condition)
            return f"if ({condition}) {{"
        return line

    def _process_else_if_statement(self, line):
        """Process an else-if statement"""
        # "lsf (condition) {" -> "else if (condition) {"
        if line.startswith('lsf ('):
            condition = line[line.find('(')+1:line.rfind(')')]
            # Convert boolean literals in the condition
            condition = re.sub(r'\btr\b', '1', condition)
            condition = re.sub(r'\bfls\b', '0', condition)
            return f"else if ({condition}) {{"
        return line

    def _process_while_loop(self, line):
        """Process a while loop"""
        # "whl (condition) {" -> "while (condition) {"
        if line.startswith('whl ('):
            condition = line[line.find('(')+1:line.rfind(')')]
            # Convert boolean literals in the condition
            condition = re.sub(r'\btr\b', '1', condition)
            condition = re.sub(r'\bfls\b', '0', condition)
            return f"while ({condition}) {{"
        return line

    def _process_for_loop(self, line):
        """Process a for loop"""
        # "fr (init; condition; update) {" -> "for (init; condition; update) {"
        if line.startswith('fr ('):
            content = line[line.find('(')+1:line.rfind(')')]
            # Convert boolean literals in the condition part
            parts = content.split(';')
            if len(parts) == 3:
                # Convert boolean literals in the condition (middle part)
                parts[1] = re.sub(r'\btr\b', '1', parts[1])
                parts[1] = re.sub(r'\bfls\b', '0', parts[1])
                content = ';'.join(parts)
            return f"for ({content}) {{"
        return line

    def _process_do_while_condition(self, line):
        """Process the condition part of a do-while loop"""
        # "whl (condition);" -> "} while (condition);"
        if line.startswith('whl ('):
            condition = line[line.find('(')+1:line.rfind(')')]
            # Convert boolean literals in the condition
            condition = re.sub(r'\btr\b', '1', condition)
            condition = re.sub(r'\bfls\b', '0', condition)
            if line.endswith(';'):
                return f"}} while ({condition});"
            else:
                return f"}} while ({condition})"
        return line

    def _process_switch(self, line):
        """Process a switch statement"""
        # "swtch (expression) {" -> "switch (expression) {"
        if line.startswith('swtch ('):
            expression = line[line.find('(')+1:line.rfind(')')]
            return f"switch ({expression}) {{"
        return line

    def _process_case(self, line):
        """Process a case statement in a switch"""
        # "cs value:" -> "case value:"
        if line.startswith('cs '):
            value = line[3:].strip()
            if value.endswith(':'):
                value = value[:-1].strip()
            return f"case {value}:"
        return line

    def _process_function(self, line):
        """Process a function declaration"""
        # "fnctn vd myFunc()" -> "void myFunc()"
        if line.startswith('fnctn '):
            parts = line[6:].strip().split(' ', 1)
            if len(parts) == 2:
                return_type = parts[0]
                func_sig = parts[1]
                
                if return_type in self.type_mapping:
                    c_type = self.type_mapping[return_type]
                    if func_sig.endswith('{'):
                        func_sig = func_sig[:-1].strip() + " {"
                    return f"{c_type} {func_sig}"
            
            # Fall back - just remove "fnctn "
            return line[6:]
        return line

    def _process_return(self, line):
        """Process a return statement"""
        # "rtrn value;" -> "return value;"
        if line.startswith('rtrn '):
            value = line[5:].strip()
            # Handle boolean literals in return values
            value = re.sub(r'\btr\b', '1', value)
            value = re.sub(r'\bfls\b', '0', value)
            return f"return {value}"
        elif line == 'rtrn;':
            return "return;"
        return line

    def _process_struct(self, lines, start_index):
        """Process a struct declaration"""
        # "strct MyStruct {" -> "typedef struct MyStruct {"
        line = lines[start_index].strip()
        processed_line = ""
        struct_lines = 0
        
        if line.startswith('strct '):
            struct_name = line[6:line.find('{')].strip()
            processed_line = f"typedef struct {struct_name} {{"
            
            # Count the lines in the struct body
            bracket_count = 1
            for i in range(start_index + 1, len(lines)):
                struct_lines += 1
                curr_line = lines[i].strip()
                
                if '{' in curr_line:
                    bracket_count += curr_line.count('{')
                if '}' in curr_line:
                    bracket_count -= curr_line.count('}')
                
                if bracket_count == 0:
                    # Found the end of the struct
                    if curr_line == '};':
                        # Replace the closing bracket with the typedef ending
                        lines[i] = f"}} {struct_name};"
                    break
        
        return processed_line, struct_lines

    def _process_other_statement(self, line):
        """Process other statements (assignments, expressions, etc.)"""
        # Process boolean literals
        for key, value in self.bool_mapping.items():
            # Match whole words only to avoid replacing substrings
            line = re.sub(r'\b' + key + r'\b', value, line)
        
        # Replace remaining Conso keywords with C equivalents
        for key, value in self.keyword_mapping.items():
            if key + " " in line or key + "(" in line:
                line = line.replace(key + " ", value + " ")
                line = line.replace(key + "(", value + "(")
        
        return line

# Create a TranspilerError class for error handling
class TranspilerError(Exception):
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self):
        if self.line is not None and self.column is not None:
            return f"Transpiler Error at line {self.line}, column {self.column}: {self.message}"
        return f"Transpiler Error: {self.message}"

# Function to transpile Conso code to C
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
    transpiler = ConsoTranspiler()
    c_code = transpiler._generate_headers()
    c_code += transpiler._generate_helper_functions()

    # State
    output_lines = []
    indent_level = 0
    i = 0
    n = len(token_list)
    def get_token_type_value(tok):
        if hasattr(tok, 'type') and hasattr(tok, 'value'):
            return tok.type, tok.value
        elif isinstance(tok, tuple):
            if len(tok) == 4:
                return tok[0], tok[1]
            elif len(tok) == 3:
                return tok[0], tok[0]
        return None, None

    # Use the provided symbol_table from semantic analysis

    while i < n:
        token = token_list[i]
        ttype, tvalue = get_token_type_value(token)

        # Skip EOF
        if ttype == "EOF":
            i += 1
            continue

        # Main function
        if ttype == "mn":
            output_lines.append("int main(int argc, char *argv[]) {")
            indent_level = 1
            # Skip possible '(' ... ')' and '{'
            while i+1 < n:
                next_type, _ = get_token_type_value(token_list[i+1])
                if next_type in ["(", ")", "{"]:
                    i += 1
                else:
                    break
            i += 1
            continue

        # End statement
        if ttype == "end":
            output_lines.append(transpiler._indent(indent_level) + "return 0;")
            i += 1
            continue

        # Variable declarations (nt, dbl, bln, chr, strng)
        if ttype in transpiler.type_mapping:
            var_type = transpiler.type_mapping[ttype]
            j = i + 1
            
            # For collecting multiple declarations of the same type
            variables = []
            
            # Process all variables of this type until semicolon
            while j < n:
                # Skip to identifier
                if get_token_type_value(token_list[j])[0] == "id":
                    var_name = get_token_type_value(token_list[j])[1]
                    j += 1
                    
                    # Check for assignment
                    if j < n and get_token_type_value(token_list[j])[0] == "=":
                        j += 1
                        
                        # Get the value
                        value_tokens = []
                        while j < n:
                            next_token_type, next_token_value = get_token_type_value(token_list[j])
                            
                            # End of this declaration
                            if next_token_type in [";", ","]:
                                break
                                
                            # Add token to value
                            value_tokens.append((next_token_type, next_token_value))
                            j += 1
                        
                        # Process the value based on type
                        processed_value = ""
                        for val_type, val in value_tokens:
                            if ttype == "bln" and val_type == "blnlit":
                                if val == "tr":
                                    processed_value += "1"
                                elif val == "fls":
                                    processed_value += "0"
                            elif ttype == "strng" and val_type == "strnglit":
                                processed_value += f'"{val}"'
                            elif ttype == "chr" and val_type == "chrlit":
                                processed_value += f"'{val}'"
                            else:
                                processed_value += str(val)
                        
                        variables.append((var_name, processed_value))
                    else:
                        # Just a variable declaration without assignment - add default initialization
                        if ttype in transpiler.default_values:
                            default_value = transpiler.default_values[ttype]
                            variables.append((var_name, default_value))
                        else:
                            variables.append((var_name, None))

                    
                    # Check if there's another declaration (comma)
                    if j < n and get_token_type_value(token_list[j])[0] == ",":
                        j += 1
                        continue
                
                # End of declarations for this type
                if j < n and get_token_type_value(token_list[j])[0] == ";":
                    j += 1
                    break
                
                j += 1
            
            # Add the declaration line(s)
            if variables:
                # For string type, we need to declare each variable separately
                if ttype == "strng":
                    for var_name, value in variables:
                        if value is not None:
                            output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_name} = {value};")
                        else:
                            output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_name};")
                else:
                    # For other types (nt, dbl, bln, chr), we can use comma-separated declarations
                    formatted_vars = []
                    for var_name, value in variables:
                        if value is not None:
                            formatted_vars.append(f"{var_name} = {value}")
                        else:
                            formatted_vars.append(var_name)
                    
                    output_lines.append(transpiler._indent(indent_level) + f"{var_type} {', '.join(formatted_vars)};")
            
            i = j
            continue

        # Print statement
        if ttype == "prnt":
            # Parse prnt ( ... );
            # Find the opening '('
            j = i + 1
            while j < n:
                next_type, _ = get_token_type_value(token_list[j])
                if next_type == "(":
                    break
                j += 1
            # Find the closing ')'
            k = j + 1
            paren_count = 1
            args_tokens = []
            while k < n and paren_count > 0:
                curr_type, curr_value = get_token_type_value(token_list[k])
                if curr_type == "(":
                    paren_count += 1
                elif curr_type == ")":
                    paren_count -= 1
                    if paren_count == 0:
                        break
                if paren_count > 0:
                    args_tokens.append((curr_type, curr_value))
                k += 1

            # Split arguments by commas
            arg_groups = []
            curr_arg = []
            for t_type, t_value in args_tokens:
                if t_type == ",":
                    if curr_arg:
                        arg_groups.append(curr_arg)
                        curr_arg = []
                else:
                    curr_arg.append((t_type, t_value))
            if curr_arg:
                arg_groups.append(curr_arg)

            # Build format string and argument list
            format_parts = []
            arg_exprs = []
            for arg in arg_groups:
                # Single token: variable or literal
                if len(arg) == 1:
                    atype, avalue = arg[0]
                    # Variable: look up type
                    if atype == "id" and symbol_table and symbol_table.lookup(avalue):
                        vtype = symbol_table.lookup(avalue).data_type
                        if vtype == "strng":
                            format_parts.append("%s")
                        elif vtype == "dbl":
                            format_parts.append("%.2f")
                        elif vtype == "nt":
                            format_parts.append("%d")
                        elif vtype == "chr":
                            format_parts.append("%c")
                        elif vtype == "bln":
                            format_parts.append("%d")
                        else:
                            format_parts.append("%s")
                        arg_exprs.append(avalue)
                    # String literal
                    elif atype == "strnglit":
                        format_parts.append("%s")
                        arg_exprs.append(f'"{avalue}"')
                    # Char literal
                    elif atype == "chrlit":
                        format_parts.append("%c")
                        arg_exprs.append(f"'{avalue}'")
                    # Number literal
                    elif atype in ["ntlit", "~ntlit"]:
                        format_parts.append("%d")
                        arg_exprs.append(avalue)
                    elif atype in ["dbllit", "~dbllit"]:
                        format_parts.append("%.2f")
                        arg_exprs.append(avalue)
                    # Boolean literal
                    elif atype == "blnlit":
                        format_parts.append("%d")
                        arg_exprs.append("1" if avalue == "tr" else "0")
                    else:
                        format_parts.append("%s")
                        arg_exprs.append(str(avalue))
                else:
                    # Expression: try to infer type (if any operand is dbl, treat as double)
                    expr_str = ' '.join(str(val) for _, val in arg)
                    expr_types = set()
                    for xtype, xvalue in arg:
                        print(f"DEBUG: token in expr: xtype={xtype}, xvalue={xvalue}")  # Debug
                        if xtype == "id":
                            dtype = None
                            if symbol_table and symbol_table.lookup(xvalue):
                                dtype = symbol_table.lookup(xvalue).data_type
                            else:
                                # Fallback: assume int for unknown ids (restores original behavior)
                                dtype = "nt"
                            expr_types.add(dtype)
                        elif xtype in ["dbllit", "~dbllit"]:
                            expr_types.add("dbl")
                        elif xtype in ["ntlit", "~ntlit"]:
                            expr_types.add("nt")
                        elif xtype == "strnglit":
                            expr_types.add("strng")
                        elif xtype == "chrlit":
                            expr_types.add("chr")
                        elif xtype == "blnlit":
                            expr_types.add("bln")
                    # Use original heuristic: string > double > int > char > bool
                    if "strng" in expr_types:
                        format_parts.append("%s")
                    elif "dbl" in expr_types:
                        format_parts.append("%.2f")
                    elif "nt" in expr_types:
                        format_parts.append("%d")
                    elif "chr" in expr_types:
                        format_parts.append("%c")
                    elif "bln" in expr_types:
                        format_parts.append("%d")
                    else:
                        format_parts.append("%s")
                    print(f"DEBUG: print expr '{expr_str}' inferred types {expr_types}")  # Debug
                    
                    # Convert boolean literals in expressions
                    for idx, (tok_type, tok_value) in enumerate(arg):
                        if tok_type == "blnlit":
                            if tok_value == "tr":
                                arg[idx] = (tok_type, "1")
                            elif tok_value == "fls":
                                arg[idx] = (tok_type, "0")
                    
                    # Rebuild expression with converted boolean literals
                    expr_str = ' '.join(str(val) for _, val in arg)
                    arg_exprs.append(expr_str)
            
            format_str = " ".join(format_parts) + "\\n"
            output_lines.append(transpiler._indent(indent_level) + f'printf("{format_str}", {", ".join(arg_exprs)}); fflush(stdout);')
            i = k + 1
            if i < n:
                next_type, _ = get_token_type_value(token_list[i])
                if next_type == ";":
                    i += 1
            continue

        # Opening brace
        if ttype == "{":
            indent_level += 1
            output_lines.append(transpiler._indent(indent_level - 1) + "{")
            i += 1
            continue

        # Closing brace
        if ttype == "}":
            indent_level -= 1
            output_lines.append(transpiler._indent(indent_level) + "}")
            i += 1
            continue

        # Other statements (assignments, expressions, etc.)
        if ttype in ["id", "=", "+", "-", "*", "/", "%", "++", "--", "+=", "-=", "*=", "/=", "%=", "==", "!=", "<", "<=", ">", ">=", "tr", "fls", "npt", "cntn", "rtrn"]:
            stmt_tokens = []
            j = i
            while j < n:
                curr_type, curr_value = get_token_type_value(token_list[j])
                if curr_type == ";":
                    j += 1
                    break
                    
                # Convert boolean literals
                if curr_type == "blnlit" or curr_value in ["tr", "fls"]:
                    if curr_value == "tr":
                        stmt_tokens.append("1")
                    elif curr_value == "fls":
                        stmt_tokens.append("0")
                else:
                    stmt_tokens.append(str(curr_value))
                j += 1
                
            output_lines.append(transpiler._indent(indent_level) + ' '.join(stmt_tokens) + ";")
            i = j
            continue

        if ttype == ";":
            i += 1
            continue

        if ttype == ",":
            i += 1
            continue

        i += 1

    c_code += '\n'.join(output_lines)
    return c_code

# Example usage if script is run directly
if __name__ == "__main__":
    # Example Conso code
    conso_code = """
    mn() {
        nt x = 5;
        prnt("Value of x is: %d", x);
        end;
    }
    """
    
    # Transpile to C
    c_code = transpile(conso_code)
    print(c_code)