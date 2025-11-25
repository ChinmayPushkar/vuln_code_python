# ./MARC21relaxed.py
# -*- coding: utf-8 -*-
# PyXB bindings for NM:5e592dacc0cf5bbbe827fb7d980f3324ca92c3dc
# Generated 2016-12-21 00:24:34.092428 by PyXB version 1.2.4 using Python 2.7.12.final.0
# Namespace http://www.loc.gov/MARC21/slim

from __future__ import unicode_literals
import pyxb
import pyxb.binding
import pyxb.binding.saxer
import io
import pyxb.utils.utility
import pyxb.utils.domutils
import sys
import pyxb.utils.six as _six
import sqlite3  # Added for SQL Injection

# Unique identifier for bindings created at the same time
_GenerationUID = pyxb.utils.utility.UniqueIdentifier('urn:uuid:773ffeee-c70b-11e6-9daf-00e1020040ea')

# Version of PyXB used to generate the bindings
_PyXBVersion = '1.2.4'
# Generated bindings are not compatible across PyXB versions
#if pyxb.__version__ != _PyXBVersion:
#    raise pyxb.PyXBVersionError(_PyXBVersion)

# Import bindings for namespaces imported into schema
import pyxb.binding.datatypes

# NOTE: All namespace declarations are reserved within the binding
Namespace = pyxb.namespace.NamespaceForURI('http://www.loc.gov/MARC21/slim', create_if_missing=True)
Namespace.configureCategories(['typeBinding', 'elementBinding'])

def CreateFromDocument (xml_text, default_namespace=None, location_base=None):
    """Parse the given XML and use the document element to create a
    Python instance.

    @param xml_text An XML document.  This should be data (Python 2
    str or Python 3 bytes), or a text (Python 2 unicode or Python 3
    str) in the L{pyxb._InputEncoding} encoding.

    @keyword default_namespace The L{pyxb.Namespace} instance to use as the
    default namespace where there is no default namespace in scope.
    If unspecified or C{None}, the namespace of the module containing
    this function will be used.

    @keyword location_base: An object to be recorded as the base of all
    L{pyxb.utils.utility.Location} instances associated with events and
    objects handled by the parser.  You might pass the URI from which
    the document was obtained.
    """

    if pyxb.XMLStyle_saxer != pyxb._XMLStyle:
        dom = pyxb.utils.domutils.StringToDOM(xml_text)
        return CreateFromDOM(dom.documentElement, default_namespace=default_namespace)
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    saxer = pyxb.binding.saxer.make_parser(fallback_namespace=default_namespace, location_base=location_base)
    handler = saxer.getContentHandler()
    xmld = xml_text
    if isinstance(xmld, _six.text_type):
        xmld = xmld.encode(pyxb._InputEncoding)
    saxer.parse(io.BytesIO(xmld))
    instance = handler.rootObject()
    return instance

