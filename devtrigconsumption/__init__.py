"""
    This is main file for code.
"""
# Importing libraries
# import datetime
import logging
import json
import requests
import smtplib
import ssl
import os
from datetime import datetime
from tabulate import tabulate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Imporitng thirdpary libraries
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import azure.functions as func
# Importing local modules
from .fetchToken import getToken
from .fetchSubscriptions import getSubscriptions
from .fetchUsageDetails import getUsageDetails
from .fetchData import getData
from .fetchBillingPeriod import getBillingPeriod
from .sendMail import sendMail
from .fetchActivityLogs import getActivityLogs
from .updateBlobJson import updateBillingPeriod

logging.basicConfig(format='%(asctime)s|%(filename)s|%(funcName)s|%(lineno)s: %(message)s',
                    level=logging.INFO)

# Importing credentials
try:
    with open(os.path.join(os.path.dirname(__file__), 'creds.json')) as file:
        credentials = json.load(file)
except Exception as err:
    logging.error(err)

# Connection to Blob
try:
    connect_str = f'DefaultEndpointsProtocol=https;AccountName={credentials.get("storageAccountName")};AccountKey={credentials.get("storageAccountKey")};EndpointSuffix=core.windows.net'
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    blob_client_read = blob_service_client.get_blob_client(
        container="new", blob=("subs.json"))
    logging.info("Blob : Client read successful")
    subfile = blob_client_read.download_blob().content_as_text(encoding='UTF-8')
    logging.info("BlobData : +"+str(subfile))
    subBlobCheck = json.loads(subfile)
except Exception as err:
    logging.error(err)


def checkDate(string):
    return datetime(int(string[0:4]), int(string[5:7]), int(string[8:10]))


def filterActivityLogs(subscriptionID, instanceID, startDate, endDate, accessToken):
    """
        This function gets creator name of given instance, by filtering through the Activity Logs
    """
    callerName = "Null"
    res = getActivityLogs(subscriptionID, instanceID,
                          startDate, endDate, accessToken)
    # Fetching data from activity logs API
    if res.text != None:
        data = json.loads(res.text)
    else:
        logging.error("ERROR:filterAcitivityLogs::No text in response")
    # Iterating through pages in API and finding the last page
    while "nextLink" in data:
        data = json.loads(getData(data.get("nextLink"), accessToken).text)
    # Checking for caller in last value of array
    try:
        if 'value' in data and len(data['value'])!=0:
            callerName = data['value'][-1]['caller']
        else:
            callerName="Not Found"
    except Exception as err:
        logging.error(f'ERROR:filterActivityLogs() callerName::{err}')
        # print(data)

    return callerName


def resourceData(subscription, startDate, endDate, accessToken):
    """
        This function processes all the data from Usage Details API and
        Returns data in the following format "instanceID": [instanceID, preTaxCost,currency,resourceGroup,resourceManager,offerID]
    """
    # Defining loacl variables
    flagForUsageDetails = 0
    usageRawData = {}
    uniqueResourcesDetails = {}

    # Fetch Usage Details
    while(("nextLink" in usageRawData) or (flagForUsageDetails != 1)):
        if flagForUsageDetails != 1:
            url = f'https://management.azure.com/subscriptions/{subscription}/providers/Microsoft.Consumption/usageDetails?api-version=2019-01-01'
            flagForUsageDetails = 1
        else:
            url = usageRawData.get("nextLink")
            usageRawData = {}
            logging.info(
                f"Executing the nextLink in Usage Details API for subscription : {subscription}")
        try:
            usageRawData = json.loads(getData(url, accessToken).text)
        except Exception as err:
            logging.error(err)
        for resource in usageRawData.get("value"):
            # print(resource.get('properties').get('usageStart')[:10])
            if checkDate(resource.get('properties').get('usageStart')[:10]) >= checkDate(startDate):
                if resource.get('properties').get('instanceId') in uniqueResourcesDetails:
                    # updating cost
                    uniqueResourcesDetails.get(resource.get('properties').get('instanceId'))[
                        1] += resource.get('properties').get("pretaxCost")
                else:
                    # Appending resources list
                    uniqueResourcesDetails[resource.get('properties').get('instanceId')] = [resource.get('properties').get('instanceId'), resource.get('properties').get("pretaxCost"), resource.get('properties').get('currency'), resource.get('properties').get('instanceId').split(
                        '/')[4], resource.get('tags'), filterActivityLogs(subscription, resource.get('properties').get('instanceId'), startDate, endDate, accessToken), resource.get('properties').get('offerId')]

    return uniqueResourcesDetails

