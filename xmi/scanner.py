import string
import types
import os
import sys
import parser
import symbol
import token
import pprint
from types import ListType, TupleType
from StringIO import StringIO
import zipfile
import zlib
import wingdbstub
import model

# Command Line Option Globals
verbose = None
tool = None
templatedirs = []
extensions = []

PARAMETER_DEFAULT_PATTERN_NUMBER = (
    symbol.test,
    (symbol.and_test,
     (symbol.not_test,
      (symbol.comparison,
       (symbol.expr,
        (symbol.xor_expr,
         (symbol.and_expr,
          (symbol.shift_expr,
           (symbol.arith_expr,
            (symbol.term,
             (symbol.factor,
              (symbol.power,
               (symbol.atom,
                (token.NUMBER, ['default']))))))))))))))

PARAMETER_DEFAULT_PATTERN_STRING = (
    symbol.test,
    (symbol.and_test,
     (symbol.not_test,
      (symbol.comparison,
       (symbol.expr,
        (symbol.xor_expr,
         (symbol.and_expr,
          (symbol.shift_expr,
           (symbol.arith_expr,
            (symbol.term,
             (symbol.factor,
              (symbol.power,
               (symbol.atom,
                (token.STRING, ['default']))))))))))))))

PARAMETER_DEFAULT_PATTERN_NAME = (
    symbol.test,
    (symbol.and_test,
     (symbol.not_test,
      (symbol.comparison,
       (symbol.expr,
        (symbol.xor_expr,
         (symbol.and_expr,
          (symbol.shift_expr,
           (symbol.arith_expr,
            (symbol.term,
             (symbol.factor,
              (symbol.power,
               (symbol.atom,
                (token.NAME, ['default']))))))))))))))

# This pattern and the match function are swiped from the example.py distributed
# with the python sources

#(300, (4, ''), (5, ''), (267, (268, (269, (270, (327, (304, (305, (306, (307, (308, (310, (311, (312, (313, (314, (315, (316, (317, (318, (3,
DOCSTRING_STMT_PATTERN = (267, (268, (269, (270, (327, (304, (305, (306, (307, (308, (310, (311, (312, (313, (314, (315, (316, (317, (318, (3, ['docstring'])))))))))))))))))), (4, '')))

##DOCSTRING_STMT_PATTERN = (
##    symbol.stmt,
##    (symbol.simple_stmt,
##     (symbol.small_stmt,
##      (symbol.expr_stmt,
##       (symbol.testlist,
##        (symbol.test,
##         (symbol.and_test,
##          (symbol.not_test,
##           (symbol.comparison,
##            (symbol.expr,
##             (symbol.xor_expr,
##              (symbol.and_expr,
##               (symbol.shift_expr,
##                (symbol.arith_expr,
##                 (symbol.term,
##                  (symbol.factor,
##                   (symbol.power,
##                    (symbol.atom,
##                     (token.STRING, ['docstring'])
##                     )))))))))))))))),
##     (token.NEWLINE, '')
##     ))

def xml_encode(s):
    out = StringIO()
    for c in s:
        if c == '&':
            out.write('&amp;')
        elif c == '<':
            out.write('&lt;')
        elif c == '>':
            out.write('&gt;')
        else:
            out.write(c)
    return out.getvalue()

def match(pattern, data, vars=None):
    """Match `data' to `pattern', with variable extraction.

    pattern
        Pattern to match against, possibly containing variables.

    data
        Data to be checked and against which variables are extracted.

    vars
        Dictionary of variables which have already been found.  If not
        provided, an empty dictionary is created.

    The `pattern' value may contain variables of the form ['varname'] which
    are allowed to match anything.  The value that is matched is returned as
    part of a dictionary which maps 'varname' to the matched value.  'varname'
    is not required to be a string object, but using strings makes patterns
    and the code which uses them more readable.

    This function returns two values: a boolean indicating whether a match
    was found and a dictionary mapping variable names to their associated
    values.
    """

    if vars is None:
        vars = {}
    if type(pattern) is ListType:       # 'variables' are ['varname']
        vars[pattern[0]] = data
        return 1, vars
    if type(pattern) is not TupleType:
        return (pattern == data), vars
    if len(data) != len(pattern):
        return 0, vars
    for pattern, data in map(None, pattern, data):
        same, vars = match(pattern, data, vars)
        if not same:
            break
    return same, vars

def to_name(i):
    if symbol.sym_name.has_key(i):
        return symbol.sym_name[i]
    elif token.tok_name.has_key(i):
        return token.tok_name[i]
    else:
        return i

def ast_dump(tup):
    l = []
    for i in tup:
        if type(i) == type(()):
            l.append(ast_dump(i))
        else:
            if symbol.sym_name.has_key(i):
                l.append(symbol.sym_name[i])
            elif token.tok_name.has_key(i):
                l.append(token.tok_name[i])
            else:
                l.append(i)
    return l

def dump(tup):
    if type(tup) == TupleType:
        pprint.pprint(ast_dump(tup))
    else:
        print to_name(tup)

