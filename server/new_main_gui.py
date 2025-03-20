import tkinter as tk
from tkinter import ttk, filedialog, PhotoImage, font
from lexer import Lexer
from parser import *
from definitions import *
from semantic import *
import re

# Create the main application window
root = tk.Tk()
root.title("Conso Lexer & Parser")
root.geometry("1920x1080")  # Set window size

# Conso keywords for syntax highlighting
CONSO_KEYWORDS = [
    'npt', 'prnt', 'nt', 'dbl', 'strng', 'bln', 'chr', 
    'f', 'ls', 'lsf', 'swtch', 'fr', 'whl', 'd', 'mn', 'cs', 
    'dflt', 'brk', 'cnst', 'tr', 'fls', 'fnctn', 'rtrn', 'nll',
    'end', 'cntn', 'strct', 'dfstrct', 'vd'
]

# Function to update line numbers
def update_line_numbers(event=None):
    line_numbers.config(state="normal")
    line_numbers.delete("1.0", "end")
    lines = text_editor.get("1.0", "end").count("\n")
    line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
    line_numbers.config(state="disabled")
    line_numbers.tag_add("center", "1.0", "end")
    line_numbers.tag_configure("center", justify="center")

    # Ensure line numbers stay aligned with the text editor
    line_numbers.yview_moveto(text_editor.yview()[0])

# Function to handle tab key press - insert 4 spaces instead of a tab character
def handle_tab(event):
    text_editor.insert(tk.INSERT, " " * 4)
    return "break"  # Prevents the default tab behavior

# Function to run lexer and parser automatically on text change
def on_text_change(event=None):
    update_line_numbers()  # Keep line numbers updated
    clear_semantic_messages()  # Clear semantic messages when text changes
    highlight_syntax_simple()  # Simple syntax highlighting
    root.after(300, run_lexer)  # Delay execution to prevent excessive calls

# Simple syntax highlighting that won't conflict with analyzers
def highlight_syntax_simple():
    # Clear all existing tags
    for tag in ["keyword", "string", "number"]:
        text_editor.tag_remove(tag, "1.0", "end")
    
    # Configure tags if not already done
    if not hasattr(text_editor, "highlight_tags_configured"):
        text_editor.tag_configure("keyword", foreground="#569CD6")  # Blue for keywords
        text_editor.tag_configure("string", foreground="#CE9178")   # Orange for strings
        text_editor.tag_configure("number", foreground="#B5CEA8")   # Light green for numbers
        text_editor.highlight_tags_configured = True
    
    # Simple direct keyword highlighting
    for keyword in CONSO_KEYWORDS:
        pos = "1.0"
        while True:
            # Find the keyword with word boundaries
            pos = text_editor.search(f"\\y{keyword}\\y", pos, "end", regexp=True)
            if not pos:
                break
            
            # Apply tag
            end_pos = f"{pos}+{len(keyword)}c"
            text_editor.tag_add("keyword", pos, end_pos)
            pos = end_pos
    
    # Highlight strings
    pos = "1.0"
    while True:
        # Find opening quote
        pos = text_editor.search('"', pos, "end")
        if not pos:
            break
        
        # Find closing quote
        end_quote = text_editor.search('"', f"{pos}+1c", "end")
        if not end_quote:
            # No closing quote found, move to next position
            pos = f"{pos}+1c"
            continue
        
        # Apply tag to the entire string including quotes
        text_editor.tag_add("string", pos, f"{end_quote}+1c")
        pos = f"{end_quote}+1c"
    
    # Highlight numbers
    pos = "1.0"
    while True:
        # Find numbers (both integers and decimals)
        pos = text_editor.search(r'\d+(\.\d+)?', pos, "end", regexp=True)
        if not pos:
            break
        
        # Get the matched text length
        match_end = text_editor.search(r'[^\d.]', f"{pos}+1c", f"{pos} lineend", regexp=True)
        if not match_end:
            match_end = f"{pos} lineend"
        
        # Apply tag
        text_editor.tag_add("number", pos, match_end)
        pos = match_end

# Function to run lexer and parser automatically on text change
def on_text_change(event=None):
    update_line_numbers()  # Keep line numbers updated
    clear_semantic_messages()  # Clear semantic messages when text changes
    highlight_syntax_simple()  # Simple syntax highlighting
    root.after(300, run_lexer)  # Delay execution to prevent excessive calls

def sync_scroll(*args):
    """Sync the scrolling of the text editor and line numbers."""
    line_numbers.yview_moveto(args[0])
    text_editor.yview_moveto(args[0])

def on_scroll(*args):
    """Handle vertical scrolling for both widgets."""
    text_editor.yview(*args)
    line_numbers.yview(*args)

def clear_semantic_messages():
    """Clear semantic analysis related messages from the terminal"""
    # Get all text from terminal
    terminal_text = terminal.get("1.0", tk.END)
    # Remove semantic analysis related messages
    lines = terminal_text.split('\n')
    filtered_lines = [line for line in lines if not any(msg in line for msg in 
        ["Semantic analysis completed successfully",
         "Semantic errors found:",
         "  - "])]
    # Clear terminal and rewrite filtered content
    terminal.delete("1.0", tk.END)
    terminal.insert(tk.END, '\n'.join(filtered_lines))

