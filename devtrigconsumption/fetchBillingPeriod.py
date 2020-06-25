import requests
import logging


def getBillingPeriod(subscriptionID, bearerToken):
    """
        This modules fetchs billing period of a given Subscription.
    """
    url = f'https://management.azure.com/subscriptions/{subscriptionID}/providers/Microsoft.Billing/billingPeriods?api-version=2017-04-24-preview'
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
