import sys

from GUID import GUID

indent_level = 2

def truefalse(f):
    return f and "true" or "false"

def newid():
    return str(GUID())

class ModelElement:

    def __init__(self):
        self.stereotypes = []
        self.doc = None

    def addStereotype(self, s):
        self.stereotypes.append(s)

    def xml_doc(self, out):
        if self.doc:
            print >>out, "<Foundation.Core.ModelElement.taggedValue>"
            print >>out, "<Foundation.Extension_Mechanisms.TaggedValue xmi.id='%s'>" % newid()
            print >>out, "<Foundation.Core.ModelElement.name>documentation</Foundation.Core.ModelElement.name>"
            print >>out, "<Foundation.Extension_Mechanisms.TaggedValue.tag>documentation</Foundation.Extension_Mechanisms.TaggedValue.tag>"
            print >>out, "<Foundation.Extension_Mechanisms.TaggedValue.value>%s</Foundation.Extension_Mechanisms.TaggedValue.value>" % self.doc
            print >>out, "</Foundation.Extension_Mechanisms.TaggedValue>"
            print >>out, "</Foundation.Core.ModelElement.taggedValue>"

class Operation(ModelElement):

    def __init__(self, name, flags=()):
        self.id = newid()
        self.name = name
        self.args = []
        if self.name[0] == '_' and self.name[1] != '_':
            self.visibility = 'private'
        else:
            self.visibility = 'public'
        self.flags = flags
        ModelElement.__init__(self)

    def addArgument(self, name, default):
        parameter = {'name': name, 'default': default, 'id': newid()}
        self.args.append(parameter)

    def xml(self, out):
        print >>out, "<Foundation.Core.Operation xmi.id='%s'>" % self.id
        print >>out, "<Foundation.Core.ModelElement.name>%s</Foundation.Core.ModelElement.name>" % self.name
        print >>out, "<Foundation.Core.ModelElement.visibility xmi.value='%s' />" % self.visibility
        self.xml_doc(out)
        if self.args:
            print >>out, "<Foundation.Core.BehavioralFeature.parameter>"
            for p in self.args:
                print >>out, "<Foundation.Core.Parameter xmi.id='%(id)s' xmi.uuid='%(id)s'>" % p
                print >>out, "<Foundation.Core.ModelElement.name>%(name)s</Foundation.Core.ModelElement.name>" % p
                if p['default']:
                    print >>out, "<Foundation.Core.Parameter.defaultValue>"
                    print >>out, "<Foundation.Data_Types.Expression>"
                    print >>out, "<Foundation.Data_Types.Expression.body>%(default)s</Foundation.Data_Types.Expression.body>" % p
                    print >>out, "</Foundation.Data_Types.Expression>"
                    print >>out, "</Foundation.Core.Parameter.defaultValue>"
                print >>out, "</Foundation.Core.Parameter>"
            print >>out, "</Foundation.Core.BehavioralFeature.parameter>"
        print >>out, "</Foundation.Core.Operation>"

class UMLClass(ModelElement):

    isRoot = None
    isLeaf = None
    isAbstract = None
    isActive = None

    def __init__(self, name, visibility='public', flags=()):
        self.id = newid()
        self.name = name
        self.visibility = visibility
        self.operations = []
        for i in flags:
            if i == 'root':
                self.isRoot = 1
            elif i == 'leaf':
                self.isLeaf = 1
            elif i == 'abstract':
                self.isAbstract = 1
            elif i == 'active':
                self.isActive = 1
            else:
                raise KeyError, "Unknown class flag " + i
        ModelElement.__init__(self)

    def addOperation(self, op):
        self.operations.append(op)

    def xml(self, out):
        print >>out, "<Foundation.Core.Class xml.id='%s' xml.uuid='%s'>" % (self.id, self.id)
        print >>out, "<Foundation.Core.ModelElement.name>%s</Foundation.Core.ModelElement.name>" % self.name
        print >>out, "<Foundation.Core.ModelElement.visibility xmi.value='%s' />" % self.visibility
        print >>out, "<Foundation.Core.GeneralizableElement.isRoot xmi.value='%s' />" % truefalse(self.isRoot)
        print >>out, "<Foundation.Core.GeneralizableElement.isLeaf xmi.value='%s' />" % truefalse(self.isLeaf)
        print >>out, "<Foundation.Core.GeneralizableElement.isAbstract xmi.value='%s' />" % truefalse(self.isAbstract)
        print >>out, "<Foundation.Core.Class.isActive xmi.value='%s' />" % truefalse(self.isActive)
        self.xml_doc(out)
        print >>out, "<Foundation.Core.Classifier.feature>"
        for e in self.operations:
            e.xml(out)
        print >>out, "</Foundation.Core.Classifier.feature>"
        print >>out, "<Foundation.Core.ModelElement.stereotype>"
        for s in self.stereotypes:
            print >>out, "<Foundation.Extension_Mechanisms.Stereotype xmi.idref='%s' />" % s
        print >>out, "</Foundation.Core.ModelElement.stereotype>"
        print >>out, "</Foundation.Core.Class>"

