# test_parser.py
import definitions
import sys
from lexer import Lexer
from parser import parse

# Load your Conso file
with open('test.conso', 'r') as f:
    source_code = f.read()

# Run the lexer
print("Running lexer...")
lexer = Lexer(source_code)
tokens, errors = lexer.make_tokens()

if errors:
    print(f"Lexer errors: {errors}")
    sys.exit(1)

print(f"Lexer produced {len(tokens)} tokens")

# Reset definitions module globals
print("Resetting definitions module globals...")
definitions.token = []
definitions.state = []
definitions.lexeme = []
definitions.idens = []

# Manually populate the token list
print("Populating token list...")
for t in tokens:
    definitions.token.append((t.type, t.value, t.line, t.column))

print(f"Token list in definitions module now has {len(definitions.token)} tokens")

# Check what's in token before parsing
print(f"First 5 tokens: {definitions.token[:5]}")
print(f"Last 5 tokens: {definitions.token[-5:]}")

# Now try to parse
print("About to call parse()...")
print(f"Is token imported correctly in parser.py? Let's see if parse() can access it...")

try:
    log_messages, error_message, syntax_valid = parse()
    print(f"Parser returned: syntax_valid={syntax_valid}")
    if not syntax_valid:
        print(f"Parser errors: {error_message}")
    else:
        print("Parsing successful!")
except Exception as e:
    print(f"Exception during parsing: {e}")