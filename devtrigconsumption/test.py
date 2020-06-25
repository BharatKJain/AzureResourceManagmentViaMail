# Importing libraries
import datetime
import logging
import json
import requests
import smtplib
import ssl
import os
from tabulate import tabulate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Imporitng thirdpary libraries
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import azure.functions as func
# Importing local modules
from fetchToken import getToken
from fetchSubscriptions import getSubscriptions
from fetchUsageDetails import getUsageDetails
from fetchData import getData
from fetchBillingPeriod import getBillingPeriod
from sendMail import sendMail
from fetchActivityLogs import getActivityLogs

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
except Exception as err:
    logging.error(err)


def filterActivityLogs(subscriptionID, instanceID, startDate, endDate, accessToken):
    """
        This function gets creator name of given instance
    """
    callerName = "Null"
    # Fetching data from activity logs API
    data = json.loads(getActivityLogs(
        subscriptionID, instanceID, startDate, endDate, accessToken).text)
    # Iterating through pages in API and finding the last page
    while "nextLink" in data:
        data = json.loads(getData(data.get("nextLink"), accessToken).text)
    # Checking for caller in last value of array
    try:
        callerName = data['value'][-1]['caller']
    except Exception as err:
        logging.error(err)

    return callerName


def resourceData(subscription, startDate, endDate, accessToken):
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
            if resource.get('properties').get('instanceId') in uniqueResourcesDetails:
                # updating cost
                uniqueResourcesDetails.get(resource.get('properties').get('instanceId'))[
                    1] += resource.get('properties').get("pretaxCost")
            else:
                # Appending resources list
                data = {resource.get('properties').get('instanceId'): [resource.get('properties').get('instanceId'), resource.get(
                    'properties').get('pretaxCost'), resource.get('properties').get('currency'), resource.get('properties').get('instanceId').split('/')[4], resource.get('tags'), filterActivityLogs(subscription, resource.get('properties').get('instanceId'), startDate, endDate, accessToken)]}
                uniqueResourcesDetails.update(data)

    return uniqueResourcesDetails

# def main(mytimer: func.TimerRequest) -> None:


def main():
    # utc_timestamp = datetime.datetime.utcnow().replace(
    #    tzinfo=datetime.timezone.utc).isoformat()
    #
    # if mytimer.past_due:
    #    logging.info('The timer is past due!')
    #
    # logging.info('Python timer trigger function ran at %s', utc_timestamp)

    # Declaring Variables

    subscriptionsList = {}

    # Fetching bearer token
    try:
        accessToken = json.loads(getToken(credentials.get("clientID"), credentials.get(
            "clientSecret"), credentials.get("tenantID")).text).get("access_token")
    except Exception as err:
        logging.error(err)

    # Fetching all subscription
    try:
        subscriptionsData = json.loads(
            getSubscriptions(accessToken).text).get("value")
    except Exception as err:
        logging.error(err)
    for subName in subscriptionsData:
        subscriptionsList.update(
            {subName.get("displayName"): subName.get("subscriptionId")})

    # Formatting data and sending mail
    for subscription in subscriptionsList:
        # Fetching current billing period
        billingData = json.loads(getBillingPeriod(subscriptionsList.get(subscription), accessToken).text).get(
            "value")[0].get("properties")
        # Fetching subscription data
        Data = resourceData(subscriptionsList.get(subscription), billingData.get(
            'billingPeriodStartDate'), billingData.get('billingPeriodEndDate'), accessToken)

        # Calculating toal cost
        totalCost = sum([value[1] for key, value in Data.items()])

        # The string that is responsible for converting the data to html
        topResourcesArray = [[key, value[1], value[3], value[4], value[5]]
                             for key, value in Data.items()]
        topResourcesArray.sort(key=lambda x: x[1], reverse=True)
        topResourcesTable = tabulate(topResourcesArray[0:5], headers=[
            "Resource Instance ID", "Cost of Resource", "Resource Group", "Tags", "Resource Managers", "Resource Creator/User"], tablefmt="html")
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
        message['Subject'] = "{}".format(' Urgent-Subscription Limit Exceeded')
        try:
            sendMail(credentials.get('senderID'), credentials.get(
                'password'), message, credentials.get('serverAddress'), credentials.get('port'))
        except Exception as err:
            logging.error(err)


if __name__ == "__main__":
    main()
