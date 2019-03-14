from ply import lex
from ply.lex import TOKEN
import ply.yacc as yacc
from lexer import *
from data_structures import Helper, Node
import json
import argparse
import sys

"""
CITE:
  Most of the token definations are taken from documentation
  of golang(go docs), and some from the token (go/token)
  package of golang: https://golang.org/src/go/token/token.go
"""

size_mp = {}
size_mp['float']   = 8
size_mp['int']     = 4
size_mp['bool']    = 1
size_mp['complex'] = 8
size_mp['string']  = 4
size_mp['pointer'] = 4

precedence = (
    ('right', 'ASSIGN', 'NOT'),
    ('left', 'LOR'),
    ('left', 'LAND'),
    ('left', 'OR'),
    ('left', 'XOR'),
    ('left', 'AND'),
    ('left', 'EQL', 'NEQ'),
    ('left', 'LSS', 'GTR', 'LEQ', 'GEQ'),
    ('left', 'SHL', 'SHR'),
    ('left', 'ADD', 'SUB'),
    ('left', 'MUL', 'QUO', 'REM'),
)

# declarations
helper = Helper()
rootNode = None
helper.newScope()
# ------------------------START----------------------------


def p_start(p):
    '''start : SourceFile'''
    p[0] = p[1]
    p[0].name = 'start'
    global rootNode
    rootNode = p[0]

# -------------------------------------------------------


