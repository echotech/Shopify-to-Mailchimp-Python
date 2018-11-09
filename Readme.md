# Shopify to Mailchimp Sync 
None of the Shopify to mailchimp integrations could handle my unique setup. I had a couple specific requirements:

- To sync users to one of multiple different lists based on a cart attribute set by my shopify store.

- To sync more than just email address. (Integromat, Automate.io, and Zapier integrations didn't offer this.)

- To update existing users if they didn't have this data already.

## How it works

In a file called Properties.py I have my properties listed like this:

`shopifyURL = 'https://MY_API_KEY:GET_YOURS_FROM_SHOPIFY_DOCUMENTATION@MY-STORE.myshopify.com/admin/orders.json'`

`mailchimpAPIKey = "MY_MAILCHIMP_KEY"`

`mailchimpBaseURL = "https://MY_SERVER.api.mailchimp.com/3.0"`

`mailchimpSearchURL = "https://MY_SERVER.api.mailchimp.com/3.0/search-members?fields=exact_matches&query="`

All the properties are pretty self-explanatory except mailchimpSearchURL. The fields query parameter ensures that I'm only returning exact matches.

In order for this to work for you fully you'd need to set a cart attribute on your Shopify cart called "club" that contains the mailchimp list ID you want to add that customer to.

