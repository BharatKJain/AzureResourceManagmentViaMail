import requests
import logging


def getData(url, bearerToken):
    """
        This modules fetchs data from any Azure REST API
    """
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
                f'Successfully fetched data')
    except Exception as err:
        logging.error(err)

    return response
