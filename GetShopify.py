import requests
import Properties
import logging
from datetime import datetime, timedelta

#Set logging level
logging.basicConfig(level=logging.ERROR, filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

#Get date range for past 24 hours
date = datetime.now() - timedelta(days=1)

#Sets URL and parameters for request
url = Properties.shopifyURL
params = dict(
    #created_at_min = date,
    fields='name,contact_email,buyer_accepts_marketing,note_attributes,billing_address'
)

#Get request from Shopify and creates orders list from json.
r = requests.get(url, params)
data = r.json()
orders = data['orders']


#Shopify response
logging.debug(r.status_code)
logging.debug(r.reason)
logging.debug(r.content)
if r.status_code != 200:
    logging.error("Shopify request failed:")
    logging.error(r.status_code)
    logging.error(r.reason)
    logging.error(r.content)

#Mailchimp API Key and url (from Properties file)
mailchimpAPIKey = Properties.mailchimpAPIKey
mailchimpBaseURL = Properties.mailchimpBaseURL

#Iterates through orders and assigns variables to be used in POST/UPDATE
for order in orders:
    # orderNumber = order['order_number']
    acceptsMarketing = order['buyer_accepts_marketing']
    email = order['contact_email']
    firstName = order['billing_address']['first_name']
    lastName = order['billing_address']['last_name']

    #Iterating through the notes sub-list to get the mailchimp list ID
    for note in order['note_attributes']:
        if note['name'] == 'Club':
            club = note['value']
            if not club:
                logging.error(("No clubID found in order: "+orderNumber))

    #Verifies user accepts marketing then attempts to add user to Mailchimp list as new subscriber
    if acceptsMarketing:
        subscriber = '{"email_address": "'+email+'","status": "subscribed","merge_fields": {"FNAME": "'+firstName+'","LNAME": "'+lastName+'"}}'
        requestUrl = mailchimpBaseURL + "/lists/" + club + "/members"
        postSub = requests.post(requestUrl, data=subscriber, auth=('python', mailchimpAPIKey))
        logging.debug(postSub.status_code)
        logging.debug(postSub.reason)
        logging.debug(postSub.content)
        if postSub.status_code != 200:
            logging.error("User could not be added:")
            logging.error(postSub.status_code)
            logging.error(postSub.reason)
            logging.error(postSub.content)


        #If attempt to add new user fails, attempts to update user by doing a lookup.
        if postSub.status_code != "200":
            searchSub = requests.get((Properties.mailchimpSearchURL + email), auth=('python', mailchimpAPIKey))
            logging.debug(searchSub.status_code)
            logging.debug(searchSub.reason)
            logging.debug(searchSub.content)
            matchData = searchSub.json()
            members = matchData['exact_matches']['members']
            #Iterates through exact matches for the email address
            for member in members:
                listId = member['list_id']
                userId = member['id']
                mergeFirstName = member['merge_fields']['FNAME']
                #Checks for null firstname field and updates user if it isn't present
                if not mergeFirstName:
                    updateSub = requests.put((mailchimpBaseURL+"/lists/"+listId+"/members/"+userId), data=subscriber, auth=('python', mailchimpAPIKey))
                    logging.debug(updateSub.status_code)
                    logging.debug(updateSub.reason)
                    logging.debug(updateSub.content)

                    if updateSub.status_code != 200:
                        logging.error("User could not be updated:")
                        logging.error(updateSub.status_code)
                        logging.error(updateSub.reason)
                        logging.error(updateSub.content)