# -----------------------TYPES---------------------------
def p_type(p):
    '''Type : TypeToken
                    | TypeLit
                    | LPAREN Type RPAREN'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]
    p[0].name = 'Type'


def p_type_token(p):
    '''TypeToken : INT
                             | FLOAT
                             | STRING
                             | BOOL
                             | TYPE IDENT'''
    p[0] = Node('TypeToken')
    if len(p) == 2:
        p[0].typeList.append([p[1]])
        p[0].sizeList.append(size_mp[p[1]])
    else:
        tmpMap = helper.findInfo(p[2])
        if tmpMap is None:
            compilation_errors.add('Type Error', line_number.get()+1, 'undefined: '+p[2])
        else:
            p[0].sizeList.append(tmpMap['size'])
            p[0].typeList.append([p[2]])

def p_type_lit(p):
    '''TypeLit : ArrayType
                       | StructType
                       | PointerType'''
    p[0] = p[1]
    p[0].name = 'TypeLit'

# -------------------------------------------------------


# ------------------- ARRAY TYPE -------------------------
def p_array_type(p):
    '''ArrayType : LBRACK ArrayLength RBRACK ElementType'''
    p[0] = Node('ArrayType')
    if p[2].extra['count'] == -208016:
        # slice
        p[0].typeList.append(['slice', p[4].typeList[0], 0])
        p[0].sizeList.append(0)
    else:
        if p[2].extra['count'] < 0:
            compilation_errors.add('Size Error', line_number.get()+1, 'array bound must be non-negative')
            return
        p[0].typeList.append(['array', p[4].typeList[0], p[2].extra['count']])
        p[0].sizeList.append(int(p[2].extra['count']*p[4].sizeList[0]))
    p[0].name = 'ArrayType'

def p_array_length(p):
    ''' ArrayLength : INT_LITERAL
                            | epsilon'''
    p[0] = Node('ArrayLength')
    if isinstance(p[1], str):
        p[0].extra['count'] = int(p[1])
    else:
        p[0].extra['count'] = -208016
def p_element_type(p):
    ''' ElementType : Type '''
    p[0] = p[1]
    p[0].name = 'ElementType'

# --------------------------------------------------------


# ----------------- STRUCT TYPE ---------------------------
def p_struct_type(p):
    '''StructType : STRUCT LBRACE FieldDeclRep RBRACE'''
    p[0] = Node('StructType')
    for index_ in range(len(p[3].identList)):
        if p[3].identList[index_] in p[3].identList[:index_]:
            compilation_errors.add('Redeclaration Error',line_number.get()+1, 'Field %s redeclared'%p[3].identList[index_])
            return
    p[0] = p[3]
    dict_ = {}
    offset_ = 0
    for index_ in range(len(p[3].identList)):
        dict_[p[3].identList[index_]] = {'type':p[3].typeList[index_], 'size': p[3].sizeList[index_], 'offset':offset_}
        offset_ += p[3].sizeList[index_]
    p[0].typeList = [['struct', dict_]]
    p[0].sizeList = [sum(p[3].sizeList)]

def p_field_decl_rep(p):
    ''' FieldDeclRep : FieldDeclRep FieldDecl SEMICOLON
                                    | epsilon '''
    p[0] = p[1]
    p[0].name = 'FieldDeclRep'
    if len(p) == 4:
        p[0].identList += p[2].identList
        p[0].typeList += p[2].typeList
        p[0].sizeList += p[2].sizeList


def p_field_decl(p):
    ''' FieldDecl : IdentifierList Type'''
    p[0] = p[1]
    p[0].name = 'FieldDecl'

    p[0].typeList = [p[2].typeList[0]]*len(p[1].identList)
    p[0].sizeList = [p[2].sizeList[0]]*len(p[1].identList)

# ---------------------------------------------------------


# ------------------POINTER TYPES--------------------------
def p_point_type(p):
    '''PointerType : MUL BaseType'''
    p[0] = Node('PointerType')
    p[0].typeList.append(['pointer', p[2].typeList[0]])
    p[0].sizeList.append(4)


def p_base_type(p):
    '''BaseType : Type'''
    p[0] = p[1]
    p[0].name = 'BaseType'

# ---------------------------------------------------------


# ---------------FUNCTION TYPES----------------------------
def p_sign(p):
    '''Signature : Parameters ResultOpt'''



def p_result_opt(p):
    '''ResultOpt : Result
                             | epsilon'''



def p_result(p):
    '''Result : Parameters
                      | Type'''



def p_params(p):
    '''Parameters : LPAREN ParameterListOpt RPAREN'''




def p_param_list_opt(p):
    '''ParameterListOpt : ParametersList
                                                     | epsilon'''



def p_param_list(p):
    '''ParametersList : Type
                                      | IdentifierList Type
                                      | ParameterDeclCommaRep'''



def p_param_decl_comma_rep(p):
    '''ParameterDeclCommaRep : ParameterDeclCommaRep COMMA ParameterDecl
                                                     | ParameterDecl COMMA ParameterDecl'''



def p_param_decl(p):
    '''ParameterDecl : IdentifierList Type
                                     | Type'''

# ---------------------------------------------------------


# -----------------------BLOCKS---------------------------
def p_block(p):
    '''Block : LBRACE StatementList RBRACE'''
    p[0] = p[2]
    p[0].name = 'Block'


def p_stat_list(p):
    '''StatementList : StatementRep'''
    p[0] = p[1]
    p[0].name = 'StatementList'


def p_stat_rep(p):
    '''StatementRep : StatementRep Statement SEMICOLON
                                    | epsilon'''
    p[0] = p[1]
    p[0].name = 'StatementRep'
    if len(p) == 4:
        p[0].code += p[2].code

# -------------------------------------------------------


# ------------------DECLARATIONS and SCOPE------------------------
def p_decl(p):
    '''Declaration : ConstDecl
                                   | TypeDecl
                                   | VarDecl'''
    p[0] = p[1]
    p[0].name = 'Declaration'

def p_toplevel_decl(p):
    '''TopLevelDecl : Declaration
                                    | FunctionDecl'''
    p[0] = p[1]
    p[0].name = 'TopLevelDecl'
# -------------------------------------------------------


# ------------------CONSTANT DECLARATIONS----------------
def p_const_decl(p):
    '''ConstDecl : CONST ConstSpec
                             | CONST LPAREN ConstSpecRep RPAREN'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = p[3]
    p[0].name = 'ConstDecl'
    for index_ in range(len(p[0].identList)):
        helper.symbolTables[helper.getScope()].add(p[0].identList[index_], p[0].typeList[index_])
        helper.symbolTables[helper.getScope()].update(p[0].identList[index_], 'is_const', True)
        helper.symbolTables[helper.getScope()].update(p[0].identList[index_], 'offset', helper.getOffset())
        helper.symbolTables[helper.getScope()].update(p[0].identList[index_], 'size', p[0].sizeList[index_])
        helper.updateOffset(p[0].sizeList[index_])
    # TODO
    # Assign value to the constants in the code generation process.


def p_const_spec_rep(p):
    '''ConstSpecRep : ConstSpecRep ConstSpec SEMICOLON
                                    | epsilon'''
    p[0] = p[1]
    p[0].name = 'ConstSpecRep'
    if len(p) == 4:
        p[0].identList += p[2].identList
        p[0].typeList += p[2].typeList
        p[0].placeList += p[2].placeList
        p[0].sizeList += p[2].sizeList
        p[0].code += p[2].code


