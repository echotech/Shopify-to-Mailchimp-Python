import requests
import Properties
import logging
import hashlib
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
    created_at_min=date,
    # Returns only the fields below
    fields='name,contact_email,buyer_accepts_marketing,note_attributes,billing_address',
    status='any',
    # last_id='944696590378',
    limit='250'
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
            clubName = note['value']

            if not clubName:
                logging.error(("No clubID found in order: " + order['order_number']))

    # Verifies user accepts marketing then attempts to add user to Mailchimp list as new subscriber
    # if acceptsMarketing:
    # Attempt to lookup user in mailchimp
    # searchSub = requests.get((Properties.mailchimpSearchURL + email), auth=('python', mailchimpAPIKey))
    # matchData = searchSub.json()
    # members = matchData['exact_matches']['members']

    # Try to add users and if fails, update user.
    # Add user to mailchimp
    subscriber = '{"email_address": "' + email + '","status": "subscribed","merge_fields": {"FNAME": "' + firstName + '","LNAME": "' + lastName + '"}}'
    requestUrl = mailchimpBaseURL + "/lists/" + clubName + "/members"
    postSub = requests.post(requestUrl, data=subscriber, auth=('python', mailchimpAPIKey))
    # If user was added successfully, log it.
    if postSub.status_code == 200:
        addedCount = addedCount + 1
        logging.info("Added user " + email + "to list " + clubName)
        continue

    # If attempt fails, log it
    if postSub.status_code != 200:
        #logging.info("Unable to add user " + email + " to list " + clubName + " attempting update.")
        subscriber_hash = hashlib.md5(email.encode('utf-8')).hexdigest()
        # print(email + ", " + firstName + ", " + lastName + ", " + subscriber_hash + ", " + clubName)
        updateSub = requests.put(
            (mailchimpBaseURL + "/lists/" + clubName + "/members/" + subscriber_hash),
            data=subscriber, auth=('python', mailchimpAPIKey))

        if updateSub.status_code != 200:
            logging.error("User could not be updated:")
            logging.error(updateSub.status_code)
            logging.error(updateSub.reason)
            logging.error(updateSub.content)
            continue

        if updateSub.status_code == 200:
            updatedCount = updatedCount + 1
            logging.info("Updated user " + email + "in list " + clubName)
            continue

logging.info(str(datetime.now()) + ": " + "Added " + str(addedCount) + " users.")
logging.info(str(datetime.now()) + ": " + "Updated " + str(updatedCount) + " users.")