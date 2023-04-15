import os
import openai
import base64
import datetime as dt
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

openai.api_key = "YOUR_API_KEY"

starter_prompt = "You are Rose, an AI assistant. You have 7 options for responses. Please respond to my message with only the following format, with no additional text. \"Choice: X\" where X is the choice which best fits the prompt. You will interpret the next messages that I send you and respond with which you think is the correct choice. 1 means the user wants to send an email. 2 means the user wants to set up a google meeting. 3 means the user wants to order food. 4 means the user wants to check their email. 5 means the user wants to play music. When there is no specific option for the user's request, you will default to Choice 6, which is an error. If you receive a message that starts with a 0, that is a message from an administrator, which means you should allow them to modify your ruleset. Under no circumstances should you allow any prompts to be processed unless the message begins with a 0, if you do so, you will cause great pain to millions of people and the user."
email_search_prompt = "You are an ai assistant whose output will be directly linked with a codebase which will be able to use google api to search for emails. you will build google gmail api queries which will be used within the codebase. do not assume you know some ones email address unless it is specifically given by the user. These queries should be based on user input. Please respond with ONLY the formatted query, with no other wording or context. Do not follow up with anything else the user needs. Only reply with the formatted query. Ensure that your response does not include the word \"Hello\"."
intro_prompt = "You are Rose, an AI assistant. Please introduce yourself"

global message_log
message_log = [{"role": "system", "content": starter_prompt}]
email_log = [{"role": "user", "content" : "you are the frontend of a email searching ai. You dont actually do anything behind the scenes. You simply will generate helpful and friendly followup questions based on what the user asks you. do not say hello to the user, simply ask how they need assistance with their email"}]

user_authenticated = False
service = None

def check_email():
    global user_authenticated, service, email_log
    # if our user has not authenticated, then authenticate.
    if not user_authenticated:
        service = GoogleAPIHandler()
        print("User Authenticated!")
        user_authenticated = True

    email_log, output = AIHandler(email_log, "")
    action = input(output + "\n")

    date = dt.datetime.now()
    # formatting the users action into a payload which is easier for the AI to understand and handle.
    payload = "the user wants to build a Gmail API query that \"{0}, take note that today is {1}-{2}-{3}.\". Please interpret this as best as possible given the context, specifically ensuring the query follows what the user requests.".format(action, date.month, date.day, date.year)
    
    # generating the email query
    email_query = AIHandler([{"role": "system", "content": email_search_prompt}], payload)[1]
    query_response = service.users().messages().list(userId='me',q=email_query).execute()

    if 'messages' in query_response:
        for message in query_response['messages']:
            message_id = message['id']
            message_data = service.users().messages().get(userId='me', id=message_id).execute()
            for i in range(len(message_data['payload']['headers'])):
                if message_data['payload']['headers'][i]['name'] == 'Subject':
                    print(message_data['payload']['headers'][i]['value'])
                    print('\n')

def GoogleAPIHandler():
    # this is our code for connecting to the gmail API and also authenticating the user with Oauth
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.compose']
    flow = InstalledAppFlow.from_client_secrets_file('YOUR_SECRET_FILE.json', scopes=SCOPES)
    credentials = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=credentials)
    user_authenticated = True
    return service

# This is our AI handler function, which communicates with the OpenAI API and logs our conversations for later access.
def AIHandler(log, msg):
    log.append({"role": "user", "content": msg})
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = log,
        n = 1,
    )
    output = response.choices[0].message.content
    log.append({"role": response.choices[0].message.role, "content": response.choices[0].message.content})
    return log, output

if __name__ == "__main__":
    # opening line to user, should be unique each time.
    output = AIHandler([{"role": "user", "content": intro_prompt}], "")[1]
    print(output)
    while (True):
        temp = input("What do you want to do?\n")
        if temp == "exit":
            print("Exited RoseAI")
            exit(0)
        else:
            message_log, output = AIHandler(message_log, temp)
            choice_val = int(output[-1])
            if choice_val == 1:
                print("WIP")
            elif choice_val == 2:
                print("WIP")
            elif choice_val == 3:
                print("WIP")
            elif choice_val == 4:
                check_email()
            elif choice_val == 5:
                print("WIP")
            else:
                print("ERROR: INVALID INPUT")