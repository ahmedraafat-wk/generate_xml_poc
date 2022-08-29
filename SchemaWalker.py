import requests as req
from lxml import etree


def get_tag_suffix(element):
    return element.tag.split('}')[1]


def find_by_name(import_root, base_name):
    for child_elem in import_root:
        if child_elem.get('name') == base_name:
            return child_elem

    return None


class SchemaWalker:

    @staticmethod
    def _initiate_row(element):
        return [
            element.get('name', 'Placeholder Name'),
            element.get('type', 'No type specified')
        ]

    def __init__(self, schema_path='FunduszInwestycyjny_v1-6.xsd', verbose=True):
        
        with open(schema_path) as file:
            self._schema_doc = etree.parse(file)

        self._schema = self._schema_doc.getroot()  # Returns schema element with namespace imports and root at the end
        self._root_element = self._schema.getchildren()[-1]  # Get actual root element
        self._tag_prefix = '{' + self._schema.nsmap.get('xsd') + '}'  # All tags are prefixed with this xsd namespace
        self._result = []
        self._verbose = verbose

    def _process_tree_element(self, element):
        """
        Each element is processed differently and can be nested under each other element.
        Choosing to go with recursive approach and switch on element type.
        """
        tag_suffix = get_tag_suffix(element)

        if tag_suffix == 'element':
            self._process_element_tag(element)
        elif tag_suffix == 'complexType':
            self._process_complex_type_tag(element)
        elif tag_suffix == 'complexContent':
            self._process_complex_content_tag(element)
        elif tag_suffix == 'sequence':
            for sequence_child in element.iterchildren():
                self._process_tree_element(sequence_child)
        else:
            pass

    def _process_element_tag(self, element):
        """
        Element tags are the ones we're most interested in. They define the tags that need to be in the xml in question.
        Usually have 1 annotation + doccumentation child tag with additional info.
        Might have other children tags
        """
        row = self._initiate_row(element)
        if len(list(element)) < 1:
            row.extend(['No documentation'])
            self._result.append(row)
        else:
            for child in element.iterchildren():
                if get_tag_suffix(child) == 'annotation':
                    docstring = child[0].text
                    row.append(docstring)
                    self._result.append(row)
                else:
                    self._process_tree_element(child)
    
    def _process_complex_type_tag(self, element):
        """
        ComplexType tag usually just has 1 child, the sequence tag.
        """
        elem_children = list(element)
        if len(elem_children) > 1:
            # If the complexType tag has multiple children and not just the sequence, it must have an annotation & a
            # sequence tags. Therefore, treat it as an element tag
            self._process_element_tag(element)
        else:
            child_tag = elem_children[0]
            self._process_tree_element(child_tag)

    def _process_complex_content_tag(self, element):
        """
        Complex content tag appears once, has an extension tag and a sequence tag as children. Need to make network
        requests to process the extension
        """
        extension_tag = element[0]
        self._process_extension_tag(extension_tag)
        sequence_tag = extension_tag[0]
        self._process_tree_element(sequence_tag)
    
    def _process_extension_tag(self, element):
        """
        To process this tag we need to pull the element that is being extended from a different namespace.
        The root element has import tags that give web addresses for where to pull the namespace from.
        The namespace is a similar xml document with a bunch of elements besides what we actually need.
        """

        base_element = self.load_base_element(element)
        self._process_tree_element(base_element)

    def parse_tree(self):
        """
        Kick off the recursive tree walker function on root element
        :return: The matrix intended to be passed to spreadsheets API for the client to fill in data
        """
        self._process_tree_element(self._root_element)
        if self._verbose:
            # for row in self._result:
            #     print(row)
            print(self._result)

        return self._result

    def load_base_element(self, element):
        """
        Get the base element of the extension tag from the remote namespace
        :param element: Extension element of the schema
        :return: Base element of the extension argument element
        """
        base_tag = element.get('base')
        if base_tag is None:
            raise ValueError('Extension element does not have *base* attribute')

        needed_namespace_prefix, base_name = base_tag.split(':')
        needed_namespace = self._root_element.nsmap.get(needed_namespace_prefix)
        if needed_namespace is None:
            raise ValueError('Needed namespace prefix not in namespace map')

        import_tag = None
        for child in self._schema:
            if (child.tag == self._tag_prefix + 'import') and (child.get('namespace') == needed_namespace):
                import_tag = child
        if import_tag is None:
            raise ValueError('Import tag with needed namespace was not found')

        import_namespace_url = import_tag.get('schemaLocation')
        if import_namespace_url is None:
            raise ValueError('Import tag does not have *schemaLocation* attribute')

        schema_response = req.get(import_namespace_url)
        if not schema_response.ok:
            raise RuntimeError('Request for imported namespace did not go through')
        import_root = etree.fromstring(schema_response.content)
        base_element = find_by_name(import_root, base_name)
        if base_element is None:
            raise ValueError('Base element was not found in the imported namespace xml')

        return base_element

    def get_root_name(self):
        return self._root_element.get('name')

    def get_root(self):
        return self._root_element

    def get_schema(self):
        return self._schema

    def get_tag_prefix(self):
        return self._tag_prefix


if __name__ == '__main__':
    schema_walker = SchemaWalker()
    output_list = schema_walker.parse_tree()
