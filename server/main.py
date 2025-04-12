from transpiler import Transpiler, TranspilerError

def transpile_conso_to_c(source_code):
    """
    Transpile Conso code to C code.
    
    Args:
        source_code (str): The source code in Conso language
        
    Returns:
        str: The resulting C code
        
    Raises:
        TranspilerError: If any error occurs during transpilation
    """
    transpiler = Transpiler()
    try:
        c_code = transpiler.transpile(source_code)
        return c_code
    except TranspilerError as e:
        raise e

def main():
    # Example usage
    conso_code = """
    mn() {
        prnt("Hello, World!");
        end;
    }
    """
    
    try:
        c_code = transpile_conso_to_c(conso_code)
        print("Transpiled C code:")
        print("===================")
        print(c_code)
    except TranspilerError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()