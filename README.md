# Introduction

Subscription Credit Consumption API

1. Brief Introduction:

The intention to develop this API was to warn/alert the subscription owners, managers and others about a certain subscription’s credit consumption exceeding 8000 credits via mail, as well as to figure out which Resource Groups and Resources(as well as people associated to that resource) are responsible for substantial credit consumption.
This will allow people working in an organization to easily identify the sectors with heavy credit-consumption and block/alert the people associated with the same.

2. Azure REST APIs used:
   a. Usage Details API:
   i. Link: https://docs.microsoft.com/en-us/rest/api/consumption/usagedetails/list
   ii. Description: We have fetched information such as “preTaxCost”, Resource group by splitting the “id” i.e. Resource ID string etc.
   iii. NOTE: Paged API, so there will be a “nextLink”
   b. Activity Logs API:
   i. Link: https://docs.microsoft.com/en-us/rest/api/monitor/activitylogs/list
   ii. Description: We have filtered information such as “caller” which is the person associated with certain resource by using “Administrative” logs.
   iii. NOTE: Paged API, so there will be a “nextLink”
   c. Subscription List API:
   i. Link: https://docs.microsoft.com/en-us/rest/api/resources/subscriptions/list
   ii. Description: We have fetched the subscriptions under a service principle such that we can dynamically fetch data for required subscription as compared to a hard coded list of subscription names with their IDs.
   d. Bearer Token API(for other API authentication):
   i. URL for API: https://login.microsoftonline.com/{Tenant ID}/oauth2/token?client_id={client ID}&grant_type=client_credentials&resource=https://management.azure.com/&client_secret={client_secret}
   ii. Requires “client ID”, “tenant ID” and “client secret” as query parameters as well as body parameters.
   iii. Description: Use the “access_token” value as a bearer token for using above mentioned API.
   e. Billing Period API:
   i. Link: https://docs.microsoft.com/en-us/rest/api/billing/2017-04-24-preview/billingperiods/list
   ii. Description: To fetch the billing period i.e. start date and end date of a particular subscription
3. Flow Diagram:

4. Concept Explained:
   a. Azure Function App:
   i. With Python as the development language, the type of trigger is timer trigger i.e. set for 2 hrs, such that after triggering it will check all subscriptions for credits consumption.
   ii. The function app is set at consumption plan
   b. Azure Blob Storage:
   i. After once the subscriptions are check for credit consumption, we check whether the person is already informed about the information by using a JSON imported from Blob which contains the ‘key: value’ as ‘subscription:{1/0}’ such that if the value is 0 then the mail will be sent to the recipients.
   ii. The values can be updated manually for testing purposes.
   c. Code:
   i. Part-1: Gathering Information
5. By using the above mentioned API(s) we fetch the information in the following sequence:
   a. Fetch Bearer Token
   b. Fetch Subscriptions Under Service Principle
   c. Fetch Data For-Each Subscription Using Usage Details API And Activity Logs API
6. Now, we sum up all the logs from Usage Details API by using “preTaxCost” as key to get the current credit consumption of single Subscription, and while doing that we fetch the top-5 credit consuming resources.
7. To identify the person or people associated with a certain resource we have used activity logs in which we filter information by using “Caller” and “Administrative” key values. (Still under construction)
   ii. Part-2: Formatting Data and Sending Data:
8. By using MIME (Multipurpose Internet Mail Extensions) Multipart email, the HTML and plain-text are combined and they are handled by Python’s email.Mime module.
9. By using smtplib in python, we can setup a smtp server to connect with Office365 server and login via outlook credentials, with TLS protocol.

# Things to Improve

1.Fetch Activity logs only for top 5 resources
2.Sum total cost in resourceData loop, remove the external for loop
3.fetch resource group in the resourceData loop, remove the extrernal loop--> refer to old ver 1 code line number
4.Change the location of blob update of none or 0 counter records in the end all together...to reduce time consumed
5.Check again for loops and optimizations