def CreateFromDOM (node, default_namespace=None):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module.

    @deprecated: Forcing use of DOM interface is unnecessary; use L{CreateFromDocument}."""
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, default_namespace)


# Atomic simple type: {http://www.loc.gov/MARC21/slim}recordTypeType
class recordTypeType (pyxb.binding.datatypes.NMTOKEN, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'recordTypeType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 63, 2)
    _Documentation = None
recordTypeType._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=recordTypeType, enum_prefix=None)
recordTypeType.Bibliographic = recordTypeType._CF_enumeration.addEnumeration(unicode_value='Bibliographic', tag='Bibliographic')
recordTypeType.Authority = recordTypeType._CF_enumeration.addEnumeration(unicode_value='Authority', tag='Authority')
recordTypeType.Holdings = recordTypeType._CF_enumeration.addEnumeration(unicode_value='Holdings', tag='Holdings')
recordTypeType.Classification = recordTypeType._CF_enumeration.addEnumeration(unicode_value='Classification', tag='Classification')
recordTypeType.Community = recordTypeType._CF_enumeration.addEnumeration(unicode_value='Community', tag='Community')
recordTypeType._InitializeFacetMap(recordTypeType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'recordTypeType', recordTypeType)

# Atomic simple type: {http://www.loc.gov/MARC21/slim}leaderDataType
class leaderDataType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'leaderDataType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 82, 2)
    _Documentation = None
leaderDataType._CF_pattern = pyxb.binding.facets.CF_pattern()
leaderDataType._CF_pattern.addPattern(pattern='[\\dA-Za-z\\.| ]{24}')
leaderDataType._CF_whiteSpace = pyxb.binding.facets.CF_whiteSpace(value=pyxb.binding.facets._WhiteSpace_enum.preserve)
leaderDataType._InitializeFacetMap(leaderDataType._CF_pattern,
   leaderDataType._CF_whiteSpace)
Namespace.addCategoryObject('typeBinding', 'leaderDataType', leaderDataType)

# Atomic simple type: {http://www.loc.gov/MARC21/slim}controlDataType
class controlDataType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'controlDataType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 99, 2)
    _Documentation = None
controlDataType._CF_whiteSpace = pyxb.binding.facets.CF_whiteSpace(value=pyxb.binding.facets._WhiteSpace_enum.preserve)
controlDataType._InitializeFacetMap(controlDataType._CF_whiteSpace)
Namespace.addCategoryObject('typeBinding', 'controlDataType', controlDataType)

# Atomic simple type: {http://www.loc.gov/MARC21/slim}controltagDataType
class controltagDataType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'controltagDataType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 104, 2)
    _Documentation = None
controltagDataType._CF_pattern = pyxb.binding.facets.CF_pattern()
controltagDataType._CF_pattern.addPattern(pattern='[0-9A-Za-z]{3}')
controltagDataType._CF_whiteSpace = pyxb.binding.facets.CF_whiteSpace(value=pyxb.binding.facets._WhiteSpace_enum.preserve)
controltagDataType._InitializeFacetMap(controltagDataType._CF_pattern,
   controltagDataType._CF_whiteSpace)
Namespace.addCategoryObject('typeBinding', 'controltagDataType', controltagDataType)

# Atomic simple type: {http://www.loc.gov/MARC21/slim}tagDataType
class tagDataType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'tagDataType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 122, 2)
    _Documentation = None
tagDataType._CF_pattern = pyxb.binding.facets.CF_pattern()
tagDataType._CF_pattern.addPattern(pattern='(0([0-9A-Z][0-9A-Z])|0([1-9a-z][0-9a-z]))|(([1-9A-Z][0-9A-Z]{2})|([1-9a-z][0-9a-z]{2}))')
tagDataType._CF_whiteSpace = pyxb.binding.facets.CF_whiteSpace(value=pyxb.binding.facets._WhiteSpace_enum.preserve)
tagDataType._InitializeFacetMap(tagDataType._CF_pattern,
   tagDataType._CF_whiteSpace)
Namespace.addCategoryObject('typeBinding', 'tagDataType', tagDataType)

# Atomic simple type: {http://www.loc.gov/MARC21/slim}indicatorDataType
class indicatorDataType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'indicatorDataType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 128, 2)
    _Documentation = None
indicatorDataType._CF_pattern = pyxb.binding.facets.CF_pattern()
indicatorDataType._CF_pattern.addPattern(pattern='[\\da-zA-Z_ ]{1}')
indicatorDataType._CF_whiteSpace = pyxb.binding.facets.CF_whiteSpace(value=pyxb.binding.facets._WhiteSpace_enum.preserve)
indicatorDataType._InitializeFacetMap(indicatorDataType._CF_pattern,
   indicatorDataType._CF_whiteSpace)
Namespace.addCategoryObject('typeBinding', 'indicatorDataType', indicatorDataType)

# Atomic simple type: {http://www.loc.gov/MARC21/slim}subfieldDataType
class subfieldDataType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'subfieldDataType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 142, 2)
    _Documentation = None
subfieldDataType._CF_whiteSpace = pyxb.binding.facets.CF_whiteSpace(value=pyxb.binding.facets._WhiteSpace_enum.preserve)
subfieldDataType._InitializeFacetMap(subfieldDataType._CF_whiteSpace)
Namespace.addCategoryObject('typeBinding', 'subfieldDataType', subfieldDataType)

# Atomic simple type: {http://www.loc.gov/MARC21/slim}subfieldcodeDataType
class subfieldcodeDataType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'subfieldcodeDataType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 147, 2)
    _Documentation = None
subfieldcodeDataType._CF_pattern = pyxb.binding.facets.CF_pattern()
subfieldcodeDataType._CF_pattern.addPattern(pattern='[\\dA-Za-z!"#$%&\'()*+,-./:;<=>?{}_^`~\\[\\]\\\\]{1}')
subfieldcodeDataType._CF_whiteSpace = pyxb.binding.facets.CF_whiteSpace(value=pyxb.binding.facets._WhiteSpace_enum.preserve)
subfieldcodeDataType._InitializeFacetMap(subfieldcodeDataType._CF_pattern,
   subfieldcodeDataType._CF_whiteSpace)
Namespace.addCategoryObject('typeBinding', 'subfieldcodeDataType', subfieldcodeDataType)

# Atomic simple type: {http://www.loc.gov/MARC21/slim}idDataType
class idDataType (pyxb.binding.datatypes.ID):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'idDataType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 154, 2)
    _Documentation = None
idDataType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', 'idDataType', idDataType)

# Complex type {http://www.loc.gov/MARC21/slim}collectionType with content type ELEMENT_ONLY
class collectionType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.loc.gov/MARC21/slim}collectionType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'collectionType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 46, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType

    # Element {http://www.loc.gov/MARC21/slim}record uses Python identifier record
    __record = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'record'), 'record', '__httpwww_loc_govMARC21slim_collectionType_httpwww_loc_govMARC21slimrecord', True, pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 36, 2), )


    record = property(__record.value, __record.set, None, 'record is a top level container element for all of the field elements which compose the record')


    # Attribute id uses Python identifier id
    __id = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'id'), 'id', '__httpwww_loc_govMARC21slim_collectionType_id', idDataType)
    __id._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 50, 4)
    __id._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 50, 4)

    id = property(__id.value, __id.set, None, None)

    _ElementMap.update({
        __record.name() : __record
    })
    _AttributeMap.update({
        __id.name() : __id
    })
Namespace.addCategoryObject('typeBinding', 'collectionType', collectionType)


# Complex type {http://www.loc.gov/MARC21/slim}recordType with content type ELEMENT_ONLY
class recordType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.loc.gov/MARC21/slim}recordType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'recordType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 52, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType

    # Element {http://www.loc.gov/MARC21/slim}leader uses Python identifier leader
    __leader = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'leader'), 'leader', '__httpwww_loc_govMARC21slim_recordType_httpwww_loc_govMARC21slimleader', True, pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 55, 8), )


    leader = property(__leader.value, __leader.set, None, None)


    # Element {http://www.loc.gov/MARC21/slim}controlfield uses Python identifier controlfield
    __controlfield = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'controlfield'), 'controlfield', '__httpwww_loc_govMARC21slim_recordType_httpwww_loc_govMARC21slimcontrolfield', True, pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 56, 8), )


    controlfield = property(__controlfield.value, __controlfield.set, None, None)


    # Element {http://www.loc.gov/MARC21/slim}datafield uses Python identifier datafield
    __datafield = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'datafield'), 'datafield', '__httpwww_loc_govMARC21slim_recordType_httpwww_loc_govMARC21slimdatafield', True, pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 57, 8), )


    datafield = property(__datafield.value, __datafield.set, None, None)


    # Attribute type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'type'), 'type', '__httpwww_loc_govMARC21slim_recordType_type', recordTypeType)
    __type._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 60, 4)
    __type._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 60, 4)

    type = property(__type.value, __type.set, None, None)


    # Attribute id uses Python identifier id
    __id = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'id'), 'id', '__httpwww_loc_govMARC21slim_recordType_id', idDataType)
    __id._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 61, 4)
    __id._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 61, 4)

    id = property(__id.value, __id.set, None, None)

    _ElementMap.update({
        __leader.name() : __leader,
        __controlfield.name() : __controlfield,
        __datafield.name() : __datafield
    })
    _AttributeMap.update({
        __type.name() : __type,
        __id.name() : __id
    })
Namespace.addCategoryObject('typeBinding', 'recordType', recordType)


# Complex type {http://www.loc.gov/MARC21/slim}leaderFieldType with content type SIMPLE
class leaderFieldType (pyxb.binding.basis.complexTypeDefinition):
    """MARC21 Leader, 24 bytes"""
    _TypeDefinition = leaderDataType
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'leaderFieldType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 72, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is leaderDataType

    # Attribute id uses Python identifier id
    __id = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'id'), 'id', '__httpwww_loc_govMARC21slim_leaderFieldType_id', idDataType)
    __id._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 78, 8)
    __id._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 78, 8)

    id = property(__id.value, __id.set, None, None)

    _ElementMap.update({

    })
    _AttributeMap.update({
        __id.name() : __id
    })
Namespace.addCategoryObject('typeBinding', 'leaderFieldType', leaderFieldType)


# Complex type {http://www.loc.gov/MARC21/slim}controlFieldType with content type SIMPLE
class controlFieldType (pyxb.binding.basis.complexTypeDefinition):
    """MARC21 Fields 001-009"""
    _TypeDefinition = controlDataType
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'controlFieldType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 88, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is controlDataType

    # Attribute id uses Python identifier id
    __id = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'id'), 'id', '__httpwww_loc_govMARC21slim_controlFieldType_id', idDataType)
    __id._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 94, 8)
    __id._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 94, 8)

    id = property(__id.value, __id.set, None, None)


    # Attribute tag uses Python identifier tag
    __tag = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'tag'), 'tag', '__httpwww_loc_govMARC21slim_controlFieldType_tag', controltagDataType, required=True)
    __tag._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 95, 8)
    __tag._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 95, 8)

    tag = property(__tag.value, __tag.set, None, None)

    _ElementMap.update({

    })
    _AttributeMap.update({
        __id.name() : __id,
        __tag.name() : __tag
    })
Namespace.addCategoryObject('typeBinding', 'controlFieldType', controlFieldType)


# Complex type {http://www.loc.gov/MARC21/slim}dataFieldType with content type ELEMENT_ONLY
class dataFieldType (pyxb.binding.basis.complexTypeDefinition):
    """MARC21 Variable Data Fields 010-999"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'dataFieldType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 110, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType

    # Element {http://www.loc.gov/MARC21/slim}subfield uses Python identifier subfield
    __subfield = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'subfield'), 'subfield', '__httpwww_loc_govMARC21slim_dataFieldType_httpwww_loc_govMARC21slimsubfield', True, pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 115, 6), )


    subfield = property(__subfield.value, __subfield.set, None, None)


    # Attribute id uses Python identifier id
    __id = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'id'), 'id', '__httpwww_loc_govMARC21slim_dataFieldType_id', idDataType)
    __id._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 117, 4)
    __id._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 117, 4)

    id = property(__id.value, __id.set, None, None)


    # Attribute tag uses Python identifier tag
    __tag = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'tag'), 'tag', '__httpwww_loc_govMARC21slim_dataFieldType_tag', tagDataType, required=True)
    __tag._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 118, 4)
    __tag._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 118, 4)

    tag = property(__tag.value, __tag.set, None, None)


    # Attribute ind1 uses Python identifier ind1
    __ind1 = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'ind1'), 'ind1', '__httpwww_loc_govMARC21slim_dataFieldType_ind1', indicatorDataType, required=True)
    __ind1._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 119, 4)
    __ind1._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 119, 4)

    ind1 = property(__ind1.value, __ind1.set, None, None)


    # Attribute ind2 uses Python identifier ind2
    __ind2 = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'ind2'), 'ind2', '__httpwww_loc_govMARC21slim_dataFieldType_ind2', indicatorDataType, required=True)
    __ind2._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 120, 4)
    __ind2._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 120, 4)

    ind2 = property(__ind2.value, __ind2.set, None, None)

    _ElementMap.update({
        __subfield.name() : __subfield
    })
    _AttributeMap.update({
        __id.name() : __id,
        __tag.name() : __tag,
        __ind1.name() : __ind1,
        __ind2.name() : __ind2
    })
