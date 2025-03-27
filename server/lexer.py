class LexerError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column

# Token Types
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
TT_TR = 'blnlit'
TT_FLS = 'blnlit'
TT_FNCTN = 'fnctn'
TT_RTRN = 'rtrn'
TT_END = 'end'
TT_NULL = 'nll'
TT_CNTN = 'cntn'
TT_STRCT = 'strct'
TT_DFSTRCT = 'dfstrct'
TT_VD = 'vd'
TT_IDENTIFIER = 'id'
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
TT_MEMBER = 'member'
TT_INTEGERLIT = 'ntlit'
TT_NEGINTLIT = '~ntlit'
TT_DOUBLELIT = 'dbllit'
TT_NEGDOUBLELIT = '~dbllit'
TT_STRINGLIT = 'strnglit'
TT_CHARLIT = 'chrlit'
TT_STRCTACCESS = '.'
TC_FUNC = 1
TC_MAIN = 2
TC_USERFUNC = 3
TC_CONDITIONAL = 4
TC_JUMP = 5
TC_DATATYPE = 6
TC_CVAR = 7
TC_LOOP = 8
TC_LOGIC = 9
TC_CONDITION = 10
TC_DOLS = 11
TC_DEFAULT = 12
TC_RETURN = 13
TC_OPENPAREN = 14
TC_CLOSEPAREN = 15
TC_ARITH = 16
TC_LSQUARE = 17
TC_RSQUARE = 18
TC_LCURL = 19
TC_RCURL = 20
TC_INCDEC = 21
TC_ASSIGN = 22
TC_COMMA = 23
TC_NUM = 24
TC_DBL = 25
TC_IDENTIFIERS = 26
TC_RELATIONAL = 27
TC_COLONSEMI = 28
TC_NEGATIVE = 29
TC_LOGICOP = 30
TC_STRLIT = 31
TC_NOT = 32
TC_CHRLIT = 33
TC_STRCONCAT = 34

ZERO = '0'
DIGIT = '123456789'
DIGITZERO = ZERO + DIGIT

LOWALPHA = 'abcdefghijklmnopqrstuvwxyz'
UPALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

ALPHA = LOWALPHA + UPALPHA
ALPHA_NUMERIC = ALPHA + DIGITZERO

DELIMITERS = {
'del1': {' '},
'del2': {';'},
'del3': {' ', '{'},
'del4': {':',},
'del5': {' ', '('},
'del6': {' ', ';', ',', '=', '>', '<', '!', '}', ')'},
'del7': {'('},
'del8': {' ', ';'},
'del9': set(ALPHA + '(' + ',' + ';' + ')' + ' '),
'del10': {' ', ';', ')'},
'del11': {' ', '\n'},
'del12': set(ALPHA + DIGITZERO + ']' + '~'),
'del13': {' ', ';', ')', '['},
'del14': set(ALPHA + DIGITZERO + ' ' + '\n' + '"' + "'" + '{'),
'del15': {' ', '\n', ';', '}', ','},
'del16': set(ALPHA_NUMERIC + ')' + '"' + '!' + '(' + '[' + '' + '\''),
'del17': {' ', '}', ';', ',', '+', '-', '*', '/', '%', '=' , '>', '<', '!', '&', '|'},
'del18': {' ', ';', '{', ')', '&', '|', '+', '-', '*', '/', '%'},
'del19': {' ', ';', ',', '}', ')', '=', '>', '<', '!'},
'del20': set(ALPHA + DIGITZERO + ' ' + '"' + "'" + '{'),
'del21': set(DIGIT),
'del22': {' ', ',', ';', '(', ')', '{', '[', ']'}, 
'del23': {' ', ';', ',', '}', ']', ')', ':', '+', '-', '*', '/', '%', '=' , '>', '<', '!', '&', '|'},
'del24': set(' ' + DIGITZERO + ALPHA + '~' + '('),
'del25': set(' ' + DIGITZERO + ALPHA + '~' + '"' + "'"),
'del26': {' ', ';', ',', '}', ')', '=', '>', '<', '!', ':'},
'del27': {' ', '"'}
}


