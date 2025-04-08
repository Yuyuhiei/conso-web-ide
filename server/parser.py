from definitions import *

class ParserError(Exception):
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message
        self.line = line if line is not None else None
        self.column = column

    def __str__(self):
        if self.line is not None and self.column is not None:
            return f"{self.message} (Line {self.line}, Column {self.column})"
        return self.message

def parse(token_list=None):
    add_all_set()
    
    # Use provided token list or fall back to global
    tokens_to_parse = token_list if token_list is not None else token
    
    if not tokens_to_parse:
        raise ParserError("Syntax Error: No tokens provided.")

    stack = ["<program>"]
    current_token_index = 0
    log_messages = []
    error_message = []
    syntax_valid = False  # Add this flag

    def get_lookahead():
        """Safely retrieve the current token and its position."""
        if current_token_index < len(tokens_to_parse):  # FIXED: Use tokens_to_parse instead of token
            token_data = tokens_to_parse[current_token_index]
            
            # Handle Token objects
            if hasattr(token_data, 'type') and hasattr(token_data, 'line') and hasattr(token_data, 'column'):
                curr_token = token_data.type
                line = token_data.line
                column = token_data.column
            # Handle token tuples with various formats
            elif isinstance(token_data, tuple):
                if len(token_data) == 3:
                    curr_token, line, column = token_data
                elif len(token_data) == 4:
                    curr_token, token_value, line, column = token_data
                else:
                    return "$", None, None
            else:
                # Fallback for other formats
                return "$", None, None
            
            if isinstance(curr_token, str) and curr_token.startswith("id"):
                return "id", line, column
            return curr_token, line, column
        return "$", None, None

    try: 
        while stack:
            top = stack.pop()
            lookahead, line, column = get_lookahead()

            # Debugging logs
            print(f"Current Index: {current_token_index}")
            log_messages.append(f"Stack Top: {top}, Lookahead: {lookahead} (Line {line-1 if line is not None else line}, Column {column})")

            if lookahead == "$" and top != "$":
                raise ParserError("Syntax Error: Unexpected end of input.", line, column)

            if top == lookahead:
                log_messages.append(f"Matched: {lookahead} (Line {line-1 if line is not None else line}, Column {column})")  # Debug
                current_token_index += 1
            elif top in parsing_table:
                rule = parsing_table[top].get(lookahead)
                if rule:
                    if rule == ["null"]:  # Handle `null` (epsilon) productions
                        log_messages.append(f"Skipping {top} (Epsilon Production)")
                    else:
                        log_messages.append(f"Applying Rule: {top} -> {' '.join(rule)}")  # Debug
                        stack.extend(reversed(rule))
                else:
                    expected_tokens = list(parsing_table[top].keys())
                    raise ParserError(f"Syntax Error: Unexpected token '{lookahead}', expected one of: {expected_tokens}", line, column)
            else:
                raise ParserError(f"Syntax Error: Unexpected symbol '{lookahead}', expected '{top}'", line, column)

        # Check if we parsed all tokens
        if not stack and current_token_index < len(tokens_to_parse) and tokens_to_parse[current_token_index][0] == "EOF":
            error_message.append("Input accepted: Syntactically correct.")
            syntax_valid = True  # Set flag to True when syntax is correct
        else:
            raise ParserError("Input rejected: Syntax Error - Unexpected tokens remaining.")

    except ParserError as e:
        error_message.append(str(e))
        syntax_valid = False  # Ensure flag is False on errors
    except Exception as e:
        error_message.append(f"Unexpected error: {str(e)}")
        syntax_valid = False  # Ensure flag is False on errors

    return log_messages, error_message, syntax_valid  # Return the flag