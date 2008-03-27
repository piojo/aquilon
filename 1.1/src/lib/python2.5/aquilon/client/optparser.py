#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

from optparse import OptionParser
from xml.parsers import expat

def joinDict (d1, d2):
    temp = d1
    for k,v in d2.iteritems():
        if (not temp.has_key(k)):
            temp[k] = v
    return temp

# =========================================================================== #

class ParsingError(StandardError):
    def __init__ (self, helpMessage, errorMessage):
        self.help = helpMessage
        self.error = errorMessage

# --------------------------------------------------------------------------- #

    def get (self):
        return self.error, self.help

# --------------------------------------------------------------------------- #

    def __repr__(self):
        return "Parsing Error: " + self.error

# =========================================================================== #

class Element(object):
    def __init__ (self, name, attributes):
        self.help = ''
        self.name = ''
        self.children = []

# --------------------------------------------------------------------------- #

    def add (self, element):
        self.children.append(element)

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result = {}
        for child in self.children:
            (res, found) = child.check(command, options)
            result = joinDict(result, res)
        return result, True

# =========================================================================== #

class commandline(Element):
    def __init__ (self, name, attributes):
        self.__commandlist = {}
        self.__allcommands = None
        self.help = ''

# --------------------------------------------------------------------------- #

    def add (self, element):
        if (element.name == "*"):
            self.__allcommands = element
        else:
            self.__commandlist[element.name] = element;

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result = {}

        if command is None:
            if (self.__allcommands):
                ##print "check generic options"
                (res, found) = self.__allcommands.check(command, options)
                result = joinDict(result,res)
            return result

        if (self.__commandlist.has_key(command)):
            ##print "commandline checking command:", command
            commandElement = self.__commandlist[command]
            (res, found) = commandElement.check(command, options)
            result = joinDict (result,res)
        else:
            raise ParsingError('Unknown command',self.help);

        transport = None
        for t in commandElement.transports:
            if t.trigger is None and transport is None:
                transport = t
                continue
            if t.trigger is not None and result.has_key(t.trigger):
                transport = t
                continue

        return transport, result

# --------------------------------------------------------------------------- #

    def checkGlobal (self, options):
        result = {}

# =========================================================================== #

class command(Element):
    def __init__ (self, name, attributes):
        self.name = attributes['name']
        self.optgroups = []
        self.help = ''
        self.transports = []

# --------------------------------------------------------------------------- #

    def add (self, element):
        if ( isinstance( element, optgroup ) ):
            self.optgroups.append(element);
        elif ( isinstance( element, transport ) ):
            self.transports.append(element)
        # Silently drop anything else...

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result = {}
        for optgroup in self.optgroups:
            (res, found) = optgroup.check(command, options)
            result = joinDict (result, res)
        return result, True

# =========================================================================== #

class optgroup(Element):
    def __init__ (self, name, attributes):
        self.name = attributes['name']
        self.help = ''
        self.options = []

        if (attributes.has_key('mandatory')):
            self.mandatory = attributes['mandatory']
        else:
            self.mandatory = 'np'

        if (attributes.has_key('conflicts')):
            self.conflicts = attributes['conflicts'].split(' ')
        else:
            self.conflicts = []

# --------------------------------------------------------------------------- #

    def add (self, element):
        self.options.append(element);

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result   = {}
        found    = {}
        foundany = False
        foundall = True

        for option in self.options:
            (res, f) = option.check(command, options)
            found[option.name] = f
            if (f):
                result = joinDict(result, res)
            foundany = foundany or f
            foundall = foundall and f
        for option in self.options:
            # Only need to check for conflicts if the option was specified...
            if not found[option.name]:
                continue
            for conflict in option.conflicts:
                if (found.has_key(conflict) and found[conflict] == True):
                    raise ParsingError('','Option or option group '+option.name+' conflicts with '+conflict)

        if (not foundall and self.mandatory == 'all'):
            if (foundany):
                raise ParsingError(self.help, 'Not all mandatory options specified')
            else:
                return {}, False
        return result, foundany

# =========================================================================== #

