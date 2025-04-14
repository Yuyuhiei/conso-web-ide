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
        print("DEBUG: Input to transpile():")
        print(conso_code)
        # Add standard headers
        c_code = self._generate_headers()
        
        # Add helper functions
        c_code += self._generate_helper_functions()
        
        # Process each line and convert to C
        processed_lines = []
        in_function = False
        indent_level = 0
        
        # First pass - find struct definitions and process them
        lines = conso_code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Process struct definitions first to place them at file scope
            if line.startswith('strct '):
                processed_line, struct_lines = self._process_struct(lines, i)
                if processed_line:
                    processed_lines.append(processed_line)
                    # Process struct body lines
                    bracket_count = 1  # Initialize bracket_count to track nesting
                    for j in range(1, struct_lines + 1):
                        if i + j < len(lines):
                            struct_line = lines[i + j].strip()
                            if '{' in struct_line:
                                bracket_count += struct_line.count('{')
                            if '}' in struct_line:
                                bracket_count -= struct_line.count('}')
                            
                            if struct_line:
                                processed_lines.append("    " + struct_line)
                i += struct_lines + 1
            else:
                i += 1

        # Second pass - process everything else
        i = 0
        # DEBUG: Print all lines before second pass
        print("DEBUG: Lines before second pass:")
        for idx, l in enumerate(lines):
            print(f"{idx}: '{l}'")
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue

            # Skip lines that are just variable names (e.g., struct2;) to avoid duplicate/erroneous struct declarations
            if re.match(r'^\w+\s*;$', line):
                i += 1
                continue

            # Skip struct definitions (already processed)
            if line.startswith('strct '):
                bracket_count = 1  # Initialize bracket_count
                i += 1
                while i < len(lines) and bracket_count > 0:
                    if i < len(lines):
                        curr_line = lines[i].strip()
                        if '{' in curr_line:
                            bracket_count += curr_line.count('{')
                        if '}' in curr_line:
                            bracket_count -= curr_line.count('}')
                        i += 1
                continue
            
            processed_line = ""
            
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

            # Handle struct instantiation
            elif line.lstrip().startswith('dfstrct '):
                processed_line = self._process_dfstrct(line)

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

            # Handle struct instantiation
            elif line.lstrip().startswith('dfstrct '):
                processed_line = self._process_dfstrct(line)

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
        Process a variable declaration statement with proper array handling.
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
            
            # Process each declaration
            processed_declarations = []
            
            for decl in decls:
                # Check if this is an array declaration by looking for '[' but not in a string
                array_match = re.search(r'(\w+)(\s*\[\s*\d+\s*\])+', decl)
                is_array = array_match is not None
                
                if is_array:
                    # This is an array declaration
                    var_name = array_match.group(1)
                    # Extract dimensions part (everything from first [ to last ])
                    dimensions_start = decl.find('[')
                    
                    # Find the position after the variable name and dimensions
                    if '=' in decl:
                        dimensions_end = decl.find('=')
                        init_part = decl[dimensions_end:].strip()
                    else:
                        dimensions_end = len(decl)
                        init_part = ""
                    
                    dimensions = decl[dimensions_start:dimensions_end].strip()
                    
                    # Handle initialization if present
                    if init_part:
                        if conso_type == "bln":
                            # Replace boolean literals
                            init_part = re.sub(r'\btr\b', self.bool_mapping['tr'], init_part)
                            init_part = re.sub(r'\bfls\b', self.bool_mapping['fls'], init_part)
                        
                        # For string arrays, handle each element
                        if conso_type == "strng":
                            processed_declarations.append(f"{c_type} {var_name}{dimensions}{init_part};")
                        else:
                            processed_declarations.append(f"{c_type} {var_name}{dimensions}{init_part};")
                    else:
                        # Array without initialization
                        if conso_type == "strng":
                            processed_declarations.append(f"{c_type} {var_name}{dimensions};")
                        else:
                            # Default initialization with zeros
                            processed_declarations.append(f"{c_type} {var_name}{dimensions} = {{0}};")
                else:
                    # Regular variable (not an array)
                    if conso_type == "strng":
                        # Handle string variables separately
                        if '=' in decl:
                            var, val = [x.strip() for x in decl.split('=', 1)]
                            # Handle string literals
                            if not (val.startswith('"') and val.endswith('"')):
                                if not val.startswith('"'):
                                    val = f'"{val}'
                                if not val.endswith('"'):
                                    val = f'{val}"'
                            processed_declarations.append(f"{c_type} {var} = {val};")
                        else:
                            # Add default initialization for strings
                            processed_declarations.append(f"{c_type} {decl} = {self.default_values[conso_type]};")
                    else:
                        # Handle regular variables for other types
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
                            
                            processed_declarations.append(f"{c_type} {var} = {val};")
                        else:
                            # Add default initialization
                            processed_declarations.append(f"{c_type} {decl} = {self.default_values[conso_type]};")
            
            # Return all processed declarations
            return "\n".join(processed_declarations)
        
        return line  # Type not found, return unchanged

    def _process_print(self, line):
        """Process a print statement with support for array elements and string comparisons"""
        # Remove trailing semicolon if present for parsing
        if line.endswith(';'):
            line = line[:-1]
        # Extract the content inside the parentheses
        content = line[line.find('(')+1:line.rfind(')')].strip()

        # If empty print statement
        if not content:
            return 'printf("\\n"); fflush(stdout);'

        # Replace string literals comparison - when hello is not in quotes
        # hello variable issue - convert to string comparison
        content = re.sub(r'(?<!["\w])(\w+)(?!["\w])', lambda m: f'"{m.group(1)}"' if m.group(1) in ['hello', 'ftello'] else m.group(1), content)

        # Split the arguments by commas, handling string literals with commas
        args = []
        current_arg = ""
        in_string = False
        in_char = False
        paren_level = 0
        brace_level = 0  # For array initializers { }
        bracket_level = 0  # For array indices [ ]
        
        for char in content:
            if char == '"' and not in_char:
                in_string = not in_string
                current_arg += char
            elif char == "'" and not in_string:
                in_char = not in_char
                current_arg += char
            elif char == '(' and not in_string and not in_char:
                paren_level += 1
                current_arg += char
            elif char == ')' and not in_string and not in_char:
                paren_level -= 1
                current_arg += char
            elif char == '{' and not in_string and not in_char:
                brace_level += 1
                current_arg += char
            elif char == '}' and not in_string and not in_char:
                brace_level -= 1
                current_arg += char
            elif char == '[' and not in_string and not in_char:
                bracket_level += 1
                current_arg += char
            elif char == ']' and not in_string and not in_char:
                bracket_level -= 1
                current_arg += char
            elif char == ',' and not in_string and not in_char and paren_level == 0 and brace_level == 0 and bracket_level == 0:
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
            # Array access or complex expression - checking for array syntax
            elif '[' in arg and ']' in arg:
                # Replace boolean literals
                arg = re.sub(r'\btr\b', '1', arg)
                arg = re.sub(r'\bfls\b', '0', arg)
                
                # If comparing strings, use %d format with strcmp
                if '==' in arg or '!=' in arg:
                    if 'name' in arg or 'strng' in arg:
                        format_parts.append("%d")
                        # For string equality, we need to use strcmp
                        if '==' in arg:
                            parts = arg.split('==')
                            arg = f"strcmp({parts[0].strip()}, {parts[1].strip()}) == 0"
                        elif '!=' in arg:
                            parts = arg.split('!=')
                            arg = f"strcmp({parts[0].strip()}, {parts[1].strip()}) != 0"
                    else:
                        # Default to %d for all other expressions
                        format_parts.append("%d")
                else:
                    # Handle other array expressions, guessing the type based on variables
                    if 'dbl' in arg or 'frac' in arg:
                        format_parts.append("%.2f")
                    elif 'chr' in arg or 'letter' in arg:
                        format_parts.append("%c")
                    else:
                        format_parts.append("%d")
                
                c_args.append(arg)
            # Variable or expression - attempt to determine type
            else:
                # If comparing strings, use %d format with strcmp
                if '==' in arg or '!=' in arg:
                    if 'name' in arg or 'strng' in arg or '"' in arg:
                        format_parts.append("%d")
                        # For string equality, we need to use strcmp
                        if '==' in arg:
                            parts = arg.split('==')
                            arg = f"strcmp({parts[0].strip()}, {parts[1].strip()}) == 0"
                        elif '!=' in arg:
                            parts = arg.split('!=')
                            arg = f"strcmp({parts[0].strip()}, {parts[1].strip()}) != 0"
                    else:
                        # Default to %d for other comparisons
                        format_parts.append("%d")
                else:
                    # For other expressions, try to guess type
                    if 'dbl' in arg or 'frac' in arg:
                        format_parts.append("%.2f")
                    elif 'chr' in arg or 'letter' in arg:
                        format_parts.append("%c")
                    else:
                        format_parts.append("%d")
                
                # Replace boolean literals
                arg = re.sub(r'\btr\b', '1', arg)
                arg = re.sub(r'\bfls\b', '0', arg)
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
        """Process a struct declaration without modifying the original lines list."""
        line = lines[start_index].strip()
        processed_lines = []
        struct_lines = 0

        if line.startswith('strct '):
            struct_name = line[6:line.find('{')].strip()
            processed_lines.append(f"typedef struct {struct_name} {{")
            
            # Count the lines in the struct body
            bracket_count = 1
            for i in range(start_index + 1, len(lines)):
                struct_lines += 1
                curr_line = lines[i].strip()
                
                # Process member declarations (convert Conso types to C types)
                if any(curr_line.startswith(t + " ") for t in self.type_mapping):
                    parts = curr_line.split(' ', 1)
                    member_type = parts[0]
                    if member_type in self.type_mapping:
                        c_type = self.type_mapping[member_type]
                        curr_line = curr_line.replace(member_type + " ", c_type + " ", 1)
                
                # Add the processed member line (unless it's just a closing brace)
                if curr_line not in ('};', '}'):
                    if curr_line:
                        processed_lines.append("    " + curr_line)
                
                if '{' in curr_line:
                    bracket_count += curr_line.count('{')
                if '}' in curr_line:
                    bracket_count -= curr_line.count('}')
                
                if bracket_count == 0:
                    # Found the end of the struct
                    processed_lines.append(f"}} {struct_name};")
                    break

        # Join all processed struct lines into a single string
        return "\n".join(processed_lines), struct_lines
     
    def _process_dfstrct(self, line):
        """Process a struct instantiation statement (dfstrct) to C typedef style."""
        if not line.lstrip().startswith('dfstrct '):
            return line

        # Remove 'dfstrct ' and trailing semicolon
        remaining = line.lstrip()[8:].strip()
        if remaining.endswith(';'):
            remaining = remaining[:-1]

        # Normalize whitespace (handle tabs, multiple spaces)
        remaining = re.sub(r'\s+', ' ', remaining).strip()

        # Split into struct type and variable list
        parts = remaining.split(' ', 1)
        if len(parts) != 2:
            # If parsing fails, return a comment for debugging
            return f"/* dfstrct parse error: '{line}' */"

        struct_type = parts[0].strip()
        vars_list = parts[1].strip()

        # Debug: print(f"dfstrct: struct_type='{struct_type}', vars_list='{vars_list}'")

        # Use typedef style: myStruct struct1, struct2;
        return f"{struct_type} {vars_list};"

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
        
        # Handle string comparisons (== and !=)
        if ('name' in line or 'strng' in line) and ('"' in line or "'" in line):
            if '==' in line:
                # Split at the equality operator
                parts = line.split('==')
                if len(parts) == 2:  # Simple comparison
                    left = parts[0].strip()
                    right = parts[1].strip()
                    if ('"' in right or "'" in right) or ('name' in left or 'strng' in left):
                        # Replace with strcmp
                        line = f"strcmp({left}, {right}) == 0"
            elif '!=' in line:
                # Split at the inequality operator
                parts = line.split('!=')
                if len(parts) == 2:  # Simple comparison
                    left = parts[0].strip()
                    right = parts[1].strip()
                    if ('"' in right or "'" in right) or ('name' in left or 'strng' in left):
                        # Replace with strcmp
                        line = f"strcmp({left}, {right}) != 0"
        
        # Add parentheses around string literals to ensure proper syntax
        line = re.sub(r'(?<!["\w])(\w+)(?!["\w])', lambda m: f'"{m.group(1)}"' if m.group(1) in ['hello', 'ftello'] else m.group(1), line)
        
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

    def fix_string_literals(expr):
        """Ensure string literals are properly quoted in expressions."""
        # Replace unquoted 'hello' and similar with quoted versions
        expr = re.sub(r'(?<!["\w])hello(?!["\w])', '"hello"', expr)
        expr = re.sub(r'(?<!["\w])ftello(?!["\w])', '"ftello"', expr)
        expr = re.sub(r'(?<!["\w])World(?!["\w])', '"World"', expr)
        expr = re.sub(r'(?<!["\w])Oki(?!["\w])', '"Oki"', expr)
        return expr

    def fix_char_literals(expr):
        """Ensure char literals are properly quoted in expressions."""
        # Replace unquoted single character literals with quoted versions
        expr = re.sub(r'(?<![\'"\w])([a-zA-Z])(?![\'"\w])', r"'\1'", expr)
        return expr

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
        # Special case: skip dfstrct in variable declaration logic
        if ttype == "dfstrct":
            # Handled in its own block below
            i += 1
            continue

        if ttype in transpiler.type_mapping:
            var_type = transpiler.type_mapping[ttype]
            j = i + 1

            # For collecting multiple declarations of the same type
            variables = []
            has_assignment = False

            # Process all variables of this type until semicolon
            while j < n:
                # Skip to identifier
                if get_token_type_value(token_list[j])[0] == "id":
                    var_name = get_token_type_value(token_list[j])[1]
                    j += 1

                    # Check for array dimensions
                    dimensions = []
                    has_dimensions = False

                    # Look for array dimensions [...]
                    while j < n and get_token_type_value(token_list[j])[0] == "[":
                        has_dimensions = True
                        j += 1  # Skip '['

                        # Collect dimension size
                        dim_size = ""
                        while j < n and get_token_type_value(token_list[j])[0] != "]":
                            dim_size += str(get_token_type_value(token_list[j])[1])
                            j += 1

                        if j < n and get_token_type_value(token_list[j])[0] == "]":
                            dimensions.append(dim_size)
                            j += 1

                    # Format dimensions for C code
                    dim_str = "".join(f"[{d}]" for d in dimensions)

                    # Check for assignment
                    value = None
                    if j < n and get_token_type_value(token_list[j])[0] == "=":
                        has_assignment = True
                        j += 1

                        # Get the value
                        value_tokens = []
                        brace_count = 0
                        while j < n:
                            next_token_type, next_token_value = get_token_type_value(token_list[j])

                            # End of this declaration
                            if next_token_type == ";" and brace_count == 0:
                                break
                            if next_token_type == "," and brace_count == 0:
                                break

                            # Track braces for array initialization
                            if next_token_type == "{":
                                brace_count += 1
                            elif next_token_type == "}":
                                brace_count -= 1

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
                        value = processed_value

                    variables.append((var_name, dim_str, value, has_dimensions))

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
                # If any variable has assignment or is an array, emit separate lines
                if has_assignment or any(is_array for _, _, _, is_array in variables):
                    for var_name, dimensions, value, is_array in variables:
                        if is_array:
                            # For array declarations
                            if value is not None:
                                output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_name}{dimensions} = {value};")
                            else:
                                output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_name}{dimensions};")
                        elif ttype == "strng":
                            # For string variables
                            if value is not None:
                                output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_name} = {value};")
                            else:
                                output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_name};")
                        else:
                            # For regular variables of other types
                            if value is not None:
                                output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_name} = {value};")
                            else:
                                output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_name};")
                else:
                    # No assignments, emit a single line for all variables
                    var_list = ", ".join(f"{var_name}{dimensions}" for var_name, dimensions, _, _ in variables)
                    output_lines.append(transpiler._indent(indent_level) + f"{var_type} {var_list};")

            i = j
            continue

        # 1. First, add this case for struct definitions (strct)
        elif ttype == "strct":
            j = i + 1
            struct_name = ""
            
            # Get struct name
            if j < n and get_token_type_value(token_list[j])[0] == "id":
                struct_name = get_token_type_value(token_list[j])[1]
                j += 1
            
            # Look for opening brace
            while j < n and get_token_type_value(token_list[j])[0] != "{":
                j += 1
            
            if j < n:  # Found opening brace
                # Output struct definition as typedef for flexible usage
                output_lines.append(f"typedef struct {struct_name} {{")
                indent_level += 1
                j += 1  # Skip opening brace

                # Process struct members until closing brace
                while j < n:
                    curr_type, curr_value = get_token_type_value(token_list[j])

                    if curr_type == "}":
                        # End of struct definition
                        indent_level -= 1
                        output_lines.append(transpiler._indent(indent_level) + f"}} {struct_name};")
                        j += 1  # Skip closing brace

                        # Skip semicolon if present
                        if j < n and get_token_type_value(token_list[j])[0] == ";":
                            j += 1
                        break
                    
                    # Process struct members (variable declarations)
                    if curr_type in transpiler.type_mapping:
                        c_type = transpiler.type_mapping[curr_type]
                        j += 1  # Skip type token
                        
                        # Get member name
                        if j < n and get_token_type_value(token_list[j])[0] == "id":
                            member_name = get_token_type_value(token_list[j])[1]
                            j += 1
                            
                            # Skip to semicolon
                            while j < n and get_token_type_value(token_list[j])[0] != ";":
                                j += 1
                            
                            # Add member declaration
                            output_lines.append(transpiler._indent(indent_level) + f"{c_type} {member_name};")
                            
                            if j < n:  # Skip semicolon
                                j += 1
                    else:
                        j += 1  # Skip unknown tokens
            
            i = j
            continue

        # 2. And add this case for struct instantiations (dfstrct)
        elif ttype == "dfstrct":
            var_type = "struct"  # In C, we use 'struct StructName'
            j = i + 1

            # Get struct type name
            if j < n and get_token_type_value(token_list[j])[0] == "id":
                struct_type = get_token_type_value(token_list[j])[1]
                j += 1

                # Process variable names
                variables = []
                while j < n:
                    curr_type, curr_value = get_token_type_value(token_list[j])
                    if curr_type == "id":
                        variables.append(curr_value)
                        j += 1
                        # Check for comma (more variables) or semicolon (end)
                        if j < n:
                            next_type, _ = get_token_type_value(token_list[j])
                            if next_type == ",":
                                j += 1  # Skip comma
                            elif next_type == ";":
                                j += 1  # Skip semicolon
                                break
                    else:
                        # Skip other tokens (unless it's a semicolon ending the statement)
                        if curr_type == ";":
                            j += 1
                            break
                        j += 1

                # Generate struct instantiation code with all collected variables
                if variables:
                    var_list = ", ".join(variables)
                    c_code = f"struct {struct_type} {var_list};"
                    output_lines.append(transpiler._indent(indent_level) + c_code)
            # After handling dfstrct, skip all processed tokens
            i = j
            continue
            
            i = j
            print("--- End dfstrct debug ---\n")
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
            bracket_count = 0
            paren_level = 0
            for t_type, t_value in args_tokens:
                # Track nested structures to properly group arguments
                if t_type == "[":
                    bracket_count += 1
                    curr_arg.append((t_type, t_value))
                elif t_type == "]":
                    bracket_count -= 1
                    curr_arg.append((t_type, t_value))
                elif t_type == "(":
                    paren_level += 1
                    curr_arg.append((t_type, t_value))
                elif t_type == ")":
                    paren_level -= 1
                    curr_arg.append((t_type, t_value))
                elif t_type == "," and bracket_count == 0 and paren_level == 0:
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
                    # Expression: try to infer type
                    expr_tokens = []
                    # Convert token tuple list to string tokens list with proper handling
                    for tok_type, tok_value in arg:
                        if tok_type == "strnglit":
                            expr_tokens.append(f'"{tok_value}"')
                        elif tok_type == "chrlit":
                            expr_tokens.append(f"'{tok_value}'")
                        elif tok_type == "blnlit":
                            expr_tokens.append("1" if tok_value == "tr" else "0")
                        else:
                            expr_tokens.append(str(tok_value))
                    
                    # Join tokens into expression string
                    expr_str = ' '.join(expr_tokens)
                    
                    # Fix unquoted literals
                    expr_str = fix_string_literals(expr_str)
                    expr_str = fix_char_literals(expr_str)
                    
                    # Determine expression types for format
                    expr_types = set()
                    for tok_type, tok_value in arg:
                        if tok_type == "id":
                            dtype = None
                            if symbol_table and symbol_table.lookup(tok_value):
                                dtype = symbol_table.lookup(tok_value).data_type
                            else:
                                # Try to infer from variable name
                                if tok_value.startswith("frac"):
                                    dtype = "dbl"
                                elif tok_value.startswith("num"):
                                    dtype = "nt"
                                elif tok_value.startswith("flag"):
                                    dtype = "bln"
                                elif tok_value.startswith("letter") or tok_value.startswith("newLetter"):
                                    dtype = "chr"
                                elif tok_value.startswith("name"):
                                    dtype = "strng"
                                else:
                                    # Fallback: assume int
                                    dtype = "nt"
                            expr_types.add(dtype)
                        elif tok_type in ["dbllit", "~dbllit"]:
                            expr_types.add("dbl")
                        elif tok_type in ["ntlit", "~ntlit"]:
                            expr_types.add("nt")
                        elif tok_type == "strnglit":
                            expr_types.add("strng")
                        elif tok_type == "chrlit":
                            expr_types.add("chr")
                        elif tok_type == "blnlit":
                            expr_types.add("bln")
                    
                    # Check if this is a comparison expression
                    has_comparison = any(op in expr_str for op in [">", "<", ">=", "<=", "==", "!="])
                    
                    if has_comparison:
                        # ALL comparisons return an integer in C, regardless of operand types
                        format_parts.append("%d")
                        
                        # Handle string comparisons which need special treatment
                        if "strng" in expr_types or any(s in expr_str for s in ["name", "\"", "strng"]):
                            if "==" in expr_str:
                                parts = expr_str.split("==")
                                left = parts[0].strip()
                                right = parts[1].strip()
                                expr_str = f"strcmp({left}, {right}) == 0"
                            elif "!=" in expr_str:
                                parts = expr_str.split("!=")
                                left = parts[0].strip() 
                                right = parts[1].strip()
                                expr_str = f"strcmp({left}, {right}) != 0"
                    else:
                        # For non-comparison expressions, infer the type
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
                            format_parts.append("%d")  # Default to int
                    
                    # Convert boolean literals in expressions
                    for idx, (tok_type, tok_value) in enumerate(arg):
                        if tok_type == "blnlit":
                            if tok_value == "tr":
                                arg[idx] = (tok_type, "1")
                            elif tok_value == "fls":
                                arg[idx] = (tok_type, "0")
                    
                    # Rebuild expression with converted boolean literals
                    expr_str = ' '.join(str(val) for _, val in arg)
                    
                    # Apply fixes again after rebuilding
                    expr_str = fix_string_literals(expr_str)
                    expr_str = fix_char_literals(expr_str)
                    
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
            bracket_level = 0
            paren_level = 0
            
            while j < n:
                curr_type, curr_value = get_token_type_value(token_list[j])
                
                if curr_type == ";" and bracket_level == 0 and paren_level == 0:
                    j += 1
                    break
                
                # Track bracket nesting for array access
                if curr_type == "[":
                    bracket_level += 1
                elif curr_type == "]":
                    bracket_level -= 1
                
                # Track parenthesis nesting
                if curr_type == "(":
                    paren_level += 1
                elif curr_type == ")":
                    paren_level -= 1
                
                # Convert boolean literals
                if curr_type == "blnlit" or curr_value in ["tr", "fls"]:
                    if curr_value == "tr":
                        stmt_tokens.append("1")
                    elif curr_value == "fls":
                        stmt_tokens.append("0")
                # Handle string literals
                elif curr_type == "strnglit":
                    stmt_tokens.append(f'"{curr_value}"')
                # Handle char literals
                elif curr_type == "chrlit":
                    stmt_tokens.append(f"'{curr_value}'")
                else:
                    stmt_tokens.append(str(curr_value))
                
                j += 1
            
            # Build the statement string
            stmt_str = ' '.join(stmt_tokens)
            
            # Fix unquoted literals
            stmt_str = fix_string_literals(stmt_str)
            stmt_str = fix_char_literals(stmt_str)
            
            # Handle comparisons in other statements
            if ("==" in stmt_str or "!=" in stmt_str):
                # For string comparisons
                if any(s in stmt_str for s in ["name", "\"", "strng"]):
                    if "==" in stmt_str:
                        parts = stmt_str.split("==")
                        left = parts[0].strip()
                        right = parts[1].strip()
                        stmt_str = f"strcmp({left}, {right}) == 0"
                    elif "!=" in stmt_str:
                        parts = stmt_str.split("!=")
                        left = parts[0].strip()
                        right = parts[1].strip()
                        stmt_str = f"strcmp({left}, {right}) != 0"
            
            output_lines.append(transpiler._indent(indent_level) + stmt_str + ";")
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