import requests
import Properties
import logging
import hashlib

from datetime import datetime, timedelta

# Mailchimp API Key and url (from Properties file)
mailchimpAPIKey = Properties.mailchimpAPIKey
mailchimpBaseURL = Properties.mailchimpBaseURL

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
        postURL = mailchimpBaseURL + "/lists/959e620481/members/" + subscriber_hash + "/tags"
        postData = '{"tags": [{"name": "' + club + '", "status": "active"}]}'
        logging.info("Posting: " + postData + " to " + postURL)
        if tagInClub(clubName, tagNames):
            logging.info("Tag already exists, skipping.")
            continue

        postTags = requests.post(postURL, data=postData.encode('utf-8'), auth=("python", mailchimpAPIKey))
        if postTags.status_code == 204:
            logging.info("Successfully added " + club + " to " + memberEmail + ".")
            updatedCount = updatedCount + 1
        else:
            logging.error("Could not add tags to user!")
            logging.error(postTags.status_code)
            logging.error(postTags.reason)
            logging.error(postTags.content)

logging.info("Updated " + str(updatedCount) + " users.")
