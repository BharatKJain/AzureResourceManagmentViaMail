# Importing modules
import requests
import logging
import json
import os


def getToken(clientID, clientSecret, tenantID):
    """
        This function fetchs bearer token from azure, using service principles to access REST APIs.
    """

    url = f'https://login.microsoftonline.com/{tenantID}/oauth2/token'
    payload = f'client_id={clientID}&grant_type=client_credentials&resource=https%3A//management.azure.com/&client_secret={clientSecret}'
    headers = {}
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code != 200:
            logging.error(f'Response Code: {response.status_code}')
        else:
            logging.info(
                f'Successfully fetched token for tenantID: {tenantID}')
    except Exception as err:
        logging.error(err)

    return response
