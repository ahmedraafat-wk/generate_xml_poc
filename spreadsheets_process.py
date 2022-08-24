#!/usr/local/bin/python3
import requests
import json
import os
from dotenv import load_dotenv
from pprint import pp, pprint


# Load the environment variables
load_dotenv()

# AUTH_URL = os.getenv('AUTH_URL')
# SS_API_URL = os.getenv('SS_API_URL')
API_URL = os.getenv('API_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_ID = os.getenv('SHEET_ID')


class PlatformAPI:
    def __init__(self, url: str):
        self._url = url
        self._access_token = None

    def _get_headers(self):
        '''
        Returns the headers including the Authorization token
        {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            "Authorization":  "Bearer {token}"}
        '''

        if self._access_token:
            return {'Content-Type': 'application/json', 'Accept': 'application/json', "Authorization":  "Bearer " + self._access_token}
        raise ValueError(
            'Access token is not set. Must authenticate() first.')

    def _get(self, path):
        '''
        A helper function to retrieve all the data from the passed URL
        
        :param path: The path to retrieve all the data from
        
        :returns resp: The response object
        '''

        url = self._url + path
        resp = requests.get(url, headers=self._get_headers())
        return resp.json()

    def _post(self, path, data=None, body=None, headers=None):
        '''
        A helper function to do the POST request, then return the json encoded response
        
        :param path: The path to use for the post request
        :param data: (optional) list of tuples that will be added to the request body
        :param body: (optional) json list to be added to the request body
        :param headers: the request headers
        
        :returns resp: The response object
        '''

        url = self._url + path
        resp = requests.post(url, data=data, headers=headers, json=body)
        return resp.json()

    def _put(self, path, data):
        '''
        A helper function to do the PUT request, then return the request status code
        
        :param path: The path to use for the update request
        :param data: (optional) list of tuples that will be added to the request body
        
        :rerurns resp.status_code: the request response status code.
        '''

        url = self._url + path
        resp = requests.put(url, data=json.dumps(data),
                            headers=self._get_headers())
        return resp.status_code

    def authenticate(self, client_id: str, client_secret: str):
        '''
        This function authenticate the user by the client id & secret with the Workiva platform API
        
        :param client_id: a string value that represent the client ID
        :param client_secret: a string value that represent the client secret
        
        :return assign the retrieved auth token to the class access_token var.
        '''

        data = 'client_id=' + client_id + '&client_secret=' + \
            client_secret + '&grant_type=client_credentials'
        self._access_token = self._post(
            '/iam/v1/oauth2/token', data, {}, {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'})['access_token']

    def get_sheet_data(self, spreadsheet_id: str, sheet_id: str):
        '''
        A function that returns all the data for the given sheet
        
        :param spreadsheet_id: the spreadsheet ID to use in the API
        :param sheet_id: the sheet ID that we want to retrieve all the data from.
        
        "return data: A list for the retrieved data
        '''

        path = '/platform/v1/spreadsheets/' + \
            spreadsheet_id + '/sheets/' + sheet_id + '/sheetdata'
        data = self._get(path)
        return data

    def update_range(self, spreadsheet_id, sheet_id, region, values):
        '''
        This function will update a specific sheet range with the values
        
        :param spreadsheet_id: the spreadsheet ID to use in the API
        :param sheet_id: the sheet ID that we want to update
        :param region: a string value that represent the region we want to modify, i,e. A1
        :param values: A list of list for each row value. i.e. [['Row1-Col1 Data', 'Row1-Col2 Data], ['Row2-Col1 Data', 'Row2-Col2 Data]]
        
        :return just prints the status_code of the request
        '''

        path = '/spreadsheets/v1/spreadsheets/' + spreadsheet_id + \
            '/sheets/' + sheet_id + '/data/' + region
        res = self._put(path, data=values)
        pprint(res)

    def create_spreadsheet(self, spreadsheet_name):
        '''
        This function will create a new spreadsheet
        
        :param spreadsheet_name: a string value that represent the spreadsheet name
        
        :return spreadsheet_id: a string value of the created spreadsheet ID
        '''

        path = '/spreadsheets/v1/spreadsheets'
        spreadsheet_id = self._post(path, {}, {'name': spreadsheet_name}, self._get_headers())[
            'data']['id']
        return spreadsheet_id

    def create_sheet(self, spreadsheet_id, name):
        '''
        This function will create a new sheet in the assigned spreadsheet
        
        :param spreadsheet_id: the spreadsheet ID we want to add new sheet for
        :param name: a string value that represent the sheet name
        
        :return sheet_id: a string value of the created sheet ID
        '''

        path = '/spreadsheets/v1/spreadsheets/' + spreadsheet_id + '/sheets'
        body = {
            'index': 0,
            'name': name,
            'parent_id': ""
        }
        sheet_id = self._post(path, {}, body, self._get_headers())[
            'data']['id']
        return sheet_id


def get_sheet_values():
    return [
        [
            "FunduszInwestycyjny",
            "No type specified",
            "Struktura sprawozdania funduszu inwestycyjnego",
        ],
        ["NotyObjasniajaceFI", "No type specified", "Noty objasniaj\xc4\x85ce"],
        [
            "NotaObjasniajaca",
            "dtsf:TInformacjaDodatkowa",
            "Nota objasniaj\xc4\x85ca",
        ],
        ["InformacjaDodatkowaFI", "No type specified", "Informacja dodatkowa"],
        [
            "InformacjaDodatkowa",
            "dtsf:TInformacjaDodatkowa",
            "Informacja dodatkowa",
        ]
    ]


def main():
    api = PlatformAPI(API_URL)
    api.authenticate(CLIENT_ID, CLIENT_SECRET)
    spreadsheet_id = api.create_spreadsheet('Test From Local 5')
    sheet_id = api.create_sheet(spreadsheet_id, 'Schema Sheet')
    api.update_range(spreadsheet_id, sheet_id, ':',
                     {"values": get_sheet_values()})


if __name__ == "__main__":
    main()
