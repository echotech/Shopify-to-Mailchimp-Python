import hashlib

import requests
from mailchimp3.mailchimpclient import MailChimpError

import Properties
import logging
from csv import reader
from mailchimp3 import MailChimp

# Set logging level
logging.basicConfig(level=logging.INFO, filename='./updatefromcsv.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M'
                    )

# Mailchimp API Key and url (from Properties file)
mailchimpBaseURL = Properties.mailchimpBaseURL
mailchimpListID = "959e620481"
client = MailChimp(mc_api=Properties.mailchimpAPIKey)

# Counts users added and updated.
addedCount = 0
updatedCount = 0
tagErrorCount = 0
groupErrorCount = 0

logging.info("Starting Update From CSV")
with open('AllEmails.csv', newline='') as read_obj:
    csv_reader = reader(read_obj)
    header = next(csv_reader)
    # Check file as empty
    for row in csv_reader:
    # row variable is a list that represents a row in csv
        clubName = row[0]
        email = row[3]
        firstName = row[2]
        lastName = row[1]
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
        logging.info("Attempting to POST email " + email + ".")

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
                client.lists.members.update(list_id=mailchimpListID, subscriber_hash=subscriber_hash,
                                            data=subscriber)
                logging.info("SUCCESS: updated user " + email + "to list " + clubName)
                updatedCount = updatedCount + 1
            except MailChimpError as er:
                logging.error(
                    "User " + email + " couldn't be updated. Club " + clubName + ".")
                logging.error(str(er))
                errorCount = groupErrorCount + 1

        try:
            logging.info("Attempting to add tags to user.")
            client.lists.members.tags.update(list_id=mailchimpListID, subscriber_hash=subscriber_hash,
                                             data=tags)
            logging.info("SUCCESS: tagged user " + email + " with " + clubName)
        except MailChimpError as error:
            logging.error(
                "User " + email + " couldn't be tagged. Club: " + clubName + ".")
            logging.error(str(error))
            errorCount = tagErrorCount + 1

    logging.info("Added " + str(addedCount) + " users.")
    logging.info("Updated " + str(updatedCount) + " users.")
    logging.info("There were " + str(tagErrorCount) + " tagging errors.")
    logging.info("There were " + str(tagErrorCount) + " group errors.")


logging.info("Mailchimp Upload Complete!")
