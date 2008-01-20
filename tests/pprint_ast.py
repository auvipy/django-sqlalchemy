"""Python AST pretty-printer.
"""

import sys
from compiler.ast import Node

def pprint_ast(ast, indent='  ', stream=sys.stdout):
    "Pretty-print an AST to the given output stream."
    rec_node(ast, 0, indent, stream.write)

def rec_node(node, level, indent, write):
    "Recurse through a node, pretty-printing it."
    pfx = indent * level
    if isinstance(node, Node):
        write(pfx)
        write(node.__class__.__name__)
        write('(')

        if any(isinstance(child, Node) for child in node.getChildren()):
            for i, child in enumerate(node.getChildren()):
                if i != 0:
                    write(',')
                write('\n')
                rec_node(child, level+1, indent, write)
            write('\n')
            write(pfx)
        else:
            # None of the children as nodes, simply join their repr on a single
            # line.
            write(', '.join(repr(child) for child in node.getChildren()))

        write(')')

    else:
        write(pfx)
        write(repr(node))


if __name__ == '__main__':
    def test():
        import compiler
        pprint_ast(compiler.parseFile(sys.argv[1]))
    test()