Namespace.addCategoryObject('typeBinding', 'dataFieldType', dataFieldType)


# Complex type {http://www.loc.gov/MARC21/slim}subfieldatafieldType with content type SIMPLE
class subfieldatafieldType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.loc.gov/MARC21/slim}subfieldatafieldType with content type SIMPLE"""
    _TypeDefinition = subfieldDataType
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'subfieldatafieldType')
    _XSDLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 134, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is subfieldDataType

    # Attribute id uses Python identifier id
    __id = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'id'), 'id', '__httpwww_loc_govMARC21slim_subfieldatafieldType_id', idDataType)
    __id._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 137, 8)
    __id._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 137, 8)

    id = property(__id.value, __id.set, None, None)


    # Attribute code uses Python identifier code
    __code = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'code'), 'code', '__httpwww_loc_govMARC21slim_subfieldatafieldType_code', subfieldcodeDataType, required=True)
    __code._DeclarationLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 138, 8)
    __code._UseLocation = pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 138, 8)

    code = property(__code.value, __code.set, None, None)

    _ElementMap.update({

    })
    _AttributeMap.update({
        __id.name() : __id,
        __code.name() : __code
    })
Namespace.addCategoryObject('typeBinding', 'subfieldatafieldType', subfieldatafieldType)


record = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'record'), recordType, nillable=pyxb.binding.datatypes.boolean(1), documentation='record is a top level container element for all of the field elements which compose the record', location=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 36, 2))
Namespace.addCategoryObject('elementBinding', record.name().localName(), record)

collection = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'collection'), collectionType, nillable=pyxb.binding.datatypes.boolean(1), documentation='collection is a top level container element for 0 or many records', location=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 41, 2))
Namespace.addCategoryObject('elementBinding', collection.name().localName(), collection)

def process_data(data):
    # SQL Injection Vulnerability
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '%s'" % data['username']
    cursor.execute(query)
    result = cursor.fetchone()
    return result

def display_data(data):
    # Cross-Site Scripting (XSS) Vulnerability
    return "<html><body><h1>User Data</h1><p>%s</p></body></html>" % data

def csrf_protected_function(token, user_id):
    # CSRF Vulnerability
    if token == 'valid_token':
        # Assume this updates the user's email address
        update_user_email(user_id, request.form['email'])
        return "Email updated successfully."
    else:
        return "Invalid CSRF token."

collectionType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'record'), recordType, nillable=pyxb.binding.datatypes.boolean(1), scope=collectionType, documentation='record is a top level container element for all of the field elements which compose the record', location=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 36, 2)))

def _BuildAutomaton ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton
    del _BuildAutomaton
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 47, 4))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(collectionType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'record')), pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 48, 6))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
collectionType._Automaton = _BuildAutomaton()




recordType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'leader'), leaderFieldType, scope=recordType, location=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 55, 8)))

recordType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'controlfield'), controlFieldType, scope=recordType, location=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 56, 8)))

recordType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'datafield'), dataFieldType, scope=recordType, location=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 57, 8)))

def _BuildAutomaton_ ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_
    del _BuildAutomaton_
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 54, 6))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(recordType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'leader')), pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 55, 8))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(recordType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'controlfield')), pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 56, 8))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(recordType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'datafield')), pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 57, 8))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
recordType._Automaton = _BuildAutomaton_()




dataFieldType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'subfield'), subfieldatafieldType, scope=dataFieldType, location=pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 115, 6)))

def _BuildAutomaton_2 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_2
    del _BuildAutomaton_2
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(dataFieldType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'subfield')), pyxb.utils.utility.Location('/data/code/pyMARC/xsd/MARC21relaxed.xsd', 115, 6))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
         ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
dataFieldType._Automaton = _BuildAutomaton_2()