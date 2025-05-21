class LexerError(Exception):
    """Custom exception for lexical errors."""
    def __init__(self, message, line, column):
        super().__init__(message)
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
TT_EQTO = '==' #
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

# Delimiter sets based on RE1.png, RE2.png and referenced in TDs
DEL1 = WHITESPACE
DEL2 = {';'}
DEL3 = WHITESPACE | {'{'}
DEL4 = set()
DEL5 = WHITESPACE | {'('}
DEL6 = WHITESPACE | {',', ';', '=', '>', '<', '!'}
DEL7 = {'('}
DEL8 = WHITESPACE | {';'}
DEL9 = WHITESPACE | ALPHA | {'(', ',', ';', ')'}
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
DEL21_for_tilde_op = WHITESPACE | ALPHA | DIGITZERO | {'(', ';', '{', '}'} 
DEL22 = WHITESPACE | {',', '}', ']', ')', ':', '+', '-', '*', '/', '%', '=', '>', '<', '!', '&', '|'} 
DEL23 = WHITESPACE | {';', ',', '}', ')', '=', '>', '<', '!', '&', '|'} 
DEL24 = WHITESPACE | DIGITZERO | ALPHA | {'~', '('} #
DEL25 = WHITESPACE | DIGITZERO | ALPHA | {'~', '"', "'"} 
DEL26 = WHITESPACE | {';', ',', '}', ')', '=', '>', '<', '!', ':'} 
DEL27 = WHITESPACE | {'"'} 
DEL28 = WHITESPACE | DIGITZERO | ALPHA | {'"', "'", '{'} 

IDENTIFIER_CHARS = ALPHA_NUMERIC | {'_'}
CHAR_CONTENT_CHARS = {chr(i) for i in range(32, 127) if chr(i) not in {"'", '\\'}}
STRING_CONTENT_CHARS = {chr(i) for i in range(32, 127) if chr(i) not in {'"', '\\'}}


class Token:
    def __init__(self, type, value=None, line=0, column=0):
        self.type = type; self.value = value; self.line = line; self.column = column
    def __repr__(self):
        return f'Token({self.type}, {repr(self.value)}, line {self.line}, col {self.column})'

