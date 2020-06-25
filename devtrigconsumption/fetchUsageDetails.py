import requests
import logging


def getUsageDetails(subscriptionID, bearerToken):
    """
        This modules fetchs all Usage data from given subscription ID.
    """
    url = f"https://management.azure.com/subscriptions/{subscriptionID}/providers/Microsoft.Consumption/usageDetails?api-version=2019-01-01"
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
                f'Successfully fetched all Usage Details')
    except Exception as err:
        logging.error(err)

    return response