def run_lexer():
    global token  

    terminal.delete("1.0", tk.END)

    # Clear the table before inserting new values
    for item in table.get_children():
        table.delete(item)

    # Get the input from the text editor
    input_code = text_editor.get("1.0", tk.END).strip()

    if not input_code:  # Prevents running lexer on empty input
        semantic_button.config(state="disabled")
        return

    try:
        lexer = Lexer(input_code)
        tokens, errors = lexer.make_tokens()

        token.clear()
        token.extend([(tok.type, tok.line, tok.column) for tok in tokens])

        print(f"Tokens generated: {token}\n")

        # Populate the table with lexemes and token types
        for tok in tokens:
            table.insert("", "end", values=(tok.value, tok.type))

        if not errors:
            terminal.insert(tk.END, "Lexer run successfully!\n")
            run_parser()  # Automatically run the parser after lexing
        else:
            semantic_button.config(state="disabled")  # Disable semantic button when lexical errors exist
            for err in errors:
                terminal.insert(tk.END, f"Lexical Error: {str(err)}\n")

    except Exception as e:
        terminal.insert(tk.END, f"Lexer Error: {str(e)}\n")
        semantic_button.config(state="disabled")  # Disable semantic button on lexer errors

def run_parser():
    try:
        result, error_message, syntax_valid = parse()  # Get the syntax_valid flag
        terminal.insert(tk.END, "Parser run successfully!\n")

        if error_message:
            for error in error_message:
                terminal.insert(tk.END, error + "\n")
        
        # Enable/disable semantic button based on syntax validity
        if syntax_valid:
            semantic_button.config(state="normal")
        else:
            semantic_button.config(state="disabled")

    except ParserError as e:
        terminal.insert(tk.END, f"{str(e)}\n")
        semantic_button.config(state="disabled")
        
    except Exception as e:
        terminal.insert(tk.END, f"Parser Error: {str(e)}\n")
        semantic_button.config(state="disabled")

# Function to run semantic analyzer
def run_semantic_analyzer():
    global token
    input_code = text_editor.get("1.0", tk.END).strip()
    if not input_code:  # Prevents running lexer on empty input
        return
    try:
        # Save the original tokens for parser use
        original_tokens = token.copy()
        
        lexer = Lexer(input_code)
        tokens, errors = lexer.make_tokens()
        
        # Create semantic tokens in the correct format
        semantic_tokens = [(tok.type, tok.value, tok.line, tok.column) for tok in tokens]
        print(semantic_tokens)
        if not semantic_tokens:
            terminal.insert(tk.END, "Error: No tokens available. Run lexer first.\n")
            return
            
        # Create an instance of the semantic analyzer
        analyzer = SemanticAnalyzer()
        
        # Run the semantic analysis on the token stream
        success, errors = analyzer.analyze(semantic_tokens)
        
        if success:
            terminal.insert(tk.END, "Semantic analysis completed successfully!\n")
        else:
            terminal.insert(tk.END, "Semantic errors found:\n")
            for error in errors:
                terminal.insert(tk.END, f"  - {error}\n")
        
        # Restore the original tokens for the parser to use
        token[:] = original_tokens
        
    except Exception as e:
        terminal.insert(tk.END, f"Semantic Analyzer Error: {str(e)}\n")
        

# Function to save file
def save_to_cns_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".cns",
        filetypes=[("Conso Files", "*.cns"), ("All Files", "*.*")],
        title="Save File"
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                content = text_editor.get("1.0", tk.END).strip()
                file.write(content)
            file_name.set(file_path.split("/")[-1])
            terminal.insert(tk.END, f"File saved successfully: {file_path}\n")
        except Exception as e:
            terminal.insert(tk.END, f"Error saving file: {str(e)}\n")

# Function to load file
def load_cns_file():
    file_path = filedialog.askopenfilename(
        defaultextension=".cns",
        filetypes=[("Conso Files", "*.cns"), ("All Files", "*.*")],
        title="Open File"
    )
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            text_editor.delete("1.0", tk.END)
            text_editor.insert("1.0", content)
            file_name.set(file_path.split("/")[-1])
            terminal.insert(tk.END, f"File loaded successfully: {file_path}\n")
            update_line_numbers()  # Update line numbers after loading a file
            highlight_syntax_simple()  # Apply syntax highlighting after loading
        except Exception as e:
            terminal.insert(tk.END, f"Error loading file: {str(e)}\n")

# Color scheme
conso_blue = "#649ad1"
cs_black = "#1e1e1e"
dark = "#252526"
gray = "#333333"

root.configure(bg=dark)

# Button Panel at the top
button_frame = tk.Frame(root, bg=dark)
button_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

save_button = tk.Button(button_frame, text="Save File", command=save_to_cns_file, bg=conso_blue, fg="white", font=('Calibri', 12))
save_button.pack(side=tk.LEFT, padx=5, pady=0)

