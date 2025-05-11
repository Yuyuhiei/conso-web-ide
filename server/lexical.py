class LexerError(Exception):
    """Custom exception for lexical errors."""
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column

    def __str__(self):
        return f"Lexical Error at line {self.line}, column {self.column}: {self.message}"

# --- Token Types ---
TT_NPT = 'npt'
TT_PRNT = 'prnt'
TT_INT = 'nt'
TT_DOUBLE = 'dbl'
TT_STRING = 'strng'
TT_BOOL = 'bln'
TT_CHAR = 'chr'
TT_F = 'f'
TT_LS = 'ls'
TT_LSF = 'lsf'
TT_SWTCH = 'swtch'
TT_FR = 'fr'
TT_WHl = 'whl'
TT_D = 'd'
TT_MN = 'mn'
TT_CS = 'cs'
TT_DFLT = 'dflt'
TT_BRK = 'brk'
TT_CNST = 'cnst'
TT_TR = 'tr'
TT_FLS = 'fls'
TT_FNCTN = 'fnctn'
TT_RTRN = 'rtrn'
TT_END = 'end'
TT_NULL = 'null'
TT_CNTN = 'cntn'
TT_STRCT = 'strct'
TT_DFSTRCT = 'dfstrct'
TT_VD = 'vd'
TT_IDENTIFIER = 'id'

# Operators and Delimiters
TT_PLUS = '+'
TT_MINUS = '-'
TT_MUL = '*'
TT_DIV = '/'
TT_MOD = '%'
TT_EXP = '**'
TT_EQ = '='
TT_EQTO = '=='
TT_PLUSEQ = '+='
TT_MINUSEQ = '-='
TT_MULTIEQ = '*='
TT_DIVEQ = '/='
TT_MODEQ = '%='
TT_LPAREN = '('
TT_RPAREN = ')'
TT_SEMICOLON = ';'
TT_COMMA = ','
TT_COLON = ':'
TT_BLOCK_START = '{'
TT_BLOCK_END = '}'
TT_LT = '<'
TT_GT = '>'
TT_LTEQ = '<='
TT_GTEQ = '>='
TT_NOTEQ = '!='
TT_EOF = 'EOF'
TT_AND = '&&'
TT_OR = '||'
TT_NOT = '!'
TT_INCREMENT = '++'
TT_DECREMENT = '--'
TT_LSQBR = '['
TT_RSQBR = ']'
TT_NEGATIVE = '~'
TT_INTEGERLIT = 'ntlit'
TT_DOUBLELIT = 'dbllit'
TT_STRINGLIT = 'strnglit'
TT_CHARLIT = 'chrlit'
TT_STRCTACCESS = '.'


# --- Character Sets (Based on RE1 & RE2) ---
ZERO = {'0'}
DIGIT = {'1', '2', '3', '4', '5', '6', '7', '8', '9'}
DIGITZERO = DIGIT | ZERO

LOWALPHA = set("abcdefghijklmnopqrstuvwxyz")
UPALPHA = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ALPHA = LOWALPHA | UPALPHA
ALPHA_NUMERIC = ALPHA | DIGITZERO

NEWLINE = {'\n'}
TAB = {'\t'}
WHITESPACE = {' ', '\t', '\n'}

# Based on RE1 & RE2 - carefully transcribing the sets
DEL1 = WHITESPACE
DEL2 = {';'}
DEL3 = WHITESPACE | {'{'}
DEL4 = set()
DEL5 = WHITESPACE | {'('}
DEL6 = WHITESPACE | {';', ',', '=', '>', '<', '!', '}', ')'}
DEL7 = {'('}
DEL8 = WHITESPACE | {';'}
DEL9 = WHITESPACE | ALPHA | {'(', ',', ';', ')'}
DEL10 = WHITESPACE | {';', ')'}
DEL11 = WHITESPACE | NEWLINE
DEL12 = ALPHA | DIGITZERO | {']', '~'}
DEL13 = WHITESPACE | {';', '{', ')', ']', '<', '>', '=', '|', '&', '+', '-', '/', '*', '%', ',', '\n'}
DEL14 = WHITESPACE | NEWLINE | {'"', "'", '{'} | ALPHA | DIGITZERO
DEL15 = WHITESPACE | NEWLINE | {'}'}
DEL16 = ALPHA | DIGITZERO | {'"', '(', ')'}
DEL17 = WHITESPACE | {';', ',', '}', ')', '+', '-', '*', '/', '%', '=', '>', '<', '!', '&', '|', '['}
DEL18 = WHITESPACE | {';', '{', ')', '&', '|', '+', '-', '*', '/', '%'}
DEL19 = WHITESPACE | {',', '}', ')', '=', '>', '<', '!'}
DEL20 = WHITESPACE | ALPHA | DIGITZERO | {'"', "'", '{'}
DEL21 = DIGIT
DEL22 = WHITESPACE | {',', '}', ']', ')', ':', '+', '-', '*', '/', '%', '=', '>', '<', '!', '&', '|'}
DEL23 = WHITESPACE | {';', ',', '}', ')', '=', '>', '<', '!', '&', '|'}
DEL24 = WHITESPACE | DIGITZERO | ALPHA | {'~', '('}
DEL25 = WHITESPACE | DIGITZERO | ALPHA | {'~', '"', "'"}
DEL26 = WHITESPACE | {';', ',', '}', ')', '=', '>', '<', '!', ':'}
DEL27 = WHITESPACE | {'"'}


# Combined set for characters allowed in identifiers (after the first character)
IDENTIFIER_CHARS = ALPHA_NUMERIC | {'_'}

# Characters allowed inside string literals (excluding '"' and '\')
STRING_CHARS = {chr(i) for i in range(32, 127) if chr(i) not in {'"', '\\'}}

# Characters allowed inside character literals (excluding "'" and '\')
CHAR_CHARS = {chr(i) for i in range(32, 127) if chr(i) not in {"'", '\\'}}

# --- Token Class ---
class Token:
    """Represents a token with type, value, line, and column."""
    def __init__(self, type, value=None, line=0, column=0):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        # Include line and column in representation for easier debugging
        return f'Token({self.type}, {repr(self.value)}, line {self.line}, col {self.column})'