class Lexer:
    def __init__(self, text):
        self.text = text; self.pos = -1; self.current_char = None
        self.line = 1; self.column = 0; self.advance()

    def advance(self):
        if self.current_char == '\n': self.line += 1; self.column = 0
        self.pos += 1
        if self.pos < len(self.text): self.current_char = self.text[self.pos]; self.column += 1
        else: self.current_char = None

    def peek(self, offset=1):
        peek_pos = self.pos + offset
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def step_back(self):
        if self.pos < 0: return
        self.pos -= 1
        if self.pos >=0:
             self.current_char = self.text[self.pos]
             if self.current_char != '\n': self.column -=1
             if self.column < 1 and self.current_char != '\n' : self.column =1 
        else: self.current_char = None; self.pos = -1; self.column = 0

    def make_tokens(self):
        tokens = []; errors = []; state = 0; lexeme = ""
        start_line = 1; start_column = 0
        keywords = { # Keyword mapping
            "bln": TT_BOOL, "brk": TT_BRK, "chr": TT_CHAR, "cst": "TT_CST_DIAGRAM", # TD1 'cst'
            "cntn": TT_CNTN, "d": TT_D, "dbl": TT_DOUBLE, "dflt": TT_DFLT,
            "dfstrct": TT_DFSTRCT, "end": TT_END, "f": TT_F, "fls": TT_FLS,
            "fnctn": TT_FNCTN, "fr": TT_FR, "ls": TT_LS, "lsf": TT_LSF, "mn": TT_MN,
            "npt": TT_NPT, "nt": TT_INT, "prnt": TT_PRNT, "rtrn": TT_RTRN,
            "strct": TT_STRCT, "strng": TT_STRING, "swtch": TT_SWTCH,
            "tr": TT_TR, "vd": TT_VD, "whl": TT_WHl,
            "nll": TT_NULL, "cnst": TT_CNST, "cs": TT_CS # User's original keywords
        }

        while self.current_char is not None or state != 0:
            if state == 0: # Initial state dispatch
                lexeme = ""; start_line = self.line; start_column = self.column
                if self.current_char is None: break
                if self.current_char in WHITESPACE: self.advance(); continue
                if self.current_char == '#': state = 161; self.advance(); continue # TD5 Comment

                if self.current_char in ALPHA: # Keywords & Identifiers (TD1, TD2, TD6)
                    if self.current_char == 'b': state = 1; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'c': state = 8; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'd': state = 21; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'e': state = 36; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'f': state = 40; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'l': state = 52; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'm': state = 57; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'n': state = 60; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'p': state = 66; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'r': state = 71; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 's': state = 76; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 't': state = 90; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'v': state = 93; lexeme += self.current_char; self.advance(); continue
                    elif self.current_char == 'w': state = 96; lexeme += self.current_char; self.advance(); continue
                    else: state = 180; lexeme += self.current_char; self.advance(); continue # TD6 Identifier

                elif self.current_char == '~': # Could be TD7 number or TD5 operator
                    if self.peek() in DIGITZERO: # Check if part of a number
                        state = 195; lexeme += self.current_char; self.advance(); continue # TD7 Number
                    else: # Standalone tilde operator from TD5
                        state = 159; lexeme += self.current_char; self.advance(); continue
                elif self.current_char in DIGITZERO: # Number starting with digit
                    state = 195; lexeme += self.current_char; self.advance(); continue # TD7 Number
                
                elif self.current_char == '"': state = 167; lexeme += self.current_char; self.advance(); continue # TD5 String
                elif self.current_char == "'": state = 163; lexeme += self.current_char; self.advance(); continue # TD5 Char
                
                elif self.current_char == '+': state = 100; lexeme += self.current_char; self.advance(); continue # TD3
                elif self.current_char == '-': state = 106; lexeme += self.current_char; self.advance(); continue # TD3
                elif self.current_char == '*': state = 112; lexeme += self.current_char; self.advance(); continue # TD3
                elif self.current_char == '/': state = 116; lexeme += self.current_char; self.advance(); continue # TD3
                elif self.current_char == '%': state = 120; lexeme += self.current_char; self.advance(); continue # TD3
                elif self.current_char == '=': state = 125; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == '>': state = 129; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == '<': state = 133; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == '!': state = 137; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == ':': state = 141; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == ';': state = 143; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == '[': state = 145; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == ']': state = 147; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == '{': state = 149; lexeme += self.current_char; self.advance(); continue # TD4
                elif self.current_char == '}': state = 151; lexeme += self.current_char; self.advance(); continue # TD5
                elif self.current_char == '(': state = 153; lexeme += self.current_char; self.advance(); continue # TD5
                elif self.current_char == ')': state = 155; lexeme += self.current_char; self.advance(); continue # TD5
                elif self.current_char == ',': state = 157; lexeme += self.current_char; self.advance(); continue # TD5
                elif self.current_char == '&': state = 170; lexeme += self.current_char; self.advance(); continue # TD5 &&
                elif self.current_char == '|': state = 173; lexeme += self.current_char; self.advance(); continue # TD5 ||
                elif self.current_char == '.': state = 176; lexeme += self.current_char; self.advance(); continue # TD5 .
                elif self.current_char == '`': state = 178; lexeme += self.current_char; self.advance(); continue # TD5 `
                
                else:
                    errors.append(LexerError(f"Illegal character: '{self.current_char}'", start_line, start_column))
                    self.advance(); state = 0; continue
            
            # --- Keyword States (TD1 & TD2, States 1-99) ---
            elif state == 1: # lexeme "b"
                if self.current_char == 'l': state = 2; lexeme += self.current_char; self.advance()
                elif self.current_char == 'r': state = 5; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'b'", self.line, self.column)); state = 0; self.advance()
            elif state == 2: # lexeme "bl"
                if self.current_char == 'n': state = 3; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'bl'", self.line, self.column)); state = 0; self.advance()
            elif state == 3: # lexeme "bln"
                if self.current_char is None or self.current_char in DEL1: state = 4; # Delimiter check
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'bln'", self.line, self.column)); state = 0; self.advance()
            elif state == 4: tokens.append(Token(TT_BOOL, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back() # Step back after tokenizing

            elif state == 5: # lexeme "br"
                if self.current_char == 'k': state = 6; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'br'", self.line, self.column)); state = 0; self.advance()
            elif state == 6: # lexeme "brk"
                if self.current_char is None or self.current_char in DEL2: state = 7; 
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'brk'", self.line, self.column)); state = 0; self.advance()
            elif state == 7: tokens.append(Token(TT_BRK, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()

            elif state == 8: # lexeme "c"
                if self.current_char == 'h': state = 9; lexeme += self.current_char; self.advance()   # for chr
                elif self.current_char == 'n': state = 12; lexeme += self.current_char; self.advance() # for cntn (TD1) or cnst (user code)
                elif self.current_char == 's': state = 16; lexeme += self.current_char; self.advance() # for cst (TD1) or cs (user code)
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'c'", self.line, self.column)); state = 0; self.advance()
            elif state == 9: # lexeme "ch"
                if self.current_char == 'r': state = 10; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'ch'", self.line, self.column)); state = 0; self.advance()
            elif state == 10: # lexeme "chr"
                if self.current_char is None or self.current_char in DEL1: state = 11; 
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'chr'", self.line, self.column)); state = 0; self.advance()
            elif state == 11: tokens.append(Token(TT_CHAR, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            
            elif state == 12: # lexeme "cn"
                if self.current_char == 't': state = 13; lexeme += self.current_char; self.advance() # For TD1 'cntn'
                elif self.current_char == 's': state = 701; lexeme += self.current_char; self.advance() # For user 'cnst' -> new internal state 701
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'cn'", self.line, self.column)); state = 0; self.advance()
            elif state == 13: # lexeme "cnt" for cntn
                if self.current_char == 'n': state = 14; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'cnt'", self.line, self.column)); state = 0; self.advance()
            elif state == 14: # lexeme "cntn"
                if self.current_char is None or self.current_char in DEL2: state = 15; 
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'cntn'", self.line, self.column)); state = 0; self.advance()
            elif state == 15: tokens.append(Token(TT_CNTN, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 16: # lexeme "cs"
                if self.current_char == 't': state = 17; lexeme += self.current_char; self.advance() # For TD1 'cst'
                elif self.current_char is None or self.current_char in DEL26: # For user 'cs' keyword
                    tokens.append(Token(TT_CS, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char or delimiter after 'cs'", self.line, self.column)); state = 0; self.advance()
            elif state == 17: # lexeme "cst"
                if self.current_char is None or self.current_char in DEL1: state = 18; 
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'cst'", self.line, self.column)); state = 0; self.advance()
            elif state == 18: tokens.append(Token("TT_CST_DIAGRAM", lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # ... (States 21 to 99 for other keywords from TD1 & TD2, following similar pattern) ...
            # Example for 'd' and 'dbl'
            elif state == 21: # lexeme "d"
                if self.current_char == 'b': state = 23; lexeme += self.current_char; self.advance()  # for dbl
                elif self.current_char == 'f': state = 26; lexeme += self.current_char; self.advance()  # for dflt
                elif self.current_char == 's': state = 30; lexeme += self.current_char; self.advance()  # for dfstrct
                elif self.current_char is None or self.current_char in DEL3: state = 22; # for 'd' keyword
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'd'", self.line, self.column)); state = 0; self.advance()
            elif state == 22: tokens.append(Token(TT_D, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            elif state == 23: # lexeme "db"
                if self.current_char == 'l': state = 24; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'db'", self.line, self.column)); state = 0; self.advance()
            elif state == 24: # lexeme "dbl"
                if self.current_char is None or self.current_char in DEL1: state = 25;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'dbl'", self.line, self.column)); state = 0; self.advance()
            elif state == 25: tokens.append(Token(TT_DOUBLE, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            
            # ... (dflt: 26-29, dfstrct: 30-35)
            elif state == 26: # dflt path
                if self.current_char == 'l': state = 27; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'df'", self.line, self.column)); state = 0; self.advance()
            elif state == 27:
                if self.current_char == 't': state = 28; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'dfl'", self.line, self.column)); state = 0; self.advance()
            elif state == 28:
                if self.current_char is None or self.current_char in DEL4: state = 29; # DEL4 is empty set, so essentially means no specific char needed
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'dflt'", self.line, self.column)); state = 0; self.advance()
            elif state == 29: tokens.append(Token(TT_DFLT, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()

            elif state == 30: # dfstrct path
                if self.current_char == 't': state = 31; lexeme += self.current_char; self.advance()
                # ... (fallback logic similar to above)
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'ds'", self.line, self.column)); state = 0; self.advance()
            elif state == 31:
                if self.current_char == 'r': state = 32; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'dst'", self.line, self.column)); state = 0; self.advance()
            elif state == 32:
                if self.current_char == 'c': state = 33; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'dstr'", self.line, self.column)); state = 0; self.advance()
            elif state == 33:
                if self.current_char == 't': state = 34; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'dstrc'", self.line, self.column)); state = 0; self.advance()
            elif state == 34:
                if self.current_char is None or self.current_char in DEL1: state = 35;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'dfstrct'", self.line, self.column)); state = 0; self.advance()
            elif state == 35: tokens.append(Token(TT_DFSTRCT, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # end: 36-39
            elif state == 36: # lexeme "e"
                if self.current_char == 'n': state = 37; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'e'", self.line, self.column)); state = 0; self.advance()
            elif state == 37: # lexeme "en"
                if self.current_char == 'd': state = 38; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'en'", self.line, self.column)); state = 0; self.advance()
            elif state == 38: # lexeme "end"
                if self.current_char is None or self.current_char in DEL2: state = 39; 
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'end'", self.line, self.column)); state = 0; self.advance()
            elif state == 39: tokens.append(Token(TT_END, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # f, fls, fnctn, fr: 40-51
            elif state == 40: # lexeme "f"
                if self.current_char == 'l': state = 42; lexeme += self.current_char; self.advance()  # for fls
                elif self.current_char == 'n': state = 45; lexeme += self.current_char; self.advance()  # for fnctn
                elif self.current_char == 'r': state = 50; lexeme += self.current_char; self.advance()  # for fr
                elif self.current_char is None or self.current_char in DEL5: state = 41; # for 'f' keyword
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'f'", self.line, self.column)); state = 0; self.advance()
            elif state == 41: tokens.append(Token(TT_F, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 42: # fls path
                if self.current_char == 's': state = 43; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'fl'", self.line, self.column)); state = 0; self.advance()
            elif state == 43:
                if self.current_char is None or self.current_char in DEL6: state = 44;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'fls'", self.line, self.column)); state = 0; self.advance()
            elif state == 44: tokens.append(Token(TT_FLS, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            elif state == 45: # fnctn path
                if self.current_char == 'c': state = 46; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'fn'", self.line, self.column)); state = 0; self.advance()
            elif state == 46:
                if self.current_char == 't': state = 47; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'fnc'", self.line, self.column)); state = 0; self.advance()
            elif state == 47:
                if self.current_char == 'n': state = 48; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'fnct'", self.line, self.column)); state = 0; self.advance()
            elif state == 48:
                if self.current_char is None or self.current_char in DEL1: state = 49;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'fnctn'", self.line, self.column)); state = 0; self.advance()
            elif state == 49: tokens.append(Token(TT_FNCTN, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            elif state == 50: # fr path
                if self.current_char is None or self.current_char in DEL5: state = 51;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance() # 'fr' could be start of ID
                else: errors.append(LexerError(f"Invalid delimiter for 'fr'", self.line, self.column)); state = 0; self.advance()
            elif state == 51: tokens.append(Token(TT_FR, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # ls, lsf: 52-56
            elif state == 52: # lexeme "l"
                if self.current_char == 's': state = 53; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'l'", self.line, self.column)); state = 0; self.advance()
            elif state == 53: # lexeme "ls"
                if self.current_char == 'f': state = 55; lexeme += self.current_char; self.advance() # for lsf
                elif self.current_char is None or self.current_char in DEL3: state = 54; # for ls
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid char or delimiter for 'ls'/'lsf'", self.line, self.column)); state = 0; self.advance()
            elif state == 54: tokens.append(Token(TT_LS, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 55: # lexeme "lsf"
                if self.current_char is None or self.current_char in DEL5: state = 56;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'lsf'", self.line, self.column)); state = 0; self.advance()
            elif state == 56: tokens.append(Token(TT_LSF, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()

            # mn: 57-59
            elif state == 57: # lexeme "m"
                if self.current_char == 'n': state = 58; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'm'", self.line, self.column)); state = 0; self.advance()
            elif state == 58: # lexeme "mn"
                if self.current_char is None or self.current_char in DEL7: state = 59;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'mn'", self.line, self.column)); state = 0; self.advance()
            elif state == 59: tokens.append(Token(TT_MN, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()

            # npt, nt: 60-65
            elif state == 60: # lexeme "n"
                if self.current_char == 'p': state = 61; lexeme += self.current_char; self.advance() # for npt
                elif self.current_char == 't': state = 64; lexeme += self.current_char; self.advance() # for nt
                # Add path for 'nll' if it starts with 'n' and is distinct
                elif self.current_char == 'l' and self.peek() == 'l': # Check for 'nll'
                    state = 704; lexeme += self.current_char; self.advance() # Go to internal state for 'nl' part of 'nll'
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'n'", self.line, self.column)); state = 0; self.advance()
            elif state == 61: # npt path
                if self.current_char == 't': state = 62; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'np'", self.line, self.column)); state = 0; self.advance()
            elif state == 62:
                if self.current_char is None or self.current_char in DEL7: state = 63;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'npt'", self.line, self.column)); state = 0; self.advance()
            elif state == 63: tokens.append(Token(TT_NPT, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            elif state == 64: # nt path
                if self.current_char is None or self.current_char in DEL1: state = 65;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'nt'", self.line, self.column)); state = 0; self.advance()
            elif state == 65: tokens.append(Token(TT_INT, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()

            # prnt: 66-70
            elif state == 66: # lexeme "p"
                if self.current_char == 'r': state = 67; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'p'", self.line, self.column)); state = 0; self.advance()
            elif state == 67: # lexeme "pr"
                if self.current_char == 'n': state = 68; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'pr'", self.line, self.column)); state = 0; self.advance()
            elif state == 68: # lexeme "prn"
                if self.current_char == 't': state = 69; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'prn'", self.line, self.column)); state = 0; self.advance()
            elif state == 69: # lexeme "prnt"
                if self.current_char is None or self.current_char in DEL7: state = 70;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'prnt'", self.line, self.column)); state = 0; self.advance()
            elif state == 70: tokens.append(Token(TT_PRNT, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # rtrn: 71-75
            elif state == 71: # lexeme "r"
                if self.current_char == 't': state = 72; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'r'", self.line, self.column)); state = 0; self.advance()
            elif state == 72: # lexeme "rt"
                if self.current_char == 'r': state = 73; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'rt'", self.line, self.column)); state = 0; self.advance()
            elif state == 73: # lexeme "rtr"
                if self.current_char == 'n': state = 74; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'rtr'", self.line, self.column)); state = 0; self.advance()
            elif state == 74: # lexeme "rtrn"
                if self.current_char is None or self.current_char in DEL8: state = 75;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'rtrn'", self.line, self.column)); state = 0; self.advance()
            elif state == 75: tokens.append(Token(TT_RTRN, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # strct, strng, swtch: 76-89
            elif state == 76: # lexeme "s"
                if self.current_char == 't': state = 77; lexeme += self.current_char; self.advance() # for strct or strng
                elif self.current_char == 'w': state = 85; lexeme += self.current_char; self.advance() # for swtch
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 's'", self.line, self.column)); state = 0; self.advance()
            elif state == 77: # lexeme "st"
                if self.current_char == 'r': state = 78; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'st'", self.line, self.column)); state = 0; self.advance()
            elif state == 78: # lexeme "str"
                if self.current_char == 'c': state = 79; lexeme += self.current_char; self.advance() # for strct
                elif self.current_char == 'n': state = 82; lexeme += self.current_char; self.advance() # for strng
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'str'", self.line, self.column)); state = 0; self.advance()
            elif state == 79: # strct path
                if self.current_char == 't': state = 80; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'strc'", self.line, self.column)); state = 0; self.advance()
            elif state == 80:
                if self.current_char is None or self.current_char in DEL1: state = 81;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'strct'", self.line, self.column)); state = 0; self.advance()
            elif state == 81: tokens.append(Token(TT_STRCT, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            elif state == 82: # strng path
                if self.current_char == 'g': state = 83; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'strn'", self.line, self.column)); state = 0; self.advance()
            elif state == 83:
                if self.current_char is None or self.current_char in DEL1: state = 84;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'strng'", self.line, self.column)); state = 0; self.advance()
            elif state == 84: tokens.append(Token(TT_STRING, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            elif state == 85: # swtch path
                if self.current_char == 't': state = 86; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'sw'", self.line, self.column)); state = 0; self.advance()
            elif state == 86:
                if self.current_char == 'c': state = 87; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'swt'", self.line, self.column)); state = 0; self.advance()
            elif state == 87:
                if self.current_char == 'h': state = 88; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'swtc'", self.line, self.column)); state = 0; self.advance()
            elif state == 88:
                if self.current_char is None or self.current_char in DEL5: state = 89;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'swtch'", self.line, self.column)); state = 0; self.advance()
            elif state == 89: tokens.append(Token(TT_SWTCH, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()

            # tr: 90-92
            elif state == 90: # lexeme "t"
                if self.current_char == 'r': state = 91; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 't'", self.line, self.column)); state = 0; self.advance()
            elif state == 91: # lexeme "tr"
                if self.current_char is None or self.current_char in DEL6: state = 92;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'tr'", self.line, self.column)); state = 0; self.advance()
            elif state == 92: tokens.append(Token(TT_TR, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # vd: 93-95
            elif state == 93: # lexeme "v"
                if self.current_char == 'd': state = 94; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'v'", self.line, self.column)); state = 0; self.advance()
            elif state == 94: # lexeme "vd"
                if self.current_char is None or self.current_char in DEL1: state = 95;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'vd'", self.line, self.column)); state = 0; self.advance()
            elif state == 95: tokens.append(Token(TT_VD, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # whl: 96-99
            elif state == 96: # lexeme "w"
                if self.current_char == 'h': state = 97; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'w'", self.line, self.column)); state = 0; self.advance()
            elif state == 97: # lexeme "wh"
                if self.current_char == 'l': state = 98; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'wh'", self.line, self.column)); state = 0; self.advance()
            elif state == 98: # lexeme "whl"
                if self.current_char is None or self.current_char in DEL5: state = 99;
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'whl'", self.line, self.column)); state = 0; self.advance()
            elif state == 99: tokens.append(Token(TT_WHl, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            # --- Operator States (TD3: 100-124) ---
            elif state == 100: # lexeme is "+"
                if self.current_char == '=': state = 102; lexeme += self.current_char; self.advance()
                elif self.current_char == '+': state = 104; lexeme += self.current_char; self.advance()
                elif self.current_char is None or self.current_char in DEL24: state = 101; 
                else: errors.append(LexerError(f"Invalid char after '+'", self.line, self.column)); state = 0; self.advance()
            elif state == 101: tokens.append(Token(TT_PLUS, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 102: # lexeme is "+="
                if self.current_char is None or self.current_char in DEL24: state = 103; 
                else: errors.append(LexerError(f"Invalid char after '+='", self.line, self.column)); state = 0; self.advance()
            elif state == 103: tokens.append(Token(TT_PLUSEQ, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 104: # lexeme is "++"
                if self.current_char is None or self.current_char in DEL9: state = 105; 
                else: errors.append(LexerError(f"Invalid char after '++'", self.line, self.column)); state = 0; self.advance()
            elif state == 105: tokens.append(Token(TT_INCREMENT, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            elif state == 106: # lexeme is "-"
                if self.current_char == '=': state = 108; lexeme += self.current_char; self.advance()
                elif self.current_char == '-': state = 110; lexeme += self.current_char; self.advance()
                elif self.current_char is None or self.current_char in DEL24: state = 107; 
                else: errors.append(LexerError(f"Invalid char after '-'", self.line, self.column)); state = 0; self.advance()
            elif state == 107: tokens.append(Token(TT_MINUS, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 108: # lexeme is "-="
                if self.current_char is None or self.current_char in DEL24: state = 109; 
                else: errors.append(LexerError(f"Invalid char after '-='", self.line, self.column)); state = 0; self.advance()
            elif state == 109: tokens.append(Token(TT_MINUSEQ, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 110: # lexeme is "--"
                if self.current_char is None or self.current_char in DEL9: state = 111; 
                else: errors.append(LexerError(f"Invalid char after '--'", self.line, self.column)); state = 0; self.advance()
            elif state == 111: tokens.append(Token(TT_DECREMENT, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 112: # lexeme is "*"
                if self.current_char == '=': state = 114; lexeme += self.current_char; self.advance()
                elif self.current_char == '*': state = 800; lexeme += self.current_char; self.advance() # TT_EXP
                elif self.current_char is None or self.current_char in DEL24: state = 113; 
                else: errors.append(LexerError(f"Invalid char after '*'", self.line, self.column)); state = 0; self.advance()
            elif state == 113: tokens.append(Token(TT_MUL, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 114: # lexeme is "*="
                if self.current_char is None or self.current_char in DEL24: state = 115; 
                else: errors.append(LexerError(f"Invalid char after '*='", self.line, self.column)); state = 0; self.advance()
            elif state == 115: tokens.append(Token(TT_MULTIEQ, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            
            elif state == 116: # lexeme is "/"
                if self.current_char == '=': state = 118; lexeme += self.current_char; self.advance()
                elif self.current_char is None or self.current_char in DEL24: state = 117; 
                else: errors.append(LexerError(f"Invalid char after '/'", self.line, self.column)); state = 0; self.advance()
            elif state == 117: tokens.append(Token(TT_DIV, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 118: # lexeme is "/="
                if self.current_char is None or self.current_char in DEL24: state = 119; 
                else: errors.append(LexerError(f"Invalid char after '/='", self.line, self.column)); state = 0; self.advance()
            elif state == 119: tokens.append(Token(TT_DIVEQ, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            elif state == 120: # lexeme is "%"
                if self.current_char == '=': state = 123; lexeme += self.current_char; self.advance()
                elif self.current_char is None or self.current_char in DEL24: state = 121; 
                else: errors.append(LexerError(f"Invalid char after '%'", self.line, self.column)); state = 0; self.advance()
            elif state == 121: tokens.append(Token(TT_MOD, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 123: # lexeme is "%="
                if self.current_char is None or self.current_char in DEL24: state = 124; 
                else: errors.append(LexerError(f"Invalid char after '%='", self.line, self.column)); state = 0; self.advance()
            elif state == 124: tokens.append(Token(TT_MODEQ, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            # --- Operator States (TD4: 125-150) ---
            elif state == 125: # lexeme is "="
                if self.current_char == '=': state = 127; lexeme += self.current_char; self.advance()
                elif self.current_char is None or self.current_char in DEL28: state = 126; 
                else: errors.append(LexerError(f"Invalid char after '='", self.line, self.column)); state = 0; self.advance()
            elif state == 126: tokens.append(Token(TT_EQ, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 127: # lexeme is "=="
                if self.current_char is None or self.current_char in DEL25: state = 128; 
                else: errors.append(LexerError(f"Invalid char after '=='", self.line, self.column)); state = 0; self.advance()
            elif state == 128: tokens.append(Token(TT_EQTO, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            elif state == 129: # lexeme is ">"
                if self.current_char == '=': state = 131; lexeme += self.current_char; self.advance()
                elif self.current_char is None or self.current_char in DEL25: state = 130; 
                else: errors.append(LexerError(f"Invalid char after '>'", self.line, self.column)); state = 0; self.advance()
            elif state == 130: tokens.append(Token(TT_GT, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            elif state == 131: # lexeme is ">="
                if self.current_char is None or self.current_char in DEL25: state = 132; 
                else: errors.append(LexerError(f"Invalid char after '>='", self.line, self.column)); state = 0; self.advance()
            elif state == 132: tokens.append(Token(TT_GTEQ, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 133: # lexeme is "<"
                if self.current_char == '=': state = 135; lexeme += self.current_char; self.advance()
                elif self.current_char is None or self.current_char in DEL25: state = 134; 
                else: errors.append(LexerError(f"Invalid char after '<'", self.line, self.column)); state = 0; self.advance()
            elif state == 134: tokens.append(Token(TT_LT, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 135: # lexeme is "<="
                if self.current_char is None or self.current_char in DEL25: state = 136; 
                else: errors.append(LexerError(f"Invalid char after '<='", self.line, self.column)); state = 0; self.advance()
            elif state == 136: tokens.append(Token(TT_LTEQ, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            elif state == 137: # lexeme is "!"
                if self.current_char == '=': state = 139; lexeme += self.current_char; self.advance()
                elif self.current_char is None or self.current_char in DEL25: state = 138; 
                else: errors.append(LexerError(f"Invalid char after '!'", self.line, self.column)); state = 0; self.advance()
            elif state == 138: tokens.append(Token(TT_NOT, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 139: # lexeme is "!="
                if self.current_char is None or self.current_char in DEL25: state = 140; 
                else: errors.append(LexerError(f"Invalid char after '!='", self.line, self.column)); state = 0; self.advance()
            elif state == 140: tokens.append(Token(TT_NOTEQ, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()

            elif state == 141: # lexeme is ":"
                if self.current_char is None or self.current_char in DEL11: state = 142;
                else: errors.append(LexerError(f"Invalid char after ':'", self.line, self.column)); state = 0; self.advance()
            elif state == 142: tokens.append(Token(TT_COLON, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            
            elif state == 143: # lexeme is ";"
                if self.current_char is None or self.current_char in DEL11: state = 144;
                else: errors.append(LexerError(f"Invalid char after ';'", self.line, self.column)); state = 0; self.advance()
            elif state == 144: tokens.append(Token(TT_SEMICOLON, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            elif state == 145: # lexeme is "["
                if self.current_char is None or self.current_char in DEL12: state = 146;
                else: errors.append(LexerError(f"Invalid char after '['", self.line, self.column)); state = 0; self.advance()
            elif state == 146: tokens.append(Token(TT_LSQBR, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 147: # lexeme is "]"
                if self.current_char is None or self.current_char in DEL13: state = 148;
                else: errors.append(LexerError(f"Invalid char after ']'", self.line, self.column)); state = 0; self.advance()
            elif state == 148: tokens.append(Token(TT_RSQBR, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            elif state == 149: # lexeme is "{"
                if self.current_char is None or self.current_char in DEL14: state = 150;
                else: errors.append(LexerError(f"Invalid char after '{{'", self.line, self.column)); state = 0; self.advance()
            elif state == 150: tokens.append(Token(TT_BLOCK_START, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            # --- TD5 Specific States (151-160) ---
            elif state == 151: # lexeme is "}"
                if self.current_char is None or self.current_char in DEL15: state = 152
                else: errors.append(LexerError(f"Invalid char after '}}'", self.line, self.column)); state = 0; self.advance()
            elif state == 152: tokens.append(Token(TT_BLOCK_END, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            
            elif state == 153: # lexeme is "("
                if self.current_char is None or self.current_char in DEL16: state = 154
                else: errors.append(LexerError(f"Invalid char after '('", self.line, self.column)); state = 0; self.advance()
            elif state == 154: tokens.append(Token(TT_LPAREN, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 155: # lexeme is ")"
                if self.current_char is None or self.current_char in DEL18: state = 156 
                else: errors.append(LexerError(f"Invalid char after ')'", self.line, self.column)); state = 0; self.advance()
            elif state == 156: tokens.append(Token(TT_RPAREN, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 157: # lexeme is ","
                if self.current_char is None or self.current_char in DEL20: state = 158
                else: errors.append(LexerError(f"Invalid char after ','", self.line, self.column)); state = 0; self.advance()
            elif state == 158: tokens.append(Token(TT_COMMA, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 159: # lexeme is "~" (standalone operator)
                if self.current_char is None or self.current_char in DEL21_for_tilde_op: state = 160 # Using custom DEL for unary tilde
                else: errors.append(LexerError(f"Invalid char after '~' operator", self.line, self.column)); state = 0; self.advance()
            elif state == 160: tokens.append(Token(TT_NEGATIVE, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            # --- Internal states for user-defined keywords (if needed) ---
            elif state == 701: # lexeme "cns" (internal state after 'cns' for 'cnst')
                if self.current_char == 't': state = 702; lexeme += self.current_char; self.advance() 
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: 
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'cns'", self.line, self.column)); state = 0; self.advance()
            elif state == 702: # lexeme "cnst"
                if self.current_char is None or self.current_char in DEL1: state = 703; 
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'cnst'", self.line, self.column)); state = 0; self.advance()
            elif state == 703: tokens.append(Token(TT_CNST, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()
            
            elif state == 704: # lexeme "nl" (internal state for 'nll')
                if self.current_char == 'l': state = 705; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else:
                    if self.current_char is None or self.current_char in DEL22: tokens.append(Token(TT_IDENTIFIER, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Invalid char after 'nl'", self.line, self.column)); state = 0; self.advance()
            elif state == 705: # lexeme "nll"
                if self.current_char is None or self.current_char in DEL22: state = 706; # DEL22 was used in original user code for 'nll'
                elif self.current_char is not None and self.current_char in IDENTIFIER_CHARS: state = 180; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Invalid delimiter for 'nll'", self.line, self.column)); state = 0; self.advance()
            elif state == 706: tokens.append(Token(TT_NULL, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()

            elif state == 800: # lexeme is "**" (for TT_EXP)
                if self.current_char is None or self.current_char in DEL24: state = 801; # Assuming DEL24 for TT_EXP
                else: errors.append(LexerError(f"Invalid char after '**'", self.line, self.column)); state = 0; self.advance()
            elif state == 801: tokens.append(Token(TT_EXP, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()


            # --- Comment, Char/String Literal, Identifier, Number states ---
            # ... (States 161-222, 900-901 as previously defined and corrected) ...
            # Note: step_back() is added after tokenizing in most keyword/operator final states
            # to allow the delimiter to be processed as the start of the next token if it's not whitespace.

            # '#' Comment
            elif state == 161: 
                if self.current_char is not None and self.current_char != '\n': self.advance() 
                elif self.current_char == '\n': state = 162 
                elif self.current_char is None: state = 162 
            elif state == 162: state = 0; # Newline will be consumed by advance or it's EOF

            # ''' Char Literal (TD5: 163-166)
            elif state == 163: 
                if self.current_char == '\\': state = 900; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char in CHAR_CONTENT_CHARS:
                    state = 164; lexeme += self.current_char; self.advance()
                elif self.current_char == "'": errors.append(LexerError("Empty character literal", start_line, start_column)); state = 0
                else: errors.append(LexerError(f"Invalid character in char literal: {self.current_char}", start_line, start_column)); state = 0; 
                if self.current_char is not None: self.advance()
            elif state == 900: 
                valid_escapes = {"'": "'", "\\": "\\", "n": "\n", "t": "\t", "0": "\0"}
                if self.current_char is not None and self.current_char in valid_escapes:
                    lexeme += self.current_char; state = 164; self.advance()
                else: errors.append(LexerError(f"Invalid escape sequence: \\{self.current_char}", start_line, start_column)); state = 0; 
                if self.current_char is not None: self.advance()
            elif state == 164: 
                if self.current_char == "'": state = 165; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError(f"Unclosed character literal, expected ' found {self.current_char}", start_line, start_column)); state = 0; 
                if self.current_char is not None: self.advance()
            elif state == 165: 
                if self.current_char is None or self.current_char in DEL26: state = 166
                else: errors.append(LexerError(f"Invalid delimiter after char literal: {self.current_char}", self.line, self.column)); state = 0; self.advance()
            elif state == 166:
                val = lexeme[1:-1]; actual_val = ""
                if len(val) == 2 and val[0] == '\\': 
                    escape_map = {"'": "'", "\\": "\\", "n": "\n", "t": "\t", "0": "\0"}
                    actual_val = escape_map.get(val[1], val[1]) 
                elif len(val) == 1: actual_val = val
                else: errors.append(LexerError(f"Invalid char literal content: {val}", start_line, start_column));
                if not errors or actual_val: tokens.append(Token(TT_CHARLIT, actual_val, start_line, start_column)); 
                state = 0; 
                if self.current_char is not None: self.step_back()
            
            elif state == 167: 
                if self.current_char == '"': state = 168; lexeme += self.current_char; self.advance()
                elif self.current_char == '\\': state = 901; lexeme += self.current_char; self.advance()
                elif self.current_char is not None and self.current_char != '\n': lexeme += self.current_char; self.advance()
                elif self.current_char == '\n': errors.append(LexerError("Newline in string literal", start_line, start_column)); state = 0
                elif self.current_char is None: errors.append(LexerError("Unterminated string literal (EOF)", start_line, start_column)); state = 0
                else: errors.append(LexerError(f"Unexpected char in string: {self.current_char}", start_line, start_column)); state = 0; self.advance()
            elif state == 901: 
                valid_escapes = {'"': '"', '\\': '\\', 'n': '\n', 't': '\t', '0': '\0'}
                if self.current_char is not None and self.current_char in valid_escapes:
                    lexeme += self.current_char; state = 167; self.advance()
                else: errors.append(LexerError(f"Invalid string escape sequence: \\{self.current_char}", start_line, start_column)); state = 167; 
                if self.current_char is not None: self.advance()
            elif state == 168: 
                if self.current_char is None or self.current_char in DEL19: state = 169
                else: errors.append(LexerError(f"Invalid delimiter after string literal: {self.current_char}", self.line, self.column)); state = 0; self.advance()
            elif state == 169:
                raw_val = lexeme[1:-1]; actual_val = ""; i = 0
                while i < len(raw_val):
                    if raw_val[i] == '\\':
                        if i + 1 < len(raw_val):
                            esc_char = raw_val[i+1]
                            escape_map = {'"': '"', '\\': '\\', 'n': '\n', 't': '\t', '0': '\0'}
                            actual_val += escape_map.get(esc_char, esc_char) 
                            i += 2
                        else: actual_val += raw_val[i]; i+=1 
                    else: actual_val += raw_val[i]; i+=1
                tokens.append(Token(TT_STRINGLIT, actual_val, start_line, start_column)); state = 0; 
                if self.current_char is not None: self.step_back()

            # TD5 &&, ||, ., `
            elif state == 170: # lexeme is "&"
                if self.current_char == '&': state = 171; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError("Expected '&' for '&&', found single '&'", self.line, self.column)); state = 0; # Single '&' is error unless defined elsewhere
            elif state == 171: # lexeme is "&&"
                if self.current_char is None or self.current_char in DEL25: state = 172
                else: errors.append(LexerError(f"Invalid char after '&&'", self.line, self.column)); state = 0; self.advance()
            elif state == 172: tokens.append(Token(TT_AND, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 173: # lexeme is "|"
                if self.current_char == '|': state = 174; lexeme += self.current_char; self.advance()
                else: errors.append(LexerError("Expected '|' for '||', found single '|'", self.line, self.column)); state = 0;
            elif state == 174: # lexeme is "||"
                if self.current_char is None or self.current_char in DEL25: state = 175
                else: errors.append(LexerError(f"Invalid char after '||'", self.line, self.column)); state = 0; self.advance()
            elif state == 175: tokens.append(Token(TT_OR, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            elif state == 176: # lexeme is "."
                # TD5 shows transition on alpha to 177 (final). This means '.' is a token, and alpha starts next.
                tokens.append(Token(TT_STRCTACCESS, lexeme, start_line, start_column))
                state = 0 # Reset to process the alpha (or other char)
                # No advance() here, current_char is the char *after* '.', which starts next token.
                # No step_back() needed as '.' is a single char token here.
            # State 177 is implicit tokenization of '.'

            elif state == 178: # lexeme is "`"
                if self.current_char is None or self.current_char in DEL27: state = 179
                else: errors.append(LexerError(f"Invalid char after '`'", self.line, self.column)); state = 0; self.advance()
            elif state == 179: tokens.append(Token(TT_CONCAT, lexeme, start_line, start_column)); state = 0;
            if self.current_char is not None: self.step_back()


            # --- Identifier State (TD6: 180) ---
            elif state == 180: 
                if self.current_char is not None and self.current_char in IDENTIFIER_CHARS:
                    if len(lexeme) < 25: lexeme += self.current_char; self.advance()
                    else:
                        errors.append(LexerError(f"Identifier '{lexeme}{self.current_char}' exceeds max length 25", start_line, start_column))
                        while self.current_char is not None and self.current_char in IDENTIFIER_CHARS: self.advance()
                        state = 0 
                elif self.current_char is None or self.current_char in DEL22: 
                    token_type = keywords.get(lexeme, TT_IDENTIFIER)
                    tokens.append(Token(token_type, lexeme, start_line, start_column))
                    state = 0 
                    if self.current_char is not None: self.step_back() # Delimiter might start next token
                else: 
                    errors.append(LexerError(f"Invalid char '{self.current_char}' in identifier '{lexeme}'", self.line, self.column)); state = 0; self.advance()

            # --- Number Literal States (TD7: 195-222) ---
            elif state == 195: 
                if lexeme == "~" and not (self.current_char in DIGITZERO): 
                    errors.append(LexerError("Stray '~'; not a valid number prefix here.", start_line, start_column)); state = 0; continue
                elif self.current_char in DIGITZERO: lexeme += self.current_char; state = 196; self.advance()
                elif self.current_char == '.': 
                     if lexeme == "~" and self.peek() not in DIGITZERO : errors.append(LexerError("Digit expected after '~.'", start_line, start_column)); state = 0;
                     else: lexeme += self.current_char; state = 213; self.advance() 
                elif self.current_char is None or self.current_char in DEL23: 
                    tokens.append(Token(TT_INTEGERLIT, lexeme, start_line, start_column)); state = 0;
                    if self.current_char is not None: self.step_back()
                else: errors.append(LexerError(f"Invalid char '{self.current_char}' starting number '{lexeme}'", self.line, self.column)); state = 0; self.advance()
            elif state >= 196 and state <= 209: 
                if self.current_char in DIGITZERO: lexeme += self.current_char; state += 1; self.advance()
                elif self.current_char == '.': lexeme += self.current_char; state = 213; self.advance()
                elif self.current_char is None or self.current_char in DEL23: state = 212; 
                else: errors.append(LexerError(f"Invalid char '{self.current_char}' in integer part '{lexeme}'", self.line, self.column)); state = 0; self.advance()
            elif state == 210: 
                if self.current_char in DIGITZERO: lexeme += self.current_char; state = 211; self.advance()
                elif self.current_char == '.': lexeme += self.current_char; state = 213; self.advance()
                elif self.current_char is None or self.current_char in DEL23: state = 212; 
                else: errors.append(LexerError(f"Invalid char '{self.current_char}' in integer part '{lexeme}'", self.line, self.column)); state = 0; self.advance()
            elif state == 211: 
                if self.current_char == '.': lexeme += self.current_char; state = 213; self.advance()
                elif self.current_char is None or self.current_char in DEL23: state = 212; 
                else: errors.append(LexerError(f"Expected '.' or delimiter after integer part, got '{self.current_char}'", self.line, self.column)); state = 0; self.advance()
            elif state == 212: tokens.append(Token(TT_INTEGERLIT, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            elif state == 213: 
                if self.current_char in DIGITZERO: lexeme += self.current_char; state = 214; self.advance()
                elif self.current_char is None or self.current_char in DEL17:
                    if lexeme.endswith('.'): tokens.append(Token(TT_DOUBLELIT, lexeme, start_line, start_column)); state = 0; 
                    if self.current_char is not None: self.step_back()
                    else: errors.append(LexerError(f"Malformed double ending with dot: '{lexeme}'", self.line, self.column)); state = 0; self.advance()
                else: errors.append(LexerError(f"Digit expected after '.', got '{self.current_char}'", self.line, self.column)); state = 0; self.advance()
            elif state >= 214 and state <= 220: 
                if self.current_char in DIGITZERO: lexeme += self.current_char; state += 1; self.advance()
                elif self.current_char is None or self.current_char in DEL17: state = 222; 
                else: errors.append(LexerError(f"Invalid char '{self.current_char}' in fractional part '{lexeme}'", self.line, self.column)); state = 0; self.advance()
            elif state == 221: 
                if self.current_char in DIGITZERO: 
                    lexeme += self.current_char; self.advance() 
                    if self.current_char is None or self.current_char in DEL17: state = 222; 
                    else: errors.append(LexerError(f"Expected delimiter DEL17 after fractional part, got '{self.current_char}'", self.line, self.column)); state = 0 
                elif self.current_char is None or self.current_char in DEL17: state = 222
                else: errors.append(LexerError(f"Invalid char '{self.current_char}' in fractional part '{lexeme}'", self.line, self.column)); state = 0; self.advance()
            elif state == 222: tokens.append(Token(TT_DOUBLELIT, lexeme, start_line, start_column)); state = 0; 
            if self.current_char is not None: self.step_back()
            
            else: # Unhandled state
                if state != 0:
                    errors.append(LexerError(f"Lexer in unhandled state {state} for lexeme '{lexeme}' with char '{self.current_char}'", self.line, self.column))
                    if self.current_char is not None: self.advance()
                    state = 0

        if not tokens or tokens[-1].type != TT_EOF:
             tokens.append(Token(TT_EOF, 'EOF', self.line, self.column if self.current_char else self.column))
        return tokens, errors

