Q: What is the Conso programming language?
A: Conso is a case-sensitive programming language designed to be simple and performant, inspired by Python and C. It uses a unique vowel-less syntax and supports both procedural and functional programming.

Q: How are variables named in Conso?
A: Variable names, also called identifiers, are case-sensitive. They must begin with a letter and can be followed by letters, numbers, or the underscore symbol. Their length must be between 1 and 16 characters.

Q: How do you write comments in Conso?
A: Single-line comments begin with the hash symbol (#). The compiler will ignore all text from the hash symbol to the end of that line.

Q: How do you handle user input and console output?
A: User input is handled with the `npt` statement, which prompts the user and assigns the input to a variable. For example, you would write `myVar = npt("Enter a value");`. Console output is handled with the `prnt` statement, which can display multiple items separated by commas, like this: `prnt("The value is: ", myVar);`.

Q: What are the basic data types in Conso?
A: The basic data types are `nt` for integers, `dbl` for double-precision floating-point numbers, `strng` for text strings, `bln` for boolean values (true or false), and `chr` for single characters.

Q: How do you write an if-else conditional statement?
A: Conditional logic is handled using `f` for an "if" block, `ls` for an "else" block, and `lsf` for an "else-if" block.

Q: How do you create loops in Conso?
A: Conso provides three kinds of loops: a `fr` loop which is similar to a for-loop, a `whl` loop which is similar to a while-loop, and a `d-whl` loop which is similar to a do-while loop.

Q: How are functions defined in Conso?
A: Functions are defined using the `fnctn` keyword, followed by a return type, a function name, and parameters in parentheses. For example, a function that adds two integers could be written as: `fnctn nt add(nt a, nt b) { rtrn a + b; }`.

Q: What arithmetic operators does Conso support?
A: The standard arithmetic operators are supported: plus (+) for addition, minus (-) for subtraction, asterisk (*) for multiplication, slash (/) for division, and percent (%) for modulus.

Q: How do you declare and use an array?
A: Arrays are declared with a fixed size, for example: `nt numbers[3];`. You can initialize them with values in curly braces, such as: `strng names[2] = {"dan", "erdz"};`. You can access elements using zero-based indexing, for example `names[0]`.

Q: What is a struct and how is it used?
A: A struct is a custom data structure that groups several related variables into a single unit. You define a struct's template using the `strct` keyword and then create actual instances of it using the `dfstrct` keyword. Members of a struct instance are accessed using dot notation.

Q: How do you declare a constant?
A: You can declare a read-only constant using the `cnst` keyword. A constant must be initialized at the time of its declaration. For example: `cnst nt MAX_VALUE = 100;`.

Q: What are the logical operators in Conso?
A: The logical operators are `&&` for a logical AND, `||` for a logical OR, and `!` for a logical NOT. These are used to combine or invert boolean values.

Q: How does Conso handle relational comparisons?
A: Conso can compare values using `==` for equal to, `!=` for not equal to, `>` for greater than, `<` for less than, `>=` for greater than or equal to, and `<=` for less than or equal to.