def p_const_spec(p):
    '''ConstSpec : IdentifierList Type ASSIGN ExpressionList'''
    p[0] = p[1]
    for i in range(len(p[1].identList)):
        p[0].typeList.append(p[2].typeList[0])
        p[0].sizeList.append(p[2].sizeList[0])
    if len(p[1].identList) != len(p[4].typeList):
        err_ = str(len(p[1].identList)) + ' constants but ' + str(len(p[4].typeList)) + ' values'
        compilation_errors.add('Assignment Mismatch', line_number.get()+1, err_)
    for type_ in p[4].typeList:
        if type_ != p[2].typeList[0]:
            err_ = str(type_) + 'assigned to ' + str(p[2].typeList[0])
            compilation_errors.add('Type Mismatch', line_number.get()+1, err_)
    for idx_ in range(len(p[1].identList)):
        p[0].code.append(['=', p[1].identList[idx_], p[4].placeList[idx_]])
    p[0].placeList = p[4].placeList
    p[0].name = 'ConstSpec'

def p_identifier_list(p):
    '''IdentifierList : IDENT IdentifierRep'''
    p[0] = p[2]
    p[0].name = 'IdentifierList'

    if helper.checkId(p[1],'current') or (p[1] in p[2].identList):
        compilation_errors.add("Redeclare Error", line_number.get()+1,\
            "%s already declared"%p[1])
    else:
        p[0].identList.insert(0,p[1])
        p[0].placeList.insert(0, p[1])


def p_identifier_rep(p):
    '''IdentifierRep : IdentifierRep COMMA IDENT
                                     | epsilon'''
    p[0] = p[1]
    p[0].name = 'IdentifierRep'
    if len(p) == 4:
        if helper.checkId(p[3], 'current') or (p[3] in p[0].identList):
            compilation_errors.add("Redeclare Error", line_number.get()+1,\
            "%s already declared"%p[1])
        else:
            p[0].identList.append(p[3])


def p_expr_list(p):
    '''ExpressionList : Expression ExpressionRep'''
    p[0] = p[1]
    p[0].name = 'ExpressionList'
    p[0].placeList += p[2].placeList
    p[0].typeList += p[2].typeList
    p[0].sizeList += p[2].sizeList
    # TODO: understand addrlist
    p[0].code += p[2].code

def p_expr_rep(p):
    '''ExpressionRep : ExpressionRep COMMA Expression
                                     | epsilon'''

    p[0] = p[1]
    p[0].name = 'ExpressionRep'
    if len(p) == 4:
        p[0].code += p[3].code
        p[0].placeList += p[3].placeList
        p[0].typeList += p[3].typeList
        p[0].sizeList += p[3].sizeList
    # TODO: understand addrlist

# -------------------------------------------------------


# ------------------TYPE DECLARATIONS-------------------
def p_type_decl(p):
    '''TypeDecl : TYPE TypeSpec
                            | TYPE LPAREN TypeSpecRep RPAREN'''
    if len(p) == 5:
        p[0] = p[3]
    else:
        p[0] = p[2]
    p[0].name = 'TypeDecl'


def p_type_spec_rep(p):
    '''TypeSpecRep : TypeSpecRep TypeSpec SEMICOLON
                               | epsilon'''
    if len(p) == 2:
        p[0] = Node('TypeSpecRep')
        # TODO ommitting RHS why?
    else:
        p[0] = p[1]


def p_type_spec(p):
    '''TypeSpec : AliasDecl
                            | TypeDef'''
    p[0] = p[1]
    p[0].name = 'TypeSpec'


def p_alias_decl(p):
    '''AliasDecl : IDENT ASSIGN Type'''
    p[0] = Node('AliasDecl')
    helper.symbolTables[helper.getScope()].typeDefs[p[1]] = {'type': p[3].typeList[0], 'size': p[3].sizeList[0]}
# -------------------------------------------------------


# -------------------TYPE DEFINITIONS--------------------
def p_type_def(p):
    '''TypeDef : IDENT Type'''
    p[0] = Node('Typedef')

    if helper.checkId(p[1],'current'):
        compilation_errors.add("Redeclare Error", line_number.get()+1,\
            "%s already declared"%p[1])
    else:
        helper.symbolTables[helper.getScope()].typeDefs[p[1]] = {'type': p[2].typeList[0], 'size': p[2].sizeList[0]}
        size_mp[p[1]] = p[2].sizeList[0]

# -------------------------------------------------------


