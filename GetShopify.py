import requests
from mailchimp3.mailchimpclient import MailChimpError

import Properties
import logging
import hashlib
from datetime import datetime, timedelta
from mailchimp3 import MailChimp

# Set logging level
logging.basicConfig(level=logging.INFO, filename='./shopify-mailchimp.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M'
                    )

# Get date range for past 24 hours
date = datetime.now() - timedelta(days=1)

client = MailChimp(mc_api=Properties.mailchimpAPIKey)

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
mailchimpListID = "959e620481"

# Counts users added and updated.
addedCount = 0;
updatedCount = 0;
tagErrorCount = 0;
groupErrorCount = 0;

# Iterates through orders and assigns variables to be used in POST/UPDATE
for order in orders:
    acceptsMarketing = order['buyer_accepts_marketing']
    email = order['contact_email']
    firstName = order['billing_address']['first_name']
    lastName = order['billing_address']['last_name']
    # Iterating through the notes sub-list to get the mailchimp list ID
    for note in order['note_attributes']:
        if note['name'] == 'ClubName':
            clubName = note['value'].strip()
            logging.info("ClubName for order " + order['name'] + " is " + clubName)
            if not clubName:
                logging.error("No clubID found in order: " + order['name'])

    # Try to add users and if fails, update user.
    # Add user to mailchimp
    try:
        mailchimpInterestId = Properties.mailchimpInterests[clubName.strip()]
    except KeyError as e:
        logging.error("Couldn't find an ID for club " + clubName + ".")
    except AttributeError as a:
        logging.error("NoneType error for " + clubName)

    # Set the subscriber_hash
    try:
        subscriber_hash = hashlib.md5(email.encode('utf-8')).hexdigest()
    except AttributeError as a:
        logging.error("User has no email")
        continue

    subscriber = {
        "status": "subscribed",
        "email_address": email,

        "merge_fields": {
            "FNAME": firstName,
            "LNAME": lastName,
        },
        "interests": {
            mailchimpInterestId: True
        }
    }

    tags = {
        "tags":
            [
                {
                    "name": clubName,
                    "status": "active"
                }
            ]
    }

    logging.info("Attempting to POST email " + email + " from order " + order['name'])

    try:
        client.lists.members.create(list_id=mailchimpListID, data=subscriber)
        # If user was added successfully, log it.
        addedCount = addedCount + 1
        logging.info("SUCCESS: added user " + email + "to list " + clubName)
    except MailChimpError as e:
        # If attempt fails, log it
        logging.error(str(e))
        logging.info("WARN: Unable to add user " + email + " to list " + clubName + " attempting update.")
        try:
            client.lists.members.update(list_id=mailchimpListID, subscriber_hash=subscriber_hash, data=subscriber)
            logging.info("SUCCESS: updated user " + email + "to list " + clubName)
            updatedCount = updatedCount + 1
        except MailChimpError as er:
            logging.error("User " + email + " couldn't be updated. Club " + clubName + " Order  " + order['name'])
            logging.error(str(er))
            errorCount = groupErrorCount + 1

        try:
            logging.info("Attempting to add tags to user.")
            client.lists.members.tags.update(list_id=mailchimpListID, subscriber_hash=subscriber_hash, data=tags)
            logging.info("SUCCESS: tagged user " + email + " with " + clubName)
        except MailChimpError as error:
            logging.error("User " + email + " couldn't be tagged. Club: " + clubName + " Order  " + order['name'])
            logging.error(str(error))
            errorCount = tagErrorCount + 1


logging.info("Added " + str(addedCount) + " users.")
logging.info("Updated " + str(updatedCount) + " users.")
logging.info("There were " + str(tagErrorCount) + " tagging errors.")
logging.info("There were " + str(tagErrorCount) + " group errors.")
