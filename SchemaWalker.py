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

        match tag_suffix:
            case 'element':
                self._process_element_tag(element)
            case 'complexType':
                self._process_complex_type_tag(element)
            case 'complexContent':
                self._process_complex_content_tag(element)
            case 'sequence':
                for sequence_child in element.iterchildren():
                    self._process_tree_element(sequence_child)
            case _:
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
    test_against = [['FunduszInwestycyjny', 'No type specified', 'Struktura sprawozdania funduszu inwestycyjnego'], ['Naglowek', 'fi:TNaglowekSprawozdaniaFinansowegoFunduszInwestycyjny', 'Nagłówek'], ['WprowadzenieDoSprawozdaniaFinansowegoFI', 'No type specified', 'Wprowadzenie do sprawozdania finansowego'], ['P_1', 'No type specified', 'Dane identyfikacyjne funduszu'], ['P_1A', 'dtsf:TNazwaFirmy', 'Nazwa funduszu'], ['P_1B', 'etd:TTekstowy', 'Typ funduszu'], ['P_1C', 'etd:TTekstowy', 'Numer w rejestrze funduszy'], ['P_1D', 'etd:TNrNIP', 'NIP'], ['P_1E', 'dtsf:TDataSF', 'Data utworzenia funduszu'], ['P_1F', 'dtsf:TZakresDatOpcjonalnych', 'Okres, na jaki fundusz został utworzony'], ['P_2', 'No type specified', 'Odnośnie do funduszy, o których mowa w art. 170 ustawy, w przypadku sprawozdania finansowego funduszu powiązanego wskazanie nazwy funduszu podstawowego, a w przypadku sprawozdania finansowego funduszu podstawowego wskazanie nazw wszystkich funduszy powiązanych'], ['P_2A', 'dtsf:TNazwaSiedziba', 'Nazwy i siedziby funduszy powiązanych'], ['P_3', 'etd:TTekstowy', 'Zwięzły opis celu inwestycyjnego, specjalizacji i stosowanych ograniczeń inwestycyjnych funduszu'], ['P_4', 'No type specified', 'Firma, siedziba i adres towarzystwa będącego organem funduszu, ze wskazaniem właściwego rejestru'], ['P_4A', 'dtsf:TNazwaSiedziba', 'Firma'], ['P_4B', 'dtsf:TAdresZOpcZagranicznym', 'Adres'], ['P_4C', 'etd:TTekstowy', 'Rejstr właściwy dla towarzystwa'], ['P_5', 'No type specified', 'Okres sprawozdawczy'], ['TZakresDatSF', 'No type specified', 'Zakres dat od - do z uwzględnieniem ograniczeń dla elektronicznych sprawozdań finansowych'], ['DataOd', 'dtsf:TDataSF', 'No documentation'], ['DataDo', 'dtsf:TDataSF', 'No documentation'], ['P_5A', 'dtsf:TDataSF', 'Dzień bilansowy'], ['P_6', 'No type specified', 'Wskazanie, czy sprawozdanie finansowe zostało sporządzone przy założeniu kontynuowania działalności przez fundusz w dającej się przewidzieć przyszłości oraz czy nie istnieją okoliczności wskazujące na zagrożenie kontynuowania działalności funduszu'], ['P_6A', 'xsd:boolean', 'Wskazanie, czy sprawozdanie finansowe zostało sporządzone przy założeniu kontynuowania działalności przez fundusz w dającej się przewidzieć przyszłości'], ['P_6B', 'xsd:boolean', 'Wskazanie, czy nie istnieją okoliczności wskazujące na zagrożenie kontynuowania działalności funduszu'], ['P_6C', 'etd:TTekstowy', 'Opis okoliczności'], ['P_7', 'No type specified', 'W przypadku sprawozdania finansowego sporządzonego za okres, w ciągu którego nastąpiło połączenie funduszy, wskazanie, że jest to sprawozdanie finansowe sporządzone po połączeniu funduszy, oraz określenie nazw i numerów w rejestrach funduszy, które zostały połączone'], ['P_7A', 'xsd:boolean', 'Wskazanie, że jest to sprawozdanie finansowe sporządzone po połączeniu funduszy'], ['P_7B', 'No type specified', 'Określenie nazw i numerów w rejestrach funduszy, które zostały połączone'], ['P_7B_1', 'dtsf:TNazwaFirmy', 'Nazwa'], ['P_7B_2', 'etd:TTekstowy', 'Numer w rejestrze'], ['P_8', 'etd:TTekstowy', 'Wskazanie podmiotu, który przeprowadził badanie (przegląd) sprawozdania finansowego'], ['P_9', 'etd:TTekstowy', 'Wskazanie rynku, na którym notowane są certyfikaty inwestycyjne'], ['P_10', 'No type specified', 'Wskazanie serii certyfikatów inwestycyjnych i cech je różnicujących'], ['P_10A', 'etd:TTekstowy', 'Seria'], ['P_10B', 'etd:TTekstowy', 'Cechy różnicujące'], ['P_11', 'etd:TTekstowy', 'Wskazanie emisji certyfikatów inwestycyjnych'], ['P_12', 'No type specified', 'Wskazanie kategorii jednostek uczestnictwa i cech je różnicujących'], ['P_12A', 'etd:TTekstowy', 'Kategoria'], ['P_12B', 'etd:TTekstowy', 'Cechy różnicujące'], ['P_13', 'No type specified', 'Informacja uszczegóławiająca, wynikająca z potrzeb lub specyfiki jednostki'], ['P_13A', 'dtsf:TPozycjaUzytkownika', 'Informacja uszczegóławiająca, wynikająca z potrzeb lub specyfiki jednostki'], ['ZestawienieLokat', 'No type specified', 'Zestawienie lokat'], ['TabelaGlowna', 'fi:TabelaGlowna', 'Tabela główna'], ['TabeleUzupelniajace', 'fi:TabeleUzupelniajace', 'Tabela uzupełniająca'], ['TabeleDodatkowe', 'fi:TabeleDodatkowe', 'Tabela dodatkowa'], ['Bilans', 'fi:BilansFI', 'Bilans'], ['RachunekWynikuZOperacji', 'fi:RachunekWynikuZOperacjiFI', 'Rachunek wyniku z operacji'], ['AktywaZmiany', 'fi:AktywaZmianyFI', 'Zestawienie zmian w aktywach netto'], ['Przeplywy', 'fi:PrzeplywyFI', 'Zestawienie przepływów pieniężnych'], ['NotyObjasniajaceFI', 'No type specified', 'Noty objasniające'], ['NotaObjasniajaca', 'dtsf:TInformacjaDodatkowa', 'Nota objasniająca'], ['InformacjaDodatkowaFI', 'No type specified', 'Informacja dodatkowa'], ['InformacjaDodatkowa', 'dtsf:TInformacjaDodatkowa', 'Informacja dodatkowa']]
    assert output_list == test_against
