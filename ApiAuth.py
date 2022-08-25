#!/usr/local/bin/python3
import json

import requests


class ApiAuth:
    def __init__(self, url):
        self._url = url
        self._headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}

    def authenticate(self, client_id: str, client_secret: str):
        '''
        This function authenticate the user by the client id & secret with the Workiva platform API

        :param client_id: a string value that represent the client ID
        :param client_secret: a string value that represent the client secret

        :return assign the retrieved auth token to the class access_token var.
        '''

        data = 'client_id=' + client_id + '&client_secret=' + \
            client_secret + '&grant_type=client_credentials'

        response = requests.post(
            self._url + '/iam/v1/oauth2/token', data=data, headers=self._headers)
        token_data = json.loads(response.text)
        return token_data['access_token']
