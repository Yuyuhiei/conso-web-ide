# Conso Programming Language

## Introduction

Conso is an innovative, strictly case-sensitive programming language designed to combine the simplicity and elegance of Python with the performance and versatility of C. It features a unique vowel-less syntax and supports multiple programming paradigms, including procedural and functional programming. The language's explicit syntax rules help reduce errors and ensure that code is well-structured and easy to maintain, making it a powerful tool for developers of all skill levels.

## Syntax and Naming Conventions

### Identifiers
Identifiers are names assigned to program elements like variables, functions, and arrays.
* **Case-Sensitivity:** Identifiers are case-sensitive (e.g., `myVar` is different from `myvar`).
* **Naming Rules:** Must start with a letter. Subsequent characters can be letters, numbers (0-9), or the underscore (`_`).
* **Length:** Identifiers can be from 1 to 16 characters long.
* **Invalid Characters:** Special characters other than the underscore are not permitted.

### Comments
Conso supports single-line comments, which start with the `#` symbol. The compiler ignores all text from the `#` to the end of the line.

## Reserved Words and Symbols

### Keywords

**Input and Output**
* `npt`: Represents input operations, similar to `scanf`.
* `prnt`: Represents output operations, similar to `printf`.

**Data Types**
* `nt`: Represents an integer data type.
* `dbl`: Represents a decimal (double) number.
* `strng`: Represents a sequence of characters or text.
* `bln`: Represents a boolean data type (`tr` or `fls`).
* `chr`: Represents a single-character value.

**Conditional Statements**
* `f`: Executes a block of code if a condition is true.
* `ls`: Executes a block of code if the previous condition(s) are false.
* `lsf`: Combines `ls` and `f` for additional conditional checks.
* `swtch`: Begins a switch block for multi-way branching.

**Loop Statements**
* `fr`: Creates a loop that iterates over a sequence (for loop).
* `whl`: Creates a loop that continues as long as a condition is true (while loop).
* `d`: Creates a loop that executes once before checking the condition (do-while loop).

**Functions and Program Structure**
* `mn`: Serves as the main function of the program.
* `fnctn`: Defines a function.
* `rtrn`: Exits a function, optionally returning a value.
* `vd`: Specifies a void return type for a function that does not return a value.
* `end`: Exits the main (`mn`) function.

**Constants and Structures**
* `cnst`: Declares a constant with a value that cannot be changed.
* `strct`: Defines a structured data type.
* `dfstrct`: Instantiates a structured data type.

**Control Flow and Values**
* `cs`: Indicates a specific condition within a `swtch` block.
* `dflt`: Specifies the default case in a `swtch` block.
* `brk`: Exits a loop or `swtch` block.
* `cntn`: Skips the current iteration of a loop and proceeds to the next.
* `tr`: Represents the boolean value `true`.
* `fls`: Represents the boolean value `false`.
* `nll`: Represents the absence of a value, or a null value.

### Operators and Symbols

**Arithmetic Operators**
* `+`: Addition
* `-`: Subtraction
* `*`: Multiplication
* `/`: Division
* `%`: Modulus (remainder)

**Assignment Operators**
* `=`: Assigns the value on the right to the variable on the left.
* `+=`: Adds and assigns.
* `-=`: Subtracts and assigns.
* `*=`: Multiplies and assigns.
* `/=`: Divides and assigns.
* `%=`: Computes modulus and assigns.

**Logical Operators**
* `&&`: Logical AND. Returns `tr` if both operands are true.
* `||`: Logical OR. Returns `tr` if at least one operand is true.
* `!`: Logical NOT. Reverses the logical state of its operand.

**Increment/Decrement Operators**
* `++`: Increments by 1.
* `--`: Decrements by 1.

**Comparison/Relational Operators**
* `==`: Equal to.
* `!=`: Not equal to.
* `>`: Greater than.
* `<`: Less than.
* `>=`: Greater than or equal to.
* `<=`: Less than or equal to.

**Delimiters and Other Symbols**
* `;`: Terminates a statement.
* `:`: Used in `swtch` cases.
* `.`: Used to access struct members and to identify a `dbl` data type.
* `` ` ``: Concatenates strings.
* `,`: Separates multiple variable declarations.
* `{ }`: Encloses a block of executable statements (e.g., in a function or loop). Also used for array initialization.
* `( )`: Encloses conditional statements, function arguments, and parameters.
* `[ ]`: Encloses elements of a list/array.
* `' '`: Encloses a single `chr` data type.
* `" "`: Encloses a `strng` data type.
* `~`: Identifies negative numbers.
* `\n`: Newline character.
* `\t`: Tab character.
* `\"`: Escaped double quote character.

