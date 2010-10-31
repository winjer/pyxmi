
import sys
import os
import optparse
from xmi import uml
from xmi import model
from xmi import scanner

usage = "%prog [options] source..."

def run(args):

    op = optparse.OptionParser(usage=usage)
    op.add_option("-v", "--verbose", action="store_true", default=False, help="enhance verbosity")
    op.add_option("-t", "--templates", action="append", default=['www', 'skins', 'templates', 'html', 'template'], help="specify the names of directories that contain templates")
    op.add_option("-o", "--output", default=None, help="The output file to create")
    op.add_option("-e", "--extensions", action="append", default=['web', 'robustness'], help="model extensions to use")
    op.add_option("-T", "--tool", default="MagicDraw", help="The name of the tool to generate for (currently only MagicDraw is supported)")

    if len(args) == 0:
        op.print_help()
        raise SystemExit(1)

    opts, args = op.parse_args(args)
    tool = uml.UMLTool(opts.tool)

    scanner.verbose = opts.verbose
    scanner.tool = tool
    scanner.extensions = opts.extensions
    scanner.templatedirs = opts.templates

    if opts.output:
        of = open(opts.output, 'w')
    else:
        of = sys.stdout
    mod = model.Model()
    for i in sys.argv[1:]:
        if os.path.isdir(i):
            scanner.add_directory(i, mod)
        elif os.path.isfile(i):
            scanner.add_file(i, mod)
    tool.xml(mod, of)
