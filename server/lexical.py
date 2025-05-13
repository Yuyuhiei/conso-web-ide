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
TT_CONCAT = '`'
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
DEL28 = WHITESPACE | DIGITZERO | ALPHA | {'"', "'", '{'} # Based on RE2 image for DEL28

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
            # Simple column adjustment - assumes not stepping back over a newline
            if self.current_char != '\n' and self.column > 0:
                 self.column -= 1
            self.current_char = self.text[self.pos]


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
                    # Check for specific keyword starting characters and transition
                    if self.current_char == 'b':
                         state = 1 # TD1
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'c':
                         state = 9 # TD1
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'd':
                         state = 22 # TD1
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'e':
                         state = 36 # TD1
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'f':
                         state = 40 # TD1
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'l':
                         state = 52 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'm':
                         state = 58 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'n':
                         state = 61 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'p':
                         state = 67 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'r':
                         state = 72 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 's':
                         state = 77 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 't':
                         state = 88 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'v':
                         state = 91 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    elif self.current_char == 'w':
                         state = 94 # TD2
                         lexeme += self.current_char
                         self.advance()
                         continue
                    else:
                         # If it starts with alpha but not a keyword starting char, it's an identifier
                         state = 180 # Starting state for identifiers in TD6
                         lexeme += self.current_char
                         self.advance()
                         continue


                # Numbers (Starts with Digit or ~ followed by Digit) - TD7
                if self.current_char in DIGITZERO or (self.current_char == '~' and self.peek() in DIGITZERO):
                    state = 195 # Starting state for numbers in TD7 (from 0 on ~ or digitzero)
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
                      state = 164 # Transition to character consumed state (TD5)
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid character in character literal: '{self.current_char}'", start_line, start_column))
                      state = 0 # Error, return to initial state

            elif state == 164: # from 163 on character/escape - Expecting closing single quote (TD5)
                 if self.current_char == "'":
                      state = 165 # Transition to final state (TD5)
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Expected closing single quote for character literal (found '{self.current_char}')", start_line, start_column))
                      state = 0 # Error, return to initial state

            elif state == 165: # Final state for character literal (TD5)
                 if self.current_char is None or self.current_char in DEL26: # DEL26 is delimiter for char literal
                      state = 166 # Tokenize state (TD5)
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after character literal: '{self.current_char}'", start_line, start_column))
                      state = 0 # Error, return to initial state

            elif state == 166: # Tokenize character literal (TD5)
                 token_value = lexeme[1:-1]
                 tokens.append(Token(TT_CHARLIT, token_value, start_line, start_column))
                 state = 0 # Return to initial state

            elif state == 294: # Escape sequence in character literal (Assuming new state based on tokenizer.py)
                 escape_map = {"'": "'", "\\": "\\", "n": "\n", "t": "\t", "r": "\r", '0': '\0', '"': '"'}
                 if self.current_char is None:
                      errors.append(LexerError("Unterminated escape sequence in character literal", start_line, start_column))
                      state = 0
                 elif self.current_char in escape_map:
                      state = 164 # Transition back to character consumed state (TD5)
                      lexeme += self.current_char
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
                      state = 168 # Transition to closing quote state (TD5)
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char == '\\':
                      state = 272 # Transition to escape sequence state (TD5)
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


            elif state == 168: # from 167 on '"' - Final state for string literal (TD5)
                 if self.current_char is None or self.current_char in DEL19: # DEL19 is delimiter for string literal
                      state = 169 # Tokenize state (TD5)
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after string literal: '{self.current_char}'", start_line, start_column))
                      state = 0 # Error, return to initial state

            elif state == 169: # Tokenize string literal (TD5)
                 token_value = lexeme[1:-1]
                 # Handle empty string case
                 if token_value == "":
                      token_value = "empty" # Based on tokenizer.py output for empty string ""
                 tokens.append(Token(TT_STRINGLIT, token_value, start_line, start_column))
                 state = 0 # Return to initial state

            elif state == 272: # Escape sequence in string literal (TD5)
                 escape_map = {"'": "'", "\\": "\\", "n": "\n", "t": "\t", "r": "\r", '0': '\0', '"': '"'}
                 if self.current_char is None:
                      errors.append(LexerError("Unterminated escape sequence in string literal", start_line, start_column))
                      state = 0
                 elif self.current_char in escape_map:
                      state = 167 # Transition back to string char consumption (TD5)
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid escape sequence in string literal: \\{self.current_char}", start_line, start_column))
                      state = 0


            # Identifier and Keyword States (TD6, TD1, TD2)
            # Starting state 180 is handled in state 0 (for general alpha).
            # States 180-194 are for consuming identifier characters.
            # State 277 is also for consuming identifier characters (from tokenizer.py)
            # States 195 and 278 are final states for identifiers/keywords.

            # States for 'b' -> 'bln' (TD1)
            elif state == 1: # from 0 on 'b'
                if self.current_char == 'l': # Corrected transition
                    state = 2 # Corrected next state
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
            elif state == 2: # from 1 on 'l' (Corrected)
                if self.current_char == 'n': # Corrected transition
                    state = 3 # Corrected next state
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
            elif state == 3: # from 2 on 'n' (Corrected) - Expecting DEL1 (TD1)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 4 # Final state for 'bln' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'bln': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 4: # Final state for 'bln' (TD1)
                 tokens.append(Token(TT_BOOL, lexeme, start_line, start_column))
                 state = 0

            # States for 'b' -> 'brk' (TD1)
            elif state == 5: # from 1 on 'r' (Corrected state number based on TD1)
                if self.current_char == 'k':
                    state = 6 # Corrected next state
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
            elif state == 6: # from 5 on 'k' (Corrected) - Expecting DEL2 (TD1)
                 if self.current_char is None or self.current_char in DEL2:
                      state = 7 # Final state for 'brk' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'brk': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 7: # Final state for 'brk' (TD1)
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
            elif state == 11: # from 10 on 'r' - Expecting DEL1 (TD1)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 12 # Final state for 'chr' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'chr': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 12: # Final state for 'chr' (TD1)
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
            elif state == 15: # from 14 on 't' - Expecting DEL1 (TD1)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 16 # Final state for 'cnst' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'cnst': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 16: # Final state for 'cnst' (TD1)
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
            elif state == 20: # from 19 on 'n' - Expecting DEL1 (TD1)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 21 # Final state for 'cntn' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'cntn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 21: # Final state for 'cntn' (TD1)
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
            elif state == 24: # from 23 on 'l' - Expecting DEL1 (TD1)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 25 # Final state for 'dbl' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'dbl': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 25: # Final state for 'dbl' (TD1)
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
            elif state == 28: # from 27 on 't' - Expecting DEL4 (TD1)
                 if self.current_char is None or self.current_char in DEL4:
                      state = 29 # Final state for 'dflt' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'dflt': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 29: # Final state for 'dflt' (TD1)
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
            elif state == 34: # from 33 on 't' - Expecting DEL1 (TD1)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 35 # Final state for 'dfstrct' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'dfstrct': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 35: # Final state for 'dfstrct' (TD1)
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
            elif state == 38: # from 37 on 'd' - Expecting DEL2 (TD1)
                 if self.current_char is None or self.current_char in DEL2:
                      state = 39 # Final state for 'end' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'end': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 39: # Final state for 'end' (TD1)
                 tokens.append(Token(TT_END, lexeme, start_line, start_column))
                 state = 0

            # States for 'f' -> 'f' (TD1)
            elif state == 40: # from 0 on 'f'
                # Expecting DEL5 (TD1)
                 if self.current_char is None or self.current_char in DEL5:
                      state = 41 # Final state for 'f' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'f': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 41: # Final state for 'f' (TD1)
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
            elif state == 43: # from 42 on 's' - Expecting DEL6 (TD1)
                 if self.current_char is None or self.current_char in DEL6:
                      state = 44 # Final state for 'fls' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'fls': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 44: # Final state for 'fls' (TD1)
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
            elif state == 48: # from 47 on 'n' - Expecting DEL1 (TD1)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 49 # Final state for 'fnctn' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'fnctn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 49: # Final state for 'fnctn' (TD1)
                 tokens.append(Token(TT_FNCTN, lexeme, start_line, start_column))
                 state = 0

            # States for 'f' -> 'fr' (TD1)
            elif state == 50: # from 40 on 'r' - Expecting DEL5 (TD1)
                 if self.current_char is None or self.current_char in DEL5:
                      state = 51 # Final state for 'fr' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'fr': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 51: # Final state for 'fr' (TD1)
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
            elif state == 53: # from 52 on 's' - Expecting DEL3 (TD2)
                 if self.current_char is None or self.current_char in DEL3:
                      state = 54 # Final state for 'ls' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'ls': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 54: # Final state for 'ls' (TD2)
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
            elif state == 56: # from 55 on 'f' - Expecting DEL5 (TD2)
                 if self.current_char is None or self.current_char in DEL5:
                      state = 57 # Final state for 'lsf' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'lsf': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 57: # Final state for 'lsf' (TD2)
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
            elif state == 59: # from 58 on 'n' - Expecting DEL7 (TD2)
                 if self.current_char is None or self.current_char in DEL7:
                      state = 60 # Final state for 'mn' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'mn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 60: # Final state for 'mn' (TD2)
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
            elif state == 63: # from 62 on 't' - Expecting DEL7 (TD2)
                 if self.current_char is None or self.current_char in DEL7:
                      state = 64 # Final state for 'npt' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'npt': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 64: # Final state for 'npt' (TD2)
                 tokens.append(Token(TT_NPT, lexeme, start_line, start_column))
                 state = 0

            # States for 'n' -> 'nt' (TD2)
            elif state == 65: # from 61 on 't' - Expecting DEL1 (TD2)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 66 # Final state for 'nt' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'nt': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 66: # Final state for 'nt' (TD2)
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
            elif state == 70: # from 69 on 't' - Expecting DEL7 (TD2)
                 if self.current_char is None or self.current_char in DEL7:
                      state = 71 # Final state for 'prnt' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'prnt': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 71: # Final state for 'prnt' (TD2)
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
            elif state == 75: # from 74 on 'n' - Expecting DEL8 (TD2)
                 if self.current_char is None or self.current_char in DEL8:
                      state = 76 # Final state for 'rtrn' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'rtrn': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 76: # Final state for 'rtrn' (TD2)
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
            elif state == 81: # from 80 on 'h' - Expecting DEL5 (TD2)
                 if self.current_char is None or self.current_char in DEL5:
                      state = 82 # Final state for 'swtch' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'swtch': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 82: # Final state for 'swtch' (TD2)
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
            elif state == 86: # from 85 on 'g' - Expecting DEL1 (TD2)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 87 # Final state for 'strng' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'strng': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 87: # Final state for 'strng' (TD2)
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
            elif state == 89: # from 88 on 'r' - Expecting DEL6 (TD2)
                 if self.current_char is None or self.current_char in DEL6:
                      state = 90 # Final state for 'tr' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'tr': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 90: # Final state for 'tr' (TD2)
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
            elif state == 92: # from 91 on 'd' - Expecting DEL1 (TD2)
                 if self.current_char is None or self.current_char in DEL1:
                      state = 93 # Final state for 'vd' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'vd': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 93: # Final state for 'vd' (TD2)
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
            elif state == 96: # from 95 on 'l' - Expecting DEL5 (TD2)
                 if self.current_char is None or self.current_char in DEL5:
                      state = 97 # Final state for 'whl' (TD2)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'whl': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 97: # Final state for 'whl' (TD2)
                 tokens.append(Token(TT_WHl, lexeme, start_line, start_column))
                 state = 0

            # States for 'd' -> 'd' (TD1)
            elif state == 98: # from 22 on 'd' - Expecting DEL3 (TD1)
                 if self.current_char is None or self.current_char in DEL3:
                      state = 99 # Final state for 'd' (TD1)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'd': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 99: # Final state for 'd' (TD1)
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
            elif state == 190: # from 189 on 'l' - Expecting DEL22 (TD6)
                 if self.current_char is None or self.current_char in DEL22:
                      state = 196 # Final state for 'nll' (TD6)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'nll': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 196: # Final state for 'nll' (TD6)
                 tokens.append(Token(TT_NULL, lexeme, start_line, start_column))
                 state = 0

            # States for 'i' -> 'nt' (TD1) - Already implemented (States 65, 66)

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
                    state = 287 # New state for 'cs' (based on tokenizer.py)
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
            elif state == 287: # New state for 'cs' - Expecting DEL26 (tokenizer.py)
                 if self.current_char is None or self.current_char in DEL26:
                      state = 288 # Final state for 'cs' (tokenizer.py)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      state = 277
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid delimiter after 'cs': '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state == 288: # Final state for 'cs' (tokenizer.py)
                 tokens.append(Token(TT_CS, lexeme, start_line, start_column))
                 state = 0


            # --- Number Literal States (TD7) ---
            # Starting state 195 is handled in state 0.
            # State 195: from 0 on ~ or digitzero
            elif state == 195:
                if self.current_char is not None and self.current_char in DIGITZERO:
                    lexeme += self.current_char
                    state = 196
                    self.advance()
                elif self.current_char == '.':
                    state = 213 # Transition to state 213 on '.' (TD7)
                    lexeme += self.current_char
                    self.advance()
                elif self.current_char is None or self.current_char in DEL23: # DEL23 is delimiter for numbers (TD7)
                    state = 211 # Final state for integer (TD7)
                    if self.current_char is not None:
                        self.step_back()
                else:
                    errors.append(LexerError(f"Invalid character in number: '{self.current_char}'", start_line, start_column))
                    state = 0

            # States for integer part (196-210)
            elif state >= 196 and state <= 210:
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      state += 1
                      self.advance()
                 elif self.current_char == '.':
                      state = 213 # Transition to state 213 on '.' (TD7)
                      lexeme += self.current_char
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL23: # DEL23 is delimiter for numbers (TD7)
                      state = 211 # Final state for integer (TD7)
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in number: '{self.current_char}'", start_line, start_column))
                      state = 0

            # Final state for integer (TD7)
            elif state == 211:
                 tokens.append(Token(TT_INTEGERLIT, lexeme, start_line, start_column))
                 state = 0

            # State 212 is a final state for the integer literal '0' (TD7)
            elif state == 212:
                 if self.current_char is None or self.current_char in DEL23: # DEL23 is delimiter for numbers (TD7)
                      state = 211 # Transition to the general integer final state (TD7)
                      if self.current_char is not None:
                           self.step_back()
                 elif self.current_char == '.':
                      state = 213 # Transition to state 213 on '.' (TD7)
                      lexeme += self.current_char
                      self.advance()
                 else:
                      errors.append(LexerError(f"Invalid character after '0': '{self.current_char}'", start_line, start_column))
                      state = 0

            # States for decimal part (213-221)
            elif state == 213: # from integer states on '.'
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      state = 214
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL17: # DEL17 is delimiter for numbers (TD7)
                      state = 222 # Final state for double (TD7)
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Missing digit after decimal point: '{self.current_char}'", start_line, start_column))
                      state = 0
            elif state >= 214 and state <= 221: # Consuming digits for decimal part
                 if self.current_char is not None and self.current_char in DIGITZERO:
                      lexeme += self.current_char
                      state += 1
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL17: # DEL17 is delimiter for numbers (TD7)
                      state = 222 # Final state for double (TD7)
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in decimal part: '{self.current_char}'", start_line, start_column))
                      state = 0

            # Final state for double (TD7)
            elif state == 222:
                 tokens.append(Token(TT_DOUBLELIT, lexeme, start_line, start_column))
                 state = 0

            # Handling of '~' for negative numbers (State 195 in TD7 is the start)
            # This is handled by the initial transition from state 0 to 195 on '~' followed by digitzero or '.'
            # The subsequent states (196 onwards for integer part, 213 onwards for decimal part)
            # handle the rest of the number. The negative sign is part of the lexeme.
            # The token type is determined in the final states (211 for integer, 222 for double)
            # based on whether the lexeme starts with '~'.


            # --- Identifier States (TD6) ---
            # Starting state 180 is handled in state 0 (for general alpha).
            # States 180-194 are for consuming identifier characters.
            # State 277 is also for consuming identifier characters (from tokenizer.py)
            # States 195 and 278 are final states for identifiers/keywords.

            elif state == 180: # from 0 on any alpha that doesn't start a keyword
                 if self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      lexeme += self.current_char
                      state = 181 # Transition to next state in identifier sequence (TD6)
                      self.advance()
                 elif self.current_char is None or self.current_char in DEL22: # DEL22 is delimiter for identifiers (TD6)
                      state = 195 # Final state for identifier (TD6)
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in identifier: '{self.current_char}'", start_line, start_column))
                      state = 0

            elif state >= 181 and state <= 194: # Consuming more identifier characters (TD6)
                 if self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                      lexeme += self.current_char
                      # Check identifier length constraint (up to 25 characters based on tokenizer.py)
                      if len(lexeme) > 25:
                           errors.append(LexerError(f"Identifier '{lexeme}' exceeds maximum length of 25 characters", start_line, start_column))
                           state = 0 # Error state, stop processing this token
                      else:
                           state += 1
                           self.advance()
                 elif self.current_char is None or self.current_char in DEL22: # DEL22 is delimiter for identifiers (TD6)
                      state = 195 # Final state for identifier (TD6)
                      if self.current_char is not None:
                           self.step_back()
                 else:
                      errors.append(LexerError(f"Invalid character in identifier: '{self.current_char}'", start_line, start_column))
                      state = 0

            # State 277 and 278 are from tokenizer.py, let's align with TD6 states 180-195
            # We will use 180-195 for identifier processing based on TD6.
            # State 195 is the final state for identifiers in TD6.

            # Final state for identifier (TD6)
            elif state == 195: # This state is also used as a starting state for numbers in TD7, need to differentiate
                 # If the lexeme was started by an alpha character (meaning it's an identifier)
                 if lexeme and lexeme[0] in ALPHA:
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
                 # If the lexeme was started by '~' or digit, it's a number, handled in number states.
                 # If state is 195 and lexeme does not start with alpha, it must be a number state transition.
                 # This indicates an issue with state numbering overlap between TD6 and TD7.
                 # Let's adjust the number states to avoid conflict with identifier states.
                 # TD7 starts numbers from state 195. TD6 ends identifiers in 195.
                 # This overlap needs careful handling or re-numbering in implementation.
                 # Based on the diagrams, state 195 in TD7 is the *start* of a number after initial char.
                 # State 195 in TD6 is a *final* state for identifiers.
                 # This is a direct conflict in state numbering across diagrams.
                 # To resolve this, I will use separate state ranges internally for clarity,
                 # even if the diagrams use overlapping numbers.
                 # Let's keep the TD numbers in comments for reference but use internal logic.
                 # Re-evaluating TD7: State 0 transitions to 195 on ~ or digitzero.
                 # State 195 then transitions to 196 on digitzero or 213 on '.'.
                 # This means 195 is *not* a final state for numbers.
                 # The final states for numbers are 211 (integer) and 222 (double).
                 # State 195 in TD6 *is* a final state for identifiers.
                 # The overlap is manageable if we check the starting character to differentiate.
                 pass # Handled in the number states section

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
