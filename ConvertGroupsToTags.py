import requests
import Properties
import logging
import hashlib
from mailchimp3 import MailChimp

from datetime import datetime, timedelta
from mailchimp3.mailchimpclient import MailChimpError

# Mailchimp API Key and url (from Properties file)
mailchimpAPIKey = Properties.mailchimpAPIKey
mailchimpBaseURL = Properties.mailchimpBaseURL

# Instantiate mailchimp client
client = MailChimp(mc_api=Properties.mailchimpAPIKey)
mailchimpListID = "959e620481"

# Get date range for past 24 hours
date = datetime.now() - timedelta(days=1)

# Query string for members
queryString = "?fields=members.id%2Cmembers.email_address%2Cmembers.interests%2Cmembers.tags&count=1000&offset=0&before_timestamp_opt=" + date.isoformat()

# Counts users added and updated.
updatedCount = 0;

# Set logging level
logging.basicConfig(level=logging.INFO, filename='./convertGroupsToTags.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M'
                    )
requestURL = Properties.mailchimpMembersURL + queryString
getMembers = requests.get(requestURL, auth=("python", mailchimpAPIKey))
membersJson = getMembers.json()
members = membersJson['members']


def tagInClub(clubList, tagList):
    for tag in tagList:
        if tag in clubList:
            return True
        else:
            return False


for member in members:
    memberEmail = member['email_address']
    # Set the subscriber_hash
    subscriber_hash = hashlib.md5(memberEmail.encode('utf-8')).hexdigest()

    logging.info("Updating member: " + memberEmail)
    tags = member['tags']

    # Create empty dictionary
    tagNames = []
    for tag in tags:
        tagNames.append(tag['name'])

    interests = member['interests']
    interestIds = []
    # Iterate through interests to get interest id.
    for k, v in interests.items():
        if v:
            interestIds.append(k)

    clubName = []
    for k, v in Properties.mailchimpInterests.items():
        for id in interestIds:
            if v == id:
                clubName.append(k)

    for club in clubName:

        if tagInClub(clubName, tagNames):
            logging.info("Tag already exists, skipping.")
            continue

        putTags = {
            "tags":
                [
                    {
                        "name": club,
                        "status": "active"
                    }
                ]
        }

        try:
            logging.info("Attempting to add tags to user.")
            client.lists.members.tags.update(list_id=mailchimpListID, subscriber_hash=subscriber_hash, data=putTags)
            logging.info("SUCCESS: tagged user " + memberEmail + " with " + club)
        except MailChimpError as error:
            logging.error("User " + memberEmail + " couldn't be tagged. Club: " + club + ".")
            logging.error(str(error))


logging.info("Updated " + str(updatedCount) + " users.")
