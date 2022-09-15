from lxml import etree
import requests
import tempfile


class SchemaWalker:
    def __init__(self, schema_path= 'FunduszInwestycyjny_v1-6.xsd', verbose= False):
        with open(schema_path) as file:
            self._schema_doc = etree.parse(file)

        self._schema_root = self._schema_doc.getroot()  # Returns schema element with namespace imports and root at the end

        self._tag_prefix = '{' + self._schema_root.nsmap.get('xsd') + '}'  # All tags are prefixed with this xsd namespace
        self._result = SchemaParseOutput()
        self._imported_trees = {}
        self._verbose = verbose
        self._temporary_files = []
        self._base_types = {
            'xsd:token', 'xsd:string', 'xsd:decimal', 'xsd:int', 'xsd:nonNegativeInteger', 'xsd:date', 'xsd:dateTime',
            'xsd:gYear', 'xsd:byte'
        }

    def __del__(self):
        for file in self._temporary_files:
            file.close()
        # Garbage collect temporary xsd files

    @staticmethod
    def _get_tag_suffix(element):
        return element.tag.split('}')[1]

    @staticmethod
    def _find_import_tags(imported_tree_root):
        import_tags = []
        # import elements can only be found on the top-level. No need to dive into the tree
        for child_elem in imported_tree_root.iter('import'):
            if SchemaWalker._get_tag_suffix(child_elem) == 'import':
                import_tags.append(child_elem)

        return import_tags

    def parse_tree(self):
        """
        Kick off the recursive tree walker function on root element
        :return: The matrix intended to be passed to spreadsheets API for the client to fill in data
        """
        self._process_tree_element(self._schema_root)
        if self._verbose:
            print(self._result)

        return self._result.to_list()

    def _process_tree_element(self, element):
        """
        Each element is processed differently and can be nested under each other element.
        Choosing to go with recursive approach and switch on element type.
        """
        tag_suffix_to_function_map = {
            'element': self._process_element_tag,
            'annotation': self._process_annotation_tag,
            'documentation': self._process_documentation_tag,
            'complexType': self._process_complexType_tag,
            'sequence': self._process_sequence_tag,
            'complexContent': self._process_complexContent_tag,
            'extension': self._process_extension_tag,
            'import': self._process_import_tag,
            'simpleType': self._process_simple_type,
            'restriction': self._process_restriction,
        }
        tag_suffix = self._get_tag_suffix(element)

        elem_processing_function = tag_suffix_to_function_map.get(tag_suffix)
        if elem_processing_function is None:
            if self._verbose:
                print(f'No function in map for element {tag_suffix}')
        else:
            elem_processing_function(element)

        for child_elem in element:
            self._process_tree_element(child_elem)

    def _process_element_tag(self, element):
        element_type = element.get('type')
        if element_type is not None:
            element_type = self._extend_type(element_type)

        self._result.append(SchemaParseOutputRow(
            element.get('name'),
            element_type,
            min_occurs=element.get('minOccurs'),
            max_occurs=element.get('maxOccurs')
        ))

    def _process_annotation_tag(self, element):
        pass

    def _process_documentation_tag(self, element):
        parent_row = self._result.get_last_row()
        parent_row.set_documentation(element.text)

    def _process_complexType_tag(self, element):
        pass

    def _process_sequence_tag(self, element):
        parent_row = self._result.get_last_row()
        parent_row.set_is_sequence(True)

    def _process_complexContent_tag(self, element):
        pass

    def _process_extension_tag(self, element):
        base_tag_name = element.get('base')
        if base_tag_name in self._base_types:
            self._result.get_last_row().set_type(base_tag_name)
        else:
            base_element = self._search_imports(base_tag_name)
            self._process_tree_element(base_element)

    def _process_import_tag(self, element):
        remote_schema_url = element.get('schemaLocation')
        remote_schema_namespace = element.get('namespace')
        remote_schema_bytes = requests.get(remote_schema_url).content
        imported_tree_root = etree.fromstring(remote_schema_bytes)
        self._imported_trees[remote_schema_namespace] = imported_tree_root
        self._save_tree_in_file(imported_tree_root, element)

        nested_import_tags = self._find_import_tags(imported_tree_root)
        for import_tag in nested_import_tags:
            self._process_import_tag(import_tag)

    def _save_tree_in_file(self, imported_tree, element):
        file_save = tempfile.NamedTemporaryFile()
        file_save.write(etree.tostring(imported_tree))
        self._temporary_files.append(file_save)
        element.attrib['schemaLocation'] = file_save.name

    def _extend_type(self, base_tag_name):
        base_element = self._search_imports(base_tag_name)
        self._process_tree_element(base_element)

    def _search_imports(self, base_tag):
        namespace_shorthand, tag = base_tag.split(':')
        namespace = self._schema_root.nsmap.get(namespace_shorthand)
        imported_tree = self._imported_trees.get(namespace)
        if imported_tree is None:
            if self._verbose:
                print('Namespace is not in imported_tree keys. Cannot search imports')
        else:
            for element in imported_tree.iter():
                if element.get('name') == tag:
                    return element

    def _process_simple_type(self, element):
        pass

    def _process_restriction(self, element):
        pass


class SchemaParseOutput:
    def __init__(self):
        self._rows = []

    def to_list(self):
        headers = self._rows.get_headers()
        rows = [row.to_list() for row in self._rows]
        headers.extend(rows)

        return headers

    def append(self, out_row):
        self._rows.append(out_row)

    def get_last_row(self):
        if len(self._rows):
            return self._rows[-1]
        else:
            raise RuntimeError('Trying to get parent row with no rows set')


class SchemaParseOutputRow:
    def __init__(self, tag_name, tag_type, tag_docstring='', is_sequence=False,
                 parent_row=None, min_occurs=None, max_occurs=None):
        if tag_name is None:
            raise RuntimeError('Element tag with no name')
        self._tag_name = tag_name

        if tag_type is None:
            tag_type = 'No type specified'
        self._tag_type = tag_type

        self._tag_docstring = tag_docstring
        self._is_sequence = is_sequence
        self._parent_row = parent_row

        if min_occurs is None:
            min_occurs = 0
        self._min_occurs = min_occurs

        if max_occurs is None:
            max_occurs = 0
        elif max_occurs == 'unbounded':
            max_occurs = -1
        self._max_occurs = max_occurs

    def set_documentation(self, documentation_string):
        self._tag_docstring = documentation_string

    def set_is_sequence(self, is_sequence):
        self._is_sequence = is_sequence

    def set_type(self, tag_type):
        self._tag_type = tag_type

    def to_list(self):
        return [
            self._tag_name,
            self._tag_type,
            self._tag_docstring,
            self._is_sequence,
            self._parent_row,
            self._min_occurs,
            self._max_occurs,
        ]


if __name__ == '__main__':
    sw = SchemaWalker(
        schema_path='FunduszInwestycyjny_v1-6.xsd',
        verbose=True
    )
    result_list = sw.parse_tree()
    with open('schema_walker_result.csv') as res:
        for row in result_list:
            res.write(','.join(row))
