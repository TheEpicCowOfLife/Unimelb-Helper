print("cans omeone hear me")
sys.stdout.flush()

import discord
import re
import requests
import os
TOKEN = os.environ.get('UNIMELB_HELPER_TOKEN')
client = discord.Client()

command_prefix = "?"

subject_code_regex = r"^[a-zA-Z]{4}[0-9]{5}$"
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # make sure the command is meant for our bot.
    if message.content.startswith(command_prefix):
        command = message.content[len(command_prefix):].split(" ")

        # make sure there is even a command in the first place
        if len(command) == 0:
            return        
    else:
        return

    # command is now a list of strings...

    errors = []
    channel = message.channel
    if command[0] == "hello":
        msg = 'Hello {0.author.mention}'.format(message)
        await channel.send(msg)
        # await client.send(message.channel, msg)

    elif command[0] == "subject":   
        
        if len(command) != 2:
            msg = f"{message.author.mention} Please use the command as follows: '{command_prefix}subject ABCD12345' to get more information about subject ABCD1234"
        else:
            command[1] = command[1].lower()
            if not re.match(subject_code_regex,command[1]):
                msg = f"{message.author.mention} '{command[1]}' is an invalid subject code. Subject codes are of the form 'ABCD12345'. Case insensitive."
            else:
                urls = []
                handbook_url = f"https://handbook.unimelb.edu.au/2021/subjects/{command[1]}"
                r = requests.get(handbook_url)
                if (r.status_code == 200):
                    urls.append(handbook_url)
                
                studentvip_url = f"https://studentvip.com.au/unimelb/subjects/{command[1]}"
                r = requests.get(studentvip_url)
                if (r.status_code == 200):
                    urls.append(studentvip_url)

                if len(urls) == 0:
                    msg = f"{message.author.mention} Subject code '{command[1]}' doesn't exist"
                else:
                    msg = "\n".join(urls)
        await channel.send(msg)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)