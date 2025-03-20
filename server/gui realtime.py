import tkinter as tk
from tkinter import ttk, filedialog, PhotoImage, font
from lexer import Lexer
from parser import *
from definitions import *

# Create the main application window
root = tk.Tk()
root.title("Conso Lexer & Parser")
root.geometry("1920x1080")  # Set window size

# Function to update line numbers
def update_line_numbers(event=None):
    line_numbers.config(state="normal")
    line_numbers.delete("1.0", "end")
    lines = text_editor.get("1.0", "end").count("\n")
    line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
    line_numbers.config(state="disabled")
    line_numbers.tag_add("center", "1.0", "end")
    line_numbers.config(state="disabled")
    line_numbers.tag_configure("center", justify="center")

# Function to run lexer and parser automatically on text change
def on_text_change(event=None):
    update_line_numbers()  # ✅ Keep line numbers updated
    root.after(300, run_lexer)  # ✅ Delay execution to prevent excessive calls

def run_lexer():
    global token  

    terminal.delete("1.0", tk.END)
    parser_terminal.delete("1.0", tk.END)

    # Clear the table before inserting new values
    for item in table.get_children():
        table.delete(item)

    # Get the input from the text editor
    input_code = text_editor.get("1.0", tk.END).strip()

    if not input_code:  # Prevents running lexer on empty input
        return

    try:
        lexer = Lexer(input_code)
        tokens, errors = lexer.make_tokens()

        token.clear()
        token.extend([(tok.type, tok.line, tok.column) for tok in tokens])

        terminal.insert(tk.END, f"Tokens generated: {token}\n")

        # ✅ Populate the table with lexemes and token types
        for tok in tokens:
            table.insert("", "end", values=(tok.value, tok.type))

        # Run parser automatically after lexing
        run_parser()

    except Exception as e:
        terminal.insert(tk.END, f"Lexer Error: {str(e)}\n")

def run_parser():
    parser_terminal.delete("1.0", tk.END)

    try:
        result, error_message, syntax_valid = parse()  # Unpack all three values
        terminal.insert(tk.END, "Parser run successfully!\n")

        for log in result:
            parser_terminal.insert(tk.END, log + "\n")

        if error_message:
            for error in error_message:
                terminal.insert(tk.END, error + "\n")
                parser_terminal.insert(tk.END, error + "\n")
        
        # You can also use the syntax_valid flag if needed
        if syntax_valid:
            terminal.insert(tk.END, "Syntax is valid!\n")

    except ParserError as e:
        terminal.insert(tk.END, f"{str(e)}\n")
        parser_terminal.insert(tk.END, f"{str(e)}\n")
    except Exception as e:
        terminal.insert(tk.END, f"Parser Error: {str(e)}\n")
        parser_terminal.insert(tk.END, f"Parser Error: {str(e)}\n")

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
            update_line_numbers()  # ✅ Update line numbers after loading a file
        except Exception as e:
            terminal.insert(tk.END, f"Error loading file: {str(e)}\n")

# Color scheme
conso_blue = "#649ad1"
cs_black = "#1e1e1e"
dark = "#252526"
gray = "#333333"

root.configure(bg=dark)

# Text Editor Panel
text_editor_frame = tk.Frame(root, bg=cs_black)
text_editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

file_name = tk.StringVar()
file_name.set("")
file_name_label = tk.Label(text_editor_frame, textvariable=file_name, bg=conso_blue, fg="white", font=("Calibri", 14), anchor="w")
file_name_label.pack(side=tk.TOP, fill=tk.X)

# Line Numbers Panel
line_numbers = tk.Text(text_editor_frame, width=4, bg=conso_blue, fg="#d4d4d4", state="disabled", font=("Calibri", 20), relief="flat")
line_numbers.pack(side=tk.LEFT, fill=tk.Y)

# Main Text Editor
text_editor = tk.Text(text_editor_frame, wrap="word", bg=cs_black, fg="#d4d4d4", insertbackground="white", font=("Calibri", 20), relief="flat")
text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

# Scrollbar
text_editor_scroll = ttk.Scrollbar(text_editor_frame, orient="vertical", command=text_editor.yview)
text_editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
text_editor.configure(yscrollcommand=text_editor_scroll.set)
line_numbers.configure(yscrollcommand=text_editor_scroll.set)

# Bind real-time lexer/parser execution
text_editor.bind("<KeyRelease>", on_text_change)

# Button Panel
button_frame = tk.Frame(root, bg=dark)
button_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

save_button = tk.Button(button_frame, text="Save File", command=save_to_cns_file, bg=conso_blue, fg="white", font=('Calibri', 12))
save_button.pack(side=tk.LEFT, padx=5, pady=0)

load_button = tk.Button(button_frame, text="Load File", command=load_cns_file, bg=conso_blue, fg="white", font=('Calibri', 12))
load_button.pack(side=tk.LEFT, padx=5, pady=0)

# Token Table (Lexical Analysis)
table_frame = tk.Frame(root, bg="#1e1e1e", height=300)
table_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

columns = ("Lexeme", "Token")
table = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
table.heading("Lexeme", text="Lexeme")      
table.heading("Token", text="Token")
table.column("Lexeme", anchor="center", width=200)
table.column("Token", anchor="center", width=200)

table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Parser Output Terminal
parser_terminal_frame = tk.Frame(root, height=400)
parser_terminal_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=5, pady=5)

parser_terminal_label = tk.Label(parser_terminal_frame, text="Parser Output", bg=conso_blue, fg="white", font=("Calibri", 14))
parser_terminal_label.pack(side=tk.TOP, fill=tk.X)

parser_terminal = tk.Text(parser_terminal_frame, wrap="word", bg=gray, fg="#d4d4d4", insertbackground="white", height=14, font=("Calibri", 12))
parser_terminal.pack(fill=tk.BOTH, expand=True)

# Main Terminal
terminal_frame = tk.Frame(root, height=400)
terminal_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=5, pady=5)

terminal_label = tk.Label(terminal_frame, text="Terminal", bg=conso_blue, fg="white", font=("Calibri", 14))
terminal_label.pack(side=tk.TOP, fill=tk.X)

terminal = tk.Text(terminal_frame, wrap="word", bg=gray, fg="#d4d4d4", insertbackground="white", height=14, font=("Calibri", 12))
terminal.pack(fill=tk.BOTH, expand=True)

# Start the main loop
root.mainloop()