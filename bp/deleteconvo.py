from twilio.rest import Client
import settings

def delete_conversation(conversation_sid):
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)

    try:
        client.conversations.v1.conversations(conversation_sid).delete()
        print(f"Deleted Conversation: {conversation_sid}")
    except Exception as e:
        print(f"Failed to delete Conversation {conversation_sid}: {e}")

if __name__ == "__main__":
    # Example SID - replace 'CHXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' with actual SID
    conversation_sid = 'CH8ccf8312ed97417cb471f8c6a42aa5f7'
    delete_conversation(conversation_sid)
