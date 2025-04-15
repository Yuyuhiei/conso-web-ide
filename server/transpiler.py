"""
Conso to C Transpiler (V6 - Token-Based Sequential)
This module converts Conso code to C code using a token stream provided
by earlier compiler phases (Lexer, Parser, Semantic Analyzer).
Processes top-level blocks sequentially based on tokens.
Includes default value fix in declaration processing.
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
        self.tokens = token_list
        self.symbol_table = symbol_table # Store symbol table if provided
        self.current_pos = 0
        self.output_parts = []
        self.current_indent_level = 0

        # Mappings (same as before)
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
            "nt": "0", "dbl": "0.0", "strng": "NULL",
            "bln": "0", "chr": "'\\0'"
        }

    # --- Token Helpers ---
    def _peek(self, offset=0):
        """Look at the token at the current position + offset without consuming."""
        peek_pos = self.current_pos + offset
        if 0 <= peek_pos < len(self.tokens):
            token = self.tokens[peek_pos]
            if isinstance(token, tuple) and len(token) > 0: return token[0]
            elif hasattr(token, 'type'): return token.type
        return None

    def _consume(self, expected_type=None, expected_value=None):
        """Consume the current token, optionally checking its type/value."""
        if self.current_pos < len(self.tokens):
            token = self.tokens[self.current_pos]
            token_type, token_value = None, None
            if isinstance(token, tuple) and len(token) >= 2: token_type, token_value = token[0], token[1]
            elif hasattr(token, 'type') and hasattr(token, 'value'): token_type, token_value = token.type, token.value
            line = token[2] if isinstance(token, tuple) and len(token)>2 else '?'
            if expected_type and token_type != expected_type: raise TranspilerError(f"Expected token type '{expected_type}' but got '{token_type}'", line)
            if expected_value and token_value != expected_value: raise TranspilerError(f"Expected token value '{expected_value}' but got '{token_value}'", line)
            self.current_pos += 1
            return token_type, token_value, token
        raise TranspilerError("Unexpected end of token stream")

    def _skip_token(self, count=1):
        """Advance the current position."""
        self.current_pos += count

    # --- Core Transpilation Method ---
    def transpile(self):
        """Transpile the token stream sequentially."""
        self.output_parts = [
            self._generate_headers(),
            self._generate_helper_functions()
        ]
        while self.current_pos < len(self.tokens):
            token_type = self._peek()
            if token_type == "EOF": break
            if token_type == 'strct':
                struct_def_c = self._process_struct_definition_from_tokens()
                if struct_def_c: self.output_parts.extend(["// Struct Definition", struct_def_c, ""])
            elif token_type == 'fnctn':
                func_def_c = self._process_function_definition_from_tokens()
                if func_def_c: self.output_parts.extend(["// Function Definition", func_def_c, ""])
            elif token_type == 'mn':
                main_def_c = self._process_main_definition_from_tokens()
                if main_def_c: self.output_parts.extend(["// Main Function", main_def_c, ""])
            else:
                line = self.tokens[self.current_pos][2] if isinstance(self.tokens[self.current_pos], tuple) and len(self.tokens[self.current_pos])>2 else '?'
                print(f"Warning: Ignoring unexpected top-level token '{token_type}' at line {line}")
                self._skip_token()
        return "\n".join(self.output_parts)

    # --- Token-Based Definition Processors ---
    def _process_struct_definition_from_tokens(self):
        """Processes struct definition from tokens."""
        try:
            self._consume('strct')
            _, struct_name, _ = self._consume('id')
            self._consume('{')
            definition_lines = [f"typedef struct {struct_name} {{"]
            indent = "    "
            while self._peek() != '}':
                if self._peek() == "EOF": raise TranspilerError("Unexpected EOF inside struct definition")
                member_line = self._process_statement_from_tokens(is_struct_member=True)
                if member_line: definition_lines.append(indent + member_line)
            self._consume('}')
            if self._peek() == ';': self._consume(';')
            definition_lines.append(f"}} {struct_name};")
            return "\n".join(definition_lines)
        except TranspilerError as e:
            print(f"Error processing struct: {e}")
            # Attempt to recover by skipping tokens until likely end? Difficult.
            # For now, return None to indicate failure.
            return None

    def _process_function_definition_from_tokens(self):
        """Processes function definition from tokens."""
        try:
            self._consume('fnctn')
            type_token = self._consume()
            return_type_conso = type_token[0]
            c_return_type = self.type_mapping.get(return_type_conso, return_type_conso)
            _, func_name, _ = self._consume('id')
            self._consume('(')
            params_c = self._process_parameters_from_tokens()
            self._consume(')')
            self._consume('{')
            definition_lines = [f"{c_return_type} {func_name}({params_c}) {{"]
            self.current_indent_level = 1
            while self._peek() != '}':
                if self._peek() == "EOF": raise TranspilerError("Unexpected EOF inside function definition")
                statement_c = self._process_statement_from_tokens()
                if statement_c:
                    indent_level = self.current_indent_level
                    if statement_c.startswith('}'): indent_level = max(0, indent_level - 1)
                    definition_lines.append(self._indent(indent_level) + statement_c)
                    if statement_c.endswith('{'): self.current_indent_level += 1
                    if statement_c.startswith('}'): self.current_indent_level = max(0, self.current_indent_level -1)
            self._consume('}')
            self.current_indent_level = 0
            definition_lines.append("}")
            return "\n".join(definition_lines)
        except TranspilerError as e:
            print(f"Error processing function '{func_name}': {e}")
            return None # Indicate failure


    def _process_main_definition_from_tokens(self):
        """Processes main function definition from tokens."""
        try:
            self._consume('mn')
            self._consume('(')
            self._consume(')')
            self._consume('{')
            definition_lines = ["int main(int argc, char *argv[]) {"]
            self.current_indent_level = 1
            while self._peek() != 'end':
                if self._peek() == "EOF": raise TranspilerError("Unexpected EOF inside main definition")
                statement_c = self._process_statement_from_tokens()
                if statement_c:
                    indent_level = self.current_indent_level
                    if statement_c.startswith('}'): indent_level = max(0, indent_level - 1)
                    definition_lines.append(self._indent(indent_level) + statement_c)
                    if statement_c.endswith('{'): self.current_indent_level += 1
                    if statement_c.startswith('}'): self.current_indent_level = max(0, self.current_indent_level -1)
            self._consume('end')
            self._consume(';')
            self.current_indent_level = 0
            definition_lines.append(self._indent(1) + "return 0; // Corresponds to Conso 'end;'")
            definition_lines.append("}")
            return "\n".join(definition_lines)
        except TranspilerError as e:
            print(f"Error processing main function: {e}")
            return None # Indicate failure

    def _process_parameters_from_tokens(self):
        """Processes parameters from token stream until ')' is found."""
        params = []
        if self._peek() == ')': return "void"
        while self._peek() != ')':
            if self._peek() == "EOF": raise TranspilerError("Unexpected EOF in parameter list")
            type_token = self._consume()
            param_type_conso = type_token[0]
            c_type = self.type_mapping.get(param_type_conso, param_type_conso)
            _, param_name, _ = self._consume('id')
            params.append(f"{c_type} {param_name}")
            if self._peek() == ',': self._consume(',')
            elif self._peek() == ')': break
            else: raise TranspilerError(f"Unexpected token '{self._peek()}' in parameter list")
        return ", ".join(params) if params else "void"

    # --- Statement Processing (Token-Based) ---
    def _process_statement_from_tokens(self, is_struct_member=False):
        """Processes a single statement from the current token position."""
        token_type = self._peek()
        if is_struct_member:
            if token_type in self.type_mapping and token_type != 'dfstrct':
                return self._process_declaration_from_tokens(assign_default=False)
            else:
                line = self.tokens[self.current_pos][2] if isinstance(self.tokens[self.current_pos], tuple) and len(self.tokens[self.current_pos])>2 else '?'
                print(f"Warning: Skipping non-declaration token '{token_type}' inside struct at line {line}")
                self._consume(); return ""
        # --- Processing for lines inside functions/main ---
        if token_type == '{': self._consume(); return "{"
        if token_type == '}': self._consume(); return "}"
        if token_type in self.type_mapping and token_type != 'dfstrct': return self._process_declaration_from_tokens(assign_default=True)
        elif token_type == 'dfstrct': return self._process_dfstrct_from_tokens()
        elif token_type == 'prnt': return self._process_print_from_tokens()
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
        else: return self._process_other_statement_from_tokens() # Assignment, call, etc.

    # --- Token-Based Specific Statement Processors ---
    def _process_declaration_from_tokens(self, assign_default=True):
        """Processes declaration statement from tokens."""
        type_token = self._consume()
        conso_type = type_token[0]
        c_type = self.type_mapping.get(conso_type, conso_type)
        processed_decls = []
        while True:
            _, var_name, _ = self._consume('id')
            array_suffix = ""; initializer_tokens = None; is_array = False # Initialize is_array
            if self._peek() == '[':
                is_array = True # Set flag
                self._consume('[')
                size_tokens = []
                while self._peek() != ']': size_tokens.append(self._consume()[1])
                self._consume(']')
                array_suffix = f"[{''.join(map(str, size_tokens))}]"
            if self._peek() == '=':
                self._consume('=')
                initializer_tokens = []
                brace_level = 0
                while not ((self._peek() == ',' or self._peek() == ';') and brace_level == 0):
                    tok_type, tok_val, _ = self._consume()
                    if tok_type == '{': brace_level += 1
                    elif tok_type == '}': brace_level -= 1
                    initializer_tokens.append((tok_type, tok_val))
                    if self._peek() is None: raise TranspilerError("Unexpected EOF in initializer")
            # --- Format C declaration part ---
            c_decl_part = ""
            if initializer_tokens:
                init_val_c = self._tokens_to_c_expression(initializer_tokens)
                c_decl_part = f"{c_type} {var_name}{array_suffix} = {init_val_c}"
            else: # No initializer
                if is_array: # Use the flag here
                    has_size = any(char.isdigit() for char in array_suffix)
                    if assign_default and has_size and c_type in ["int", "double", "char"]: c_decl_part = f"{c_type} {var_name}{array_suffix} = {{0}}"
                    else: c_decl_part = f"{c_type} {var_name}{array_suffix}"
                else: # Regular variable
                    if assign_default:
                        # *** FIXED DEFAULT VALUE ASSIGNMENT ***
                        default_val = self.default_values.get(conso_type, "/* unknown default */")
                        c_decl_part = f"{c_type} {var_name} = {default_val}"
                    else: c_decl_part = f"{c_type} {var_name}"
            processed_decls.append(c_decl_part)
            # Check for end of declaration list
            if self._peek() == ';': self._consume(';'); break
            elif self._peek() == ',': self._consume(',')
            else: break # Assume end
        return "; ".join(processed_decls) + ";"

    def _process_dfstrct_from_tokens(self):
        """Processes dfstrct statement from tokens."""
        self._consume('dfstrct')
        _, struct_type, _ = self._consume('id')
        var_names = []
        while self._peek() != ';':
            if self._peek() == 'id': var_names.append(self._consume('id')[1])
            elif self._peek() == ',': self._consume(',')
            else: raise TranspilerError(f"Unexpected token '{self._peek()}' in dfstrct")
        self._consume(';')
        c_declarations = [f"{struct_type} {var_name}" for var_name in var_names]
        return "; ".join(c_declarations) + ";"

    def _process_print_from_tokens(self):
        """Processes prnt statement from tokens."""
        self._consume('prnt'); self._consume('(')
        args = []; current_arg_tokens = []; paren_level = 0
        while not (self._peek() == ')' and paren_level == 0):
            if self._peek() == "EOF": raise TranspilerError("Unexpected EOF in print statement")
            tok_type, tok_val, _ = self._consume()
            if tok_type == '(': paren_level += 1
            elif tok_type == ')': paren_level -= 1
            if tok_type == ',' and paren_level == 0:
                if current_arg_tokens: args.append(self._tokens_to_c_expression(current_arg_tokens))
                current_arg_tokens = []
            else: current_arg_tokens.append((tok_type, tok_val))
        if current_arg_tokens: args.append(self._tokens_to_c_expression(current_arg_tokens))
        self._consume(')'); self._consume(';')
        format_parts = []; c_args = []
        for arg_str in args:
             if arg_str.startswith('"'): format_parts.append("%s")
             elif arg_str.startswith("'"): format_parts.append("%c")
             elif '.' in arg_str or 'e' in arg_str.lower(): format_parts.append("%.2f") # Basic check
             else: format_parts.append("%d")
             c_args.append(arg_str)
        if not format_parts: return 'printf("\\n"); fflush(stdout);'
        format_str = " ".join(format_parts) + "\\n"
        return f'printf("{format_str}", {", ".join(c_args)}); fflush(stdout);'

    def _process_input_from_tokens(self):
        """Processes input assignment statement from tokens."""
        _, var_name, _ = self._consume('id'); self._consume('='); self._consume('npt'); self._consume('(')
        prompt_tokens = []
        if self._peek() == 'strnglit': prompt_tokens.append(self._consume('strnglit')[1])
        self._consume(')'); self._consume(';')
        prompt_c = f'"{prompt_tokens[0]}"' if prompt_tokens else '""'
        return f"{var_name} = conso_input({prompt_c}); // Potential memory leak" + ";"

    def _process_return_from_tokens(self):
        """Processes return statement from tokens."""
        self._consume('rtrn')
        if self._peek() == ';': self._consume(';'); return "return;"
        expr_tokens = []
        while self._peek() != ';': expr_tokens.append(self._consume()[:2])
        self._consume(';')
        value_c = self._tokens_to_c_expression(expr_tokens)
        return f"return {value_c};"

    def _process_if_from_tokens(self):
        self._consume('f'); self._consume('(')
        condition_tokens = []; paren_level = 1
        while paren_level > 0:
             tok_type, tok_val, _ = self._consume()
             if tok_type == '(': paren_level += 1
             elif tok_type == ')': paren_level -= 1
             if paren_level > 0: condition_tokens.append((tok_type, tok_val))
        condition_c = self._tokens_to_c_expression(condition_tokens)
        return f"if ({condition_c})"

    def _process_else_if_from_tokens(self):
        self._consume('lsf'); self._consume('(')
        condition_tokens = []; paren_level = 1
        while paren_level > 0:
             tok_type, tok_val, _ = self._consume()
             if tok_type == '(': paren_level += 1
             elif tok_type == ')': paren_level -= 1
             if paren_level > 0: condition_tokens.append((tok_type, tok_val))
        condition_c = self._tokens_to_c_expression(condition_tokens)
        return f"else if ({condition_c})"

    def _process_else_from_tokens(self): self._consume('ls'); return "else"
    def _process_while_from_tokens(self):
        self._consume('whl'); self._consume('(')
        condition_tokens = []; paren_level = 1
        while paren_level > 0:
             tok_type, tok_val, _ = self._consume()
             if tok_type == '(': paren_level += 1
             elif tok_type == ')': paren_level -= 1
             if paren_level > 0: condition_tokens.append((tok_type, tok_val))
        condition_c = self._tokens_to_c_expression(condition_tokens)
        return f"while ({condition_c})"

    def _process_for_from_tokens(self):
        self._consume('fr'); self._consume('(')
        init_tokens = []; cond_tokens = []; update_tokens = []; part = 1; paren_level = 1
        while paren_level > 0:
             tok_type, tok_val, _ = self._consume()
             if tok_type == '(': paren_level += 1
             elif tok_type == ')': paren_level -= 1
             if paren_level == 0: break
             if tok_type == ';' and paren_level == 1: part += 1
             else:
                  token_tuple = (tok_type, tok_val)
                  if part == 1: init_tokens.append(token_tuple)
                  elif part == 2: cond_tokens.append(token_tuple)
                  elif part == 3: update_tokens.append(token_tuple)
        init_c = self._tokens_to_c_expression(init_tokens) if init_tokens else ""
        cond_c = self._tokens_to_c_expression(cond_tokens) if cond_tokens else ""
        update_c = self._tokens_to_c_expression(update_tokens) if update_tokens else ""
        return f"for ({init_c}; {cond_c}; {update_c})"

    def _process_do_from_tokens(self): self._consume('d'); return "do"
    def _process_switch_from_tokens(self):
        self._consume('swtch'); self._consume('(')
        expr_tokens = []; paren_level = 1
        while paren_level > 0:
             tok_type, tok_val, _ = self._consume()
             if tok_type == '(': paren_level += 1
             elif tok_type == ')': paren_level -= 1
             if paren_level > 0: expr_tokens.append((tok_type, tok_val))
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
            if self._peek() == "EOF": raise TranspilerError("Unexpected EOF in statement")
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
        # Basic implementation - joins values, handles bools/strings/chars
        c_parts = []
        last_token_type = None
        for tok_type, tok_value in tokens:
            # Add space based on context (simple heuristic)
            if c_parts and last_token_type not in ['(', '[', '.'] and tok_type not in [')', ']', '.', ';', ',']:
                 c_parts.append(" ")

            if tok_type == 'blnlit': c_parts.append(self.bool_mapping.get(tok_value, '0'))
            elif tok_type == 'strnglit': c_parts.append(f'"{tok_value}"')
            elif tok_type == 'chrlit': c_parts.append(f"'{tok_value}'")
            # Map keywords if they appear in expressions
            elif tok_type in self.keyword_mapping: c_parts.append(self.keyword_mapping[tok_type])
            else: c_parts.append(str(tok_value))
            last_token_type = tok_type

        expr = "".join(c_parts) # Join without extra spaces initially, rely on token spacing
        # Replace boolean literals again just in case
        expr = self._replace_bool_literals(expr)
        # Handle string comparisons
        if ' == ' in expr and ('"' in expr or "'" in expr):
             parts = expr.split(' == ', 1)
             if len(parts) == 2: expr = f"strcmp({parts[0].strip()}, {parts[1].strip()}) == 0"
        elif ' != ' in expr and ('"' in expr or "'" in expr):
             parts = expr.split(' != ', 1)
             if len(parts) == 2: expr = f"strcmp({parts[0].strip()}, {parts[1].strip()}) != 0"
        return expr


    # --- Helper Methods ---
    def _indent(self, level): return "    " * max(0, level)
    def _generate_headers(self): return ("#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <stdbool.h>\n#include <stddef.h>\n\n")
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
    transpiler = ConsoTranspilerTokenBased(token_list, symbol_table)
    try:
        return transpiler.transpile()
    except TranspilerError as e:
        print(f"Transpilation Error: {e}", file=sys.stderr)
        return f"// TRANSPILER ERROR: {e}"
    except Exception as e:
        print(f"Unexpected Transpiler Error: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr) # Print full traceback for unexpected errors
        return f"// UNEXPECTED TRANSPILER ERROR: {type(e).__name__}: {e}"

# _tokens_to_code is no longer needed if we transpile directly from tokens

# --- Example Usage ---
if __name__ == "__main__":
    # Example token list simulating output from previous stages
    test_token_list = [
        # strct myStruct { ... };
        ('strct', 'strct', 1, 1), ('id', 'myStruct', 1, 7), ('{', '{', 1, 16),
        ('nt', 'nt', 2, 5), ('id', 'age', 2, 8), (';', ';', 2, 11),
        ('dbl', 'dbl', 3, 5), ('id', 'grade', 3, 9), (';', ';', 3, 14),
        ('bln', 'bln', 4, 5), ('id', 'flag', 4, 9), (';', ';', 4, 13),
        ('chr', 'chr', 5, 5), ('id', 'letter', 5, 9), (';', ';', 5, 15),
        ('strng', 'strng', 6, 5), ('id', 'name', 6, 11), (';', ';', 6, 15),
        ('}', '}', 7, 1), (';', ';', 7, 2), # Assuming semicolon after struct def

        # strct ndStruct { ... };
        ('strct', 'strct', 9, 1), ('id', 'ndStruct', 9, 7), ('{', '{', 9, 16),
        ('nt', 'nt', 10, 5), ('id', 'age', 10, 8), (';', ';', 10, 11),
        ('dbl', 'dbl', 11, 5), ('id', 'grade', 11, 9), (';', ';', 11, 14),
        ('bln', 'bln', 12, 5), ('id', 'flag', 12, 9), (';', ';', 12, 13),
        ('chr', 'chr', 13, 5), ('id', 'letter', 13, 9), (';', ';', 13, 15),
        ('strng', 'strng', 14, 5), ('id', 'name', 14, 11), (';', ';', 14, 15),
        ('}', '}', 15, 1), (';', ';', 15, 2),

        # fnctn vd Test(){ ... }
        ('fnctn', 'fnctn', 17, 1), ('vd', 'vd', 17, 7), ('id', 'Test', 17, 10), ('(', '(', 17, 14), (')', ')', 17, 15), ('{', '{', 17, 16),
        ('nt', 'nt', 18, 5), ('id', 'sum', 18, 8), (';', ';', 18, 11),
        ('dbl', 'dbl', 19, 5), ('id', 'frac', 19, 9), (';', ';', 19, 13),
        ('id', 'sum', 20, 5), ('=', '=', 20, 9), ('ntlit', 3, 20, 11), (';', ';', 20, 12),
        ('}', '}', 21, 1),

        # mn(){ ... }
        ('mn', 'mn', 23, 1), ('(', '(', 23, 3), (')', ')', 23, 4), ('{', '{', 23, 5),
        ('nt', 'nt', 24, 5), ('id', 'num', 24, 8), (',', ',', 24, 11), ('id', 'num2', 24, 13), ('=', '=', 24, 18), ('ntlit', 3, 24, 20), (';', ';', 24, 21),
        ('dbl', 'dbl', 25, 5), ('id', 'frac', 25, 9), (';', ';', 25, 13),
        ('dbl', 'dbl', 26, 5), ('id', 'frac2', 26, 9), ('=', '=', 26, 15), ('dbllit', 5.28, 26, 17), (';', ';', 26, 21),
        ('bln', 'bln', 27, 5), ('id', 'flag', 27, 9), ('=', '=', 27, 14), ('blnlit', 'tr', 27, 16), (',', ',', 27, 18), ('id', 'flag2', 27, 20), ('=', '=', 27, 26), ('blnlit', 'fls', 27, 28), (';', ';', 27, 31),
        ('chr', 'chr', 28, 5), ('id', 'letter', 28, 9), ('=', '=', 28, 16), ('chrlit', 'c', 28, 18), (';', ';', 28, 21),
        ('strng', 'strng', 29, 5), ('id', 'name', 29, 11), ('=', '=', 29, 16), ('strnglit', 'John', 29, 18), (';', ';', 29, 24),
        ('prnt', 'prnt', 30, 5), ('(', '(', 30, 9), ('strnglit', 'Hi', 30, 10), (',', ',', 30, 14), ('id', 'name', 30, 16), (',', ',', 30, 20), ('ntlit', 1, 30, 22), ('+', '+', 30, 24), ('ntlit', 1, 30, 26), (')', ')', 30, 27), (';', ';', 30, 28),
        ('end', 'end', 31, 5), (';', ';', 31, 8),
        ('}', '}', 32, 1), # Note: Parser might not generate this '}' for mn block ending with 'end;'

        ('EOF', None, 33, 1)
    ]


    print("--- Transpiling User's Conso Code from Tokens ---")
    # Pass None for symbol_table for now
    generated_c_code = transpile_from_tokens(test_token_list, None)
    print("\n--- Generated C Code ---")
    print(generated_c_code)
