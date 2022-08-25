#!/usr/local/bin/python3
import json
from pprint import pprint

import requests


class SpreadsheetsApi:
    def __init__(self, url, access_token):
        self._url = url
        self._access_token = access_token

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
        return json.loads(resp.text)

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

    def _process_sheet_data(self, sheet_values):
        '''
        This function process the retrieved sheet data and change it from json format into hashmap with key, value formats

        :param sheet_values: A python object of the sheet values

        :return sheet_values_map: A map with key value pairs for the sheet values (key is the 1st cell and last non empty cell in the key's row)
        '''

        sheet_values_map = {}
        for row in sheet_values['data']['values']:
            sheet_values_map[row[0]] = row[-1]
        return sheet_values_map

    def get_sheet_data(self, spreadsheet_id, sheet_id, region):
        '''
        This function rturns a map {key: value} where is the key is the first cell in the sheet,
          and the value the last non empty cell in the key row.

        :param spreadsheet_id: the spreadsheet ID to use in the API
        :param sheet_id: the sheet ID that we want to retrieve all the data from.
        :param region: a string value that represent the region we want to read it is data, i,e. A1

        "return data: A list for the retrieved data
        '''

        path = '/spreadsheets/v1/spreadsheets/' + \
            spreadsheet_id + '/sheets/' + sheet_id + '/data/' + region
        data = self._get(path)
        return self._process_sheet_data(data)

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