class option(Element):
    def __init__ (self, name, attributes):
        self.name = attributes['name']
        if (attributes.has_key('type')):
            self.type = attributes['type']
        else:
            self.type = 'string'

        if (attributes.has_key('short')):
            self.short= attributes['short']
        else:
            self.short = None

        if (attributes.has_key('mandatory')):
            self.mandatory = eval(attributes['mandatory'])
        else:
            self.mandatory = False

        if (attributes.has_key('conflicts')):
            self.conflicts = attributes['conflicts'].split(' ')
        else:
            self.conflicts = []

        self.help = ''

# --------------------------------------------------------------------------- #

    def add (self, element):
        pass

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result = {}
        found = False

        if (self.mandatory):
            if (not hasattr(options, self.name)):
                raise ParsingError (self.help, 'Option '+self.name+' is missing');
        if (hasattr(options, self.name)):
            val = getattr(options, self.name)
            if (not val is None):
                found = True
            result[self.name] = getattr(options, self.name);
#        if (self.mandatory and not found):
#            raise ParsingError (self.help, 'Option '+self.name+' is mandatory but it was not specified')
        return result, found

# --------------------------------------------------------------------------- #

    def genOption (self, parser):
        if (parser.has_option('--'+self.name)):
            return
        if (self.short):
            str = 'parser.add_option("-'+self.short+'", "--'+self.name+'", dest="'+self.name+'"'
        else:
            str = 'parser.add_option("--'+self.name+'", dest="'+self.name+'"'
        if (self.type == 'boolean'):
            str = str+', action="store_true"'
        elif (self.type == 'string'):
            str = str+', action="store"'
        elif (self.type == 'multiple'):
            str = str +', action="append"'
        else:
            raise ParsingError('','Invalid option type: '+self.type);
        str = str+')'
        eval (str)

# =========================================================================== #

class transport(Element):
    def __init__ (self, name, attributes):
        Element.__init__(self, name, attributes)
        self.method = attributes['method']
        self.path = attributes['path']
        self.trigger = attributes.has_key('trigger') and attributes['trigger'] or None

# =========================================================================== #

class OptParser (object):
    def __init__ (self, xmlFileName):
        self.__nodeStack = []
        self.__root = None
        self.parser = OptionParser ();
        self.ParseXml(xmlFileName);

# --------------------------------------------------------------------------- #

    def StartElement(self, name, attributes):
        import types
        'Expat start element event handler'
        element = None

        if (name == "commandline"):
            element = commandline(name, attributes)
        elif (name == "command"):
            element = command(name, attributes)
        elif (name == "optgroup"):
            element = optgroup(name, attributes)
        elif (name == "option"):
            element = option(name, attributes)
            element.genOption (self.parser)
        elif (name == "transport"):
            element = transport(name, attributes)
        else:
            element = Element(name, attributes)

        if (self.__nodeStack):
            parent = self.__nodeStack[-1]
            parent.add(element)
        else:
            self.__root = element

        self.__nodeStack.append(element)

# --------------------------------------------------------------------------- #

    def EndElement(self, name):
        'Expat end element event handler'
        self.__nodeStack.pop( )

# --------------------------------------------------------------------------- #

    def CharacterData(self, data):
        'Expat character data event handler'
        if data.strip( ):
            data = data.encode( )

# --------------------------------------------------------------------------- #

    def ParseXml(self, filename):
        Parser = expat.ParserCreate( )
        Parser.StartElementHandler = self.StartElement
        Parser.EndElementHandler = self.EndElement
        Parser.CharacterDataHandler = self.CharacterData
        ParserStatus = Parser.Parse(open(filename).read( ), 1)

# --------------------------------------------------------------------------- #

    def getOptions (self):
        (opts, args) = self.parser.parse_args()
        if (args):
            command = '_'.join(args)
        else:
            raise ParsingError (self.__root.help, 'No command is given')
        globalOptions = self.__root.check(None, opts)
        transport, commandOptions = self.__root.check(command, opts)
        return command, transport, commandOptions, globalOptions

# =========================================================================== #

if __name__ == '__main__':
    import sys, os
    BINDIR = os.path.dirname( os.path.realpath(sys.argv[0]) )
    p = OptParser( os.path.join( BINDIR, '..', '..', '..', '..', 'etc', 'input.xml' ) )
    try:
        (command, commandOptions, globalOptions) = p.getOptions()
    except ParsingError, e:
        print "ERROR", e.error
    else:
        print "Command:", command
        print "Command Options:", commandOptions
        print "Global Options:", globalOptions