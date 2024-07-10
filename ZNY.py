import discord
from discord.ext import commands
import requests
import asyncio
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
ZNY_FIR = 'ZNY'

intents = discord.Intents.default()
client = commands.Bot(command_prefix='/', intents=intents)

async def fetch_vatsim_data():
    url = 'https://data.vatsim.net/v3/vatsim-data.json'
    response = requests.get(url)
    return response.json()

async def get_online_entities():
    data = await fetch_vatsim_data()
    controllers = data['controllers']
    pilots = data['pilots']
    return controllers, pilots

async def notify_new_entities(channel):
    known_controllers = set()
    known_pilots = set()
    while True:
        controllers, pilots = await get_online_entities()
        
        # Notify new controllers
        for controller in controllers:
            cid = controller['cid']
            if cid not in known_controllers:
                known_controllers.add(cid)
                name = controller['name']
                position = controller['callsign']
                time_online = controller['logon_time']
                embed = discord.Embed(
                    title=f"New ATC Online: {name} ({cid})",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Position", value=position, inline=True)
                embed.add_field(name="Since", value=time_online, inline=True)
                await channel.send(embed=embed)
        
        # Notify new pilots
        for pilot in pilots:
            cid = pilot['cid']
            if cid not in known_pilots:
                known_pilots.add(cid)
                name = pilot['name']
                callsign = pilot['callsign']
                time_online = pilot['logon_time']
                embed = discord.Embed(
                    title=f"New Pilot Online: {name} ({cid})",
                    color=0x0000ff,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Callsign", value=callsign, inline=True)
                embed.add_field(name="Since", value=time_online, inline=True)
                await channel.send(embed=embed)
        
        await asyncio.sleep(60)  # Update every minute

@client.command()
async def ZNY(ctx):
    controllers, pilots = await get_online_entities()
    zny_controllers = [c for c in controllers if ZNY_FIR in c['callsign']]
    if zny_controllers:
        embed = discord.Embed(
            title="ZNY ARTCC Controllers Online",
            color=0x0000ff,
            timestamp=datetime.utcnow()
        )
        for controller in zny_controllers:
            name = controller['name']
            cid = controller['cid']
            position = controller['callsign']
            time_online = controller['logon_time']
            embed.add_field(name=f"{name} ({cid})", value=f"Position: {position}\nSince: {time_online}", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("No controllers are currently online in the ZNY ARTCC.")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await notify_new_entities(channel)
    else:
        print(f'Channel with ID {CHANNEL_ID} not found.')

client.run(TOKEN)