class SourceParser:

    """ From a python source file, compile a signature for the classes in it """

    def __init__(self, model, filename):
        self.classes = {}
        self.filename = filename
        f = open(filename)
        source = f.read()
        f.close()
        try:
            ast = parser.suite(source)
        except Exception, e:
            print >>sys.stderr, "Syntax Error in ", filename, str(e)
            return
        tuples = ast.totuple()
        self.extract_classes(model, tuples)

    def extract_args(self, parameters, operator):

        """ Passed a parameters this constructs a function signature """

        argname = None
        argdefault = None
        if len(parameters) < 3:
            print self.filename, "Not enough parameters:", parameters
        else:
            for i in parameters[2]:
                if type(i) == TupleType and i[0] == symbol.fpdef:
                    argname = i[1][1]
                    argdefault = None
                if type(i) == TupleType and i[0] == symbol.test:
                    for t in PARAMETER_DEFAULT_PATTERN_NAME,  \
                            PARAMETER_DEFAULT_PATTERN_STRING, \
                            PARAMETER_DEFAULT_PATTERN_NUMBER:
                        found, vars = match(t, i)
                        if found:
                            argdefault = xml_encode(vars['default'])
                if type(i) == TupleType and i[0] in (token.COMMA, token.RPAR):
                    operator.addArgument(argname, argdefault)
        if argname:
            operator.addArgument(argname, argdefault)

    def extract_functions(self, parent, suite):
        for i in suite:
            if type(i) == type(()) and \
                i[0] == symbol.stmt and \
                i[1][0] == symbol.compound_stmt and \
                i[1][1][0] == symbol.funcdef:
                    function_def = i[1][1]
                    funcname = function_def[2][1]
                    op = model.Operation(funcname)
                    # function_def[3] is the parameters
                    params = filter(lambda x: type(x) == types.TupleType and x[0] == symbol.parameters, function_def)
                    self.extract_args(params[0], op)
                    #if function_def[3][0] != symbol.parameters:
                    #    print function_def[4]
                    #self.extract_args(function_def[3], op)
                    parent.addOperation(op)
                    # function_def[5] is the suite
                    op.doc = self.docstring(function_def[5])

    def atom(self, tuple):
        if type(tuple) == type(()):
            return atom(tuple[1])
        else:
            return tuple[1]

    def docstring(self, suite):
        if type(suite) == TupleType and len(suite)>2:
            found, vars = match(DOCSTRING_STMT_PATTERN, suite[3])
            if found:
                ds = vars['docstring']
                ds = ds.strip("'").strip('"')
                return xml_encode(ds)
        return ''

    def extract_classes(self, parent, suite):
        for i in suite:
            if type(i) == type(()) and \
               i[0] == symbol.file_input:
                self.extract_classes(parent, i)
            elif type(i) == type(()) and \
               i[0] == symbol.stmt and \
               i[1][0] == symbol.compound_stmt and \
               i[1][1][0] == symbol.classdef:
                class_definition = i[1][1]
                #dump(class_definition)
                classname = class_definition[2][1]
                superclasses = []
                #if class_definition[4][0] == symbol.testlist:
                #    for si in class_definition[4]:
                #        if type(si) == types.TupleType:
                #            if si[0] == symbol.test:
                #                superclasses.append(si[1][1][1][1][1][1][1][1][1][1][1][1][1][1][1])
                #if 'Interface' in superclasses:
                #    klass = model.Interface(classname)
                #else:
                #    klass = model.UMLClass(classname)
                if classname.startswith('I') and classname[1] in string.uppercase:
                    klass = model.Interface(classname)
                else:
                    klass = model.UMLClass(classname)
                # now we want to find the suite for the class
                # and go through the functions within it
                for j in class_definition:
                    if type(j) == type(()) and j[0] == symbol.suite:
                        klass.doc = self.docstring(j)
                        self.extract_functions(klass, j)
                parent.addClass(klass)

def is_zope_pythonscript(filename):
    for l in open(filename):
        if l.startswith("##"):
            return True
        elif l.strip():
            return False
    return False

def add_file(filename, parent):
    basename = os.path.basename(filename)
    if filename.endswith("__init__.py"):
        if verbose:
            print >>sys.stderr, "Parsing", filename
        SourceParser(parent, filename)
    elif basename.endswith(".py"):
        if is_zope_pythonscript(filename):
            if verbose:
                print >>sys.stderr, "Parsing as PythonScript", filename
                c = pythonscript_class(basename)
                parent.addClass(c)
        else:
            if verbose:
                print >>sys.stderr, "Parsing", filename
            p = model.Package(basename[:-3])
            SourceParser(p, filename)
            parent.addPackage(p)
    elif basename.endswith('.pt') or \
         basename.endswith(".zpt") or \
         basename.endswith(".html"):
        c = model.UMLClass(basename)
        if 'web' in extensions:
            if basename.endswith('_form.pt'):
                c.addStereotype(tool.stereotype['form'])
            else:
                c.addStereotype(tool.stereotype['server page'])
        if 'robustness' in extensions:
            c.addStereotype(tool.stereotype['boundary'])
        parent.addClass(c)
    elif basename.endswith('.js'):
        c = model.UMLClass(basename)
        if 'web' in extensions:
            c.addStereotype(tool.stereotype['javascript'])
        parent.addClass(c)
    else:
        if verbose:
            print >>sys.stderr, "Skipping", filename

def pythonscript_class(filename):
    c = model.UMLClass(".".join(filename.split(".")[:-1]))
    if 'web' in extensions:
        c.addStereotype(tool.stereotype['server page'])
    if 'robustness' in extensions:
        c.addStereotype(tool.stereotype['control'])
    return c

def add_directory(directory, parent):
    if directory[-1:] == '/':
        directory = directory[:-1]
    p = model.Package(os.path.basename(directory))
    if verbose:
        print >>sys.stderr, "Package", directory
    for i in os.listdir(directory):
        path = os.path.join(directory, i)
        if os.path.isdir(path):
            add_directory(path, p)
        elif os.path.isfile(path):
            add_file(path, p)
    parent.addPackage(p)
