Supported Tasks

The Django application integrated with the Claude model can perform a variety of tasks related to Google Workspace. Based on the provided system_prompt, you can ask it to:

1. Open Gmail
2. Send an Email
3. Read Emails
4. Open Google Drive
5. Create a Document
6. Read a Document
7. Open Google Calendar
8. Create an Event
9. List Events
10. Share a Document
11. Add a Task
12. Complete a Task
13. Search for Files

Placing Google Account Information

This application is set up to interact with the Claude model, which acts as the agent for performing tasks. For the agent to actually perform actions like sending an email or creating an event, it would need to authenticate using the user's Google account. This typically involves OAuth 2.0 authentication where you redirect users to Google's login page to get access tokens.

However, if you're just setting up and testing locally without connecting to Google's API, you can simulate these actions.

Example Prompts and Test Cases

Let's set up some example test cases you can use to interact with the application.

### Example 1: Sending an Email

Task:
Send an email with the subject "Test Email" and body "This is a test email" to "example@gmail.com".

Form Data:
- task: "Send an email with subject 'Test Email' and body 'This is a test email' to 'example@gmail.com'."
- workspace_content: "You have access to your Gmail account."

### Example 2: Creating a Document

Task:
Create a document named "Test Document" with the content "This is the content of the test document."

Form Data:
- task: "Create a document named 'Test Document' with the content 'This is the content of the test document'."
- workspace_content: "You have access to Google Drive."

### Example 3: Creating an Event

Task:
Create an event named "Meeting" on "2024-10-01" at "10:00 AM" in the location "Office".

Form Data:
- task: "Create an event named 'Meeting' on '2024-10-01' at '10:00 AM' in the location 'Office'."
- workspace_content: "You have access to Google Calendar."

### Example 4: Listing Events

Task:
List all events for the current week.

Form Data:
- task: "List all events for the current week."
- workspace_content: "You have access to Google Calendar."

### Example 5: Reading Emails

Task:
Read all unread emails from your Gmail inbox.

Form Data:
- task: "Read all unread emails from my Gmail inbox."
- workspace_content: "You have access to your Gmail account."

Testing the Application

1. Open your browser and navigate to http://127.0.0.1:8000/.
2. Fill out the form with one of the example tasks and provide the corresponding workspace content.
3. Submit the form.
4. Observe the output in the "Response" section to see the thought and actions the Claude model has generated.

### Simulating Real Tasks (with OAuth 2.0)

To make real API calls to Google services, you'll need to set up OAuth 2.0 authentication. Here are the steps for OAuth 2.0 setup:

1. Create a project in the Google Developer Console.
2. Enable the necessary APIs (Gmail API, Google Drive API, Calendar API, etc.).
3. Set up OAuth 2.0 credentials.
4. Use the obtained client ID and client secret in your Django application to authenticate users.

You can use libraries like google-auth, google-auth-oauthlib, and google-auth-httplib2 to handle OAuth 2.0 authentication in your Django application.

Conclusion

This basic setup allows you to simulate task execution using the Claude language model. For real-world tasks, especially those involving sensitive actions like sending emails or creating calendar events, OAuth 2.0 authentication and Google API integration are necessary.



## OAuth authentication feature added

```
 pip install google-auth google-auth-oauthlib google-auth-httplib2
```

