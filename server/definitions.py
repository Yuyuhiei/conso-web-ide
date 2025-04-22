import string

state = []
lexeme = []
token = []
idens = []

arithmetic_operator = ['+', '-', '*', '/']
relational_operator = ['==', '!=', '>', '<', '>=', '<=']
logical_operator = ['&&', '||', '!']
assignment_operator = ['=', '+=', '-=', '*=', '/=', '%=']
number_operator = arithmetic_operator + relational_operator + logical_operator
all_operators = number_operator + assignment_operator

punc_symbols = ['=' , '+', '-', '*', '/', '&&', '||', '!', '>', '<', '[', ']', '{', '}', '(', ')', ',', ';', ':', '#', '~', '.', '@', '$', '^', '_', '?']
quote_symbols = ['"', "'"]

alpha = list(string.ascii_letters)
digit = list(string.digits)
alphanumeric = list(string.ascii_letters + string.digits)
ascii_def = alphanumeric + punc_symbols + quote_symbols
identifier = string.ascii_lowercase

#keywords
keywords = ['npt', 'prnt', 'nt', 'dbl', 'strng', 'bln', 'chr', 'f', 'ls', 'lsf', 'swtch', 'fr', 
    'whl', 'd', 'mn', 'cs', 'dflt', 'brk', 'cnst', 'tr', 'fls', 'fnctn', 'rtrn', 'nll', 'cntn', 'strct', 'dfstrct', 'vd']

whitespace = [' ', '\t', '\n']

