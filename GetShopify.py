import requests
import Properties
import logging
import hashlib
from datetime import datetime, timedelta

# Set logging level
logging.basicConfig(level=logging.INFO, filename='/tmp/shopify-mailchimp.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M'
                    )

# Get date range for past 24 hours
date = datetime.now() - timedelta(days=30)

# Sets URL and parameters for request
url = Properties.shopifyURL
params = dict(
    # Gets everything after the date set above
    created_at_min=date,

    # Returns only the fields below
    fields='name,contact_email,buyer_accepts_marketing,note_attributes,billing_address',

    # Returns an order of any status, not just complete  
    status='any',

    # Sets the last id, can be used if you're going back in time
    # last_id='whatever',

    # Gets maximum of 250 orders at a time
    limit='250'

)

# Get request from Shopify and creates orders list from json.
logging.info("Getting Shopify Orders")
r = requests.get(url, params)
data = r.json()
orders = data['orders']

# Shopify response
if r.status_code != 200:
    logging.error("FAILURE: Shopify request failed!")
    logging.error(r.status_code)
    logging.error(r.reason)
    logging.error(r.content)

# Mailchimp API Key and url (from Properties file)
mailchimpAPIKey = Properties.mailchimpAPIKey
mailchimpBaseURL = Properties.mailchimpBaseURL

# Counts users added and updated.
addedCount = 0;
updatedCount = 0;

# Gets json response of interests
# interestUrl = mailchimpBaseURL + "/lists/959e620481/interest-categories/660a133c49/interests?fields=interests.id,interests.name&count=50"
# getGroups = requests.get(interestUrl, auth=('python', mailchimpAPIKey))
# print(getGroups.content)

# Iterates through orders and assigns variables to be used in POST/UPDATE
for order in orders:
    acceptsMarketing = order['buyer_accepts_marketing']
    email = order['contact_email']
    firstName = order['billing_address']['first_name']
    lastName = order['billing_address']['last_name']
    # Iterating through the notes sub-list to get the mailchimp list ID
    for note in order['note_attributes']:
        if note['name'] == 'ClubName':
            clubName = note['value']
            logging.info("ClubName for order " + order['name'] + " is " + clubName)
            if not clubName:
                logging.error("No clubID found in order: " + order['name'])

    # Try to add users and if fails, update user.
    # Add user to mailchimp

    subscriber = '{"email_address": "' + email + '","status": "subscribed","merge_fields": {"FNAME": "' \
                 + firstName + '","LNAME": "' + lastName + '"}, "interests": {' + clubName + ': true}}'
    requestUrl = mailchimpBaseURL + "/lists/959e620481/members"
    logging.info("Attempting to POST email " + email + " from order " + order['name'])
    postSub = requests.post(requestUrl, data=subscriber.encode('utf-8'), auth=("python", mailchimpAPIKey))

    # Set the subscriber_hash
    subscriber_hash = hashlib.md5(email.encode('utf-8')).hexdigest()

    # If user was added successfully, log it.
    if postSub.status_code == 200:
        addedCount = addedCount + 1
        logging.info("SUCCESS: added user " + email + "to list " + clubName)

    # If attempt fails, log it
    if postSub.status_code != 200:
        logging.info("WARN: Unable to add user " + email + " to list " + clubName + " attempting update.")

        # print(email + ", " + firstName + ", " + lastName + ", " + subscriber_hash + ", " + clubName)
        updateSub = requests.patch(
            (mailchimpBaseURL + "/lists/959e620481/members/" + subscriber_hash),
            data=subscriber.encode('utf-8'), auth=("python", mailchimpAPIKey))

        if updateSub.status_code == 200:
            updatedCount = updatedCount + 1
            logging.info("SUCCESS: updated user: " + email + ". Added to group: " + clubName)

        if updateSub.status_code != 200:
            logging.error("User " + email + " couldn't be updated. Club " + clubName + " Order # " + order['name'])
            logging.error(updateSub.status_code)
            logging.error(updateSub.reason)
            logging.error(updateSub.content)
            continue


logging.info("Added " + str(addedCount) + " users.")
logging.info("Updated " + str(updatedCount) + " users.")
