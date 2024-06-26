from typing import Any
import argparse
import os
import os.path

import dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from telethon import TelegramClient
from telethon.tl.functions.contacts import AddContactRequest, DeleteContactsRequest


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/contacts"]

# We are only interested in these fields
FIELDS = "names,phoneNumbers,imClients"


def get_gservice():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("people", "v1", credentials=creds)
    return service

def get_telethon():
    # Remember to use your own values from my.telegram.org!
    api_id = int(os.environ.get("TELE_API_ID", ""))
    api_hash = os.environ.get("TELE_API_HASH", "")
    client = TelegramClient('anon', api_id, api_hash)
    return client

def parse_user(s: str) -> Any:
    # Using Any instead of int | str because Telethon gives errors when assigning int
    user: Any
    try:
        # Assume input is user's ID
        user = int(s)
    except ValueError:
        # Assume input is user's username
        user = s
    return user

def do_entry():
    service = get_gservice()

    # Warmup cache by sending an empty query
    service.people().searchContacts(
      query="",
      readMask=FIELDS,
    )

    query = input("Name:")

    results = service.people().searchContacts(
      query=query,
      readMask=FIELDS,
    ).execute().get('results', [])

    if len(results) == 0:
        print("No results found")
        exit()

    if len(results) == 1:
        person = results[0]['person']
        print(f"Found one result: {person['names'][0]['displayName']}")
    else:
        for result in results:
            person = result["person"]
            print(f"{person['names'][0]['displayName']}")
        print("Found many results, taking first result")

        person = results[0]['person']

    user = input("Telegram username or ID:")

    imClient = dict(
        username=f"{user}",
        protocol="Telegram",
    )
    if 'imClients' in person:
        person['imClients'].append(imClient)
    else:
        person['imClients'] = [imClient]

        service.people().updateContact(
          resourceName=person["resourceName"],
          updatePersonFields="imClients",
          body=person,
        ).execute()

def do_sync():
    async def loop():
        try:
            results = (
            service.people()
            .connections()
            .list(
                resourceName="people/me",
                pageSize=1000,
                personFields=FIELDS,
            )
            .execute()
        )
            connections = results.get("connections", [])
            for person in connections:
                # Get name
                names = person.get("names", [])
                if not names:
                    continue
                name = names[0]
                first_name=name.get('givenName', '')
                last_name=name.get('familyName', '')

                # Get telegram id
                if 'imClients' not in person:
                    continue
                for imClient in person['imClients']:
                    if imClient['protocol'] != 'Telegram':
                        continue
                    telegram_id = imClient['username']
                    break
                else:
                    continue

                user = parse_user(telegram_id)
                try:
                    try:
                        await client(DeleteContactsRequest([user]))
                    except:
                        # Ignore deletion failures
                        pass
                    await client(AddContactRequest(
                        id=user,
                        first_name=first_name,
                        last_name=last_name,
                        phone="",
                    ))
                except Exception as e:
                    print(f"Failed for {person['names'][0]['displayName']}")
                    print(e)
                else:
                    print(f"Added {user}: {first_name} {last_name}")

        except HttpError as err:
            print(err)

    service = get_gservice()
    client = get_telethon()
    with client:
        client.loop.run_until_complete(loop())


if __name__ == "__main__":
    dotenv.load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['sync', 'entry'])
    args = parser.parse_args()

    if args.mode == 'entry':
        do_entry()
    elif args.mode == 'sync':
        do_sync()