#parsing table
parsing_table = {
    "<program>": {},
    "<global_declaration>": {"strct": ["<strct_declaration>", "<global_declaration>"]},
    "<declaration>": {"cnst": ["<cnst_dec>", ";", "<declaration>"], "dfstrct": ["dfstrct", "id", "id", "<strct_init_next>", ";", "<declaration>"]},
    "<var_dec>": {"nt": ["nt", "id", "<nt_value>", "<nt_value_next>"], "dbl": ["dbl", "id", "<dbl_value>", "<dbl_value_next>"], 
                  "bln": ["bln", "id", "<bln_value>", "<bln_value_next>"], "chr": ["chr", "id", "<chr_value>", "<chr_value_next>"], 
                  "strng": ["strng", "id", "<str_value>", "<str_value_next>"]},
    "<nt_value>": {"=": ["=", "<arithmetic_nt>"], "[": ["<nt_array_dec>"]},
    "<nt_value_next>": {",": [",", "id", "<nt_value>", "<nt_value_next>"], ";": ["null"]},
    "<arithmetic_nt>": {},
    "<nt_math_val>": {"(": ["(", "<arithmetic_nt>", ")"]},
    "<ntliterals>": {"ntlit": ["ntlit"], "~ntlit": ["~ntlit"]},
    "<unary_entities>": {"id": ["id", "<unary_next>"]},
    "<unary_next>": {},
    "<unary_inc/dec>": {"++": ["++"], "--": ["--"]},
    "<arithmetic_nt_next>": {},
    "<arithmetic_operator>": {"+": ["+"], "-": ["-"], "*": ["*"], "/": ["/"], "%": ["%"]},
    "<entities>": {"id": ["id", "<id_entity_next>"]},
    "<id_entity_next>": {"(": ["<function_call>"]},
    "<id_build>": {"id": ["id", "<id_next>"]},
    "<id_next>": {"[": ["<array_access>"], ".": ["<strct_elem_access>"]},
    "<array_access>": {"[": ["[", "<index>", "]", "<index_next>"]},
    "<index>": {},
    "<index_next>": {"[": ["[", "<index>", "]"]},
    "<strct_elem_access>": {".": [".", "id"]},
    "<function_call>": {"(": ["(", "<arguments>", ")"]},
    "<arguments>": {},
    "<args_value>": {},
    "<args_next>": {",": [",", "<args_value>", "<args_next>"], ")": ["null"]},
    "<expression>": {},
    "<rel_arith_logic_expr>": {},
    "<operands>": {"(": ["(", "<rel_arith_logic_expr>", ")"]},
    "<operand_next>": {},
    "<logical_operator>": {"&&": ["&&"], "||": ["||"]},
    "<relational_operator>": {"==": ["=="], "!=": ["!="], "<=": ["<="], ">=": [">="], "<": ["<"], ">": [">"]},
    "<arithmetic>": {},
    "<math_value>": {},
    "<dblliterals>": {"dbllit": ["dbllit"], "~dbllit": ["~dbllit"]},
    "<arithmetic_next>": {},
    "<strng_concat>": {},
    "<strng_concat_val>": {"strnglit": ["strnglit"]},
    "<strng_concat_next>": {"`": ["`", "<strng_concat_val>", "<strng_concat_next>"]},
    "<nt_array_dec>": {"[": ["[", "<array_size>", "]", "<nt_array_initializer>"]},
    "<array_size>": {"ntlit": ["ntlit"], "id": ["id"]},
    "<nt_array_initializer>": {"=": ["=", "{", "<nt_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<nt_2d_init>"]},
    "<nt_array_elem>": {},
    "<nt_array_elem_val>": {},
    "<nt_array_init_next>": {",": [",", "<nt_array_elem_val>", "<nt_array_init_next>"]},
    "<nt_2d_init>": {"=": ["=", "{", "<nt_array2d_elem>", "}"]},
    "<nt_array2d_elem>": {"{": ["{", "<nt_array_elem>", "}", "<nt_array_elem_next>"]},
    "<nt_array_elem_next>": {",": [",", "<nt_array2d_elem>"]},
    "<dbl_value>": {"=": ["=", "<arithmetic>"], "[": ["<dbl_array_dec>"]},
    "<dbl_value_next>": {",": [",", "id", "<dbl_value>", "<dbl_value_next>"]},
    "<dbl_array_dec>": {"[": ["[", "<array_size>", "]", "<dbl_array_initializer>"]},
    "<dbl_array_initializer>": {"=": ["=", "{", "<dbl_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<dbl_2d_init>"]},
    "<dbl_array_elem>": {},
    "<dbl_array_elem_val>": {},
    "<dbl_array_init_next>": {",": [",", "<dbl_array_elem_val>", "<dbl_array_init_next>"]},
    "<dbl_2d_init>": {"=": ["=", "{", "<dbl_array2d_elem>", "}"]},
    "<dbl_array2d_elem>": {"{": ["{", "<dbl_array_elem>", "}", "<dbl_array_elem_next>"]},
    "<dbl_array_elem_next>": {",": [",", "<dbl_array2d_elem>"]},
    "<bln_value>": {"=": ["=", "<equals_bln_val>"], "[": ["<bln_array_dec>"]},
    "<equals_bln_val>": {},
    "<bln_value_next>": {",": [",", "id", "<bln_value>", "<bln_value_next>"]},
    "<bln_array_dec>": {"[": ["[", "<array_size>", "]", "<bln_array_initializer>"]},
    "<bln_array_initializer>": {"=": ["=", "{", "<bln_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<bln_2d_init>"]},
    "<bln_array_elem>": {},
    "<bln_array_elem_val>": {"blnlit": ["blnlit"]},
    "<bln_array_init_next>": {",": [",", "<bln_array_elem_val>", "<bln_array_init_next>"]},
    "<bln_2d_init>": {"=": ["=", "{", "<bln_array2d_elem>", "}"]},
    "<bln_array2d_elem>": {"{": ["{", "<bln_array_elem>", "}", "<bln_array_elem_next>"]},
    "<bln_array_elem_next>": {",": [",", "<bln_array2d_elem>"]},
    "<chr_value>": {"=": ["=", "<equals_chr_val>"], "[": ["<chr_array_dec>"]},
    "<equals_chr_val>": {"id": ["<entities>"], "chrlit": ["chrlit"]},
    "<chr_value_next>": {",": [",", "id", "<chr_value>", "<chr_value_next>"]},
    "<chr_array_dec>": {"[": ["[", "<array_size>", "]", "<chr_array_initializer>"]},
    "<chr_array_initializer>": {"=": ["=", "{", "<chr_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<chr_2d_init>"]},
    "<chr_array_elem>": {},
    "<chr_array_elem_val>": {"chrlit": ["chrlit"]},
    "<chr_array_init_next>": {",": [",", "<chr_array_elem_val>", "<chr_array_init_next>"]},
    "<chr_2d_init>": {"=": ["=", "{", "<chr_array2d_elem>", "}"]},
    "<chr_array2d_elem>": {"{": ["{", "<chr_array_elem>", "}", "<chr_array_elem_next>"]},
    "<chr_array_elem_next>": {",": [",", "<chr_array2d_elem>"]},
    "<str_value>": {"=": ["=", "<equals_str_val>"], "[": ["<str_array_dec>"]},
    "<equals_str_val>": {"id": ["<entities>"], "strnglit": ["<strng_concat>"]},
    "<str_value_next>": {",": [",", "id", "<str_value>", "<str_value_next>"]},
    "<str_array_dec>": {"[": ["[", "<array_size>", "]", "<str_array_initializer>"]},
    "<str_array_initializer>": {"=": ["=", "{", "<str_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<str_2d_init>"]},
    "<str_array_elem>": {"strnglit": ["<str_array_elem_val>", "<str_array_init_next>"]},
    "<str_array_elem_val>": {"strnglit": ["strnglit"]},
    "<str_array_init_next>": {",": [",", "<str_array_elem_val>", "<str_array_init_next>"]},
    "<str_2d_init>": {"=": ["=", "{", "<str_array2d_elem>", "}"]},
    "<str_array2d_elem>": {"{": ["{", "<str_array_elem>", "}", "<str_array_elem_next>"]},
    "<str_array_elem_next>": {",": [",", "<str_array2d_elem>"]},
    "<cnst_dec>": {"cnst": ["cnst", "<cnst_dec_data_type>"]},
    "<cnst_dec_data_type>": {"nt": ["nt", "id", "<nt_cnst_initializer>"], "dbl": ["dbl", "id", "<dbl_cnst_initializer>"],
                            "bln": ["bln", "id", "<bln_cnst_initializer>"], "chr": ["chr", "id", "<chr_cnst_initializer>"],
                            "strng": ["strng", "id", "<str_cnst_initializer>"]},
    "<nt_cnst_initializer>": {"=": ["=", "<nt_cnst_init_val>"], "[": ["<cnst_nt_array_dec>"]},
    "<nt_cnst_init_val>": {},
    "<nt_cnst_next>": {",": [",", "id", "<nt_cnst_initializer>"]},
    "<cnst_nt_array_dec>": {"[": ["[", "<cnst_array_size>", "]", "<cnst_nt_array_initializer>"]},
    "<cnst_array_size>": {},
    "<cnst_nt_array_initializer>": {"=": ["=", "{", "<nt_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<nt_2d_init>"]},
    "<dbl_cnst_initializer>": {"=": ["=", "<dbl_cnst_init_val>"], "[": ["<cnst_dbl_array_dec>"]},
    "<dbl_cnst_init_val>": {},
    "<dbl_cnst_next>": {",": [",", "id", "<dbl_cnst_initializer>"]},
    "<cnst_dbl_array_dec>": {"[": ["[", "<cnst_array_size>", "]", "<cnst_dbl_array_initializer>"]},
    "<cnst_dbl_array_initializer>": {"=": ["=", "{", "<dbl_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<dbl_2d_init>"]},
    "<bln_cnst_initializer>": {"=": ["=", "<bln_cnst_init_val>"], "[": ["<cnst_bln_array_dec>"]},
    "<bln_cnst_init_val>": {"blnlit": ["blnlit", "<bln_cnst_next>"]},
    "<bln_cnst_next>": {",": [",", "id", "<bln_cnst_initializer>"]},
    "<cnst_bln_array_dec>": {"[": ["[", "<cnst_array_size>", "]", "<cnst_bln_array_initializer>"]},
    "<cnst_bln_array_initializer>": {"=": ["=", "{", "<bln_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<bln_2d_init>"]},
    "<chr_cnst_initializer>": {"=": ["=", "<chr_cnst_init_val>"], "[": ["<cnst_chr_array_dec>"]},
    "<chr_cnst_init_val>": {"chrlit": ["chrlit", "<chr_cnst_next>"]},
    "<chr_cnst_next>": {",": [",", "id", "<chr_cnst_initializer>"]},
    "<cnst_chr_array_dec>": {"[": ["[", "<cnst_array_size>", "]", "<cnst_chr_array_initializer>"]},
    "<cnst_chr_array_initializer>": {"=": ["=", "{", "<chr_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<chr_2d_init>"]},
    "<str_cnst_initializer>": {"=": ["=", "<str_cnst_init_val>"], "[": ["<cnst_str_array_dec>"]},
    "<str_cnst_init_val>": {"strnglit": ["strnglit", "<str_cnst_next>"]},
    "<str_cnst_next>": {",": [",", "id", "<str_cnst_initializer>"]},
    "<cnst_str_array_dec>": {"[": ["[", "<cnst_array_size>", "]", "<cnst_str_array_initializer>"]},
    "<cnst_str_array_initializer>": {"=": ["=", "{", "<str_array_elem>", "}"], "[": ["[", "<array_size>", "]", "<str_2d_init>"]},
    "<strct_init_next>": {",": [",", "id", "<strct_init_next>"]},
    "<strct_declaration>": {"strct": ["strct", "id", "{", "<strct_body>", "}", ";"]},
    "<strct_body>": {},
    "<strct_var_dec>": {"nt": ["nt", "id"], "dbl": ["dbl", "id"], "bln": ["bln", "id"], 
                        "chr": ["chr", "id"], "strng": ["strng", "id"]},
    "<var_dec_next>": {},
    "<function_definition>": {"fnctn": ["fnctn", "<func_type>", "id", "(", "<parameter>", ")", "{", "<func_var_dec>", "<statement>", "}", "<function_definition>"]},
    "<func_type>": {"vd": ["vd"]},
    "<data_type>": {"nt": ["nt"], "dbl": ["dbl"], "bln": ["bln"], "chr": ["chr"], "strng": ["strng"]},
    "<parameter>": {},
    "<parameter_next>": {",": [",", "<parameter>"]},
    "<func_var_dec>": {},
    "<statement>": {"id": ["<id_build_statements>", "<statement>"], "prnt": ["<output_statement>", "<statement>"], "fr": ["<fr_statement>", "<statement>"],
                    "d": ["<d-whl_statement>", "<statement>"], "whl": ["<whl_statement>", "<statement>"], "rtrn": ["<rtrn_statement>", "<statement>"]}, # di ko alam pano lalagay yung null sa first set ng <rtrn_statement>
    "<id_build_statements>": {"id": ["id", "<id_build_statement_next>"]},
    "<id_build_statement_next>": {"(": ["<function_call>", ";"]},
    "<assignment_statement>": {"=": ["=", "<assignment_value_input>"]},
    "<assign_operator>": {"+=": ["+="], "-=": ["-="], "*=": ["*="], "/=": ["/="]},
    "<assignment_value>": {},
    "<assignment_value_input>": {"npt": ["<input_statement_value>"]},
    "<input_statement_value>": {"npt": ["npt", "(", "strnglit", ")", ";"]},
    "<unary_pre_statement>": {},
    "<output_statement>": {"prnt": ["prnt", "(", "<output_value>", "<output_next>", ")", ";"]},
    "<output_value>": {},
    "<output_next>": {",": [",", "<output_value>", "<output_next>"]},
    "<conditional_statement>": {"f": ["f", "(", "<condition>", ")", "{", "<statement>", "<lsf_statement>", "<ls_statement>", "}", "<lsf_statement>", "<ls_statement>"],
                                "swtch": ["swtch", "(", "id", ")", "{", "<swtch_body>", "}"]},
    "<condition>": {},
    "<lsf_statement>": {"lsf": ["lsf", "(", "<condition>", ")", "{", "<statement>", "}", "<lsf_statement>"]},
    "<ls_statement>": {"ls": ["ls", "{", "<statement>", "}"]},
    "<swtch_body>": {"cs": ["<cs>", "<dflt>"]},
    "<cs>": {"cs": ["cs", "<swtch_value>", ":", "<statement>", "<cs_next>"]},
    "<swtch_value>": {"chrlit": ["chrlit"]},
    "<cs_next>": {"cs": ["<cs>", "<cs_next>"]},
    "<dflt>": {"dflt": ["dflt", ":", "<statement>"]},
    "<fr_statement>": {"fr": ["fr", "(", "<initialization>", ";", "<fr_condi>", ";", "<inc/dec>", ")", "{", "<statement>", "}"]},
    "<initialization>": {"id": ["<id_build>", "=", "<arithmetic_nt>"]},
    "<fr_condi>": {},
    "<inc/dec>": {"id": ["id", "<inc/dec_next>"]},
    "<inc/dec_next>": {},
    "<fr_unary>": {},
    "<inc/dec_value>": {"id": ["<id_build>"]},
    "<d-whl_statement>": {"d": ["d", "{", "<statement>", "}", "whl", "(", "<condition>", ")", ";"]},
    "<whl_statement>": {"whl": ["whl", "(", "<condition>", ")", "{", "<statement>", "}"]},
    "<rtrn_statement>": {"rtrn": ["rtrn", "<rtrn_value>", ";"]},
    "<rtrn_value>": {},
    "<control_statements>": {"brk": ["brk", ";"], "cntn": ["cntn", ";"]},
}

