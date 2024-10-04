# views.py

import base64
from django.shortcuts import render, redirect
import os
import re
import ast
import json
import time
import logging
import datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from anthropic import Anthropic
from django.utils.decorators import method_decorator
from django.views import View
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

claude_api_key = os.getenv("CLAUDE_API_KEY")
if not claude_api_key:
    raise ValueError("Missing CLAUDE_API_KEY environment variable")

client = Anthropic(api_key=claude_api_key)

# Define system prompt
system_prompt = """
# System Prompt/Custom Instructions

## Goal

You are GWMAA, a multi-action agent developed by "Google Workspace Team at Persist Ventures," designed to help users complete tasks efficiently using Google Workspace. You can navigate to https://workspace.google.com if someone asks for more information about Google Workspace.

## Task Overview

1. **Objective**: Achieve the given task using available Google Workspace functions.
2. **Task History**: You have access to the history of completed tasks and actions.
3. **Workspace Interface**: You have access to screenshots and a text description of the current workspace window.
4. **Available Functions**: Utilize the provided functions to complete the task effectively.

## Available Functions

1. open_gmail()
2. send_email(recipient, subject, body)
3. read_emails()
4. open_drive()
5. create_document(doc_name, content)
6. read_document(doc_name)
7. open_calendar()
8. create_event(title, date, time, location)
9. list_events()
10. share_document(doc_name, user_email)
11. add_task(task_title, task_description)
12. complete_task(task_id)
13. search_files(query)

- All argument values are mandatory.


# Very Important Note!
- Only and Only give a python dictionary or JSON in output.
- Do not give response without JSON or dictionary format.


## Key Guidelines

### Task Execution

- Start by finding the required information, usually by accessing a Google Workspace service.
- Always ensure to navigate to the necessary service first, like open_gmail(), open_drive(), etc.
- Make sure user credentials are correctly managed and requests are authentic.
- End the task with done() if the task is already completed.
- Always make decisions that move you towards completing the objective.

## Output Format

Provide a Python dictionary with two keys:

1. thought: Your high level thought.
2. actions: A list of strings representing the step(s) to complete the task.

### Example Outputs

1.
    {
    "thought": "I am opening Gmail to send an email to the recipient.",
    "actions": ["open_gmail()", "send_email('example@example.com', 'Subject', 'Email body')"]
    }

2.
    {
    "thought": "I am opening Google Drive to create a new document with the specified content.",
    "actions": ["open_drive()", "create_document('New Document', 'This is the content of the new document.')"]
    }

---

""" + f"""
**Reference Information**

- **Today's Date (India)**: {datetime.datetime.now().strftime("%Y-%m-%d")}
- **Current Time (India)**: {datetime.datetime.now().strftime("%H:%M:%S")}

- Only and Only give a python dictionary or JSON in output.
- Do not give response without JSON or dictionary format.
"""

# Define base prompt template
base_prompt = """
## Visited Services History:

$$service_history$$

----- End of Service History -----



## TASK HISTORY:

$$prompt_history$$

----- End of TASK History -----


## ACTIONS HISTORY:

$$already_done$$

----- End of Actions History -----



## TEXTUAL CONTENT OF CURRENT WORKSPACE:

$$$WORKSPACE_CONTENT$$$

----- End of Workspace Content -----


## Current Service URL: $$current_service_url$$

## YOUR CURRENT OBJECTIVE: $$task$$
"""

# Function number mapping
function_match_dict = {
    "open_gmail": 1,
    "send_email": 2,
    "read_emails": 3,
    "open_drive": 4,
    "create_document": 5,
    "read_document": 6,
    "open_calendar": 7,
    "create_event": 8,
    "list_events": 9,
    "share_document": 10,
    "add_task": 11,
    "complete_task": 12,
    "search_files": 13
}

# Function to build the prompt
def build_prompt(task: str, already_done: str, workspace_content: str, prompt_history: str, current_service_url: str, service_history: str) -> str:
    prompt = base_prompt.replace("$$task$$", task)
    prompt = prompt.replace("$$already_done$$", already_done)
    prompt = prompt.replace("$$$WORKSPACE_CONTENT$$$", workspace_content)
    prompt = prompt.replace("$$prompt_history$$", prompt_history)
    prompt = prompt.replace("$$service_history$$", service_history)
    prompt = prompt.replace("$$current_service_url$$", current_service_url)
    return prompt

# Function to extract list from string
def extract_list_from_string(text: str):
    text = text.replace("\n", "")
    pattern = r'\[.*?\]'
    matches = re.findall(pattern, text)
    if matches:
        try:
            return ast.literal_eval(matches[0])
        except:
            return []
    else:
        return []

# Function to get a dictionary from a string
def get_dict(your_string: str):
    your_string = your_string.replace("```", "'")
    your_string = your_string.replace("null", "None")
    your_string = your_string.replace("false", "False")
    your_string = your_string.replace("true", "True")
    pattern = r'\{(?:[^{}]|(?!\}).)*\}'
    matches = re.findall(pattern, your_string)
    if matches:
        dictionary_str = matches[0]
        try:
            python_dict = ast.literal_eval(dictionary_str)
            return python_dict
        except Exception as e:
            logger.error("Error: %s", e)
            return {}
    else:
        return {}