## Data Types and Variables

### Variable Declaration
Variables are used to store information. They can be declared globally (before the `mn` function) or locally.

* **Syntax:** Declarations start with a data type followed by an identifier and end with a semicolon.
    * `<data_type> <identifier>;`
    * `<data_type> <identifier> = <value>;`
* **Multiple Declarations:** Multiple variables of the same data type can be declared on one line, separated by commas.
    * `nt a, b, c;`
* **Default Values:** If a variable is declared without an initial value, Conso assigns a default value to ensure predictable behavior:
    * `nt`: 0
    * `dbl`: 0.00
    * `bln`: `fls`
    * `chr`: `\0` (null character)
    * `strng`: `NULL`

### Integers (`nt`)
Represents whole numbers (positive, negative, or zero).
* **Declaration:** Uses the `nt` keyword.
* **Negative Numbers:** Prefixed with a tilde (`~`). Example: `nt a = ~17;`
* **Initialization:** Can be initialized during declaration but is not required.

### Doubles (`dbl`)
Represents real numbers with decimal points for high-precision calculations.
* **Declaration:** Uses the `dbl` keyword.
* **Syntax:** Doubles must always include a decimal point. Values are formatted to two decimal places by default.
* **Precision:** Allows up to 8 digits before the decimal point and a maximum of 6 digits after.
* **Negative Numbers:** Prefixed with a tilde (`~`). Example: `dbl pi = ~3.14;`

### Booleans (`bln`)
Represents logical values `tr` (true) and `fls` (false).
* **Declaration:** Uses the `bln` keyword.
* **Values:** Can only store `tr` or `fls`. Defaults to `fls` if uninitialized.
* **Output:** When printed, `tr` is displayed as `1` and `fls` is displayed as `0`.

### Characters (`chr`)
Represents a single ASCII character.
* **Declaration:** Uses the `chr` keyword.
* **Syntax:** The character must be enclosed in single quotes (`'`).
* **Default Value:** Defaults to a null terminator (`\0`) if uninitialized.
* **Content:** Can store any single letter, digit, punctuation mark, or special symbol.

