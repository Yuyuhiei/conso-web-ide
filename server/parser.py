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

def parse():
    add_all_set()

    if not token:
        raise ParserError("❌ Syntax Error: No tokens provided.")

    stack = ["<program>"]
    current_token_index = 0
    log_messages = []
    error_message = []
    syntax_valid = False  # Add this flag

    def get_lookahead():
        """Safely retrieve the current token and its position."""
        if current_token_index < len(token):
            curr_token, line, column = token[current_token_index]  # ✅ Extract type, line, and column
            if curr_token.startswith("id"):
                return "id", line, column
            return curr_token, line, column
        return "$", None, None  # ✅ Return EOF marker with no position

    try: 
        while stack:
            top = stack.pop()
            lookahead, line, column = get_lookahead()

            # Debugging logs
            print(f"🔄 Current Index: {current_token_index}, Remaining Tokens: {token[current_token_index:]}")
            log_messages.append(f"🔍 Stack Top: {top}, Lookahead: {lookahead} (Line {line-1 if line is not None else line}, Column {column})")

            if lookahead == "$" and top != "$":
                raise ParserError("❌ Syntax Error: Unexpected end of input.", line, column)

            if top == lookahead:
                log_messages.append(f"✅ Matched: {lookahead} (Line {line-1 if line is not None else line}, Column {column})")  # Debug
                current_token_index += 1
            elif top in parsing_table:
                rule = parsing_table[top].get(lookahead)
                if rule:
                    if rule == ["null"]:  # ✅ Handle `null` (epsilon) productions
                        log_messages.append(f"🔍 Skipping {top} (Epsilon Production)")
                    else:
                        log_messages.append(f"📌 Applying Rule: {top} -> {' '.join(rule)}")  # Debug
                        stack.extend(reversed(rule))
                else:
                    expected_tokens = list(parsing_table[top].keys())
                    raise ParserError(f"❌ Syntax Error: Unexpected token '{lookahead}', expected one of: {expected_tokens}", line, column)
            else:
                raise ParserError(f"❌ Syntax Error: Unexpected symbol '{lookahead}', expected '{top}'", line, column)

        if not stack and current_token_index == len(token) - 1 and token[current_token_index][0] == "EOF":
            error_message.append("✅ Input accepted: Syntactically correct.")
            syntax_valid = True  # Set flag to True when syntax is correct
        else:
            raise ParserError("❌ Input rejected: Syntax Error - Unexpected tokens remaining.")

    except ParserError as e:
        error_message.append(str(e))
        syntax_valid = False  # Ensure flag is False on errors
    except Exception as e:
        error_message.append(f"Unexpected error: {str(e)}")
        syntax_valid = False  # Ensure flag is False on errors

    return log_messages, error_message, syntax_valid  # Return the flag
