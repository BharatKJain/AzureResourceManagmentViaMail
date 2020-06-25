# Importing Modules
import requests
import json
import os
import logging

def getSubscriptions(bearerToken):
    """
        This modules fetchs all subscriptions from given Tenant.
    """
    url = "https://management.azure.com/subscriptions?api-version=2020-01-01"
    payload = {}
    headers = {
        'Authorization': f'Bearer {bearerToken}'
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code != 200:
            logging.error(f'Response Code: {response.status_code}')
        else:
            logging.info(
                f'Successfully fetched all Subscriptions')
    except Exception as err:
        logging.error(err)

    return response
