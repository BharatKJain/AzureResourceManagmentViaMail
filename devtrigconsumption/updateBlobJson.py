# import default modules
import logging
import os
import json

# importing thrid-party modules
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

# importing local modules
from .fetchBillingPeriod import getBillingPeriod
"""
# logging setup
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w',
                    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
"""
# Importing credentials
try:
    with open(os.path.join(os.path.dirname(__file__), 'creds.json')) as file:
        credentials = json.load(file)
except Exception as err:
    logging.error(err)


def updateBillingPeriod(subBlobCheck, accessToken, subscriptionsList):
    try:
        for subscription in subscriptionsList:
            billingData = json.loads(getBillingPeriod(subscriptionsList.get(subscription), accessToken).text).get(
                "value")[0].get("properties")
            if f"subscriptionStartDate/{subscriptionsList.get(subscription)}" in subBlobCheck:
                if subBlobCheck[f"subscriptionStartDate/{subscriptionsList.get(subscription)}"] != f"{billingData.get('billingPeriodStartDate')}":
                    subBlobCheck[subscriptionsList.get(subscription)] = 0
                    subBlobCheck[f"subscriptionStartDate/{subscriptionsList.get(subscription)}"] = f"{billingData.get('billingPeriodStartDate')}"

            else:
                subBlobCheck[f"subscriptionStartDate/{subscriptionsList.get(subscription)}"] = f"{billingData.get('billingPeriodStartDate')}"
                subBlobCheck[f"{subscriptionsList.get(subscription)}"] = 0
        # print(subBlobCheck)
        # blob_client_read.upload_blob(json.dumps(subBlobCheck), overwrite=True)
        logging.info("Updated the subs.json")
        return subBlobCheck
    except Exception as err:
        logging.error(
            f"ERROR:updateBlobJson.py check function updateBillingPeriod() for details::{err}")


if __name__ == "__main__":
    update()
