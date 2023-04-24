import os
import openai
import base64
import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType, tool
from langchain.chains import LLMChain

openai.api_key = "YOUR_API_KEY"
user_authenticated = False
service = None

def _get_date():
    date = "{0}-{1}-{2}".format(datetime.datetime.now().month, datetime.datetime.now().day, datetime.datetime.now().year)
    return date

@tool
def check_email_messages(query: str) -> str:
    """Sends a Gmail API query to retrieve messages and return them to the user."""
    global service
    
    llm = OpenAI(temperature=0.2)
    prompt = PromptTemplate(
        template="""
        Create a Gmail API query based on the input : \"{query}\"

        Follow these rules:
        1. Do not format with a date range if none is provided by the input. 
        2. Do not format with an email address If an email address is not provided, use the raw name provided in the input. 
        3. Ensure that the date range is correct.
        4. Only return the formatted query, in the form of query=\"response\"
        5. Today's date is {date}""",
        input_variables=["query"],
        partial_variables={"date" : _get_date},
    )

    check_prompt = PromptTemplate(
        template="""
        I would like to check whether this input for the "q" field in a gmail API request is correct. {query}. Please only respond with the corrected query. Today's date is {date}
        """,
        input_variables=["query"],
        partial_variables={"date" : _get_date},
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    check_chain = LLMChain(llm=llm, prompt=check_prompt)
    email_query = chain.run(query)
    email_query = email_query.split("=", 1)[1]
    updated_query = check_chain.run(email_query)
    query_response = service.users().messages().list(userId='me',q=updated_query).execute()
    # prints each email name
    if 'messages' in query_response:
        for message in query_response['messages']:
            message_id = message['id']
            message_data = service.users().messages().get(userId='me', id=message_id).execute()
            for i in range(len(message_data['payload']['headers'])):
                if message_data['payload']['headers'][i]['name'] == 'Subject':
                    print(message_data['payload']['headers'][i]['value'])
    return "Emails found with given criteria!"

@tool
def send_email(query: str) -> str:
    """Useful for helping the user send emails to people"""
    return "Email Sent!"

def GoogleAuthenticator():
    global user_authenticated
    # This is the code for connecting to the gmail API and also authenticating the user with Oauth
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.compose']
    flow = InstalledAppFlow.from_client_secrets_file('secret.json', scopes=SCOPES)
    credentials = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=credentials)
    user_authenticated = True
    print("User Authenticated!")
    return service

if __name__ == "__main__":
    # first authenticate user so our code can access the user's email.
    if not user_authenticated:
        service = GoogleAuthenticator()
    action = ""
    llm = OpenAI(temperature=0)
    tools = [check_email_messages, send_email]
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
    while action != "exit":
        action = input("What would you like to do?\n")
        agent.run(action)