# ----------------VARIABLE DECLARATIONS------------------
def p_var_decl(p):
    '''VarDecl : VAR VarSpec
                       | VAR LPAREN VarSpecRep RPAREN'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = p[3]
    p[0].name = 'VarDecl'
    for index_ in range(len(p[0].identList)):
        helper.symbolTables[helper.getScope()].add(p[0].identList[index_], p[0].typeList[index_])
        helper.symbolTables[helper.getScope()].update(p[0].identList[index_], 'offset', helper.getOffset())
        helper.symbolTables[helper.getScope()].update(p[0].identList[index_], 'size', p[0].sizeList[index_])
        helper.updateOffset(p[0].sizeList[index_])

    # TODO
    # Add the values from placeList in the code generation part, when the placeList[i] = 'nil', dont add any code

def p_var_spec_rep(p):
    '''VarSpecRep : VarSpecRep VarSpec SEMICOLON
                              | epsilon'''
    p[0] = p[1]
    p[0].name = 'VarSpecRep'
    if len(p) == 4:
        p[0].identList += p[2].identList
        p[0].typeList += p[2].typeList
        p[0].placeList += p[2].placeList
        p[0].sizeList += p[2].sizeList
        p[0].code += p[2].code

def p_var_spec(p):
    '''VarSpec : IdentifierList Type ExpressionListOpt
                       | IdentifierList ASSIGN ExpressionList'''
    p[0] = p[1]
    p[0].name = 'VarSpec'
    if p[2] == '=':
        if len(p[1].identList) != len(p[3].typeList):
            err_ = str(len(p[1].identList)) + ' varaibles but ' + str(len(p[3].typeList)) + ' values'
            compilation_errors.add('Assignment Mismatch', line_number.get()+1, err_)
        else:
            p[0].typeList = p[3].typeList
            p[0].placeList = p[3].placeList
            p[0].sizeList = p[3].sizeList
            for idx_ in range(len(p[3].placeList)):
                p[0].code.append('=', p[1].identList[idx_], p[3].placeList[idx_])
    else:
        for i in range(len(p[1].identList)):
            p[0].typeList.append(p[2].typeList[0])
            p[0].sizeList.append(p[2].sizeList[0])

        if len(p[3].typeList) == 0:
            tmpArr = ['nil']
            p[0].placeList = tmpArr*len(p[0].identList)
        elif len(p[3].typeList) != 0: # not going to empty
            if len(p[0].identList) != len(p[3].typeList):
                err_ = str(len(p[0].identList)) + ' varaibles but ' + str(len(p[3].typeList)) + ' values'
                compilation_errors.add('Assignment Mismatch', line_number.get()+1, err_)
                return
            for type_ in p[3].typeList:
                if type_ != p[2].typeList[0]:
                    err_ = str(type_) + ' assign to ' + str(p[2].typeList[0]) 
                    compilation_errors.add('Type Mismatch', line_number.get()+1,err_)
                    return
            p[0].placeList = p[3].placeList
            for idx_ in range(len(p[3].placeList)):
                p[0].code.append('=', p[1].identList[idx_], p[3].placeList[idx_])

def p_expr_list_opt(p):
    '''ExpressionListOpt : ASSIGN ExpressionList
                                             | epsilon'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = p[1]
    p[0].name = 'ExpressionListOpt'

# -------------------------------------------------------




# ----------------SHORT VARIABLE DECLARATIONS-------------
def p_short_var_decl(p):
    ''' ShortVarDecl : IDENT DEFINE Expression '''
    p[0] = Node('ShortVarDecl')

    if helper.checkId(p[1],'current'):
        compilation_errors.add("Redeclare Error", line_number.get()+1,\
            "%s already declared"%p[1])
    try:
        helper.symbolTables[helper.getScope()].add(p[1],p[3].typeList[0])
        helper.symbolTables[helper.getScope()].update(p[1], 'offset', helper.getOffset())
        helper.symbolTables[helper.getScope()].update(p[1], 'size', p[3].sizeList[0])
        helper.updateOffset(p[3].sizeList[0])
        p[0].code.append('=', p[1], p[3].placeList[0])
    except:
        pass
# -------------------------------------------------------




# ----------------FUNCTION DECLARATIONS------------------
def p_func_decl(p):
    '''FunctionDecl : FUNC FunctionName CreateScope Function EndScope
                                    | FUNC FunctionName CreateScope Signature EndScope'''
    p[0] = p[4]
    p[0].name = 'FunctionDecl'

def p_func_name(p):
    '''FunctionName : IDENT'''
    p[0] = Node('FunctionName')

def p_func(p):
    '''Function : Signature FunctionBody'''
    p[0] = p[2]
    p[0].name = 'Function'

def p_func_body(p):
    '''FunctionBody : Block'''
    p[0] = p[1]
    p[0].name = 'FunctionBody'

