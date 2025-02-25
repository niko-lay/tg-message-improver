#!/usr/bin/env python3
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, Channel, User
import asyncio
import os
from configparser import ConfigParser

# Configuration
config = ConfigParser()
config_file = 'config.ini'

# Function to create config file if it doesn't exist
def create_config():
    if not os.path.exists(config_file):
        config['Telegram'] = {
            'api_id': '17349',
            'api_hash': '344583e45741c457fe1862106095a5eb',
            'phone': 'YOUR_PHONE_NUMBER',
            'session_name': 'message_editor'
        }
        config['Bot'] = {
            'append_text': ' #edited',
            'target_group': ''
        }
        
        with open(config_file, 'w') as f:
            config.write(f)
        print(f"Config file created at {config_file}. Please edit it with your credentials.")
        return False
    
    config.read(config_file)
    return True

# Setup client
async def setup_client():
    if not create_config():
        return None
    
    # Get credentials from config file
    api_id = config['Telegram']['api_id']
    api_hash = config['Telegram']['api_hash']
    phone = config['Telegram']['phone']
    session_name = config['Telegram']['session_name']
    
    # Check if credentials are properly set
    if api_id == 'YOUR_API_ID' or api_hash == 'YOUR_API_HASH':
        print("Please edit the config.ini file with your API credentials from https://my.telegram.org")
        return None
    
    # Create client
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start(phone)
    print("Client successfully connected!")
    return client

# Get list of dialogs (private chats, groups, and supergroups only - no channels or bots)
async def get_dialogs(client):
    result = await client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=100,
        hash=0
    ))
    
    dialogs = result.dialogs
    filtered_dialogs = []
    
    print("\nAvailable chats and groups (no channels or bots):")
    dialog_count = 0
    
    for i, dialog in enumerate(dialogs):
        try:
            entity = await client.get_entity(dialog.peer)
            
            # Check if entity is a broadcast channel
            is_broadcast_channel = isinstance(entity, Channel) and entity.broadcast
            
            # Check if entity is a bot
            is_bot = isinstance(entity, User) and entity.bot
            
            # Include only private chats, groups, and supergroups (exclude bots and broadcast channels)
            if not is_broadcast_channel and not is_bot:
                filtered_dialogs.append(dialog)
                title = entity.title if hasattr(entity, 'title') else (
                    f"{entity.first_name} {entity.last_name}" if hasattr(entity, 'last_name') and entity.last_name else 
                    entity.first_name if hasattr(entity, 'first_name') else 
                    "Unknown"
                )
                # Add a tag to identify the type of chat
                chat_type = "Group" if hasattr(entity, 'title') else "Private"
                print(f"{dialog_count}: {title} [{chat_type}]")
                dialog_count += 1
                
        except Exception as e:
            continue
    
    return filtered_dialogs

# Setup message monitoring
async def setup_monitoring(client, dialogs):
    # Ask for group to monitor
    group_index = int(input("\nEnter the number of the chat or group to monitor: "))
    
    try:
        target_dialog = dialogs[group_index]
        target_group = await client.get_entity(target_dialog.peer)
        
        # Get name or title depending on chat type
        if hasattr(target_group, 'title'):
            group_title = target_group.title
        else:
            group_title = f"{target_group.first_name} {target_group.last_name}" if hasattr(target_group, 'last_name') and target_group.last_name else target_group.first_name
        
        # Save selected group to config
        config['Bot']['target_group'] = str(target_group.id)
        with open(config_file, 'w') as f:
            config.write(f)
        
        print(f"Monitoring messages in: {group_title}")
        return target_group.id
    except Exception as e:
        print(f"Error setting up monitoring: {e}")
        return None

# Ask for text to append
def setup_append_text():
    append_text = input("\nEnter text to append to your messages: ")
    config['Bot']['append_text'] = append_text
    with open(config_file, 'w') as f:
        config.write(f)
    print(f"Your messages will be appended with: '{append_text}'")
    return append_text

# Main function
async def main():
    print("Telegram Message Editor Bot")
    print("---------------------------")
    
    # Setup client
    client = await setup_client()
    if not client:
        return
    
    # Check if we have already set up a target group
    target_group_id = config['Bot'].get('target_group')
    append_text = config['Bot'].get('append_text')
    
    # If no target group or user wants to change it
    if not target_group_id or input("Do you want to change the target chat/group? (y/n): ").lower() == 'y':
        dialogs = await get_dialogs(client)
        if not dialogs:
            print("No suitable chats or groups found.")
            return
        target_group_id = await setup_monitoring(client, dialogs)
        if not target_group_id:
            return
    else:
        try:
            target_entity = await client.get_entity(int(target_group_id))
            
            # Get name or title depending on chat type
            if hasattr(target_entity, 'title'):
                entity_name = target_entity.title
            else:
                entity_name = f"{target_entity.first_name} {target_entity.last_name}" if hasattr(target_entity, 'last_name') and target_entity.last_name else target_entity.first_name
                
            print(f"Monitoring messages in: {entity_name}")
        except Exception as e:
            print(f"Error retrieving chat/group info: {e}")
            dialogs = await get_dialogs(client)
            if not dialogs:
                print("No suitable chats or groups found.")
                return
            target_group_id = await setup_monitoring(client, dialogs)
            if not target_group_id:
                return
    
    # If no append text or user wants to change it
    if not append_text or input("Do you want to change the append text? (y/n): ").lower() == 'y':
        append_text = setup_append_text()
    else:
        print(f"Your messages will be appended with: '{append_text}'")
    
    # Register event handler for outgoing messages
    @client.on(events.NewMessage(outgoing=True, chats=int(target_group_id)))
    async def edit_handler(event):
        # Get the message
        message = event.message
        
        # Only edit if the message doesn't already have the append text
        if not message.text.endswith(append_text):
            # Add a short delay to ensure message is sent first
            await asyncio.sleep(0.5)
            # Edit the message with appended text
            await client.edit_message(message, message.text + append_text)
            print(f"Edited message: {message.text}")
    
    print("\nBot is now running. Press Ctrl+C to stop.")
    
    # Keep the script running
    while True:
        await asyncio.sleep(1)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())