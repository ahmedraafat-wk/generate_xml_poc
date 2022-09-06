#!/usr/local/bin/python3
import os
from pprint import pprint

from dotenv import load_dotenv
from lxml import etree

from ApiAuth import ApiAuth
from SpreadsheetsApi import SpreadsheetsApi
from SchemaWalker import SchemaWalker
from XMLBuilder import XMLBuilder

# Load the environment variables
load_dotenv()

API_URL = os.getenv('API_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_ID = os.getenv('SHEET_ID')


def get_schema_values(schema_walker):
    return schema_walker.parse_tree()


def create_spreadsheet_with_schema_values(spreadsheets_api, schema_walker):
    spreadsheet_id = spreadsheets_api.create_spreadsheet('Test From Local 9')
    sheet_id = spreadsheets_api.create_sheet(spreadsheet_id, 'Schema Sheet')
    spreadsheets_api.update_range(spreadsheet_id, sheet_id, ':',
                                  {"values": get_schema_values(schema_walker)})
    write_spreadsheet_ids_to_env(spreadsheet_id, sheet_id)


def write_spreadsheet_ids_to_env(spreadsheet_id, sheet_id):
    with open('.env', 'a') as env_file:
        env_file.writelines([
            '\nSPREADSHEET_ID = "' + spreadsheet_id+'"',
            '\nSHEET_ID = "' + sheet_id+'"'
        ])


def generate_xml(spreadsheets_api, schema_walker):
    sheet_data = spreadsheets_api.get_sheet_data(SPREADSHEET_ID, SHEET_ID, ':')
    xmlb = XMLBuilder(schema_walker, sheet_data)
    xmlb.construct_xml_from_element()

    with open('XML_from_schema.xml', 'w') as new_xml:
        string_xml = etree.tostring(
            xmlb.get_root(), pretty_print=True, xml_declaration=True).decode('ASCII')
        new_xml.write(string_xml)


if __name__ == "__main__":
    api_auth = ApiAuth(API_URL)
    access_token = api_auth.authenticate(CLIENT_ID, CLIENT_SECRET)
    spreadsheets_api = SpreadsheetsApi(API_URL, access_token)
    schema_walker = SchemaWalker(verbose=False)

    if SPREADSHEET_ID == None and SHEET_ID == None:
        create_spreadsheet_with_schema_values(spreadsheets_api, schema_walker)
    else:
        generate_xml(spreadsheets_api, schema_walker)