### Strings (`strng`)
Represents a sequence of characters treated as a single, immutable entity.
* **Declaration:** Uses the `strng` keyword.
* **Syntax:** The string must be enclosed in double quotes (`"`).
* **Default Value:** Defaults to `NULL` if uninitialized.
* **Concatenation:** Strings can be concatenated during declaration using the backtick (`` ` ``) operator. Example: `strng quote = "Conso rocks!" ` "Yeah!";`
* **Special Characters:** Supports escape sequences like `\n` (newline) and `\t` (tab).

### Constants (`cnst`)
Read-only variables whose values cannot be modified after declaration.
* **Syntax:** Must start with the `cnst` keyword, followed by a data type, identifier, and an assigned value.
* **Initialization:** All constants must be initialized at the time of declaration.
* **Example:** `cnst nt MAX_VALUE = 100;`

## Data Structures

### Arrays
A fixed-size collection of items of the same data type, stored in contiguous memory locations.
* **Declaration:** The array's size must be strictly initialized. Elements are optional and enclosed in curly braces (`{}`).
    * `nt numbers[3];`
    * `strng names[2] = {"dan", "erdz"};`
* **Indexing:** Array indexing starts at 0.
* **Accessing Elements:** Elements are accessed using the identifier followed by the index in square brackets (`[]`). Example: `names[1];`
* **Dimensions:** Arrays can be one-dimensional or two-dimensional.
* **Two-Dimensional Arrays:** Declared with row and column sizes. Elements are initialized in nested curly braces.
    * `nt dates[3][4] = {{1,2,3,4}, {5,6,7,8}, {9,10,11,12}};`
    * Access: `dates[1][2];`

### Structs (`strct`)
A way to group several related variables into a single location.
* **Declaration (`strct`):** Uses the `strct` keyword, followed by an identifier and curly braces. Members are declared inside on new lines. Structs can only be declared globally.
    ```
    strct myStruct {
        nt age;
        dbl grade;
    };
    ```
* **Instantiation (`dfstrct`):** Uses the `dfstrct` keyword to create an instance of a struct. It can be used globally or locally.
    ```
    dfstrct myStruct struct1, struct2;
    ```
* **Accessing Members:** Use dot notation (`.`) to access or assign values to members. A struct member cannot be used or accessed if it has not been initialized.
    ```
    mn(){
        dfstret myStruct s1;
        s1.age = 20;
    }
    ```

## Control Flow

### Conditional Statements (`f`, `lsf`, `ls`)
* **`f` Statement:** The condition must be enclosed in parentheses `()`, and the body in curly braces `{}`.
* **`lsf` / `ls` Statements:** An `lsf` or `ls` must follow an `f` or another `lsf` statement.
* **Nesting:** Conditional statements can be nested inside one another.

### Switch Statements (`swtch`)
Provides a multi-way branching capability.
* **Syntax:** Starts with `swtch` followed by an identifier in parentheses. The body is enclosed in curly braces `{}`.
* **Cases (`cs`):** Each case is defined with `cs <value>:` and must end with a `brk;` statement. The case value must be an integer (`nt`) or character (`chr`).
* **Default (`dflt`):** An optional `dflt:` case handles all other values and must also end with `brk;`.

### Loop Statements (`fr`, `whl`, `d`)
* **`fr` loop:** The `fr` statement requires three parts separated by semicolons: an initialization expression, a test condition, and an increment/decrement statement. The loop variable must be declared before the loop.
    ```
    nt i;
    fr(i = 0; i < 5; i++) {
        prnt("Hello");
    }
    ```
* **`whl` loop:** The `whl` statement executes a block of code as long as its condition, enclosed in `()`, is true.
* **`d-whl` loop:** Starts with the `d` keyword and its body, followed by `whl` and the condition. The body is always executed at least once.

## Functions
A self-contained, reusable block of code that performs a specific task.
* **Declaration (`fnctn`):** Starts with `fnctn`, a return type (`nt`, `dbl`, `vd`, etc.), a unique identifier, and optional parameters in parentheses `()`. Functions can only be declared globally. The body is enclosed in `{}`.
    ```
    fnctn nt add(nt a, nt b) {
        rtrn a + b;
    }
    ```
* **Return Statement (`rtrn`):** A function with a non-void return type must end with `rtrn <value>;`. A `vd` function does not use `rtrn`.
* **Function Calls:** A function is called using its identifier followed by parentheses containing any required arguments. The number, order, and data types of arguments must match the function's parameters.

## Expressions
An expression is a combination of values, variables, operators, and function calls that is evaluated to produce a result.

### Arithmetic Expressions
* **Operations:** Supports addition (`+`), subtraction (`-`), multiplication (`*`), division (`/`), and modulus (`%`).
* **Type Compatibility:** Arithmetic operations are strictly typed. They are allowed between two integers or between two doubles. Mixed-type arithmetic (e.g., `nt` and `dbl`) is not permitted.

### Relational Expressions
* **Operations:** Compares two values and evaluates to a boolean (`tr` or `fls`).
* **Type Compatibility:**
    * `==` and `!=`: Can be used on operands of the same type (integer-to-integer, string-to-string, etc.).
    * `>`, `<`, `>=`, `<=`: Are restricted to numeric types (integer-to-integer and double-to-double). Comparing other types like strings with these operators is not allowed.

### Logical Expressions
* **Operations:** Combines boolean values using logical operators `&&` (AND), `||` (OR), and `!` (NOT).
* **Type Compatibility:** Logical operators are only allowed on boolean values or expressions that evaluate to a boolean.

### Assignment Expressions
* **Syntax:** An identifier on the left, an assignment operator, and a value or expression on the right.
* **Operators:** Supports simple assignment (`=`) and compound operators (`+=`, `-=`, `*=`, `/=`, `%=`).

## Input and Output

### Input (`npt`)
The `npt` statement is used to get user input and store it in a variable.
* **Syntax:** An `npt` call must be assigned to a previously declared variable and must include a prompt string.
    * `<identifier> = npt("prompt text");`
* **Typecasting:** Input values are automatically typecast to the variable's data type. An error will occur if the input cannot be cast correctly (e.g., providing text for an `nt` variable).
* **Behavior:** The program pauses execution and waits for the user to provide input. Only one variable can be assigned per `npt` call.

### Output (`prnt`)
The `prnt` statement is used to display output to the console.
* **Syntax:** The `prnt` keyword is followed by one or more arguments enclosed in parentheses `()`.
    * `prnt("Hello, World!");`
* **Arguments:** Can accept string literals, identifiers, or expressions.
* **Concatenation:** Multiple arguments are separated by a comma (`,`), which acts as a concatenator.
    * `prnt("The value is: ", myVar);`
* **Formatting:** When printing a `dbl` value, it is automatically rounded to two decimal places. When printing a `bln` value, it is represented as `1` for `tr` and `0` for `fls`.