load_button = tk.Button(button_frame, text="Load File", command=load_cns_file, bg=conso_blue, fg="white", font=('Calibri', 12))
load_button.pack(side=tk.LEFT, padx=5, pady=0)

# Add semantic analyzer button
semantic_button = tk.Button(button_frame, text="Semantic Analysis", command=run_semantic_analyzer, bg=conso_blue, fg="white", font=('Calibri', 12))
semantic_button.pack(side=tk.LEFT, padx=5, pady=0)

# Main content area
content_frame = tk.Frame(root, bg=dark)
content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

# Left panel for editor and terminal
left_panel = tk.Frame(content_frame, bg=dark, width=1600)
left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=0, pady=0)
left_panel.pack_propagate(False)  # Prevent the frame from shrinking

# Create a PanedWindow to allow resizing between text editor and terminal
paned_window = tk.PanedWindow(left_panel, orient=tk.VERTICAL, bg=dark, sashwidth=5, sashrelief="raised")
paned_window.pack(fill=tk.BOTH, expand=True)

# Text Editor Panel (top left) - now shorter
text_editor_frame = tk.Frame(paned_window, bg=cs_black)

file_name = tk.StringVar()
file_name.set("")
file_name_label = tk.Label(text_editor_frame, textvariable=file_name, bg=conso_blue, fg="white", font=("Calibri", 13), anchor="w")
file_name_label.pack(side=tk.TOP, fill=tk.X)

# Line Numbers Panel
line_numbers_frame = tk.Frame(text_editor_frame, bg=dark, highlightbackground="white", highlightthickness=1)
line_numbers_frame.pack(side=tk.LEFT, fill=tk.Y)
line_numbers = tk.Text(line_numbers_frame, width=2, bg=cs_black, fg="#d4d4d4", state="disabled", font=("Calibri", 25), relief="flat")
line_numbers.pack(fill=tk.BOTH, expand=True)

# Main Text Editor
text_editor = tk.Text(text_editor_frame, wrap="word", bg=cs_black, fg="#d4d4d4", insertbackground="white", font=("Calibri", 25), relief="flat")
text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

# Scrollbar
text_editor_scroll = ttk.Scrollbar(text_editor_frame, orient="vertical")
text_editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# Configure text widgets to sync scrolling
text_editor.configure(yscrollcommand=lambda *args: sync_scroll(*args))
line_numbers.configure(yscrollcommand=lambda *args: sync_scroll(*args))
text_editor_scroll.config(command=on_scroll)

# Bind text editor events
text_editor.bind("<KeyRelease>", on_text_change)  # For lexer/parser and syntax highlighting
text_editor.bind("<Tab>", handle_tab)  # Custom tab handling

# Terminal Panel (bottom left) - now taller
terminal_frame = tk.Frame(paned_window, bg=cs_black)

terminal_label = tk.Label(terminal_frame, text="Terminal", bg=conso_blue, fg="white", font=("Calibri", 14))
terminal_label.pack(side=tk.TOP, fill=tk.X)

terminal = tk.Text(terminal_frame, wrap="word", bg=cs_black, fg="#d4d4d4", insertbackground="white", font=("Calibri", 20))
terminal.pack(fill=tk.BOTH, expand=True)

# Add both frames to the paned window with initial sizes
# Text editor takes 40% of the space, terminal takes 60%
paned_window.add(text_editor_frame, height=700)  # Start with smaller height for text editor
paned_window.add(terminal_frame, height=600)     # Start with larger height for terminal

# Right panel for token table (entire right side)
right_panel = tk.Frame(content_frame, bg=dark, width=300)
right_panel.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=(5, 0))

# Token Table Label
table_label = tk.Label(right_panel, text="Lexical Analysis", bg=conso_blue, fg="white", font=("Calibri", 14))
table_label.pack(side=tk.TOP, fill=tk.X)

# Token Table (Lexical Analysis)
table_frame = tk.Frame(right_panel, bg="#1e1e1e")
table_frame.pack(side=tk.TOP, fill=tk.Y, expand=True)

# --- MODIFIED: Create and configure a custom style for the Treeview with larger font ---
style = ttk.Style()
style.configure("Treeview", font=("Calibri", 14))  # Increased font size for table content
style.configure("Treeview.Heading", font=("Calibri", 14, "bold"))  # Increased font size for headers

columns = ("Lexeme", "Token")
table = ttk.Treeview(table_frame, columns=columns, show="headings", style="Treeview")
table.heading("Lexeme", text="Lexeme")      
table.heading("Token", text="Token")
table.column("Lexeme", anchor="center", width=200)
table.column("Token", anchor="center", width=100)

# --- MODIFIED: Adjust row height for better readability with larger font ---
table.configure(height=20)  # Set approximate number of visible rows
table.pack(side=tk.LEFT, fill=tk.Y, expand=True)

# Add scrollbar for the table
table_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
table_scroll.pack(side=tk.RIGHT, fill=tk.Y)
table.configure(yscrollcommand=table_scroll.set)

# Initialize syntax highlighting
text_editor.tags_configured = False

# Start the main loop
root.mainloop()