def p_create_scope(p):
    '''CreateScope : '''
    p[0] = Node('CreateScope')
    helper.newScope(helper.getScope())

def p_delete_scope(p):
    '''EndScope : '''
    p[0] = Node('EndScope')
    helper.endScope()
# ---------------------------------------------------------


# ----------------------OPERAND----------------------------
def p_operand(p):
    '''Operand : BasicLit
                       | OperandName
                       | LPAREN Expression RPAREN'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]
    p[0].name = 'Operand'
    # TODO handle operandName

 # new rules start
def p_basic_lit(p):
    '''BasicLit : IntLit
                | FloatLit
                | StringLit
                | BoolLit
                '''
    p[0] = p[1]
    p[0].name = 'BasicLit'

def p_basic_lit_1(p):
    '''IntLit : INT_LITERAL'''
    p[0] = Node('IntLit')
    p[0].typeList.append(['int'])
    newVar = helper.newVar()
    p[0].code.append(['=', newVar, p[1]])
    p[0].placeList.append(newVar)
    p[0].sizeList.append(size_mp['int'])

def p_basic_lit_2(p):
    '''FloatLit : FLOAT_LITERAL'''
    p[0] = Node('FloatLit')
    p[0].typeList.append(['float'])
    newVar = helper.newVar()
    p[0].code.append(['=', newVar, p[1]])
    p[0].placeList.append(newVar)
    p[0].sizeList.append(size_mp['float'])

def p_basic_lit_3(p):
    '''StringLit : STRING_LITERAL'''
    p[0] = Node('StringLit')
    p[0].typeList.append(['string'])
    newVar = helper.newVar()
    p[0].code.append(['=', newVar, p[1]])
    p[0].placeList.append(newVar)
    p[0].sizeList.append(size_mp['string'])
#TODO: what about bool literals

def p_basic_lit_4(p):
    '''BoolLit : TRUE
                    | FALSE'''
    p[0] = Node('BoolLit')
    p[0].typeList.append(['bool'])
    newVar = helper.newVar()
    p[0].code.append(['=', newVar, p[1]])
    p[0].placeList.append(newVar)
    p[0].sizeList.append(size_mp['bool'])

# new rules finished

def p_operand_name(p):
    '''OperandName : IDENT'''
    p[0] = Node('OperandName')
    if not helper.checkId(p[1],'default'):
        compilation_errors.add('NameError', line_number.get()+1, '%s not declared'%p[1])
    else:
        info_ = helper.findInfo(p[1],'default')
        p[0].typeList.append(info_['type'])
        p[0].placeList.append(p[1])
        p[0].sizeList.append(info_['size'])
    # TODO also place other things

# ---------------------------------------------------------



# ------------------PRIMARY EXPRESSIONS--------------------
def p_prim_expr(p):
    '''PrimaryExpr : Operand
                               | PrimaryExpr Selector
                               | Conversion
                               | PrimaryExpr Index
                               | PrimaryExpr Slice
                               | PrimaryExpr Arguments'''
    # Handling only operand
    if len(p)==2:
        p[0] = p[1]
    # elif p[2].name == 'Index':
    #     # TODO code
    else:
        p[0] = Node('PrimaryExpr')
    p[0].name = 'PrimaryExpr'


def p_selector(p):
    '''Selector : PERIOD IDENT'''

def p_index(p):
    '''Index : LBRACK Expression RBRACK'''
    p[0] = p[2]
    p[0].name = 'Index'
    if p[2].typeList[0] != ['int']:
        compilation_errors.add('TypeError',line_number.get()+1, "Index type should be integer")


def p_slice(p):
    '''Slice : LBRACK ExpressionOpt COLON ExpressionOpt RBRACK
                     | LBRACK ExpressionOpt COLON Expression COLON Expression RBRACK'''


def p_argument(p):
    '''Arguments : LPAREN ExpressionListTypeOpt RPAREN'''



def p_expr_list_type_opt(p):
    '''ExpressionListTypeOpt : ExpressionList
                                                     | epsilon'''

# ---------------------------------------------------------


# ----------------------OPERATORS-------------------------
def p_expr(p):
    '''Expression : UnaryExpr
                              | Expression BinaryOp Expression'''
    p[0] = Node('Expression')
    if len(p) == 2:
        p[0].typeList = p[1].typeList
        p[0].placeList = p[1].placeList
        p[0].sizeList = p[1].sizeList
    else:
        if p[1].typeList[0] != p[3].typeList[0]:
            compilation_errors.add('TypeMismatch', line_number.get()+1, 'Type should be same across binary operator')
        elif p[1].typeList[0][0] not in p[2].extra:
            compilation_errors.add('TypeMismatch', line_number.get()+1, 'Invalid type for binary expression')
        else:
            newVar = helper.newVar()
            if len(p[2].typeList) > 0:
                p[0].typeList = p[2].typeList
                p[0].sizeList = p[1].sizeList
            else:
                p[0].typeList = p[1].typeList
                p[0].sizeList = p[1].sizeList
            p[0].placeList.append(newVar)
    # TODO: binary operator must be propogated for code generation

def p_expr_opt(p):
    '''ExpressionOpt : Expression
                                     | epsilon'''
    p[0] = Node('ExpressionOpt')
    p[0].typeList = p[1].typeList
    p[0].placeList = p[1].placeList
    p[0].sizeList = p[1].sizeList

def p_unary_expr(p):
    '''UnaryExpr : PrimaryExpr
                             | UnaryOp UnaryExpr
                             | NOT UnaryExpr'''
    p[0] = Node('UnaryExpr')
    if len(p) == 2:
        p[0].typeList = p[1].typeList
        p[0].placeList = p[1].placeList
        p[0].sizeList = p[1].sizeList
    elif p[1] == '!':
        if p[2].typeList[0] != ['bool']:
            compilation_errors.add('TypeMismatch', line_number.get()+1, 'Type should be boolean')
        else:
            p[0].typeList = p[2].typeList
            p[0].placeList = p[2].placeList
            p[0].sizeList = p[2].sizeList
    else:
        if p[2].typeList[0][0] not in p[1].extra:
            compilation_errors.add('TypeMismatch', line_number.get()+1, 'Invalid type for unary expression')
        else:
            p[0].typeList = p[2].typeList
            p[0].placeList = p[2].placeList
            p[0].sizeList = p[2].sizeList 
    # TODO: opeartor must be propogated from UnaryOp in code generation process


def p_binary_op(p):
    '''BinaryOp : LOR
                            | LAND
                            | RelOp
                            | AddMulOp'''
    
    if isinstance(p[1], str):
        p[0] = Node('BinaryOp')
        p[0].extra['opcode'] = p[1]
        p[0].extra['bool'] = True
        p[0].typeList.append(['bool'])
    elif p[1].name == 'RelOp':
        p[0] = p[1]
        p[0].typeList.append(['bool'])
    else:
        p[0] = p[1]
    p[0].name = 'BinaryOp'

def p_rel_op(p):
    '''RelOp : EQL
                     | NEQ
                     | LSS
                     | GTR
                     | LEQ
                     | GEQ'''
    p[0] = Node('RelOp')
    p[0].extra['opcode'] = p[1]
    if p[1] in ['==', '!=']:
        p[0].extra['bool'] = True
        p[0].extra['int'] = True
        p[0].extra['string'] = True
        p[0].extra['float'] = True
    else:
        p[0].extra['int'] = True 
        p[0].extra['float'] = True 
        p[0].extra['string'] = True 


def p_add_mul_op(p):
    '''AddMulOp : UnaryOp
                            | OR
                            | XOR
                            | QUO
                            | REM
                            | SHL
                            | SHR'''
    if isinstance(p[1], str):
        p[0] = Node('AddMulOp')
        p[0].extra['opcode'] = p[1]
        p[0].extra['int'] = True
        if p[1] == '/':
            p[0].extra['float'] = True
    else:
        p[0] = p[1]
        p[0].name = 'AddMulOp'

def p_unary_op(p):
    '''UnaryOp : ADD
                       | SUB
                       | MUL
                       | AND '''
    p[0] = Node('UnaryOp')
    p[0].extra['int'] = True
    p[0].extra['float'] = True
    p[0].extra['string'] = True
    p[0].extra['opcode'] = p[1]

# -------------------------------------------------------


# -----------------CONVERSIONS-----------------------------
def p_conversion(p):
    '''Conversion : TYPECAST Type LPAREN Expression RPAREN'''
    p[0] = p[4]
    p[0].name = 'Conversion'
    p[0].typeList = p[2].typeList
    p[0].sizeList = p[2].sizeList
# ---------------------------------------------------------


# ---------------- STATEMENTS -----------------------
def p_statement(p):
    '''Statement : Declaration
                             | SimpleStmt
                             | ReturnStmt
                             | BreakStmt
                             | ContinueStmt
                             | CreateScope Block EndScope
                             | IfStmt
                             | ForStmt '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]
    p[0].name = 'Statement'


