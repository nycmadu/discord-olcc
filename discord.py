import discord
import requests
import asyncio

TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
CHANNEL_ID = YOUR_DISCORD_CHANNEL_ID  # Replace with your channel ID
ZNY_FIR = 'ZNY'

client = discord.Client(intents=discord.Intents.default())

async def fetch_vatsim_data():
    url = 'https://data.vatsim.net/v3/vatsim-data.json'
    response = requests.get(url)
    return response.json()

async def get_online_controllers():
    data = await fetch_vatsim_data()
    controllers = data['controllers']
    zny_controllers = [c for c in controllers if ZNY_FIR in c['facility']]
    return zny_controllers

async def notify_new_controllers(channel):
    known_controllers = set()
    while True:
        online_controllers = await get_online_controllers()
        for controller in online_controllers:
            cid = controller['cid']
            if cid not in known_controllers:
                known_controllers.add(cid)
                name = controller['name']
                position = controller['callsign']
                time_online = controller['logon_time']
                await channel.send(f"{name} ({cid}) is online at position {position} since {time_online}")
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await notify_new_controllers(channel)
    else:
        print(f'Channel with ID {CHANNEL_ID} not found.')

client.run(TOKEN)