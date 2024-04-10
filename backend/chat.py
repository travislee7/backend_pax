# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = 'AC5fb0766880f6ceb0e516e1a5d9191246'
auth_token = '13dc07e7dd0bbdece5c4a03c21b16632'
client = Client(account_sid, auth_token)

# create conversation
# conversation = client.conversations \
#                      .v1 \
#                      .conversations \
#                      .create(friendly_name='My First Conversation')

# // Fetch conversation
conversation = client.conversations \
                     .v1 \
                     .conversations('CH6a322946ed394b2bb445c7c39f3a54b1') \
                     .fetch()

print(conversation.chat_service_sid)

webhook = client.conversations \
    .v1 \
    .conversations('CH6a322946ed394b2bb445c7c39f3a54b1') \
    .webhooks \
    .create(
         configuration_method='Post',
         configuration_filters=['onMessageAdded', 'onConversationRemoved'],
         configuration_url='https://example.com',
         target='webhook'
     )

print(webhook.sid)

# Add message to conversation
message = client.conversations \
                .v1 \
                .conversations(conversation.sid) \
                .messages \
                .create(author='John', body='Web hook')

# Tmessage = client.conversations \
#                 .v1 \
#                 .conversations(conversation.sid) \
#                 .messages \
#                 .create(author='Travis', body='Hi !')

messages = client.conversations \
                 .v1 \
                 .conversations(conversation.sid) \
                 .messages \
                 .list(limit=20)\
                #  .list(order='desc', limit=20)

for record in messages:
    print(record.body)

# print(message.body)
# print(Tmessage.body)