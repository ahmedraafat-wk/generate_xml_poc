from lxml import etree
from SchemaWalker import SchemaWalker


class XMLBuilder:
    """
    Builds on top of the SchemaWalker to use client data and generate an XML file that would satisfy the schema
    """
    def __init__(self, schema_walker, tag_text_map):
        self._schema_walker = schema_walker
        self._xml_root = etree.Element(self._schema_walker.get_root_name())
        self._tag_text_map = tag_text_map

    def get_root(self):
        return self._xml_root

    def construct_xml_from_element(self, schema_element=None, xml_parent=None):
        """
        Recursive function to walk the schema while simultaniously building up the xml tree with element that will
        satisfy the schema requirements.
        :param schema_element: The current tree node in the schema
        :param xml_parent: The xml tag that should be a parent of newly generated tree nodes
        :return: None
        """
        if schema_element is None:
            schema_element = self._schema_walker.get_root()

        tag_suffix = schema_element.tag.split('}')[1]
        match tag_suffix:
            case 'element':
                xml_parent = self._construct_on_element(schema_element, xml_parent)
            case 'complexType':
                if schema_element.get('name') is not None and len(schema_element) > 1:
                    xml_parent = self._construct_on_element(schema_element, xml_parent)
            case 'extension':
                self._construct_on_extension(schema_element, xml_parent)
            case _:
                pass

        for schema_child in schema_element:
            self.construct_xml_from_element(schema_child, xml_parent)
    
    def _construct_on_element(self, schema_element, xml_parent):
        """
        Element node is the main one we're looking at, since it describes the tag that need to be in the xml.
        With each element node found, I am adding a tag new to the xml, keeping the child-parent structure
        :param schema_element: The element tree node in the schema that defines the xml tag
        :param xml_parent: The xml tag that should be a parent of the tag constructed here from schema element
        :return: The xml tree node that was just created, should be a parent to following elements
        """
        if xml_parent is None:
            xml_parent = self._xml_root  # xml_parent should only be None at the top of the tree
            xml_parent.text = str(self._tag_text_map.get(schema_element.get('name'), 'No user input'))
        else:
            xml_child = etree.SubElement(xml_parent, schema_element.get('name'))
            xml_child.text = str(self._tag_text_map.get(schema_element.get('name'), 'No user input'))
            xml_parent = xml_child
        
        return xml_parent
    
    def _construct_on_extension(self, schema_element, xml_parent):
        """
        Taking advantage of schema walker functionality to get the base element from remote namespace
        :param schema_element: The extension tree node in the schema that has the name of the element to be looked up
        :param xml_parent: The tree node of xml that is being constructed, that this element will be child of
        :return: None
        """

        base_element = self._schema_walker.load_base_element(schema_element)
        self.construct_xml_from_element(base_element, xml_parent)


if __name__ == '__main__':
    sw = SchemaWalker()
    xmlb = XMLBuilder(schema_walker=sw)
    xmlb.construct_xml_from_element()

    with open('XML_from_shema.xml', 'w') as new_xml:
        string_xml = etree.tostring(xmlb.get_root(), pretty_print=True, xml_declaration=True).decode('ASCII')
        new_xml.write(string_xml)
