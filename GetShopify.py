import requests
import Properties
import logging
from datetime import datetime, timedelta

# Set logging level
logging.basicConfig(level=logging.INFO, filename='/var/log/shopify-mailchimp.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M'
                    )

# Get date range for past 24 hours
date = datetime.now() - timedelta(days=1)

# Sets URL and parameters for request
url = Properties.shopifyURL
params = dict(
    # Gets everything after the date set above
    created_at_min = date,
    # Returns only the fields below
    fields='name,contact_email,buyer_accepts_marketing,note_attributes,billing_address'
)

# Get request from Shopify and creates orders list from json.
r = requests.get(url, params)
data = r.json()
orders = data['orders']

# Shopify response
if r.status_code != 200:
    logging.error("Shopify request failed:")
    logging.error(r.status_code)
    logging.error(r.reason)
    logging.error(r.content)

# Mailchimp API Key and url (from Properties file)
mailchimpAPIKey = Properties.mailchimpAPIKey
mailchimpBaseURL = Properties.mailchimpBaseURL

# Counts users added and updated.
addedCount = 0;
updatedCount = 0;

# Iterates through orders and assigns variables to be used in POST/UPDATE
for order in orders:
    acceptsMarketing = order['buyer_accepts_marketing']
    email = order['contact_email']
    firstName = order['billing_address']['first_name']
    lastName = order['billing_address']['last_name']

    # Iterating through the notes sub-list to get the mailchimp list ID
    for note in order['note_attributes']:
        if note['name'] == 'Club':
            club = note['value']
            if not club:
                logging.error(("No clubID found in order: " + order['order_number']))

    # Verifies user accepts marketing then attempts to add user to Mailchimp list as new subscriber
    if acceptsMarketing:
        # Attempt to lookup user in mailchimp
        searchSub = requests.get((Properties.mailchimpSearchURL + email), auth=('python', mailchimpAPIKey))
        matchData = searchSub.json()
        members = matchData['exact_matches']['members']

        # If there is a match on the email
        if members:
            # Iterates through exact matches for the email address
            for member in members:
                listId = member['list_id']
                userId = member['id']
                mergeFirstName = member['merge_fields']['FNAME']
                # Checks for null firstname field and updates user if it isn't present
                if not mergeFirstName:
                    updateSub = requests.put((mailchimpBaseURL + "/lists/" + listId + "/members/" + userId),
                                             data=subscriber, auth=('python', mailchimpAPIKey))
                    logging.info(updateSub.status_code)
                    logging.info(updateSub.reason)
                    logging.info(updateSub.content)
                    if updateSub.status_code != 200:
                        logging.error("User could not be updated:")
                        logging.error(updateSub.status_code)
                        logging.error(updateSub.reason)
                        logging.error(updateSub.content)
                        break
                    updatedCount += 1

        else:
            # Add user to mailchimp
            subscriber = '{"email_address": "' + email + '","status": "subscribed","merge_fields": {"FNAME": "' + firstName + '","LNAME": "' + lastName + '"}}'
            requestUrl = mailchimpBaseURL + "/lists/" + club + "/members"
            postSub = requests.post(requestUrl, data=subscriber, auth=('python', mailchimpAPIKey))
            logging.info(postSub.status_code)
            logging.info(postSub.reason)
            logging.info(postSub.content)
            logging.info("Added User: " + email + " at " + str(datetime.now()))
            # If attempt fails, log it
            if postSub.status_code != "200":
                logging.error("Unable to add user " + email + " on " + str(datetime.now()))
                logging.error(postSub.status_code)
                logging.error(postSub.reason)
                logging.error(postSub.content)
                break
            addedCount += 1


logging.info("Added " + str(addedCount) + " users.")
logging.info("Updated " + str(updatedCount) + " users.")
#print("Added " + str(addedCount) + " and updated " + str(updatedCount) + " users at " + str(datetime.now()) + ".")
