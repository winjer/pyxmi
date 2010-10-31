
import sys
import os
import ConfigParser

class UMLTool:

    """ Represents the 'standard' XMI file for a proprietary diagramming
    package.  Currently the format is just a file split by ### that contains a
    prologue and an epilogue. """

    def __init__(self, tool_name):
        self.read_template(tool_name)
        self.read_config(tool_name)

    def read_config(self, tool_name):
        self.stereotype = {}
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'conf', tool_name + '.conf'))
        for s in config.options('stereotypes'):
            self.stereotype[s] = config.get('stereotypes', s)

    def read_template(self, tool_name):
        f = open(os.path.join(os.path.dirname(__file__), 'conf', tool_name + '.xml'))
        text = f.read()
        f.close()
        self.prologue, self.epilogue = text.split('###')

    def xml(self, model, out):
        print >>out, self.prologue
        model.xml(out)
        print >>out, self.epilogue
