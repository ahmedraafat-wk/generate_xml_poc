#!/usr/local/bin/python3
import os
from pprint import pprint

from dotenv import load_dotenv

from ApiAuth import ApiAuth
from SpreadsheetsApi import SpreadsheetsApi

# Load the environment variables
load_dotenv()

API_URL = os.getenv('API_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_ID = os.getenv('SHEET_ID')


def get_sheet_values():
    return [
        [
            "FunduszInwestycyjny",
            "No type specified",
            "Struktura sprawozdania funduszu inwestycyjnego",
        ],
        ["Naglowek", "fi:TNaglowekSprawozdaniaFinansowegoFunduszInwestycyjny", "Nagłówek"],
        [
            "WprowadzenieDoSprawozdaniaFinansowegoFI",
            "No type specified",
            "Wprowadzenie do sprawozdania finansowego",
        ],
        ["P_1", "No type specified", "Dane identyfikacyjne funduszu"],
        ["P_1A", "dtsf:TNazwaFirmy", "Nazwa funduszu"],
        ["P_1B", "etd:TTekstowy", "Typ funduszu"],
        ["P_1C", "etd:TTekstowy", "Numer w rejestrze funduszy"],
        ["P_1D", "etd:TNrNIP", "NIP"],
        ["P_1E", "dtsf:TDataSF", "Data utworzenia funduszu"],
        ["P_1F", "dtsf:TZakresDatOpcjonalnych",
            "Okres, na jaki fundusz został utworzony"],
        [
            "P_2",
            "No type specified",
            "Odnośnie do funduszy, o których mowa w art. 170 ustawy, w przypadku sprawozdania finansowego funduszu powiązanego wskazanie nazwy funduszu podstawowego, a w przypadku sprawozdania finansowego funduszu podstawowego wskazanie nazw wszystkich funduszy powiązanych",
        ],
        ["P_2A", "dtsf:TNazwaSiedziba", "Nazwy i siedziby funduszy powiązanych"],
        [
            "P_3",
            "etd:TTekstowy",
            "Zwięzły opis celu inwestycyjnego, specjalizacji i stosowanych ograniczeń inwestycyjnych funduszu",
        ],
        [
            "P_4",
            "No type specified",
            "Firma, siedziba i adres towarzystwa będącego organem funduszu, ze wskazaniem właściwego rejestru",
        ],
        ["P_4A", "dtsf:TNazwaSiedziba", "Firma"],
        ["P_4B", "dtsf:TAdresZOpcZagranicznym", "Adres"],
        ["P_4C", "etd:TTekstowy", "Rejstr właściwy dla towarzystwa"],
        ["P_5", "No type specified", "Okres sprawozdawczy"],
        [
            "TZakresDatSF",
            "No type specified",
            "Zakres dat od - do z uwzględnieniem ograniczeń dla elektronicznych sprawozdań finansowych",
        ],
        ["DataOd", "dtsf:TDataSF", "No documentation"],
        ["DataDo", "dtsf:TDataSF", "No documentation"],
        ["P_5A", "dtsf:TDataSF", "Dzień bilansowy"],
        [
            "P_6",
            "No type specified",
            "Wskazanie, czy sprawozdanie finansowe zostało sporządzone przy założeniu kontynuowania działalności przez fundusz w dającej się przewidzieć przyszłości oraz czy nie istnieją okoliczności wskazujące na zagrożenie kontynuowania działalności funduszu",
        ],
        [
            "P_6A",
            "xsd:boolean",
            "Wskazanie, czy sprawozdanie finansowe zostało sporządzone przy założeniu kontynuowania działalności przez fundusz w dającej się przewidzieć przyszłości",
        ],
        [
            "P_6B",
            "xsd:boolean",
            "Wskazanie, czy nie istnieją okoliczności wskazujące na zagrożenie kontynuowania działalności funduszu",
        ],
        ["P_6C", "etd:TTekstowy", "Opis okoliczności"],
        [
            "P_7",
            "No type specified",
            "W przypadku sprawozdania finansowego sporządzonego za okres, w ciągu którego nastąpiło połączenie funduszy, wskazanie, że jest to sprawozdanie finansowe sporządzone po połączeniu funduszy, oraz określenie nazw i numerów w rejestrach funduszy, które zostały połączone",
        ],
        [
            "P_7A",
            "xsd:boolean",
            "Wskazanie, że jest to sprawozdanie finansowe sporządzone po połączeniu funduszy",
        ],
        [
            "P_7B",
            "No type specified",
            "Określenie nazw i numerów w rejestrach funduszy, które zostały połączone",
        ],
        ["P_7B_1", "dtsf:TNazwaFirmy", "Nazwa"],
        ["P_7B_2", "etd:TTekstowy", "Numer w rejestrze"],
        [
            "P_8",
            "etd:TTekstowy",
            "Wskazanie podmiotu, który przeprowadził badanie (przegląd) sprawozdania finansowego",
        ],
        [
            "P_9",
            "etd:TTekstowy",
            "Wskazanie rynku, na którym notowane są certyfikaty inwestycyjne",
        ],
        [
            "P_10",
            "No type specified",
            "Wskazanie serii certyfikatów inwestycyjnych i cech je różnicujących",
        ],
        ["P_10A", "etd:TTekstowy", "Seria"],
        ["P_10B", "etd:TTekstowy", "Cechy różnicujące"],
        ["P_11", "etd:TTekstowy", "Wskazanie emisji certyfikatów inwestycyjnych"],
        [
            "P_12",
            "No type specified",
            "Wskazanie kategorii jednostek uczestnictwa i cech je różnicujących",
        ],
        ["P_12A", "etd:TTekstowy", "Kategoria"],
        ["P_12B", "etd:TTekstowy", "Cechy różnicujące"],
        [
            "P_13",
            "No type specified",
            "Informacja uszczegóławiająca, wynikająca z potrzeb lub specyfiki jednostki",
        ],
        [
            "P_13A",
            "dtsf:TPozycjaUzytkownika",
            "Informacja uszczegóławiająca, wynikająca z potrzeb lub specyfiki jednostki",
        ],
        ["ZestawienieLokat", "No type specified", "Zestawienie lokat"],
        ["TabelaGlowna", "fi:TabelaGlowna", "Tabela główna"],
        ["TabeleUzupelniajace", "fi:TabeleUzupelniajace", "Tabela uzupełniająca"],
        ["TabeleDodatkowe", "fi:TabeleDodatkowe", "Tabela dodatkowa"],
        ["Bilans", "fi:BilansFI", "Bilans"],
        [
            "RachunekWynikuZOperacji",
            "fi:RachunekWynikuZOperacjiFI",
            "Rachunek wyniku z operacji",
        ],
        ["AktywaZmiany", "fi:AktywaZmianyFI", "Zestawienie zmian w aktywach netto"],
        ["Przeplywy", "fi:PrzeplywyFI", "Zestawienie przepływów pieniężnych"],
        ["NotyObjasniajaceFI", "No type specified", "Noty objasniające"],
        ["NotaObjasniajaca", "dtsf:TInformacjaDodatkowa", "Nota objasniająca"],
        ["InformacjaDodatkowaFI", "No type specified", "Informacja dodatkowa"],
        ["InformacjaDodatkowa", "dtsf:TInformacjaDodatkowa", "Informacja dodatkowa"],
    ]


def create_spreadsheet_with_schema_values(spreadshets_api):
    spreadsheet_id = spreadshets_api.create_spreadsheet('Test From Local 2')
    sheet_id = spreadshets_api.create_sheet(spreadsheet_id, 'Schema Sheet')
    spreadshets_api.update_range(spreadsheet_id, sheet_id, ':',
                                 {"values": get_sheet_values()})


def read_spreadsheet_data(spreadshets_api):
    sheet_values = spreadshets_api.get_sheet_data(
        SPREADSHEET_ID, SHEET_ID, ':')
    pprint(sheet_values)


if __name__ == "__main__":
    api_auth = ApiAuth(API_URL)
    acess_token = api_auth.authenticate(CLIENT_ID, CLIENT_SECRET)
    spreadshets_api = SpreadsheetsApi(API_URL, acess_token)

    '''
    Until now I don't think it will be possible to run the two calls (create & read) at the same script.
    So, creating spreadsheet with schema keys must be done first then whenever the user finished filling the data, the user should run now the code 
    with the spreadsheet & sheet IDs to be used to read the data from.
    '''
    if SPREADSHEET_ID == None and SHEET_ID == None:
        create_spreadsheet_with_schema_values(spreadshets_api)
    else:
        read_spreadsheet_data(spreadshets_api)