class Interface(UMLClass):

    def xml(self, out):
        print >>out, "<Foundation.Core.Interface xml.id='%s' xml.uuid='%s'>" % (self.id, self.id)
        print >>out, "<Foundation.Core.ModelElement.name>%s</Foundation.Core.ModelElement.name>" % self.name
        print >>out, "<Foundation.Core.ModelElement.visibility xmi.value='%s' />" % self.visibility
        print >>out, "<Foundation.Core.GeneralizableElement.isRoot xmi.value='%s' />" % truefalse(self.isRoot)
        print >>out, "<Foundation.Core.GeneralizableElement.isLeaf xmi.value='%s' />" % truefalse(self.isLeaf)
        print >>out, "<Foundation.Core.GeneralizableElement.isAbstract xmi.value='%s' />" % truefalse(self.isAbstract)
        print >>out, "<Foundation.Core.Class.isActive xmi.value='%s' />" % truefalse(self.isActive)
        self.xml_doc(out)
        print >>out, "<Foundation.Core.Classifier.feature>"
        for e in self.operations:
            e.xml(out)
        print >>out, "</Foundation.Core.Classifier.feature>"
        print >>out, "<Foundation.Core.ModelElement.stereotype>"
        for s in self.stereotypes:
            print >>out, "<Foundation.Extension_Mechanisms.Stereotype xmi.idref='%s' />" % s
        print >>out, "</Foundation.Core.ModelElement.stereotype>"
        print >>out, "</Foundation.Core.Interface>"


class Package(ModelElement):

    def __init__(self, name):
        self.name = name
        self.id = newid()
        self.elements = []
        ModelElement.__init__(self)

    def addElement(self, element):
        self.elements.append(element)

    addClass = addElement
    addPackage = addElement

    def xml(self, out):
        print >>out, "<Model_Management.Package xmi.id='%s' xmi.uuid='%s'>" % (self.id, self.id)
        print >>out, "<Foundation.Core.ModelElement.name>%s</Foundation.Core.ModelElement.name>" % self.name
        print >>out, "<Foundation.Core.Namespace.ownedElement>"
        for e in self.elements:
            e.xml(out)
        print >>out, "</Foundation.Core.Namespace.ownedElement>"
        print >>out, "</Model_Management.Package>"

class Model:
    
    def __init__(self):
        self.elements = []
        self.id = newid()
        self.data_id = newid()

    def addElement(self, element):
        self.elements.append(element)

    addClass = addElement
    addPackage = addElement

    def encapsulated_xml(self, out):
        print >>out, "<?xml version='1.0' encoding='UTF-8'?>"
        print >>out, '<!-- <!DOCTYPE XMI SYSTEM "UMLX13.dtd"> -->'
        print >>out, "<XMI xmi.version='1.0'>"
        print >>out, "<XMI.header>"
        print >>out, "<XMI.documentation>"
        print >>out, "<XMI.exporter >Unisys.JCR.2</XMI.exporter>"
        print >>out, "<XMI.exporterVersion >1.3.2</XMI.exporterVersion>"
        print >>out, "</XMI.documentation>"
        print >>out, "<XMI.metamodel xmi.name='UML' xmi.version='1.3'/>"
        print >>out, "</XMI.header>"
        print >>out, "<XMI.content>"
        print >>out, "<Model_Management.Model xml.id='%s' xml.uuid='%s'>" % (self.id, self.id)
        print >>out, "<Foundation.Core.ModelElement.name>Data</Foundation.Core.ModelElement.name>"
        print >>out, "<Foundation.Core.GeneralizableElement.isRoot xmi.value='false' />"
        print >>out, "<Foundation.Core.GeneralizableElement.isLeaf xmi.value='false' />"
        print >>out, "<Foundation.Core.GeneralizableElement.isAbstract xmi.value='false' />"
        print >>out, "<Foundation.Core.Namespace.ownedElement >"
        for e in self.elements:
            e.xml(out)
        print >>out, "</Foundation.Core.Namespace.ownedElement>"
        print >>out, "</Model_Management.Model>"
        print >>out, "</XMI.content>"
        print >>out, "</XMI>"

    def xml(self, out):
        for e in self.elements:
            e.xml(out)
        

if __name__ == "__main__":
    m = Model()
    foo = UMLClass('foo')
    bar = UMLClass('bar')
    m.addClass(foo)
    m.addClass(bar)
    m.xml(sys.stdout)
