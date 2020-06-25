import requests
import logging


def getActivityLogs(subscriptionID, instanceID, startDate, endDate, bearerToken):
    """
        This modules fetchs all subscriptions from given Tenant.
    """

    url = f"https://management.azure.com/subscriptions/{subscriptionID}/providers/microsoft.insights/eventtypes/management/values?api-version=2015-04-01&$filter=eventTimestamp ge '{startDate}T00:00:00Z' and eventTimestamp le '{endDate}T00:00:00Z' and resourceUri eq '{instanceID}'"
    payload = {}
    headers = {
        'Authorization': f'Bearer {bearerToken}'
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code != 200:
            logging.error(
                f'Response Code: {response.status_code}::Subscription{subscriptionID}')
        else:
            logging.info(
                f'Successfully fetched all Subscriptions Details')
    except Exception as err:
        logging.error(err)
    return response
