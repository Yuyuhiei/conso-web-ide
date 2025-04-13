"""
Conso to C Transpiler
This module converts Conso code to C code, assuming the input has already passed
lexical, syntax and semantic analysis.
"""
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
        """Process a variable declaration statement"""
        # Handle variable declarations like "nt x = 5;"
        parts = line.split(' ', 1)
        if len(parts) < 2:
            return line  # Not enough parts, return unchanged
        
        conso_type = parts[0]
        rest = parts[1]
        
        if conso_type in self.type_mapping:
            c_type = self.type_mapping[conso_type]
            # Replace the Conso type with the C type
            return f"{c_type} {rest}"
        
        return line  # Type not found, return unchanged

    def _process_print(self, line):
        """Process a print statement with a more robust approach"""
        # Remove trailing semicolon if present for parsing
        if line.endswith(';'):
            line = line[:-1]
        # Extract the content inside the parentheses
        content = line[line.find('(')+1:line.rfind(')')].strip()

        # Case 1: String literal only - prnt("Hello");
        if content.startswith('"') and content.endswith('"'):
            string_content = content[1:-1]
            if "\\n" not in string_content:
                string_content += "\\n"
            return f'printf("{string_content}"); fflush(stdout);'

        # Case 2: String + expression(s) - prnt("The answer is: ", expr);
        elif content.startswith('"') and ',' in content:
            # Split on the first comma after the string
            first_quote_end = content.find('"', 1)
            if first_quote_end != -1:
                format_str = content[1:first_quote_end]
                args = content[first_quote_end+2:].strip()  # skip ","
                # If the format string does not contain any %, append %d or %f for each argument
                if "%" not in format_str:
                    # Support multiple arguments (comma-separated)
                    arg_list = [a.strip() for a in args.split(",")]
                    # Default: use %d for each argument
                    format_str += " " + " ".join(["%d" for _ in arg_list])
                if "\\n" not in format_str:
                    format_str += "\\n"
                return f'printf("{format_str}", {args}); fflush(stdout);'
            else:
                # Fallback: treat as expression
                return f'printf("%d\\n", {content}); fflush(stdout);'

        # Case 3: Expression or variable - prnt(5 + 5); or prnt(x);
        else:
            return f'printf("%d\\n", {content}); fflush(stdout);'

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
            return f"if ({condition}) {{"
        return line

    def _process_else_if_statement(self, line):
        """Process an else-if statement"""
        # "lsf (condition) {" -> "else if (condition) {"
        if line.startswith('lsf ('):
            condition = line[line.find('(')+1:line.rfind(')')]
            return f"else if ({condition}) {{"
        return line

    def _process_while_loop(self, line):
        """Process a while loop"""
        # "whl (condition) {" -> "while (condition) {"
        if line.startswith('whl ('):
            condition = line[line.find('(')+1:line.rfind(')')]
            return f"while ({condition}) {{"
        return line

    def _process_for_loop(self, line):
        """Process a for loop"""
        # "fr (init; condition; update) {" -> "for (init; condition; update) {"
        if line.startswith('fr ('):
            content = line[line.find('(')+1:line.rfind(')')]
            return f"for ({content}) {{"
        return line

    def _process_do_while_condition(self, line):
        """Process the condition part of a do-while loop"""
        # "whl (condition);" -> "} while (condition);"
        if line.startswith('whl ('):
            condition = line[line.find('(')+1:line.rfind(')')]
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
            line = line.replace(f" {key} ", f" {value} ")
            line = line.replace(f"({key})", f"({value})")
            line = line.replace(f"={key};", f"={value};")
        
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

def transpile_from_tokens(token_list):
    """
    Transpile Conso code to C code using a token stream.
    Args:
        token_list (list): List of Token objects or (type, value, line, column) tuples.
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
                curr_type, _ = get_token_type_value(token_list[k])
                if curr_type == "(":
                    paren_count += 1
                elif curr_type == ")":
                    paren_count -= 1
                    if paren_count == 0:
                        break
                if paren_count > 0:
                    args_tokens.append(token_list[k])
                k += 1
            # Build the print statement
            if args_tokens:
                first_type, first_value = get_token_type_value(args_tokens[0])
            else:
                first_type, first_value = None, None
            if args_tokens and first_type in ["strnglit", "strng"]:
                str_val = first_value
                if len(args_tokens) > 1:
                    format_str = str_val
                    arg_exprs = []
                    curr_expr = []
                    for t in args_tokens[1:]:
                        ttype2, tvalue2 = get_token_type_value(t)
                        if ttype2 == ",":
                            if curr_expr:
                                arg_exprs.append(' '.join(str(get_token_type_value(x)[1]) for x in curr_expr))
                                curr_expr = []
                        else:
                            curr_expr.append(t)
                    if curr_expr:
                        arg_exprs.append(' '.join(str(get_token_type_value(x)[1]) for x in curr_expr))
                    if "%" not in format_str:
                        format_str += " " + " ".join(["%d" for _ in arg_exprs])
                    if "\\n" not in format_str:
                        format_str += "\\n"
                    output_lines.append(transpiler._indent(indent_level) + f'printf("{format_str}", {", ".join(arg_exprs)}); fflush(stdout);')
                else:
                    if "\\n" not in str_val:
                        str_val += "\\n"
                    output_lines.append(transpiler._indent(indent_level) + f'printf("{str_val}"); fflush(stdout);')
            else:
                expr = ' '.join(str(get_token_type_value(x)[1]) for x in args_tokens)
                output_lines.append(transpiler._indent(indent_level) + f'printf("%d\\n", {expr}); fflush(stdout);')
            i = k + 1
            if i < n:
                next_type, _ = get_token_type_value(token_list[i])
                if next_type == ";":
                    i += 1
            continue

        # Opening brace
        if ttype == "{":
            indent_level += 1
            i += 1
            continue

        # Closing brace
        if ttype == "}":
            indent_level -= 1
            output_lines.append(transpiler._indent(indent_level) + "}")
            i += 1
            continue

        # Variable declarations and other statements
        if ttype in transpiler.type_mapping or ttype in ["id", "=", "+", "-", "*", "/", "%", "++", "--", "+=", "-=", "*=", "/=", "%=", "==", "!=", "<", "<=", ">", ">=", "tr", "fls", "npt", "cntn", "rtrn"]:
            stmt_tokens = [str(tvalue)]
            j = i + 1
            while j < n:
                ttype2, tvalue2 = get_token_type_value(token_list[j])
                if ttype2 == ";":
                    break
                stmt_tokens.append(str(tvalue2))
                j += 1
            if ttype in transpiler.type_mapping:
                stmt_tokens[0] = transpiler.type_mapping[ttype]
            if ttype == "tr":
                stmt_tokens[0] = "1"
            if ttype == "fls":
                stmt_tokens[0] = "0"
            output_lines.append(transpiler._indent(indent_level) + ' '.join(stmt_tokens) + ";")
            i = j + 1
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
