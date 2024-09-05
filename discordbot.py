import discord
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import re
import pytz
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')

try:
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    logger.info('Google Calendar API service built successfully.')
except Exception as e:
    logger.error(f'Failed to create Google Calendar API service: {e}')
    exit(1)

calendar_id = os.getenv('CALENDAR_ID')
discord_channel_id = os.getenv('DISCORD_CHANNEL_ID')

def parse_event_details(message_content):
    try:
        logger.debug('Parsing event details from message content.')
        lines = message_content.strip().split("\n")
        
        if len(lines) < 2:
            logger.warning('Message content does not contain enough lines.')
            return None
        
        title = lines[0]
        date_time_str = lines[1]
        
        try:
            event_date = datetime.strptime(date_time_str, '%d/%m/%Y')
            ist = pytz.timezone('Asia/Kolkata')
            start_time = event_date.replace(hour=8, minute=0)
            start_time = ist.localize(start_time)
            end_time = start_time + timedelta(hours=1)
        except ValueError as e:
            logger.error(f'Invalid date format: {e}')
            return None

        links = re.findall(r'(https?://\S+)', message_content)
        description = "Links:\n" + "\n".join(links)
        
        event_details = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        logger.debug(f'Event details parsed: {event_details}')
        return event_details
    
    except Exception as e:
        logger.error(f'Error parsing event details: {e}')
        return None

def add_event_to_calendar(event_details):
    try:
        event = service.events().insert(calendarId=calendar_id, body=event_details).execute()
        event_link = event.get('htmlLink')
        logger.info(f'Event added to calendar: {event_link}')
        return event_link
    except Exception as e:
        logger.error(f'Failed to add event to calendar: {e}')
        return None

@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.name == discord_channel_id and message.author != client.user:
        try:
            logger.info(f'Received message from {message.author}: {message.content}')
            event_details = parse_event_details(message.content)
            if event_details:
                event_link = add_event_to_calendar(event_details)
                if event_link:
                    await message.channel.send('Event added to Google Calendar!')
                    await message.channel.send(f'{event_link}')
                else:
                    await message.channel.send('Failed to add the event to Google Calendar.')
            else:
                await message.channel.send('Failed to parse the event details. Please check the format.')
        except Exception as e:
            logger.error(f'Error handling message: {e}')
            await message.channel.send('An error occurred while processing the message.')

client.run(os.getenv('DISCORD_TOKEN'))