# --- Lexer Class using Transition Diagrams ---
class Lexer:
    """
    Lexer that tokenizes input text based on transition diagrams.
    Processes input character by character, managing state transitions
    to recognize different token types.
    """
    def __init__(self, text):
        self.text = text
        self.pos = -1 # Current position in the input text
        self.current_char = None # The character currently being examined
        self.line = 1 # Current line number
        self.column = 0 # Current column number
        self.advance() # Move to the first character

    def advance(self):
        """Moves to the next character in the input text."""
        # Before advancing, check if the current character is a newline
        if self.current_char == '\n':
            self.line += 1
            self.column = 0 # Reset column for the new line
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
            self.column += 1 # Increment column for the new character
        else:
            self.current_char = None # Indicate end of input

    def peek(self, offset=1):
        """Looks ahead 'offset' characters without advancing the position."""
        peek_pos = self.pos + offset
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return None # Return None if peeking beyond the end of the text

    def step_back(self):
        """Moves the position back by one character."""
        if self.pos > 0:
            self.pos -= 1
            # Need to recalculate line/column, or store previous state
            # For simplicity here, we'll just move the position back.
            # A more robust solution would save line/column before advance.
            # Let's adjust column logic for simplicity in this implementation
            self.current_char = self.text[self.pos]
            # Simple column adjustment - assumes not stepping back over a newline
            if self.column > 0:
                 self.column -= 1


    def make_tokens(self):
        """
        Tokenizes the input text using transition diagrams.
        Returns a list of tokens and a list of errors encountered.
        """
        tokens = []
        errors = []
        state = 0
        lexeme = ""
        start_line = 1
        start_column = 0

        while self.current_char is not None or state != 0:
            # Store starting position when entering state 0
            if state == 0:
                start_line = self.line
                start_column = self.column

            # --- State Machine Implementation based on Transition Diagrams ---
            # Each case corresponds to a state in the transition diagrams.
            # The logic inside each case checks the current character and
            # transitions to the next state or recognizes a token.

            if state == 0:
                lexeme = "" # Reset lexeme at the start of a new token attempt

                # Handle whitespace and comments first (State 0 transitions)
                if self.current_char in WHITESPACE:
                    self.advance()
                    continue # Stay in state 0, skip whitespace

                if self.current_char == '#':
                    # Transition to comment state (State 161 in TD5)
                    state = 161
                    self.advance()
                    continue

                # Keywords and Identifiers (Starts with Alpha) - TD1, TD2, TD6
                if self.current_char in ALPHA:
                    state = 180 # Starting state for identifiers in TD6
                    lexeme += self.current_char
                    self.advance()
                    continue

                # Numbers (Starts with Digit or ~ followed by Digit) - TD7
                if self.current_char in DIGITZERO or (self.current_char == '~' and self.peek() in DIGITZERO):
                    state = 197 # Starting state for numbers in TD7
                    lexeme += self.current_char
                    self.advance()
                    continue

                # String Literal (Starts with '"') - TD5
                if self.current_char == '"':
                    state = 167 # Starting state for strings in TD5
                    lexeme += self.current_char
                    self.advance()
                    continue

                # Character Literal (Starts with "'") - TD5
                if self.current_char == "'":
                    state = 163 # Starting state for characters in TD5
                    lexeme += self.current_char
                    self.advance()
                    continue

                # Operators and Delimiters - TD3, TD4, TD5
                # These are handled as direct transitions from State 0 in the TDs
                if self.current_char == '+':
                    if self.peek() == '+':
                        state = 104 # TD3
                        lexeme += self.current_char
                        self.advance()
                    elif self.peek() == '=':
                        state = 102 # TD3
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 100 # TD3
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '-':
                    if self.peek() == '-':
                        state = 110 # TD3
                        lexeme += self.current_char
                        self.advance()
                    elif self.peek() == '=':
                        state = 108 # TD3
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 106 # TD3
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '*':
                    if self.peek() == '*':
                        state = 150 # TD3
                        lexeme += self.current_char
                        self.advance()
                    elif self.peek() == '=':
                        state = 148 # TD3
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 112 # TD3
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '/':
                    # Need to check for comments first, handled above
                    if self.peek() == '=':
                        state = 156 # TD3
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 116 # TD3
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '%':
                    if self.peek() == '=':
                        state = 160 # TD3
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 120 # TD3
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '=':
                    if self.peek() == '=':
                        state = 127 # TD4
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 125 # TD4
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '>':
                    if self.peek() == '=':
                        state = 131 # TD4
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 129 # TD4
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '<':
                    if self.peek() == '=':
                        state = 135 # TD4
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 133 # TD4
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '!':
                    if self.peek() == '=':
                        state = 139 # TD4
                        lexeme += self.current_char
                        self.advance()
                    else:
                        state = 137 # TD4
                        lexeme += self.current_char
                        self.advance()
                    continue

                if self.current_char == '&':
                    if self.peek() == '&':
                        state = 171 # TD5
                        lexeme += self.current_char
                        self.advance()
                    else:
                        # Error: Single '&' is not a valid token
                         errors.append(LexerError(f"Illegal character: '{self.current_char}'", start_line, start_column))
                         self.advance()
                         continue

                if self.current_char == '|':
                    if self.peek() == '|':
                        state = 174 # TD5
                        lexeme += self.current_char
                        self.advance()
                    else:
                        # Error: Single '|' is not a valid token
                         errors.append(LexerError(f"Illegal character: '{self.current_char}'", start_line, start_column))
                         self.advance()
                         continue

                if self.current_char == ',':
                    state = 157 # TD5
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == ':':
                    state = 141 # TD4
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == ';':
                    state = 143 # TD4
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == '(':
                    state = 153 # TD5
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == ')':
                    state = 155 # TD5
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == '[':
                    state = 145 # TD4
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == ']':
                    state = 147 # TD4
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == '{':
                    state = 149 # TD4
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == '}':
                    state = 151 # TD5
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == '.':
                    state = 176 # TD5
                    lexeme += self.current_char
                    self.advance()
                    continue

                if self.current_char == '`':
                    state = 178 # TD5
                    lexeme += self.current_char
                    self.advance()
                    continue

                # If none of the above matched, it's an illegal character
                errors.append(LexerError(f"Illegal character: '{self.current_char}'", start_line, start_column))
                self.advance() # Consume the illegal character and continue

            # --- State Transitions (Implementing the logic from the TDs) ---

            # Comment State (TD5)
            elif state == 161:
                # Consumes characters until newline
                if self.current_char is not None and self.current_char != '\n':
                    self.advance()
                elif self.current_char == '\n':
                    state = 162 # Transition to final state
                    self.advance()
                elif self.current_char is None:
                     # End of input while in a comment
                     state = 162 # Transition to final state (EOF acts as newline)

            elif state == 162:
                # Final state for single-line comment
                # No token is generated for comments
                state = 0 # Return to initial state
                continue # Continue the loop to process the next character

            # Character Literal States (TD5)
            elif state == 163:
                 # Expecting character or escape sequence
                 if self.current_char is None or self.current_char == '\n':
                      errors.append(LexerError("Unterminated character literal", start_line, start_column))
                      state = 0
                 elif self.current_char == '\\':
                      state = 294 # Transition to escape sequence state
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char in CHAR_CHARS:
                      state = 269 # Transition to character consumed state
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid character in character literal: '{self.current_char}'", start_line, start_column))
                      state = 0 # Error, return to initial state

            elif state == 269:
                 # Expected closing single quote
                 if self.current_char == "'":
                      state = 270 # Transition to final state
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Expected closing single quote for character literal (found '{self.current_char}')", start_line, start_column))
                      state = 0 # Error, return to initial state

            elif state == 270:
                 # Final state for character literal, check delimiter
                 if self.current_char is None or self.current_char in DEL27: # DEL27 is {whitespace, "}
                      state = 271 # Transition to tokenization state
                      # The delimiter is not part of the token, so step back if needed
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after character literal: '{self.current_char}'", start_line, start_column))
                      state = 0 # Error, return to initial state

            elif state == 271:
                 # Tokenize character literal
                 # Lexeme includes the quotes, value is the character inside
                 token_value = lexeme[1:-1]
                 # Handle escaped null character specifically if needed based on grammar
                 if token_value == '\\0':
                      token_value = '\0'
                 tokens.append(Token(TT_CHARLIT, token_value, start_line, start_column))
                 state = 0 # Return to initial state

            elif state == 294:
                 # Escape sequence in character literal
                 escape_map = {"'": "'", "\\": "\\", "n": "\n", "t": "\t", "r": "\r", '0': '\0', '"': '"'}
                 if self.current_char is None:
                      errors.append(LexerError("Unterminated escape sequence in character literal", start_line, start_column))
                      state = 0
                 elif self.current_char in escape_map:
                      state = 269 # Transition back after consuming escaped char
                      lexeme += self.current_char # Add the escaped char to lexeme (e.g., '\n')
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid escape sequence in character literal: \\{self.current_char}", start_line, start_column))
                      state = 0

            # String Literal States (TD5)
            elif state == 167:
                 # Consuming characters inside string
                 if self.current_char is None or self.current_char == '\n':
                      errors.append(LexerError("Unterminated string literal", start_line, start_column))
                      state = 0
                 elif self.current_char == '"':
                      state = 168 # Transition to closing quote state
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char == '\\':
                      state = 272 # Transition to escape sequence state (Need to verify this state number from TDs/REs)
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char in STRING_CHARS:
                      state = 167 # Stay in state, consume character
                      lexeme += self.current_char
                      self.advance()
                 else:
                      # Allow other characters in string, based on tokenizer.py's asciistr
                      state = 167
                      lexeme += self.current_char
                      self.advance()


            elif state == 168:
                 # Final state for string literal, check delimiter
                 if self.current_char is None or self.current_char in DEL19: # DEL19 is {whitespace, ,, }, ), =, >, <, !}
                      state = 169 # Transition to tokenization state
                      # Step back the delimiter if needed
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after string literal: '{self.current_char}'", start_line, start_column))
                      state = 0 # Error, return to initial state

            elif state == 169:
                 # Tokenize string literal
                 # Lexeme includes the quotes, value is the string inside
                 token_value = lexeme[1:-1]
                 # Handle empty string case
                 if token_value == "":
                      token_value = "empty" # Based on tokenizer.py output for empty string ""
                 tokens.append(Token(TT_STRINGLIT, token_value, start_line, start_column))
                 state = 0 # Return to initial state

            # Need to find the correct state for string escape sequences based on TDs/REs.
            # The tokenizer.py uses state 272 for string char consumption and 273 for closing quote.
            # Let's assume a state for string escape sequences is needed, similar to char.
            # Based on tokenizer.py state 272 transition for '\', let's use a new state, say 295.
            elif state == 272: # This state seems to be for consuming string characters in tokenizer.py
                 if self.current_char in STRING_CHARS:
                      state = 272
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char == '"':
                      state = 273 # Transition to closing quote state
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char == '\\':
                      state = 295 # Transition to string escape sequence state (Assuming new state)
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char is None or self.current_char == '\n':
                      errors.append(LexerError("Unterminated string literal", start_line, start_column))
                      state = 0
                 else:
                      # Allow other characters in string, based on tokenizer.py's asciistr
                      state = 272
                      lexeme += self.current_char
                      self.advance()

            elif state == 273: # Closing quote for string in tokenizer.py
                 if self.current_char is None or self.current_char in DEL19: # DEL19 is {whitespace, ,, }, ), =, >, <, !}
                      state = 274 # Final state in tokenizer.py
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after string literal: '{self.current_char}'", start_line, start_column))
                      state = 0

            elif state == 274: # Tokenization state for string in tokenizer.py
                 token_value = lexeme[1:-1]
                 if token_value == "":
                      token_value = "empty"
                 tokens.append(Token(TT_STRINGLIT, token_value, start_line, start_column))
                 state = 0

            elif state == 295: # Assuming this is the string escape sequence state
                 escape_map = {"'": "'", "\\": "\\", "n": "\n", "t": "\t", "r": "\r", '0': '\0', '"': '"'}
                 if self.current_char is None:
                      errors.append(LexerError("Unterminated escape sequence in string literal", start_line, start_column))
                      state = 0
                 elif self.current_char in escape_map:
                      state = 272 # Transition back to string char consumption
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid escape sequence in string literal: \\{self.current_char}", start_line, start_column))
                      state = 0


            # Identifier and Keyword States (TD6, TD1, TD2)
            # TD6 starts with state 180 for alpha
            elif state >= 180 and state <= 194: # States for identifier/keyword building in TD6
                 if self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      lexeme += self.current_char
                      # Check identifier length constraint (up to 25 characters based on tokenizer.py)
                      if len(lexeme) > 25:
                           errors.append(LexerError(f"Identifier '{lexeme}' exceeds maximum length of 25 characters", start_line, start_column))
                           state = 0 # Error state, stop processing this token
                      else:
                           # Stay in a state that accepts identifier characters
                           # The specific state transitions in TD6 (180->181->...->194)
                           # represent consuming identifier characters.
                           # We can simplify this in code by staying in a 'building' state.
                           # Let's check for keyword match when a delimiter is hit.
                           state = 277 # Transition to a state that checks for delimiter (based on tokenizer.py)
                           self.advance()
                 elif self.current_char is None or self.current_char in DEL22: # DEL22 is delimiter for identifiers in TD6
                      state = 195 # Final state in TD6
                      if self.current_char is not None:
                           self.step_back() # Step back the delimiter
                 else:
                      errors.append(LexerError(f"Invalid character in identifier: '{self.current_char}'", start_line, start_column))
                      state = 0 # Error state

            elif state == 277: # State in tokenizer.py for continued identifier building
                 if self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      lexeme += self.current_char
                      if len(lexeme) > 25:
                           errors.append(LexerError(f"Identifier '{lexeme}' exceeds maximum length of 25 characters", start_line, start_column))
                           state = 0
                      else:
                           state = 277 # Stay in this state
                           self.advance()
                 elif self.current_char is None or self.current_char in DEL22:
                      state = 278 # Final state in tokenizer.py
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in identifier: '{self.current_char}'", start_line, start_column))
                      state = 0

            elif state == 195 or state == 278: # Final states for identifier/keyword
                 # Check if the lexeme is a keyword
                 keywords = {
                    "bln": TT_BOOL, "dbl": TT_DOUBLE, "dflt": TT_DFLT,
                    "prnt": TT_PRNT, "npt": TT_NPT, "fls": TT_FLS,
                    "cnst": TT_CNST, "fr": TT_FR, "f": TT_F,
                    "lsf": TT_LSF, "nt": TT_INT, "chr": TT_CHAR,
                    "mn": TT_MN, "cs": TT_CS, "npt": TT_NPT, # 'reads' maps to 'npt'
                    "rtrn": TT_RTRN, "fnctn": TT_FNCTN, "swtch": TT_SWTCH,
                    "cntn": TT_CNTN, "strng": TT_STRING, "strct": TT_STRCT,
                    "tr": TT_TR, "d": TT_D, "vd": TT_VD,
                    "whl": TT_WHl, "==": TT_EQTO, "!=": TT_NOTEQ,
                    "nll": TT_NULL # 'notin' maps to 'nll'
                 }
                 token_type = keywords.get(lexeme, TT_IDENTIFIER)
                 tokens.append(Token(token_type, lexeme, start_line, start_column))
                 state = 0 # Return to initial state

            # Number Literal States (TD7)
            elif state >= 197 and state <= 240: # Integer part states in TD7
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      # Check integer length constraint (up to 13 digits based on tokenizer.py state 239, 266)
                      if len(lexeme.lstrip('-')) > 13:
                           errors.append(LexerError(f"Integer literal '{lexeme}' exceeds maximum length of 13 digits", start_line, start_column))
                           state = 0
                      else:
                           state = state + 1 if state < 240 else 240 # Move through states 197-240
                           self.advance()
                 elif self.current_char == '.':
                      state = 241 # Transition to decimal part state
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL17: # DEL17 is delimiter for numbers
                      state = 223 # Final state for integer in TD7
                      if self.current_char is not None:
                           self.step_back() # Step back the delimiter
                 else:
                      errors.append(LexerError(f"Invalid character in integer literal: '{self.current_char}'", start_line, start_column))
                      state = 0

            elif state >= 241 and state <= 266: # Decimal part states in TD7
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      # Check decimal part length constraint (up to 8 digits based on original lexer.py)
                      decimal_part = lexeme.split('.')[-1]
                      if len(decimal_part) > 8:
                           errors.append(LexerError(f"Double literal's decimal part '{decimal_part}' exceeds maximum length of 8 digits", start_line, start_column))
                           state = 0
                      else:
                           state = state + 1 if state < 266 else 266 # Move through states 241-266
                           self.advance()
                 elif self.current_char is None or self.current_char in DEL17: # DEL17 is delimiter for numbers
                      state = 223 # Final state for double in TD7
                      if self.current_char is not None:
                           self.step_back() # Step back the delimiter
                 else:
                      errors.append(LexerError(f"Invalid character in double literal: '{self.current_char}'", start_line, start_column))
                      state = 0

            elif state == 223: # Final state for number literal (integer or double)
                 # Determine if it's integer or double based on lexeme containing '.'
                 if '.' in lexeme:
                      # Double literal
                      # Handle negative zero (e.g., -0.00)
                      if lexeme.startswith('-0.') and all(c == '0' for c in lexeme[3:]):
                           lexeme = lexeme[1:] # Normalize to "0.00..."
                      tokens.append(Token(TT_DOUBLELIT, lexeme, start_line, start_column))
                 else:
                      # Integer literal
                      # Handle negative zero (-0)
                      if lexeme == '-0':
                           lexeme = '0'
                      tokens.append(Token(TT_INTEGERLIT, lexeme, start_line, start_column))
                 state = 0 # Return to initial state

            # Handling of '~' for negative numbers (State 214 in TD7)
            # This transition is from State 0 to 214 on '~' followed by digit/period
            # The logic for consuming digits/period is then handled by states 215 onwards.
            # The token type should reflect negative integer/double.
            # This is implicitly handled by checking if the lexeme starts with '-'
            # in the final state 223.

            # Operators and Delimiters - Need to implement states for multi-character ones
            # Based on TD3, TD4, TD5

            # '+' Operator States (TD3)
            elif state == 100: # Transition from 0 on '+'
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '+'
                      state = 101 # Final state for '+'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '+': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 101: # Tokenize '+'
                 tokens.append(Token(TT_PLUS, lexeme, start_line, start_column))
                 state = 0

            elif state == 102: # Transition from 0 on '+='
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '+='
                      state = 103 # Final state for '+='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '+=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 103: # Tokenize '+='
                 tokens.append(Token(TT_PLUSEQ, lexeme, start_line, start_column))
                 state = 0

            elif state == 104: # Transition from 0 on '++'
                 if self.current_char is None or self.current_char in DEL9: # DEL9 is delimiter for '++'
                      state = 105 # Final state for '++'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '++': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 105: # Tokenize '++'
                 tokens.append(Token(TT_INCREMENT, lexeme, start_line, start_column))
                 state = 0

            # '-' Operator States (TD3)
            elif state == 106: # Transition from 0 on '-'
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '-'
                      state = 107 # Final state for '-'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '-': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 107: # Tokenize '-'
                 tokens.append(Token(TT_MINUS, lexeme, start_line, start_column))
                 state = 0

            elif state == 108: # Transition from 0 on '-='
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '-='
                      state = 109 # Final state for '-='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '-=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 109: # Tokenize '-='
                 tokens.append(Token(TT_MINUSEQ, lexeme, start_line, start_column))
                 state = 0

            elif state == 110: # Transition from 0 on '--'
                 if self.current_char is None or self.current_char in DEL9: # DEL9 is delimiter for '--'
                      state = 111 # Final state for '--'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '--': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 111: # Tokenize '--'
                 tokens.append(Token(TT_DECREMENT, lexeme, start_line, start_column))
                 state = 0

            # '*' Operator States (TD3)
            elif state == 112: # Transition from 0 on '*'
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '*'
                      state = 113 # Final state for '*'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '*': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 113: # Tokenize '*'
                 tokens.append(Token(TT_MUL, lexeme, start_line, start_column))
                 state = 0

            elif state == 148: # Transition from 0 on '*='
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '*='
                      state = 149 # Final state for '*='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '*=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 149: # Tokenize '*='
                 tokens.append(Token(TT_MULTIEQ, lexeme, start_line, start_column))
                 state = 0

            elif state == 150: # Transition from 0 on '**'
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '**'
                      state = 151 # Final state for '**'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '**': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 151: # Tokenize '**'
                 tokens.append(Token(TT_EXP, lexeme, start_line, start_column))
                 state = 0

            # '/' Operator States (TD3)
            elif state == 116: # Transition from 0 on '/'
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '/'
                      state = 117 # Final state for '/'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '/': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 117: # Tokenize '/'
                 tokens.append(Token(TT_DIV, lexeme, start_line, start_column))
                 state = 0

            elif state == 156: # Transition from 0 on '/='
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '/='
                      state = 157 # Final state for '/='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '/=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 157: # Tokenize '/='
                 tokens.append(Token(TT_DIVEQ, lexeme, start_line, start_column))
                 state = 0

            # '%' Operator States (TD3)
            elif state == 120: # Transition from 0 on '%'
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '%'
                      state = 121 # Final state for '%'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '%': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 121: # Tokenize '%'
                 tokens.append(Token(TT_MOD, lexeme, start_line, start_column))
                 state = 0

            elif state == 160: # Transition from 0 on '%='
                 if self.current_char is None or self.current_char in DEL24: # DEL24 is delimiter for '%='
                      state = 161 # Final state for '%='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '%=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 161: # Tokenize '%='
                 tokens.append(Token(TT_MODEQ, lexeme, start_line, start_column))
                 state = 0

            # '=' Operator States (TD4)
            elif state == 125: # Transition from 0 on '='
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '='
                      state = 126 # Final state for '='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 126: # Tokenize '='
                 tokens.append(Token(TT_EQ, lexeme, start_line, start_column))
                 state = 0

            elif state == 127: # Transition from 0 on '=='
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '=='
                      state = 128 # Final state for '=='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '==': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 128: # Tokenize '=='
                 tokens.append(Token(TT_EQTO, lexeme, start_line, start_column))
                 state = 0

            # '>' Operator States (TD4)
            elif state == 129: # Transition from 0 on '>'
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '>'
                      state = 130 # Final state for '>'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '>': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 130: # Tokenize '>'
                 tokens.append(Token(TT_GT, lexeme, start_line, start_column))
                 state = 0

            elif state == 131: # Transition from 0 on '>='
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '>='
                      state = 132 # Final state for '>='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '>=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 132: # Tokenize '>='
                 tokens.append(Token(TT_GTEQ, lexeme, start_line, start_column))
                 state = 0

            # '<' Operator States (TD4)
            elif state == 133: # Transition from 0 on '<'
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '<'
                      state = 134 # Final state for '<'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '<': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 134: # Tokenize '<'
                 tokens.append(Token(TT_LT, lexeme, start_line, start_column))
                 state = 0

            elif state == 135: # Transition from 0 on '<='
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '<='
                      state = 136 # Final state for '<='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '<=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 136: # Tokenize '<='
                 tokens.append(Token(TT_LTEQ, lexeme, start_line, start_column))
                 state = 0

            # '!' Operator States (TD4)
            elif state == 137: # Transition from 0 on '!'
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '!'
                      state = 138 # Final state for '!'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '!': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 138: # Tokenize '!'
                 tokens.append(Token(TT_NOT, lexeme, start_line, start_column))
                 state = 0

            elif state == 139: # Transition from 0 on '!='
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '!='
                      state = 140 # Final state for '!='
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '!=': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 140: # Tokenize '!='
                 tokens.append(Token(TT_NOTEQ, lexeme, start_line, start_column))
                 state = 0

            # '&' Operator States (TD5)
            elif state == 170: # Transition from 0 on '&' (Error state in TD5)
                 # This state is reached on a single '&', which is an error based on TD5
                 errors.append(LexerError(f"Illegal character: '{lexeme}'", start_line, start_column))
                 state = 0

            elif state == 171: # Transition from 0 on '&&'
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '&&'
                      state = 172 # Final state for '&&'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '&&': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 172: # Tokenize '&&'
                 tokens.append(Token(TT_AND, lexeme, start_line, start_column))
                 state = 0

            # '|' Operator States (TD5)
            elif state == 173: # Transition from 0 on '|' (Error state in TD5)
                 # This state is reached on a single '|', which is an error based on TD5
                 errors.append(LexerError(f"Illegal character: '{lexeme}'", start_line, start_column))
                 state = 0

            elif state == 174: # Transition from 0 on '||'
                 if self.current_char is None or self.current_char in DEL25: # DEL25 is delimiter for '||'
                      state = 175 # Final state for '||'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '||': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 175: # Tokenize '||'
                 tokens.append(Token(TT_OR, lexeme, start_line, start_column))
                 state = 0

            # ',' Delimiter States (TD5)
            elif state == 157: # Transition from 0 on ','
                 if self.current_char is None or self.current_char in DEL20: # DEL20 is delimiter for ','
                      state = 158 # Final state for ','
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after ',': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 158: # Tokenize ','
                 tokens.append(Token(TT_COMMA, lexeme, start_line, start_column))
                 state = 0

            # ':' Delimiter States (TD4)
            elif state == 141: # Transition from 0 on ':'
                 if self.current_char is None or self.current_char in DEL11: # DEL11 is delimiter for ':'
                      state = 142 # Final state for ':'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after ':': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 142: # Tokenize ':'
                 tokens.append(Token(TT_COLON, lexeme, start_line, start_column))
                 state = 0

            # ';' Delimiter States (TD4)
            elif state == 143: # Transition from 0 on ';'
                 if self.current_char is None or self.current_char in DEL11: # DEL11 is delimiter for ';'
                      state = 144 # Final state for ';'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after ';': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 144: # Tokenize ';'
                 tokens.append(Token(TT_SEMICOLON, lexeme, start_line, start_column))
                 state = 0

            # '(' Delimiter States (TD5)
            elif state == 153: # Transition from 0 on '('
                 if self.current_char is None or self.current_char in DEL16: # DEL16 is delimiter for '('
                      state = 154 # Final state for '('
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '(': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 154: # Tokenize '('
                 tokens.append(Token(TT_LPAREN, lexeme, start_line, start_column))
                 state = 0

            # ')' Delimiter States (TD5)
            elif state == 155: # Transition from 0 on ')'
                 if self.current_char is None or self.current_char in DEL18: # DEL18 is delimiter for ')'
                      state = 156 # Final state for ')'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after ')': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 156: # Tokenize ')'
                 tokens.append(Token(TT_RPAREN, lexeme, start_line, start_column))
                 state = 0

            # '[' Delimiter States (TD4)
            elif state == 145: # Transition from 0 on '['
                 if self.current_char is None or self.current_char in DEL12: # DEL12 is delimiter for '['
                      state = 146 # Final state for '['
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '[': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 146: # Tokenize '['
                 tokens.append(Token(TT_LSQBR, lexeme, start_line, start_column))
                 state = 0

            # ']' Delimiter States (TD4)
            elif state == 147: # Transition from 0 on ']'
                 if self.current_char is None or self.current_char in DEL13: # DEL13 is delimiter for ']'
                      state = 148 # Final state for ']'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after ']': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 148: # Tokenize ']'
                 tokens.append(Token(TT_RSQBR, lexeme, start_line, start_column))
                 state = 0

            # '{' Delimiter States (TD4)
            elif state == 149: # Transition from 0 on '{'
                 if self.current_char is None or self.current_char in DEL14: # DEL14 is delimiter for '{'
                      state = 150 # Final state for '{'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '{{': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 150: # Tokenize '{'
                 tokens.append(Token(TT_BLOCK_START, lexeme, start_line, start_column))
                 state = 0

            # '}' Delimiter States (TD5)
            elif state == 151: # Transition from 0 on '}'
                 if self.current_char is None or self.current_char in DEL15: # DEL15 is delimiter for '}'
                      state = 152 # Final state for '}'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '}}': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 152: # Tokenize '}'
                 tokens.append(Token(TT_BLOCK_END, lexeme, start_line, start_column))
                 state = 0

            # '.' Delimiter States (TD5)
            elif state == 176: # Transition from 0 on '.'
                 if self.current_char is not None and self.current_char in ALPHA: # Transition on alpha
                      state = 177 # Final state for '.'
                      # The alpha character is the start of the next token, so step back
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character after '.': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 177: # Tokenize '.'
                 tokens.append(Token(TT_STRCTACCESS, lexeme, start_line, start_column))
                 state = 0

            # '`' Delimiter States (TD5)
            elif state == 178: # Transition from 0 on '`'
                 if self.current_char is None or self.current_char in DEL27: # DEL27 is delimiter for '`'
                      state = 179 # Final state for '`'
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after '`': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 179: # Tokenize '`'
                 tokens.append(Token(TT_CONCAT, lexeme, start_line, start_column))
                 state = 0

            # --- Keyword and Identifier States (TD1, TD2, TD6) ---
            # Starting state 180 is handled in state 0.
            # States 180-194 are for consuming identifier characters.
            # State 277 is also for consuming identifier characters (from tokenizer.py)
            # States 195 and 278 are final states for identifiers/keywords.

            # States for 'b' -> 'bln' (TD1)
            elif state == 1: # from 0 on 'b'
                if self.current_char == 'o':
                    state = 2
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277 # Transition to general identifier state
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278 # Final state for identifier
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 2: # from 1 on 'o'
                if self.current_char == 'o':
                    state = 3
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 3: # from 2 on 'o'
                if self.current_char == 'l':
                    state = 4
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 4: # from 3 on 'l' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 5 # Final state for 'bln'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'bln': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 5: # Final state for 'bln'
                 tokens.append(Token(TT_BOOL, lexeme, start_line, start_column))
                 state = 0

            # States for 'b' -> 'brk' (TD1)
            elif state == 6: # from 1 on 'r'
                if self.current_char == 'k':
                    state = 7
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 7: # from 6 on 'k' - Expecting DEL2
                 if self.current_char is None or self.current_char in DEL2:
                      state = 8 # Final state for 'brk'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'brk': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 8: # Final state for 'brk'
                 tokens.append(Token(TT_BRK, lexeme, start_line, start_column))
                 state = 0

            # States for 'c' -> 'chr' (TD1)
            elif state == 9: # from 0 on 'c'
                if self.current_char == 'h':
                    state = 10
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 10: # from 9 on 'h'
                if self.current_char == 'r':
                    state = 11
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 11: # from 10 on 'r' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 12 # Final state for 'chr'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'chr': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 12: # Final state for 'chr'
                 tokens.append(Token(TT_CHAR, lexeme, start_line, start_column))
                 state = 0

            # States for 'c' -> 'cnst' (TD1)
            elif state == 13: # from 9 on 'n'
                if self.current_char == 's':
                    state = 14
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 14: # from 13 on 's'
                if self.current_char == 't':
                    state = 15
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 15: # from 14 on 't' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 16 # Final state for 'cnst'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'cnst': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 16: # Final state for 'cnst'
                 tokens.append(Token(TT_CNST, lexeme, start_line, start_column))
                 state = 0

            # States for 'c' -> 'cntn' (TD1)
            elif state == 17: # from 9 on 'o'
                if self.current_char == 'n':
                    state = 18
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 18: # from 17 on 'n'
                if self.current_char == 't':
                    state = 19
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 19: # from 18 on 't'
                if self.current_char == 'n':
                    state = 20
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 20: # from 19 on 'n' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 21 # Final state for 'cntn'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'cntn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 21: # Final state for 'cntn'
                 tokens.append(Token(TT_CNTN, lexeme, start_line, start_column))
                 state = 0

            # States for 'd' -> 'dbl' (TD1)
            elif state == 22: # from 0 on 'd'
                if self.current_char == 'b':
                    state = 23
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 23: # from 22 on 'b'
                if self.current_char == 'l':
                    state = 24
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 24: # from 23 on 'l' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 25 # Final state for 'dbl'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'dbl': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 25: # Final state for 'dbl'
                 tokens.append(Token(TT_DOUBLE, lexeme, start_line, start_column))
                 state = 0

            # States for 'd' -> 'dflt' (TD1)
            elif state == 26: # from 22 on 'f'
                if self.current_char == 'l':
                    state = 27
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 27: # from 26 on 'l'
                if self.current_char == 't':
                    state = 28
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 28: # from 27 on 't' - Expecting DEL4
                 if self.current_char is None or self.current_char in DEL4:
                      state = 29 # Final state for 'dflt'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'dflt': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 29: # Final state for 'dflt'
                 tokens.append(Token(TT_DFLT, lexeme, start_line, start_column))
                 state = 0

            # States for 'd' -> 'dfstrct' (TD1)
            elif state == 30: # from 22 on 's'
                if self.current_char == 't':
                    state = 31
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 31: # from 30 on 't'
                if self.current_char == 'r':
                    state = 32
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 32: # from 31 on 'r'
                if self.current_char == 'c':
                    state = 33
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 33: # from 32 on 'c'
                if self.current_char == 't':
                    state = 34
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 34: # from 33 on 't' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 35 # Final state for 'dfstrct'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'dfstrct': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 35: # Final state for 'dfstrct'
                 tokens.append(Token(TT_DFSTRCT, lexeme, start_line, start_column))
                 state = 0

            # States for 'e' -> 'end' (TD1)
            elif state == 36: # from 0 on 'e'
                if self.current_char == 'n':
                    state = 37
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 37: # from 36 on 'n'
                if self.current_char == 'd':
                    state = 38
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 38: # from 37 on 'd' - Expecting DEL2
                 if self.current_char is None or self.current_char in DEL2:
                      state = 39 # Final state for 'end'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'end': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 39: # Final state for 'end'
                 tokens.append(Token(TT_END, lexeme, start_line, start_column))
                 state = 0

            # States for 'f' -> 'f' (TD1)
            elif state == 40: # from 0 on 'f'
                # Expecting DEL5
                 if self.current_char is None or self.current_char in DEL5:
                      state = 41 # Final state for 'f'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'f': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 41: # Final state for 'f'
                 tokens.append(Token(TT_F, lexeme, start_line, start_column))
                 state = 0

            # States for 'f' -> 'fls' (TD1)
            elif state == 42: # from 40 on 'l'
                if self.current_char == 's':
                    state = 43
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 43: # from 42 on 's' - Expecting DEL6
                 if self.current_char is None or self.current_char in DEL6:
                      state = 44 # Final state for 'fls'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'fls': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 44: # Final state for 'fls'
                 tokens.append(Token(TT_FLS, lexeme, start_line, start_column))
                 state = 0

            # States for 'f' -> 'fnctn' (TD1)
            elif state == 45: # from 40 on 'n'
                if self.current_char == 'c':
                    state = 46
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 46: # from 45 on 'c'
                if self.current_char == 't':
                    state = 47
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 47: # from 46 on 't'
                if self.current_char == 'n':
                    state = 48
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 48: # from 47 on 'n' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 49 # Final state for 'fnctn'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'fnctn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 49: # Final state for 'fnctn'
                 tokens.append(Token(TT_FNCTN, lexeme, start_line, start_column))
                 state = 0

            # States for 'f' -> 'fr' (TD1)
            elif state == 50: # from 40 on 'r' - Expecting DEL5
                 if self.current_char is None or self.current_char in DEL5:
                      state = 51 # Final state for 'fr'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'fr': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 51: # Final state for 'fr'
                 tokens.append(Token(TT_FR, lexeme, start_line, start_column))
                 state = 0

            # States for 'l' -> 'ls' (TD2)
            elif state == 52: # from 0 on 'l'
                if self.current_char == 's':
                    state = 53
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 53: # from 52 on 's' - Expecting DEL3
                 if self.current_char is None or self.current_char in DEL3:
                      state = 54 # Final state for 'ls'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'ls': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 54: # Final state for 'ls'
                 tokens.append(Token(TT_LS, lexeme, start_line, start_column))
                 state = 0

            # States for 'l' -> 'lsf' (TD2)
            elif state == 55: # from 52 on 's'
                if self.current_char == 'f':
                    state = 56
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 56: # from 55 on 'f' - Expecting DEL5
                 if self.current_char is None or self.current_char in DEL5:
                      state = 57 # Final state for 'lsf'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'lsf': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 57: # Final state for 'lsf'
                 tokens.append(Token(TT_LSF, lexeme, start_line, start_column))
                 state = 0

            # States for 'm' -> 'mn' (TD2)
            elif state == 58: # from 0 on 'm'
                if self.current_char == 'n':
                    state = 59
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 59: # from 58 on 'n' - Expecting DEL7
                 if self.current_char is None or self.current_char in DEL7:
                      state = 60 # Final state for 'mn'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'mn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 60: # Final state for 'mn'
                 tokens.append(Token(TT_MN, lexeme, start_line, start_column))
                 state = 0

            # States for 'n' -> 'npt' (TD2)
            elif state == 61: # from 0 on 'n'
                if self.current_char == 'p':
                    state = 62
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 62: # from 61 on 'p'
                if self.current_char == 't':
                    state = 63
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 63: # from 62 on 't' - Expecting DEL7
                 if self.current_char is None or self.current_char in DEL7:
                      state = 64 # Final state for 'npt'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'npt': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 64: # Final state for 'npt'
                 tokens.append(Token(TT_NPT, lexeme, start_line, start_column))
                 state = 0

            # States for 'n' -> 'nt' (TD2)
            elif state == 65: # from 61 on 't'
                # Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 66 # Final state for 'nt'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'nt': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 66: # Final state for 'nt'
                 tokens.append(Token(TT_INT, lexeme, start_line, start_column))
                 state = 0

            # States for 'p' -> 'prnt' (TD2)
            elif state == 67: # from 0 on 'p'
                if self.current_char == 'r':
                    state = 68
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 68: # from 67 on 'r'
                if self.current_char == 'n':
                    state = 69
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 69: # from 68 on 'n'
                if self.current_char == 't':
                    state = 70
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 70: # from 69 on 't' - Expecting DEL7
                 if self.current_char is None or self.current_char in DEL7:
                      state = 71 # Final state for 'prnt'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'prnt': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 71: # Final state for 'prnt'
                 tokens.append(Token(TT_PRNT, lexeme, start_line, start_column))
                 state = 0

            # States for 'r' -> 'rtrn' (TD2)
            elif state == 72: # from 0 on 'r'
                if self.current_char == 't':
                    state = 73
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 73: # from 72 on 't'
                if self.current_char == 'r':
                    state = 74
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 74: # from 73 on 'r'
                if self.current_char == 'n':
                    state = 75
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 75: # from 74 on 'n' - Expecting DEL8
                 if self.current_char is None or self.current_char in DEL8:
                      state = 76 # Final state for 'rtrn'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'rtrn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 76: # Final state for 'rtrn'
                 tokens.append(Token(TT_RTRN, lexeme, start_line, start_column))
                 state = 0

            # States for 's' -> 'swtch' (TD2)
            elif state == 77: # from 0 on 's'
                if self.current_char == 'w':
                    state = 78
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 78: # from 77 on 'w'
                if self.current_char == 't':
                    state = 79
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 79: # from 78 on 't'
                if self.current_char == 'c':
                    state = 80
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 80: # from 79 on 'c'
                if self.current_char == 'h':
                    state = 81
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 81: # from 80 on 'h' - Expecting DEL5
                 if self.current_char is None or self.current_char in DEL5:
                      state = 82 # Final state for 'swtch'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'swtch': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 82: # Final state for 'swtch'
                 tokens.append(Token(TT_SWTCH, lexeme, start_line, start_column))
                 state = 0

            # States for 's' -> 'strng' (TD2)
            elif state == 83: # from 77 on 't'
                if self.current_char == 'r':
                    state = 84
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 84: # from 83 on 'r'
                if self.current_char == 'n':
                    state = 85
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 85: # from 84 on 'n'
                if self.current_char == 'g':
                    state = 86
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 86: # from 85 on 'g' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 87 # Final state for 'strng'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'strng': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 87: # Final state for 'strng'
                 tokens.append(Token(TT_STRING, lexeme, start_line, start_column))
                 state = 0

            # States for 't' -> 'tr' (TD2)
            elif state == 88: # from 0 on 't'
                if self.current_char == 'r':
                    state = 89
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 89: # from 88 on 'r' - Expecting DEL6
                 if self.current_char is None or self.current_char in DEL6:
                      state = 90 # Final state for 'tr'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'tr': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 90: # Final state for 'tr'
                 tokens.append(Token(TT_TR, lexeme, start_line, start_column))
                 state = 0

            # States for 'v' -> 'vd' (TD2)
            elif state == 91: # from 0 on 'v'
                if self.current_char == 'd':
                    state = 92
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 92: # from 91 on 'd' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 93 # Final state for 'vd'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'vd': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 93: # Final state for 'vd'
                 tokens.append(Token(TT_VD, lexeme, start_line, start_column))
                 state = 0

            # States for 'w' -> 'whl' (TD2)
            elif state == 94: # from 0 on 'w'
                if self.current_char == 'h':
                    state = 95
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 95: # from 94 on 'h'
                if self.current_char == 'l':
                    state = 96
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 96: # from 95 on 'l' - Expecting DEL5
                 if self.current_char is None or self.current_char in DEL5:
                      state = 97 # Final state for 'whl'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'whl': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 97: # Final state for 'whl'
                 tokens.append(Token(TT_WHl, lexeme, start_line, start_column))
                 state = 0

            # States for 'd' -> 'd' (TD1)
            elif state == 98: # from 22 on 'd' - Expecting DEL3
                 if self.current_char is None or self.current_char in DEL3:
                      state = 99 # Final state for 'd'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'd': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 99: # Final state for 'd'
                 tokens.append(Token(TT_D, lexeme, start_line, start_column))
                 state = 0

            # States for 'n' -> 'nll' (TD2)
            elif state == 188: # from 0 on 'n'
                if self.current_char == 'l':
                    state = 189
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 189: # from 188 on 'l'
                if self.current_char == 'l':
                    state = 190
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 190: # from 189 on 'l' - Expecting DEL22
                 if self.current_char is None or self.current_char in DEL22:
                      state = 196 # Final state for 'nll' (based on TD6)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'nll': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 196: # Final state for 'nll' (based on TD6)
                 tokens.append(Token(TT_NULL, lexeme, start_line, start_column))
                 state = 0

            # States for 'i' -> 'nt' (TD1) - Already implemented (States 65, 66)

            # States for 't' -> 'strct' (TD1) - Needs clarification, 'strct' starts with 's'
            # Assuming this was a typo and 'strct' starts with 's' as in original lexer.py
            # States for 's' -> 'strct' (TD2)
            elif state == 83: # from 77 on 't'
                if self.current_char == 'r':
                    state = 84
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            # ... states 84, 85, 86, 87 already implemented for 'strng'

            # States for 'd' -> 'dfstrct' (TD1) - Already implemented (States 30-35)

            # States for 'c' -> 'cs' (TD1)
            elif state == 8: # from 9 on 'i'
                if self.current_char == 's':
                    state = 9 # This state number seems wrong based on TD1. Let's use a new state.
                    state = 287 # New state for 'cs'
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 287: # New state for 'cs' - Expecting DEL26
                 if self.current_char is None or self.current_char in DEL26:
                      state = 288 # Final state for 'cs'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'cs': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 288: # Final state for 'cs'
                 tokens.append(Token(TT_CS, lexeme, start_line, start_column))
                 state = 0


            # --- Number Literal States (TD7) - Continued Implementation ---
            # Starting state 197 is handled in state 0.
            # States 197-240 are for integer part.
            # States 241-266 are for decimal part.
            # State 223 is final state for numbers.
            # State 214 is for negative sign.

            # States for integer part (197-240) - Already have a simplified range check.
            # Let's add explicit states for better clarity and strictness based on TD7
            elif state == 197: # from 0 on digit or ~digit
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      state = 198
                      self.advance()
                 elif self.current_char == '.':
                      state = 241
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL17:
                      state = 223
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in number: '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state >= 198 and state <= 211: # Consuming more digits for integer part
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      state += 1
                      self.advance()
                 elif self.current_char == '.':
                      state = 241
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL17:
                      state = 223
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in number: '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 212: # State 212 in TD7 seems to be a final state for 0
                 if self.current_char is None or self.current_char in DEL17:
                      state = 213 # Final state for 0
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char == '.':
                      state = 241
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid character after 0: '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 213: # Final state for integer 0
                 tokens.append(Token(TT_INTEGERLIT, '0', start_line, start_column))
                 state = 0

            elif state == 214: # from 0 on '~' followed by digit/period
                 if self.current_char is not None and self.current_char in DIGIT:
                      lexeme += self.current_char
                      state = 215
                      self.advance()
                 elif self.current_char == '.':
                      state = 241
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid character after '~': '{self.current_char}'", start_line, start_column))
                      state = 0

            elif state >= 215 and state <= 222: # Consuming digits after '~'
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      state += 1
                      self.advance()
                 elif self.current_char == '.':
                      state = 241
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL17:
                      state = 223 # Final state for negative integer
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in negative number: '{self.current_char}'", start_line, start_column))
                      state = 0

            # States for decimal part (241-266) - Already have a simplified range check.
            # Let's add explicit states for better clarity and strictness based on TD7
            elif state == 241: # from integer states on '.'
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      state = 242
                      self.advance()
                 else:
                      errors.append(LexerError(f"Missing digit after decimal point: '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state >= 242 and state <= 266: # Consuming digits for decimal part
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      state += 1
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL17:
                      state = 223 # Final state for double
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in decimal part: '{self.current_char}'", start_line, start_column))
                      state = 0

            # State 223 is the final state for both integers and doubles, handled above.

            # --- Remaining Keyword States (TD1, TD2) ---
            # Need to add states for:
            # d -> d (98, 99) - Added
            # e -> els (27-31) - Needs implementation
            # e -> elsif (32-35) - Needs implementation
            # s -> scope (90-95) - Needs implementation
            # s -> select (96-101) - Needs implementation
            # t -> task (112-116) - Needs implementation

            # States for 'e' -> 'els' (TD1)
            elif state == 27: # from 0 on 'e'
                if self.current_char == 'l':
                    state = 28
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 28: # from 27 on 'l'
                if self.current_char == 's':
                    state = 29
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 29: # from 28 on 's' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 30 # Final state for 'ls'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'ls': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 30: # Final state for 'ls'
                 tokens.append(Token(TT_LS, lexeme, start_line, start_column))
                 state = 0

            # States for 'e' -> 'elsif' (TD1)
            elif state == 32: # from 29 on 'i'
                if self.current_char == 'f':
                    state = 33
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 33: # from 32 on 'f' - Expecting DEL5
                 if self.current_char is None or self.current_char in DEL5:
                      state = 34 # Final state for 'lsf'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'lsf': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 34: # Final state for 'lsf'
                 tokens.append(Token(TT_LSF, lexeme, start_line, start_column))
                 state = 0

            # States for 's' -> 'scope' (TD1)
            elif state == 90: # from 0 on 's'
                if self.current_char == 'c':
                    state = 91
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 91: # from 90 on 'c'
                if self.current_char == 'o':
                    state = 92
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 92: # from 91 on 'o'
                if self.current_char == 'p':
                    state = 93
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 93: # from 92 on 'p'
                if self.current_char == 'e':
                    state = 94
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 94: # from 93 on 'e' - Expecting DEL7
                 if self.current_char is None or self.current_char in DEL7:
                      state = 95 # Final state for 'fnctn'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'fnctn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 95: # Final state for 'fnctn'
                 tokens.append(Token(TT_FNCTN, lexeme, start_line, start_column))
                 state = 0

            # States for 's' -> 'select' (TD1)
            elif state == 96: # from 90 on 'e'
                if self.current_char == 'l':
                    state = 97
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 97: # from 96 on 'l'
                if self.current_char == 'e':
                    state = 98
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 98: # from 97 on 'e'
                if self.current_char == 'c':
                    state = 99
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 99: # from 98 on 'c'
                if self.current_char == 't':
                    state = 100 # This state number is used for '+', needs new state
                    state = 289 # New state for 'select'
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 289: # New state for 'select' - Expecting DEL5
                 if self.current_char is None or self.current_char in DEL5:
                      state = 290 # Final state for 'swtch'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'swtch': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 290: # Final state for 'swtch'
                 tokens.append(Token(TT_SWTCH, lexeme, start_line, start_column))
                 state = 0

            # States for 't' -> 'task' (TD1)
            elif state == 112: # from 0 on 't'
                if self.current_char == 'a':
                    state = 113
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 113: # from 112 on 'a'
                if self.current_char == 's':
                    state = 114
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 114: # from 113 on 's'
                if self.current_char == 'k':
                    state = 115
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    state = 277
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL22:
                    state = 278
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in token: '{self.current_char}'", start_line, start_column))
                    state = 0
            elif state == 115: # from 114 on 'k' - Expecting DEL1
                 if self.current_char is None or self.current_char in DEL1:
                      state = 116 # Final state for 'strct'
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'strct': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 116: # Final state for 'strct'
                 tokens.append(Token(TT_STRCT, lexeme, start_line, start_column))
                 state = 0

            # Let's add the EOF token when processing is finished and state is 0
            if self.current_char is None and state == 0:
                 tokens.append(Token(TT_EOF, 'EOF', self.line, self.column))
                 break # Exit the loop

            # If we are in a non-zero state but current_char is None, it means
            # the input ended unexpectedly while parsing a token.
            if self.current_char is None and state != 0:
                 errors.append(LexerError(f"Unexpected end of input while processing token starting with '{lexeme}'", start_line, start_column))
                 state = 0 # Reset state to avoid infinite loop

        return tokens, errors

# --- Example Usage (for testing) ---
# lexer = Lexer("nt main() { prnt(\"Hello\"); }")
# tokens, errors = lexer.make_tokens()
# if errors:
#     for error in errors:
#         print(error)
# else:
#     for token in tokens:
#         print(token)

# lexer2 = Lexer("dbl num = ~123.456;")
# tokens2, errors2 = lexer2.make_tokens()
# if errors2:
#     for error in errors2:
#         print(error)
# else:
#     for token in tokens2:
#         print(token)

# lexer3 = Lexer("chr char = 'a';")
# tokens3, errors3 = lexer3.make_tokens()
# if errors3:
#     for error in errors3:
#         print(error)
# else:
#     for token in tokens3:
#         print(token)

# lexer4 = Lexer("strng str = \"hello world\";")
# tokens4, errors4 = lexer4.make_tokens()
# if errors4:
#     for error in errors4:
#         print(error)
# else:
#     for token in tokens4:
#         print(token)

# lexer5 = Lexer("f (id > id) { id++; }")
# tokens5, errors5 = lexer5.make_tokens()
# if errors5:
#     for error in errors5:
#         print(error)
# else:
#     for token in tokens5:
#         print(token)