# Token Class
class Token:
    def __init__(self, type, value=None, line=0, column=0):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f'({self.type}, {self.value}, line {self.line}, col {self.column})' if self.value else f'({self.type}, line {self.line}, col {self.column})'

# Lexer Class
class Lexer:

    LEXER_SUCCESS = "success"
    
    KEYWORDS = {
    "npt": TT_NPT,       # Not used type
    "prnt": TT_PRNT,     # Print function
    "nt": TT_INT,        # Integer type
    "dbl": TT_DOUBLE,    # Double type
    "strng": TT_STRING,  # String type
    "bln": TT_BOOL,       # Boolean type
    "chr": TT_CHAR,      # Character type
    "f": TT_F,           # If keyword
    "ls": TT_LS,         # List type
    "lsf": TT_LSF,       # List function type
    "swtch": TT_SWTCH,   # Switch keyword
    "fr": TT_FR,         # For loop
    "whl": TT_WHl,       # While loop
    "d": TT_D,           # Data type (could be used as a general type)
    "mn": TT_MN,         # Main function or entry point
    "cs": TT_CS,         # Case for switch statement
    "dflt": TT_DFLT,     # Default case for switch
    "brk": TT_BRK,       # Break statement
    "cnst": TT_CNST,     # Constant keyword
    "tr": TT_TR,         # True keyword
    "fls": TT_FLS,       # False keyword
    "fnctn": TT_FNCTN,   # Function keyword
    "rtrn": TT_RTRN,     # Return statement
    "end": TT_END,       # End keyword
    "nll": TT_NULL,      # Null keyword
    "cntn": TT_CNTN,     # Continue statement
    "strct": TT_STRCT,   # Structure type
    "dfstrct": TT_DFSTRCT, # Structure definition
    "vd": TT_VD,         # Void type (function return type)
    }

    KEYWORDS_CATEGORY = {
        TT_INT: TC_DATATYPE,        # Integer type
        TT_DOUBLE: TC_DATATYPE,    # Double type
        TT_STRING: TC_DATATYPE,  # String type
        TT_BOOL: TC_DATATYPE,       # Boolean type
        TT_CHAR: TC_DATATYPE,      # Character type
        TT_VD: TC_DATATYPE,         # Void type
        TT_MN: TC_MAIN,             # Main type
        TT_FNCTN: TC_USERFUNC,      # Function type
        TT_STRCT: TC_USERFUNC,      # Struct type
        TT_LSF: TC_CONDITIONAL,      # Else if type
        TT_F: TC_CONDITIONAL,       # If type
        TT_SWTCH: TC_CONDITIONAL,    # Switch type
        TT_BRK: TC_JUMP,            # Break type
        TT_CNTN: TC_JUMP,            # Continue type
        TT_CNST: TC_CVAR,         # Constant type
        TT_FR: TC_LOOP,       # For type
        TT_WHl: TC_LOOP,     # While type
        TT_TR: TC_LOGIC,        # True type
        TT_FLS: TC_LOGIC,        # False type
        TT_CS: TC_CONDITION,       # Case type
        TT_D: TC_DOLS,              # Do type
        TT_LS: TC_DOLS,             # Else type
        TT_DFLT: TC_DEFAULT,        # Default type
        TT_PRNT: TC_FUNC,           # Print type
        TT_NPT: TC_FUNC,            # Input type
        TT_RTRN: TC_RETURN,         # Return type
        TT_LPAREN: TC_OPENPAREN,
        TT_RPAREN: TC_CLOSEPAREN,
        TT_PLUS: TC_ARITH,
        TT_MINUS: TC_ARITH,
        TT_MUL: TC_ARITH,
        TT_DIV: TC_ARITH,
        TT_MOD: TC_ARITH,
        TT_EXP: TC_ARITH,
        TT_LSQBR: TC_LSQUARE,
        TT_RSQBR: TC_RSQUARE,
        TT_BLOCK_START: TC_LCURL,
        TT_BLOCK_END: TC_RCURL,
        TT_INCREMENT: TC_INCDEC,
        TT_DECREMENT: TC_INCDEC,
        TT_EQ: TC_ASSIGN,
        TT_PLUSEQ: TC_ASSIGN,
        TT_MINUSEQ: TC_ASSIGN,
        TT_MULTIEQ: TC_ASSIGN,
        TT_DIVEQ: TC_ASSIGN,
        TT_MODEQ: TC_ASSIGN,
        TT_COMMA: TC_COMMA,
        TT_INTEGERLIT: TC_NUM,
        TT_DOUBLELIT: TC_DBL,
        TT_IDENTIFIER: TC_IDENTIFIERS,
        TT_EQTO: TC_RELATIONAL,
        TT_LT: TC_RELATIONAL,
        TT_LTEQ: TC_RELATIONAL,
        TT_GT: TC_RELATIONAL,
        TT_GTEQ: TC_RELATIONAL,
        TT_NOTEQ: TC_RELATIONAL,
        TT_COLON: TC_COLONSEMI,
        TT_SEMICOLON: TC_COLONSEMI,
        TT_NEGATIVE: TC_NEGATIVE,
        TT_STRINGLIT: TC_STRLIT,
        TT_CHARLIT: TC_CHRLIT,
        TT_NOT: TC_NOT,
        TT_AND: TC_LOGICOP,
        TT_OR: TC_LOGICOP,
        TT_CONCAT: TC_STRCONCAT
    }
    def __init__(self, text):
        self.text = text
        self.pos = -1
        self.current_char = None
        self.line = 1
        self.column = 0
        self.advance()

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            if self.current_char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def next_char(self):
        if self.pos + 1 < len(self.text):
            return self.text[self.pos + 1]
        return None

    def make_char(self):
        start_line = self.line
        start_column = self.column

        self.advance()  # Skip the opening single quote

        if self.current_char is None:
            raise LexerError("Unterminated character literal", start_line, start_column)

        char_value = self.current_char
        if len(char_value) != 1:
            raise LexerError("Character literal must be exactly one character", start_line, start_column)

        self.advance()  # Move past the character

        # Handle escape sequences
        if char_value == "\\":
            try:
                escape_map = {"'": "'", "\\": "\\", "n": "\n", "t": "\t", "r": "\r"}
                char_value = escape_map[self.current_char]
                self.advance()
            except KeyError:
                return None, LexerError(f"Invalid escape sequence: \\{self.current_char}", start_line, start_column)

        if self.current_char != "'":
            return None, LexerError("Expected closing single quote for character literal", start_line, start_column)

        self.advance()  # Skip the closing single quote
        return Token(TT_CHARLIT, char_value, start_line, start_column), None
    
    def skip_comment(self):
        start_line = self.line
        start_column = self.column

        while self.current_char is not None and self.current_char != '\n':
            self.advance()  # Skip each character in the comment
        
        if self.current_char == '\n':
            self.advance()

    def make_tokens(self):
        tokens = []
        errors = []

        try:
            open_parentheses = 0  # Track parentheses balance

            while self.current_char is not None:
                start_line = self.line
                start_column = self.column
                            
                if self.current_char in ' \t\n':  # Skip whitespace TODO: fix? why is it not skipping whitespace? FIXED: it skips the checks on whitespace, confusing the code above.
                    self.advance()
                    continue

                if self.current_char == '#':  # Check for comments
                    self.skip_comment()
                    continue

                if self.current_char.isalpha() or self.current_char == '_':  # Handle keywords/identifiers
                    token, error = self.process_keyword_or_identifier()
                    if error:
                        errors.append(error)
                    else:
                        tokens.append(token)
                elif self.current_char.isdigit():  # Handle numbers
                    token, error = self.make_number()
                    if error:
                        errors.append(error)
                    else:
                        tokens.append(token)
                elif self.current_char == '+':
                    if self.next_char() == '+':  # Check for '++'
                        self.advance()
                        self.advance()
                        current_line = self.line
                        current_column = self.column

                        tokens.append(Token(TT_INCREMENT, '++', current_line, current_column))
                    elif self.next_char() == '=':
                        self.advance()
                        self.advance()
                        current_line = self.line
                        current_column = self.column

                        tokens.append(Token(TT_PLUSEQ, '+=', current_line, current_column))
                    else:
                        tokens.append(Token(TT_PLUS, '+', self.line, self.column))
                        self.advance()
                elif self.current_char == '-':
                    if self.next_char() == '-':  # Check for '--'
                        self.advance()
                        self.advance()
                        current_line = self.line
                        current_column = self.column

                        tokens.append(Token(TT_DECREMENT, '--', current_line, current_column))
                    elif self.next_char() == '=':
                        self.advance()
                        self.advance()
                        current_line = self.line
                        current_column = self.column

                        tokens.append(Token(TT_MINUSEQ, '-=', current_line, current_column))
                    else:
                        tokens.append(Token(TT_MINUS, '-', self.line, self.column))
                        self.advance()
                elif self.current_char == '&':
                    if self.next_char() == '&':
                        self.advance()
                        self.advance()
                        current_line = self.line
                        current_column = self.column

                        tokens.append(Token(TT_AND, '&&', current_line, current_column))
                    else:
                        errors.append(LexerError(f"Illegal character: {self.current_char}", self.line, self.column))
                        self.advance()
                elif self.current_char == '|':
                    if self.next_char() == '|':
                        self.advance()
                        self.advance()
                        current_line = self.line
                        current_column = self.column

                        tokens.append(Token(TT_OR, '||', current_line, current_column))
                    else:
                        errors.append(LexerError(f"Illegal character: {self.current_char}", self.line, self.column))
                        self.advance()
                elif self.current_char == '<':
                    if self.next_char() == '=':
                        current_line = self.line
                        current_column = self.column
                        self.advance()
                        tokens.append(Token(TT_LTEQ, '<=', current_line, current_column))
                    else:
                        tokens.append(Token(TT_LT, '<', self.line, self.column))
                    self.advance()
                elif self.current_char == '>':
                    if self.next_char() == '=':
                        current_line = self.line
                        current_column = self.column
                        self.advance()
                        tokens.append(Token(TT_GTEQ, '>=', current_line, current_column))
                    else:
                        tokens.append(Token(TT_GT, '>', self.line, self.column))
                    self.advance()
                # # Handle invalid operator case (example: invalid operator `@`)
                # elif self.current_char not in ['+', '-', '*', '/', '%', '=', '(', ')', '{', '}', '[', ']', ';', ',', ':', '&', '|', '!', '^', '~', '', '"', "'", '>', '<', ':']:
                #     return [tokens, LexerError(f"Invalid operator: {self.current_char}", self.line, self.column)]
                # Handle multiplication (*)
                elif self.current_char == '*':
                    if self.next_char() == '*':
                        self.advance()
                        tokens.append(Token(TT_EXP, '**'))  # Include lexeme
                    elif self.next_char() == '=':
                        current_line = self.line
                        current_column = self.column
                        self.advance()
                        tokens.append(Token(TT_MULTIEQ, '*=', current_line, current_column))
                    else:
                        tokens.append(Token(TT_MUL, '*'))  # Include lexeme
                    self.advance()
                # Handle division (/)
                elif self.current_char == '/':
                    if self.next_char() == '=':
                        current_line = self.line
                        current_column = self.column
                        self.advance()
                        tokens.append(Token(TT_DIVEQ, '/=', current_line, current_column))
                    else:
                        tokens.append(Token(TT_DIV, '/', self.line, self.column))
                    self.advance()
                # Handle modulo (%)
                elif self.current_char == '%':
                    if self.next_char() == '=':
                        current_line = self.line
                        current_column = self.column
                        self.advance()
                        tokens.append(Token(TT_MODEQ, '%=', current_line, current_column))
                    else:
                        tokens.append(Token(TT_MOD, '%', self.line, self.column))
                    self.advance()
                    
                # Handle parentheses
                elif self.current_char == '(':
                    open_parentheses += 1  # Increment open parentheses count
                    tokens.append(Token(TT_LPAREN, '(', self.line, self.column))
                    self.advance()
                elif self.current_char == ')':
                    open_parentheses -= 1  # Decrement open parentheses count
                    tokens.append(Token(TT_RPAREN, ')', self.line, self.column))
                    self.advance()
                # Handle curly braces
                elif self.current_char == '{':
                    tokens.append(Token(TT_BLOCK_START, '{', self.line, self.column))
                    self.advance()
                elif self.current_char == '}':
                    tokens.append(Token(TT_BLOCK_END, '}', self.line, self.column))
                    self.advance()
                # Handle square brackets
                elif self.current_char == '[':
                    tokens.append(Token(TT_LSQBR, '[', self.line, self.column))
                    self.advance()
                elif self.current_char == ']':
                    tokens.append(Token(TT_RSQBR, ']', self.line, self.column))
                    self.advance()
                elif self.current_char == '!':
                    if self.next_char() == '=':
                        current_line = self.line
                        current_column = self.column
                        self.advance()
                        tokens.append(Token(TT_NOTEQ, '!=', self.line, self.column))
                    else:
                        tokens.append(Token(TT_NOT, '!', self.line, self.column))
                    self.advance()
                elif self.current_char == ':':
                    tokens.append(Token(TT_COLON, ':', self.line, self.column))
                    self.advance()
                elif self.current_char == '~' and self.next_char().isdigit():
                    token, error = self.make_number()
                    if error:
                        errors.append(error)
                    else:
                        tokens.append(token)
                # Handle semicolons
                elif self.current_char == ';':
                    tokens.append(Token(TT_SEMICOLON, ';', self.line, self.column))
                    self.advance()
                # Handle commas
                elif self.current_char == ',':
                    tokens.append(Token(TT_COMMA, ',', self.line, self.column))
                    self.advance()
                elif self.current_char == '.':
                    tokens.append(Token(TT_STRCTACCESS, '.', self.line, self.column))
                    self.advance()
                elif self.current_char == '`':
                    tokens.append(Token(TT_CONCAT, '`', self.line, self.column))
                    self.advance()
                # Handle double quotes for strings
                elif self.current_char == '"':
                    token, error = self.make_string()
                    if error:
                        errors.append(error)
                    else:
                        tokens.append(token)
                # Handle single quotes for character literals
                elif self.current_char == "'":
                    token, error = self.make_char()
                    if error:
                        errors.append(error)
                    else:
                        tokens.append(token)
                elif self.current_char == '=':
                    if self.next_char() == '=':
                        self.advance()
                        self.advance()
                        current_line = self.line
                        current_column = self.column

                        tokens.append(Token(TT_EQTO, '==', current_line, current_column))
                    else:
                        tokens.append(Token(TT_EQ, '=', self.line, self.column))
                        self.advance()
                else:
                    # Catch invalid characters or unexpected sequences
                    errors.append(LexerError(f"Illegal character", self.line, self.column))
                    self.advance()
                
                if self.current_char is None:
                    continue

                if tokens:
                    category = self.KEYWORDS_CATEGORY.get(tokens[-1].type)
                    if category is not None:
                        if category == TC_DATATYPE:
                                if self.current_char not in DELIMITERS['del1']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_MAIN:
                                if self.current_char not in DELIMITERS['del7']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_USERFUNC:
                                if self.current_char not in DELIMITERS['del1']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_CONDITIONAL:
                                if self.current_char not in DELIMITERS['del5']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_JUMP:
                                if self.current_char not in DELIMITERS['del2']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_CVAR:
                                if self.current_char not in DELIMITERS['del1']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_LOOP:
                                if self.current_char not in DELIMITERS['del5']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_LOGIC:
                                if self.current_char not in DELIMITERS['del6']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_CONDITION:
                                if self.current_char not in DELIMITERS['del1']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_DOLS:
                                if self.current_char not in DELIMITERS['del3']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_DEFAULT:
                                if self.current_char not in DELIMITERS['del4']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_FUNC:
                                if self.current_char not in DELIMITERS['del7']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_RETURN:
                                if self.current_char not in DELIMITERS['del8']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_OPENPAREN:
                                if self.current_char not in DELIMITERS['del16']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_CLOSEPAREN:
                                if self.current_char not in DELIMITERS['del18']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_ARITH:
                                if self.current_char not in DELIMITERS['del24']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_LSQUARE:
                                if self.current_char not in DELIMITERS['del12']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_RSQUARE:
                                if self.current_char not in DELIMITERS['del13']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_LCURL:
                                if self.current_char not in DELIMITERS['del14']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_RCURL:
                                if self.current_char not in DELIMITERS['del15']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_INCDEC:
                                if self.current_char not in DELIMITERS['del9']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_ASSIGN:
                                if self.current_char not in DELIMITERS['del24']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_COMMA:
                                if self.current_char not in DELIMITERS['del20']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_NUM:
                                if self.current_char not in DELIMITERS['del23']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_DBL:
                                if self.current_char not in DELIMITERS['del23']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        # elif category == TC_IDENTIFIERS:
                        #         if self.current_char not in DELIMITERS['del22']:
                        #             errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at {self.line} col {self.column}", self.line, self.column)]
                        elif category == TC_RELATIONAL:
                                if self.current_char not in DELIMITERS['del25']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_COLONSEMI:
                                if self.current_char not in DELIMITERS['del11']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_NEGATIVE:
                                if self.current_char not in DELIMITERS['del21']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_LOGICOP:
                                if self.current_char not in DELIMITERS['del25']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_STRLIT:
                                if self.current_char not in DELIMITERS['del19']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_CHRLIT:
                                if self.current_char not in DELIMITERS['del26']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))  
                        elif category == TC_NOT:
                                if self.current_char not in DELIMITERS['del9']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))
                        elif category == TC_STRCONCAT:
                                if self.current_char not in DELIMITERS['del27']:
                                    errors.append(LexerError(f"Unexpected delimiter '{self.current_char}' at line {self.line} col {self.column}", self.line, self.column))  

            # Add EOF token with line and column information
            tokens.append(Token(TT_EOF, 'EOF', self.line, self.column))
            
            remove_tokens = []

            t_index = 0
            for token in tokens:
                for error in errors:
                    print(token)
                    print(error)
                    if token.line == error.line:
                        if token.column == error.column:
                            remove_tokens.append(token)
                    t_index += 1
            
            for token in remove_tokens:
                print(tokens.remove(token))

            print(remove_tokens)
            return tokens, errors
        except Exception as e:
            # Re-raise any unhandled exceptions as LexerError if they aren't already
            if not isinstance(e, LexerError):
                errors.append(LexerError(str(e), self.line, self.column))
            
            else:
                errors.append(e)
            return tokens, errors


    def process_keyword_or_identifier(self):
        key = ""
        line = self.line
        column = self.column
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            key += self.current_char
            self.advance()

        # Check if the first character is valid
        if not (key[0].isalpha()):
            return None, LexerError(f"Identifier '{key}' must start with a letter", self.line, self.column)
        
        # Check if the identifier length is valid (1 to 16 characters)
        if len(key) > 16:
            return None, LexerError(f"Identifier '{key}' exceeds maximum length of 16 characters", self.line, self.column)

        # Return token for keywords or identifiers
        if key in self.KEYWORDS:
            return Token(self.KEYWORDS[key], key, line, column), None
        
        return Token(TT_IDENTIFIER, key, line, column), None

    def make_number(self):
        start_line = self.line
        start_column = self.column
        number_str = ""
        is_decimal = False
        is_negative = False

        if self.current_char == '~':
            is_negative = True
            number_str += '-'
            self.advance()

        # Handle leading zeros for integers
        leading_zeros = 0
        while self.current_char == '0':
            leading_zeros += 1
            self.advance()
        
        # If there were leading zeros and the next char is not a digit or decimal point
        # then the number is just 0
        if leading_zeros > 0 and (self.current_char is None or (not self.current_char.isdigit() and self.current_char != '.')):
            # If the number is just 0 or -0, normalize to 0 (remove negative sign for -0)
            if is_negative:
                # Negative zero is normalized to regular zero
                number_str = "0"
                is_negative = False
            else:
                number_str = "0"
            token_type = TT_INTEGERLIT
            return Token(token_type, number_str, start_line, start_column), None
        
        # If we had leading zeros but the next char is a digit, add just one zero
        # if the next char is a decimal point
        if leading_zeros > 0 and self.current_char == '.':
            number_str += "0"
        elif leading_zeros > 0 and self.current_char is not None and self.current_char.isdigit():
            # Skip the leading zeros for integer (nt) values
            pass
        elif leading_zeros > 0:
            # If there were only zeros and no more digits/decimal point, set to 0
            number_str += "0"

        # Continue collecting the rest of the number
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if is_decimal:
                    return None, LexerError("Invalid number format: multiple decimal points", self.line, self.column)
                is_decimal = True
            number_str += self.current_char
            self.advance()

        # Check if the next character is alphabetic or an underscore
        if self.current_char is not None and (self.current_char.isalpha() or self.current_char == '_'):
            return None, LexerError(f"Invalid identifier starting with a number: '{number_str + self.current_char}'", start_line, start_column)

        # Validate Integer (nt)
        if not is_decimal:
            # For integers, remove any leading zeros
            if number_str.startswith('-'):
                clean_number = '-' + number_str[1:].lstrip('0')
                # If it was all zeros, keep one
                if clean_number == '-' or clean_number == '':
                    clean_number = '0'  # Normalize -0 to 0
                    is_negative = False
            else:
                clean_number = number_str.lstrip('0')
                # If it was all zeros, keep one
                if clean_number == '':
                    clean_number = '0'
                    
            if len(clean_number) > 16 and not clean_number.startswith('-'):
                return None, LexerError(f"Integer exceeds maximum length of 16 digits", start_line, start_column)
            if len(clean_number) > 17 and clean_number.startswith('-'):  # Account for negative sign
                return None, LexerError(f"Integer exceeds maximum length of 16 digits", start_line, start_column)
            
            token_type = TT_NEGINTLIT if is_negative else TT_INTEGERLIT
            return Token(token_type, clean_number, start_line, start_column), None

        # Validate Double (dbl)
        else:
            # For doubles, handle trailing zeros in decimal part
            parts = number_str.split('.')
            
            # Clean the whole number part (remove leading zeros)
            if parts[0].startswith('-'):
                whole_part = '-' + parts[0][1:].lstrip('0')
                if whole_part == '-':
                    whole_part = '-0'
            else:
                whole_part = parts[0].lstrip('0')
                if whole_part == '':
                    whole_part = '0'
            
            # Clean the decimal part (remove trailing zeros, keep at least 2 digits)
            decimal_part = parts[1].rstrip('0')
            if decimal_part == '':
                decimal_part = '00'  # Ensure at least 2 decimal places
            elif len(decimal_part) == 1:
                decimal_part = decimal_part + '0'  # Ensure at least 2 decimal places
                
            # Check for length limits
            if len(whole_part) > 16 and not whole_part.startswith('-'):
                return None, LexerError("Double's whole number part exceeds 16 digits", start_line, start_column)
            if len(whole_part) > 17 and whole_part.startswith('-'):  # Account for negative sign
                return None, LexerError("Double's whole number part exceeds 16 digits", start_line, start_column)
            if len(decimal_part) < 1 or len(decimal_part) > 8:
                return None, LexerError("Double's decimal part must be between 1 and 8 digits", start_line, start_column)
            
            # Reconstruct the cleaned double
            clean_number = whole_part + '.' + decimal_part
            
            # Normalize -0.00 to 0.00
            if clean_number.startswith('-0.') and all(d == '0' for d in clean_number[3:]):
                clean_number = clean_number[1:]  # Remove the negative sign
                is_negative = False
                
            token_type = TT_NEGDOUBLELIT if is_negative else TT_DOUBLELIT
            return Token(token_type, clean_number, start_line, start_column), None

    def make_string(self):
        start_line = self.line
        start_column = self.column
        string_value = ''
        self.advance()  # Skip the opening quote

        if self.current_char == '"':
            self.advance()  # Skip the closing quote
            return Token(TT_STRINGLIT, 'empty', start_line, start_column), None

        while self.current_char is not None and self.current_char != '"' and self.current_char != '\n':
            string_value += self.current_char
            self.advance()

        if self.current_char != '"':
            return None, LexerError("Unterminated string literal", start_line, start_column)

        self.advance()  # Skip the closing quote
        return Token(TT_STRINGLIT, string_value, start_line, start_column), None