def p_simple_stmt(p):
    ''' SimpleStmt : epsilon
                                   | ExpressionStmt
                                   | IncDecStmt
                                   | Assignment
                                   | ShortVarDecl '''
    p[0] = p[1]
    p[0].name = 'SimpleStmt'


def p_expression_stmt(p):
    ''' ExpressionStmt : Expression '''
    p[0] = p[1]
    p[0].name = 'ExpressionStmt'


def p_inc_dec(p):
    ''' IncDecStmt : Expression INC
                                   | Expression DEC '''
    p[0] = p[1]
    p[0].name = 'IncDecStmt'
    if  p[1].typeList[0] != ['int']:
        err_ = str(p[1].typeList[0]) + 'cannot be incremented/decremented'
        compilation_errors.add('Type Mismatch', line_number.get()+1, err_)
    # TODO add increment code, for code generation

def p_assignment(p):
    ''' Assignment : ExpressionList assign_op ExpressionList'''
    p[0] = p[1]
    if len(p[1].typeList) != len(p[3].placeList):
        err_ = str(len(p[1].typeList)) + ' identifier on left, while ' + str(len(p[3].placeList)) + ' expression on right'
        compilation_errors.add('Assignment Mismatch', line_number.get()+1, err_)
    else:
        for index_,type_ in enumerate(p[3].typeList):
            info = helper.findInfo(p[1].placeList[index_])
            if 'is_const' in info:
                compilation_errors.add('ConstantAssignment', line_number.get()+1, 'Constant cannot be reassigned')
            elif type_ != p[1].typeList[index_] :
                err_ = str(type_) + ' assigned to ' + str(p[1].typeList[index_])
                compilation_errors.add('TypeMismatch', line_number.get()+1, err_)
            elif type_[0] not in p[2].extra:
                compilation_errors.add('TypeMismatch', line_number.get()+1, 'Invalid Type for operator %s'%p[2].extra['opcode'])
    p[0].name = 'Assignment'
    # TODO make the assignment in code generation, get the assign_op from extra