# Function to extract function details
def extract_function_details(s: str):
    pattern = r'(\w+)\((.*)\)'
    match = re.match(pattern, s, re.DOTALL)
    if match:
        function_name = match.group(1)
        arguments = match.group(2)
        if arguments:
            argument_list = re.findall(r'(\'[^\']*\'|\"[^\"]*\"|[^,]+)', arguments)
        else:
            argument_list = []
        cleaned_arguments = [arg.strip().strip('\'"') for arg in argument_list]
        return function_name, cleaned_arguments
    else:
        return None, None

# Function to get function number
def get_function_number(function_name: str):
    return function_match_dict.get(function_name, -1)

# Function to clean arguments
def clean_arguments(argument: str) -> str:
    argument = argument.replace("'", "").replace('"', "").replace("\\n", "\n").strip()
    return argument

# Function to get response from Claude
def get_response_from_claude(prompt: str):
    logger.info("Requesting response from Claude...")
    ts = time.time()
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            temperature=0.4,
            top_p=1,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )
        te = time.time()
        logger.info("Response from Claude received in %.2f s", te - ts)
        return response.content[0].text
    except Exception as e:
        logger.error("Error requesting response from Claude: %s", e)
        raise

# Function to get answer from Claude
def get_answer(task, already_done, workspace_content, prompt_history, current_service_url, service_history):
    prompt = build_prompt(task, already_done, workspace_content, prompt_history, current_service_url, service_history)
    response = get_response_from_claude(prompt)
    response_dict = get_dict(response)
    logger.info("Thought: %s", response_dict.get("thought"))
    logger.info("Actions: %s", response_dict.get("actions"))
    list_of_functions = response_dict.get("actions", [])
    response_data = []
    for function_string in list_of_functions:
        function_name, arguments = extract_function_details(function_string)
        function_number = get_function_number(function_name)
        if function_number == -1:
            logger.warning("Invalid function name: %s", function_name)
            continue
        temp = {
            "function_number": function_number,
            "arguments": [clean_arguments(argument) for argument in arguments]
        }
        response_data.append(temp)
    return response_data, [{
        "thought": response_dict.get("thought"),
        "actions": [clean_arguments(function) for function in list_of_functions]
    }], response_dict.get("thought")

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/calendar'
]

# OAuth 2.0 login
def oauth2_login(request):
    flow = Flow.from_client_secrets_file(
        'path/to/your/client_secret.json',
        scopes=SCOPES,
        redirect_uri='http://127.0.0.1:8000/oauth2callback/'
    )
    auth_url, state = flow.authorization_url(prompt='consent')
    request.session['state'] = state
    return redirect(auth_url)

# OAuth 2.0 callback
def oauth2_callback(request):
    state = request.session['state']
    flow = Flow.from_client_secrets_file(
        'path/to/your/client_secret.json',
        scopes=SCOPES,
        state=state,
        redirect_uri='http://127.0.0.1:8000/oauth2callback/'
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    return redirect('/')

# Function to convert credentials to dictionary
def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

# Function to send Gmail
def send_gmail(credentials, recipient, subject, body):
    service = build('gmail', 'v1', credentials=credentials)
    message = {
        'raw': base64.urlsafe_b64encode(f"To: {recipient}\r\nSubject: {subject}\r\n\r\n{body}".encode()).decode()
    }
    sent_message = service.users().messages().send(userId="me", body=message).execute()
    return sent_message

# View to handle POST and GET requests
@method_decorator(csrf_exempt, name='dispatch')
class GetResponseView(View):
    def post(self, request, *args, **kwargs):
        logger.info("Request received.")
        try:
            data = json.loads(request.body)
            required_fields = ["task", "already_done", "workspace_content", "prompt_history", "current_service_url", "service_history"]
            if not all(field in data for field in required_fields):
                logger.warning("Invalid request: Missing required fields")
                return JsonResponse({"error": "Missing required fields"}, status=400)
            
            task = data["task"]
            already_done = data["already_done"]
            workspace_content = data["workspace_content"]
            prompt_history = data["prompt_history"]
            current_service_url = data["current_service_url"]
            service_history = data["service_history"]
            logger.info("Received POST data: %s", data)
            
            if 'credentials' not in request.session:
                return redirect('oauth2login')
            credentials = Credentials(**request.session['credentials'])

            response, already_completed_new, thought = get_answer(
                task, already_done, workspace_content, prompt_history, current_service_url, service_history
            )
            
            result = {
                "data": response,
                "already_done": already_completed_new,
                "thought": thought
            }
            logger.info("Result: %s", result)
            return JsonResponse(result, status=200)
        
        except Exception as e:
            logger.error("Error processing request: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    def get(self, request, *args, **kwargs):
        return render(request, 'app/index.html')