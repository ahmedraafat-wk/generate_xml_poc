from lxml import etree
import requests as req


class SchemaReader:
    def __init__(self, schema_path= 'FunduszInwestycyjny_v1-6.xsd', verbose= True):
        with open(schema_path) as schema_file:
            self._schema_doc = etree.parse(schema_file)

        self._schema = self._schema_doc.getroot()
        self._root = self._schema[-1]
        self._tag_prefix = '{' + self._schema.nsmap.get('xsd') + '}'
    
    def get_root_name(self):
        return self._root.get('name')
    
    def get_root_docstring(self):
        return self._root[0][0].text
    
    def get_root_children(self):
        return list(self._root)

    def get_root(self):
        return self._root

    def get_schema(self):
        return self._schema

    def get_tag_prefix(self):
        return self._tag_prefix


class XMLBuilder:

    def __init__(self):
        self._sr = SchemaReader()
        self._xml_root = etree.Element(self._sr.get_root_name())
        self._tag_text_map = {
            "AktywaZmiany": 49,
            "Bilans": 47,
            "DataDo": 21,
            "DataOd": 20,
            "FunduszInwestycyjny": 1,
            "InformacjaDodatkowa": 54,
            "InformacjaDodatkowaFI": 53,
            "Naglowek": 2,
            "NotaObjasniajaca": 52,
            "NotyObjasniajaceFI": 51,
            "P_1": 4,
            "P_10": 34,
            "P_10A": 35,
            "P_10B": 36,
            "P_11": 37,
            "P_12": 38,
            "P_12A": 39,
            "P_12B": 40,
            "P_13": 41,
            "P_13A": 42,
            "P_1A": 5,
            "P_1B": 6,
            "P_1C": 7,
            "P_1D": 8,
            "P_1E": 9,
            "P_1F": 10,
            "P_2": 11,
            "P_2A": 12,
            "P_3": 13,
            "P_4": 14,
            "P_4A": 15,
            "P_4B": 16,
            "P_4C": 17,
            "P_5": 18,
            "P_5A": 22,
            "P_6": 23,
            "P_6A": 24,
            "P_6B": 25,
            "P_6C": 26,
            "P_7": 27,
            "P_7A": 28,
            "P_7B": 29,
            "P_7B_1": 30,
            "P_7B_2": 31,
            "P_8": 32,
            "P_9": 33,
            "Przeplywy": 50,
            "RachunekWynikuZOperacji": 48,
            "TZakresDatSF": 19,
            "TabelaGlowna": 44,
            "TabeleDodatkowe": 46,
            "TabeleUzupelniajace": 45,
            "WprowadzenieDoSprawozdaniaFinansowegoFI": 3,
            "ZestawienieLokat": 43,
        }

    def get_root(self):
        return self._xml_root

    def construct_xml_from_element(self, schema_element = None, xml_parent= None):
        if schema_element is None:
            schema_element = self._sr.get_root()

        tag_suffix = schema_element.tag.split('}')[1]
        match tag_suffix:
            case 'element':
                xml_parent = self._construct_on_element(schema_element, xml_parent)
            case 'complexType':
                if schema_element.get('name') is not None and len(schema_element) > 1:
                    xml_parent = self._construct_on_element(schema_element, xml_parent)
            case 'complexContent':
                pass
            case 'sequence':
                pass
            case 'annotation':
                pass
            case 'extension':
                self._construct_on_extension(schema_element, xml_parent)
            case other:
                pass

        for schema_child in schema_element:
            self.construct_xml_from_element(schema_child, xml_parent)
    
    def _construct_on_element(self, schema_element, xml_parent):
        if xml_parent is None:
            xml_parent = self._xml_root
            xml_parent.text = str(self._tag_text_map.get(schema_element.get('name'), 'No user input'))
        else:
            xml_child = etree.SubElement(xml_parent, schema_element.get('name'))
            xml_child.text = str(self._tag_text_map.get(schema_element.get('name'), 'No user input'))
            xml_parent = xml_child
        
        return xml_parent
    
    def _construct_on_extension(self, schema_element, xml_parent):
        base_tag = schema_element.get('base')
        if base_tag is None:
            raise ValueError('Extension element does not have *base* attribute')

        needed_namespace_prefix, base_name = base_tag.split(':')
        needed_namespace = self._sr.get_root().nsmap.get(needed_namespace_prefix)
        if needed_namespace is None:
            raise ValueError('Needed namespace prefix not in namespace map')

        import_tag = None
        for child in self._sr.get_schema():
            if (child.tag == self._sr.get_tag_prefix() + 'import') and (child.get('namespace') == needed_namespace):
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
        
        base_element = self._find_by_name(import_root, base_name)
        if base_element is None:
            raise ValueError('Base element was not found in the imported namespace xml')
        
        self.construct_xml_from_element(base_element, xml_parent)
    
    def _find_by_name(slef, import_root, base_name):
        for child_elem in import_root:
            if child_elem.get('name') == base_name:
                return child_elem
        
        return None


xmlb = XMLBuilder()
xmlb.construct_xml_from_element()


with open('XML_from_shema.xml', 'w') as new_xml:
    new_xml.write(
        etree.tostring(xmlb.get_root(), pretty_print= True, xml_declaration= True).decode('ASCII')
        )