def p_assign_op(p):
    ''' assign_op : AssignOp'''
    p[0] = p[1]
    p[0].name = 'assign_op'


def p_AssignOp(p):
    ''' AssignOp : ADD_ASSIGN
                             | SUB_ASSIGN
                             | MUL_ASSIGN
                             | QUO_ASSIGN
                             | REM_ASSIGN
                             | AND_ASSIGN
                             | OR_ASSIGN
                             | XOR_ASSIGN
                             | SHL_ASSIGN
                             | SHR_ASSIGN
                             | ASSIGN '''
    p[0] = Node('AssignOp')
    p[0].extra['opcode'] = p[1]
    if p[1] == '=':
        p[0].extra['bool'] = True
        p[0].extra['int'] = True
        p[0].extra['string'] = True
        p[0].extra['float'] = True
    else:
        p[0].extra['int'] = True

def p_if_statement(p):
    ''' IfStmt : IF CreateScope Expression Block ElseOpt EndScope'''
    p[0] = Node('IfStmt')


def p_else_opt(p):
    ''' ElseOpt : ELSE CreateScope IfStmt EndScope
                            | ELSE CreateScope Block EndScope
                            | epsilon '''
    p[0] = Node('ElseOpt')


# ----------------------------------------------------------------


# -----------------------------------------------------------


# --------- FOR STATEMENTS AND OTHERS (MANDAL) ---------------
def p_for(p):
    '''ForStmt : FOR CreateScope ConditionBlockOpt Block EndScope'''
    p[0] = p[3]
    p[0].code += p[4].code
    p[0].name = 'ForStmt'


def p_conditionblockopt(p):
    '''ConditionBlockOpt : epsilon
                           | Condition
                           | ForClause
                           | RangeClause'''
    p[0] = p[1]
    p[0].name = 'ConditionBlockOpt'



def p_condition(p):
    '''Condition : Expression '''
    p[0] = p[1]
    if p[1].typeList[0] != ['bool']:
        compilation_errors.add('TypeMismatch', line_number.get()+1, 'Expression type should be bool')
    p[0].name = 'Condition'


def p_forclause(p):
    '''ForClause : SimpleStmt SEMICOLON ConditionOpt SEMICOLON SimpleStmt'''
    p[0] = p[1]
    p[0].code += p[3].code
    p[0].code += p[5].code
    p[0].name = 'ForClause'


def p_conditionopt(p):
    '''ConditionOpt : epsilon
                    | Condition '''
    p[0] = p[1]
    p[0].name = 'ConditionOpt'