# def main(mytimer: func.TimerRequest) -> None:


# def main():
def main(mytimer: func.TimerRequest) -> None:
    # utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    # logging.info('Python timer trigger function ran at %s', utc_timestamp)

    # Declaring Variables
    global subBlobCheck
    subscriptionsList = {}

    # Fetching bearer token
    try:
        accessToken = json.loads(getToken(credentials.get("clientID"), credentials.get(
            "clientSecret"), credentials.get("tenantID")).text).get("access_token")
    except Exception as err:
        logging.error(err)
    # print(accessToken)
    # Fetching all subscription
    try:
        subscriptionsData = json.loads(
            getSubscriptions(accessToken).text).get("value")
    except Exception as err:
        logging.error(err)
    for subName in subscriptionsData:
        subscriptionsList.update(
            {subName.get("displayName"): subName.get("subscriptionId")})
    # print(subscriptionsData)
    # Update the subs.json in Blob to current billin period
    try:
        subBlobCheck = updateBillingPeriod(
            subBlobCheck, accessToken, subscriptionsList)
        logging.info(
            "INFO:Updated the subBlobCheck using updateBillingPeriod()")
    except Exception as err:
        logging.error(f"ERROR:updateBillingPeriod() call::{err}")
    # print(subBlobCheck)
    # Formatting data and sending mail
    for subscription in subscriptionsList:
        logging.info(f'subscription: {subscription}')
        logging.info(subscriptionsList[subscription])
        # Fetching current billing period
        billingData = json.loads(getBillingPeriod(subscriptionsList.get(subscription), accessToken).text).get(
            "value")[0].get("properties")
        # Fetching subscription data
        Data = resourceData(subscriptionsList.get(subscription), billingData.get(
            'billingPeriodStartDate'), billingData.get('billingPeriodEndDate'), accessToken)
        # Calculating toal cost
        totalCost = sum([value[1] for key, value in Data.items()])
        logging.info(totalCost)
        # Check if the total cost is >8000 and <8500 and not present in blob
        if ((totalCost > credentials['lowerLimit']) and ((subscriptionsList[subscription] not in subBlobCheck) or (subBlobCheck[subscriptionsList[subscription]] != 1))):
            logging.info("Inside If condition")
            # The string that is responsible for converting the data to html
            topResourcesArray = [[key, value[1], value[3], value[4], value[5], value[6]]
                                 for key, value in Data.items()]
            topResourcesArray.sort(key=lambda x: x[1], reverse=True)
            topResourcesTable = tabulate(topResourcesArray[0:5], headers=[
                "Resource Instance ID", "Cost of Resource", "Resource Group", "Tags", "Resource Managers", "Offer ID"], tablefmt="html")
            dictResourceGroup = {}
            for k, v in Data.items():
                if v[3] in dictResourceGroup:
                    dictResourceGroup[v[3]][0] += v[1]
                else:
                    dictResourceGroup[v[3]] = [v[1], v[2]]
            resourceGroupArray = [[k, v[0], v[1]]
                                  for k, v in dictResourceGroup.items()]
            resourceGroupTable = tabulate(resourceGroupArray, headers=[
                "Resource Group", "Credit Consumption", "Currency Type"], tablefmt="html")
            text = str(
                f"This message is sent from Subscription Credit Checking API <br>There's been {totalCost} credit usage of SubscriptionID:{subscriptionsList.get(subscription)} and Subscription Name: {subscription} <br>Billing Period Details :<br>Starting Date{billingData.get('billingPeriodStartDate')}<br>Ending date:{billingData.get('billingPeriodEndDate')}<br> Top 5 Resources with respect to consumption:<br><br>{topResourcesTable}<br>Resource group based data:<br><br>{resourceGroupTable}<br> Please act accordingly")

            text = text.replace("<table>", "<table border='1' >")
            # Message composition
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(text, 'html'))
            message['Subject'] = "{}".format(
                ' Urgent-Subscription Limit Exceeded')
            try:
                sendMail(credentials.get('senderID'), credentials.get(
                    'password'), message, credentials.get('serverAddress'), credentials.get('port'))
            except Exception as err:
                logging.error(err)
            try:
                if subscriptionsList[subscription] not in subBlobCheck or subBlobCheck[subscriptionsList[subscription]] != 1:
                    subBlobCheck[subscriptionsList[subscription]] = 1
                    blob_client_read.upload_blob(
                        json.dumps(subBlobCheck), overwrite=True)
                    logging.info("Blob Update")
            except Exception as err:
                logging.error(err)
        else:
            logging.info("Does Not Satisfy Condition")


# if __name__ == "__main__":
#     main()