def add_set(set, production, prod_set):
    for terminal in set:
        if terminal not in parsing_table:
            parsing_table[production][terminal] = []
        parsing_table[production][terminal].extend(prod_set)

def add_all_set():
    add_set(["nt", "dbl", "bln", "chr", "strng", "cnst", "dfstrct", "strct", "fnctn", "mn"], "<program>", 
            ["<global_declaration>", "<function_definition>", "mn", "(", ")", "{", "<declaration>", "<statement>", "end", ";", "}"])
    add_set(["nt", "dbl", "bln", "chr", "strng"], "<global_declaration>", ["<var_dec>", ";", "<global_declaration>"])
    add_set(["cnst"], "<global_declaration>", ["<cnst_dec>", ";", "<global_declaration>"])
    add_set(["dfstrct"], "<global_declaration>", ["dfstrct", "id", "id", "<strct_init_next>", ";", "<global_declaration>"])
    
    add_set(["fnctn", "mn"], "<global_declaration>", ["null"])
    add_set(["nt", "dbl", "bln", "chr", "strng"], "<declaration>", ["<var_dec>", ";", "<declaration>"])
    add_set(["id", "++", "--", "prnt", "f", "swtch", "fr", "d", "whl", "rtrn", "brk", "cntn", "end"], "<declaration>", ["null"])
    add_set([",", ";"], "<nt_value>", ["null"])
    add_set(["ntlit", "~ntlit", "(", "++", "--", "id"], "<arithmetic_nt>", ["<nt_math_val>", "<arithmetic_nt_next>"])
    add_set(["ntlit", "~ntlit", ], "<nt_math_val>", ["<ntliterals>"])
    add_set(["++", "--", "id"], "<nt_math_val>", ["<unary_entities>"])
    add_set(["++", "--"], "<unary_entities>", ["<unary_inc/dec>", "id"])
    add_set(["++", "--"], "<unary_next>", ["<unary_inc/dec>"])
    add_set(["[", ".", "("], "<unary_next>", ["<id_entity_next>"]) #di ko alam pano lalagay yung null sa first set ng <id_entity_next>
    add_set(["+", "-", "*", "/", "%", ",", ";", ")", "&&", "||", "==", "!=", "<=", ">=", "<", ">", "]"], "<unary_next>", ["null"])
    add_set(["+", "-", "*", "/", "%"], "<arithmetic_nt_next>", ["<arithmetic_operator>", "<nt_math_val>", "<arithmetic_nt_next>"])
    add_set([",", ")", "]", ";"], "<arithmetic_nt_next>", ["null"])
    add_set(["[", "."], "<id_entity_next>", ["<id_next>"]) # di ko alam pano lalagay yung null sa first set ng <id_next>
    add_set(["+", "-", "*", "/", "%", ",", ")", "]", ";", "&&", "||", "==", "!=", "<=", ">=", "<", ">"], "<id_entity_next>", ["null"])
    add_set(["+", "-", "*", "/", "%", ",", ")", "]", ";", "=", "+=", "-=", "*=", "/=", "&&", "||", "==", "!=", "<=", ">=", "<", ">"], "<id_next>", ["null"]) # dalawa yung (,) comma sa follow set
    add_set(["ntlit", "~ntlit" "(", "++", "--", "id"], "<index>",["<arithmetic_nt>"])
    add_set(["+", "-", "*", "/", "%", ",", ")", "]", ";", "=", "+=", "-=", "*=", "/=", "&&", "||", "==", "!=", "<=", ">=", "<", ">"], "<index_next>", ["null"]) # dalawa yung (,) comma sa follow set
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<arguments>", ["<args_value>", "<args_next>"])
    add_set([")"], "<arguments>", ["null"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<args_value>", ["<expression>"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<expression>", ["<rel_arith_logic_expr>"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<rel_arith_logic_expr>", ["<operands>", "<operand_next>"])
    add_set(["dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id"], "<operands>", ["<math_value>"])
    add_set(["chrlit"], "<operands>", ["chrlit"])
    add_set(["!"], "<operands>", ["!", "<operands>"])
    add_set(["strnglit"], "<operands>", ["<strng_concat>"])
    add_set(["blnlit"], "<operands>", ["blnlit"])
    add_set(["+", "-", "*", "/", "%"], "<operand_next>", ["<arithmetic_operator>", "<rel_arith_logic_expr>"])
    add_set(["==", "!=", "<=", ">=", "<", ">"], "<operand_next>", ["<relational_operator>", "<rel_arith_logic_expr>"])
    add_set(["&&", "||"], "<operand_next>", ["<logical_operator>", "<rel_arith_logic_expr>"])
    add_set([",", ";", ")" ], "<operand_next>", ["null"])
    add_set(["dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id"], "<arithmetic>", ["<math_value>", "<arithmetic_next>"])
    add_set(["dbllit", "~dbllit"], "<math_value>", ["<dblliterals>"])
    add_set(["ntlit", "~ntlit"], "<math_value>", ["<ntliterals>"])
    add_set(["++", "--", "id"], "<math_value>", ["<unary_entities>"])
    add_set(["+", "-", "*", "/", "%"], "<arithmetic_next>", ["<arithmetic_operator>", "<arithmetic>"])
    add_set([",", ";", ")"], "<arithmetic_next>", ["null"])
    add_set(["strnglit"], "<strng_concat>", ["<strng_concat_val>", "<strng_concat_next>"])
    add_set(["==", "!=", "<=", ">=", "<", ">", "&&", "||", "+", "-", "*", "/", "%", ",", ";", ")"], "<strng_concat_next>", ["null"]) 
    add_set([",", ";"], "<nt_array_initializer>", ["null"])
    add_set(["ntlit", "~ntlit"], "<nt_array_elem>", ["<nt_array_elem_val>", "<nt_array_init_next>"])
    add_set(["ntlit", "~ntlit"], "<nt_array_elem_val>", ["<ntliterals>"])
    add_set(["}"], "<nt_array_init_next>", ["null"])
    add_set([",", ";"], "<nt_2d_init>", ["null"])
    add_set(["}"], "<nt_array_elem_next>", ["null"])
    add_set([",", ";"], "<dbl_value>", ["null"])
    add_set([";"], "<dbl_value_next>", ["null"])
    add_set([",", ";"], "<dbl_array_initializer>", ["null"])
    add_set(["dbllit", "~dbllit"], "<dbl_array_elem>", ["<dbl_array_elem_val>", "<dbl_array_init_next>"])
    add_set(["dbllit", "~dbllit"], "<dbl_array_elem_val>", ["<dblliterals>"])
    add_set(["}"], "<dbl_array_init_next>", ["null"])
    add_set([",", ";"], "<dbl_2d_init>", ["null"])
    add_set(["}"], "<dbl_array_elem_next>", ["null"])
    add_set([",", ";"], "<bln_value>", ["null"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<equals_bln_val>", ["<rel_arith_logic_expr>"])
    add_set([";"], "<bln_value_next>", ["null"])
    add_set([",", ";"], "<bln_array_initializer>", ["null"])
    add_set(["blnlit"], "<bln_array_elem>", ["<bln_array_elem_val>", "<bln_array_init_next>"])
    add_set(["}"], "<bln_array_init_next>", ["null"])
    add_set([",", ";"], "<bln_2d_init>", ["null"])
    add_set(["}"], "<bln_array_elem_next>", ["null"])
    add_set([",", ";"], "<chr_value>", ["null"])
    add_set([";"], "<chr_value_next>", ["null"])
    add_set([",", ";"], "<chr_array_initializer>", ["null"])
    add_set(["chrlit"], "<chr_array_elem>", ["<chr_array_elem_val>", "<chr_array_init_next>"])
    add_set(["}"], "<chr_array_init_next>", ["null"])
    add_set([",", ";"], "<chr_2d_init>", ["null"])
    add_set(["}"], "<chr_array_elem_next>", ["null"])
    add_set([",", ";"], "<str_value>", ["null"])
    add_set([";"], "<str_value_next>", ["null"])
    add_set([",", ";"], "<str_array_initializer>", ["null"])
    add_set(["}"], "<str_array_init_next>", ["null"])
    add_set([",", ";"], "<str_2d_init>", ["null"])
    add_set(["}"], "<str_array_elem_next>", ["null"])
    add_set(["ntlit", "~ntlit"], "<nt_cnst_init_val>", ["<ntliterals>", "<nt_cnst_next>"])
    add_set([";"], "<nt_cnst_next>", ["null"])
    add_set(["ntlit", "~ntlit"], "<cnst_array_size>", ["<ntliterals>"])
    add_set(["dbllit", "~dbllit"], "<dbl_cnst_init_val>", ["<dblliterals>", "<dbl_cnst_next>"])
    add_set([";"], "<dbl_cnst_next>", ["null"])
    add_set([";"], "<bln_cnst_next>", ["null"])
    add_set([";"], "<chr_cnst_next>", ["null"])
    add_set([";"], "<str_cnst_next>", ["null"])
    add_set([";"], "<strct_init_next>", ["null"])
    add_set(["nt", "dbl", "bln", "chr", "strng"], "<strct_body>", ["<strct_var_dec>", ";", "<var_dec_next>"])
    add_set(["nt", "dbl", "bln", "chr", "strng"], "<var_dec_next>", ["<strct_body>"])
    add_set(["}"], "<var_dec_next>", ["null"])
    add_set(["mn"], "<function_definition>", ["null"])
    add_set(["nt", "dbl", "bln", "chr", "strng"], "<func_type>", ["<data_type>"])
    add_set(["nt", "dbl", "bln", "chr", "strng"], "<parameter>", ["<data_type>", "id", "<parameter_next>"])
    add_set([")"], "<parameter>", ["null"])
    add_set([")"], "<parameter_next>", ["null"])
    add_set(["nt", "dbl", "bln", "chr", "strng"], "<func_var_dec>", ["<var_dec>", ";", "<func_var_dec>"])
    add_set(["id", "++", "--", "prnt", "f", "swtch", "fr", "d", "whl", "rtrn", "brk", "cntn" "}"], "<func_var_dec>", ["null"])
    add_set(["++", "--"], "<statement>", ["<unary_pre_statement>", "<statement>"])
    add_set(["f", "swtch"], "<statement>", ["<conditional_statement>", "<statement>"])
    add_set(["brk", "cntn"], "<statement>", ["<control_statements>", "<statement>"])
    add_set(["end", "}", "lsf", "ls", "cs", "dflt"], "<statement>", ["null"])

    add_set(["[", "."], "<id_build_statement_next>", ["<id_next>", "<assignment_statement>"]) # di ko alam pano lalagay yung null sa first set ng <id_next>
    add_set(["+=", "-=", "*=", "/=", "="], "<id_build_statement_next>", ["<assignment_statement>"])
    add_set(["++", "--"], "<id_build_statement_next>", ["<unary_inc/dec>", ";"])

    add_set(["+=", "-=", "*=", "/="], "<assignment_statement>", ["<assign_operator>", "<assignment_value>"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<assignment_value>", ["<expression>", ";"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<assignment_value_input>", ["<assignment_value>"])
    add_set(["++", "--"], "<unary_pre_statement>", ["<unary_inc/dec>", "id", ";"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<output_value>", ["<expression>"])
    add_set([")"], "<output_next>", ["null"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<condition>", ["<rel_arith_logic_expr>"])
    add_set(["ls", "}", "id", "++", "--", "prnt", "f", "swtch", "fr", "d", "whl", "rtrn", "brk", "cntn", "end"], "<lsf_statement>", ["null"])
    add_set(["}", "id", "++", "--", "prnt", "f", "swtch", "fr", "d", "whl", "rtrn", "brk", "cntn", "end"], "<ls_statement>", ["null"])
    add_set(["ntlit", "~ntlit"], "<swtch_value>", ["<ntliterals>"])
    add_set(["dflt", "}"], "<cs>", ["null"])
    add_set(["dflt", "}"], "<cs_next>", ["null"])
    add_set(["}"], "<dflt>", ["null"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<fr_condi>", ["<condition>"])
    add_set(["++", "--"], "<inc/dec>", ["<fr_unary>"])
    add_set(["+=", "-=", "*=", "/="], "<inc/dec_next>", ["<assign_operator>", "<inc/dec_value>"])
    add_set(["++", "--"], "<inc/dec_next>", ["<unary_inc/dec>"])
    add_set(["++", "--"], "<fr_unary>", ["<unary_inc/dec>", "id"])
    add_set(["ntlit", "~ntlit"], "<inc/dec_value>", ["<ntliterals>"])
    add_set(["(", "dbllit", "~dbllit", "ntlit", "~ntlit", "++", "--", "id", "chrlit", "!", "strnglit", "blnlit"], "<rtrn_value>", ["<expression>"])