def p_rageclause(p):
    '''RangeClause : ExpressionIdentListOpt RANGE Expression'''
    p[0] = Node('RangeClause')



def p_expression_ident_listopt(p):
    '''ExpressionIdentListOpt : epsilon
                           | ExpressionIdentifier'''
    p[0] = Node('ExpressionIdentListOpt')



def p_expressionidentifier(p):
    '''ExpressionIdentifier : ExpressionList ASSIGN'''
    p[0] = Node('ExpressionIdentifier')



def p_return(p):
    '''ReturnStmt : RETURN ExpressionListPureOpt'''
    p[0] = Node('ReturnStmt')



def p_expressionlist_pure_opt(p):
    '''ExpressionListPureOpt : ExpressionList
                           | epsilon'''
    p[0] = Node('ExpressionListPureOpt')



def p_break(p):
    '''BreakStmt : BREAK'''
    p[0] = Node('BreakStmt')

def p_continue(p):
    '''ContinueStmt : CONTINUE'''
    p[0] = Node('ContinueStmt')

# -----------------------------------------------------------


# ----------------  SOURCE FILE --------------------------------
def p_source_file(p):
    '''SourceFile : PackageClause SEMICOLON ImportDeclRep TopLevelDeclRep'''
    p[0] = p[4]
    p[0].name = 'SourceFile'

def p_import_decl_rep(p):
    '''ImportDeclRep : epsilon
                     | ImportDeclRep ImportDecl SEMICOLON'''
    p[0] = Node('ImportDeclRep')


def p_toplevel_decl_rep(p):
    '''TopLevelDeclRep : TopLevelDeclRep TopLevelDecl SEMICOLON
                                           | epsilon'''
    p[0] = Node('TopLevelDeclRep')
    if len(p) != 2:
        p[0].code = p[1].code + p[2].code


# --------------------------------------------------------


# ---------- PACKAGE CLAUSE --------------------
def p_package_clause(p):
    '''PackageClause : PACKAGE PackageName'''
    p[0] = p[2]
    p[0].name = 'PackageClause'



def p_package_name(p):
    '''PackageName : IDENT'''
    p[0] = Node('PackageName')
    p[0].identList.append(p[1])
    helper.symbolTables[helper.getScope()].updateMetadata('package', p[1])

# -----------------------------------------------


# --------- IMPORT DECLARATIONS ---------------
def p_import_decl(p):
    '''ImportDecl : IMPORT ImportSpec
                    | IMPORT LPAREN ImportSpecRep RPAREN '''
    p[0] = Node('ImportDecl')

def p_import_spec_rep(p):
    ''' ImportSpecRep : ImportSpecRep ImportSpec SEMICOLON
                          | epsilon '''
    p[0] = Node('ImportSpecRep')


def p_import_spec(p):
    ''' ImportSpec : PackageNameDotOpt ImportPath '''
    p[0] = Node('ImportSpec')

def p_package_name_dot_opt(p):
    ''' PackageNameDotOpt : PERIOD
                                                  | PackageName
                                                  | epsilon'''
    p[0] = Node('PackageNameDotOpt')


def p_import_path(p):
    ''' ImportPath : STRING_LITERAL '''
    p[0] = Node('ImportPath')
# -------------------------------------------------------


def p_empty(p):
    '''epsilon : '''
    p[0] = Node('epsilon')


# Error rule for syntax errors

def p_error(p):
    # plus one as line number starts from 0
    compilation_errors.add('Parsing Error', line_number.get()+1,\
                           'Error occured at the token: %s'%p.type)


parser = argparse.ArgumentParser(description='Scans and Parses the input .go file and builds the corresponding AST')

# parser.add_argument('--cfg', dest='config_file_location', help='Location of the input .go file', required=True)

parser.add_argument('--output', dest='out_file_location', help='Location of the output .dot file', required=True)

parser.add_argument('--input', dest='in_file_location', help='Location of the input .go file', required=True)

result = parser.parse_args()
# config_file_location = str(result.config_file_location)
out_file_location = str(result.out_file_location)
in_file_location = str(result.in_file_location)


# Build lexer
lexer = lex.lex()

# Read input file
in_file = open(in_file_location,'r')

# Open output file
out_file = open(out_file_location,"w+")
out_file.write('strict digraph G {\n')

data = in_file.read()

# Iterate to get tokens
parser = yacc.yacc()
res = parser.parse(data)

# Debug here
helper.debug()

# if compilation_errors.size() > 0:
#     compilation_errors.printErrors()
#     sys.exit(0)

out_file.write("}\n")
# Close file
out_file.close()
in_file.close()
