import discord
from discord import app_commands
from discord.ext import commands
import requests
from dotenv import load_dotenv
import os
import re

# Load environment variables from .env.example file
load_dotenv('.env.example')

# Retrieve the Discord bot token and channel ID from environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))  # Ensure the channel ID is an integer
VATSIM_API_URL = 'https://data.vatsim.net/v3/vatsim-data.json'
AIRPLANES_LIVE_API_URL = 'http://api.airplanes.live/v2/'

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

# Define the slash command to get ATIS information
@bot.tree.command(name="atis", description="Fetch ATIS information from VATSIM")
@app_commands.describe(icao="The ICAO code of the airport")
async def fetch_atis(interaction: discord.Interaction, icao: str):
    # Fetch data from VATSIM API
    response = requests.get(VATSIM_API_URL)
    
    if response.status_code == 200:
        data = response.json()
        atis_list = data.get('atis', [])
        atis_info = None

        # Search for the requested ICAO code in the ATIS data
        for atis in atis_list:
            if atis['callsign'].startswith(icao.upper()):
                atis_info = atis
                break

        if atis_info:
            atis_text = "\n".join(atis_info['text_atis'])
            # Create an embed with the ATIS information
            embed = discord.Embed(title=f"ATIS for {icao.upper()}", color=0x1e90ff)
            embed.add_field(name="ATIS Information", value=atis_text, inline=False)
            embed.add_field(name="Frequency", value=atis_info['frequency'], inline=True)
            embed.add_field(name="ATIS Code", value=atis_info.get('atis_code', 'N/A'), inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No ATIS data available for {icao.upper()}.")
    else:
        print(f"Error fetching VATSIM data: {response.text}")  # Log error details
        await interaction.response.send_message(f"Error fetching VATSIM data: {response.status_code}")

# Define the slash command to get METAR and TAF information
@bot.tree.command(name="weather", description="Fetch METAR and TAF information from VATSIM")
@app_commands.describe(icao="The ICAO code of the airport")
async def fetch_metar(interaction: discord.Interaction, icao: str):
    # Fetch METAR data from VATSIM METAR API
    metar_url = f"https://metar.vatsim.net/{icao}"
    print(f"Fetching METAR data from: {metar_url}")  # Log the URL
    response = requests.get(metar_url, headers={'Accept': 'text/plain'})
    
    if response.status_code == 200:
        metar_data = response.text.strip()
        decoded_metar = decode_metar(metar_data)
        
        # Create an embed with the METAR information
        embed = discord.Embed(title=f"METAR for {icao.upper()} observation at {decoded_metar['observation_time']}", color=0x1e90ff)
        embed.add_field(name="Raw METAR", value=f"`{metar_data}`", inline=False)
        embed.add_field(name="Decoded METAR", value=decoded_metar['decoded'], inline=False)
        
        # Fetch TAF data
        taf_url = f"https://metar.vatsim.net/{icao}?taf"
        taf_response = requests.get(taf_url, headers={'Accept': 'text/plain'})
        if taf_response.status_code == 200:
            taf_data = taf_response.text.strip()
            embed.add_field(name="TAF", value=f"`{taf_data}`", inline=False)
        else:
            embed.add_field(name="TAF", value="No TAF data available.", inline=False)
        
        await interaction.response.send_message(embed=embed)
    else:
        print(f"Error fetching METAR data: {response.text}")  # Log error details
        await interaction.response.send_message(f"Error fetching METAR data: {response.status_code}")

# Define the slash command to get online pilots information
@bot.tree.command(name="pilots", description="Fetch online pilots information from VATSIM")
async def fetch_pilots(interaction: discord.Interaction):
    # Fetch data from VATSIM API
    response = requests.get(VATSIM_API_URL)
    
    if response.status_code == 200):
        data = response.json()
        pilots_list = data.get('pilots', [])

        if pilots_list:
            pilots_info = []
            for pilot in pilots_list[:10]:  # Limiting to 10 pilots for simplicity
                pilots_info.append(
                    f"**{pilot['callsign']}** | {pilot['name']}\n"
                    f"Aircraft: {pilot['flight_plan']['aircraft_faa'] if pilot.get('flight_plan') else 'N/A'}\n"
                    f"Altitude: {pilot['altitude']} ft | Ground Speed: {pilot['groundspeed']} kts\n"
                    f"Location: {pilot['latitude']}, {pilot['longitude']}\n"
                )
            pilots_info_str = "\n".join(pilots_info)
            embed = discord.Embed(title="Online Pilots", description=pilots_info_str, color=0x1e90ff)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No pilots currently online.")
    else:
        print(f"Error fetching pilots data: {response.text}")  # Log error details
        await interaction.response.send_message(f"Error fetching pilots data: {response.status_code}")

# Define the slash command to get online controllers information
@bot.tree.command(name="controllers", description="Fetch online controllers information from VATSIM")
async def fetch_controllers(interaction: discord.Interaction):
    # Fetch data from VATSIM API
    response = requests.get(VATSIM_API_URL)
    
    if response.status_code == 200):
        data = response.json()
        controllers_list = data.get('controllers', [])

        if controllers_list:
            controllers_info = []
            for controller in controllers_list[:10]:  # Limiting to 10 controllers for simplicity
                controllers_info.append(
                    f"**{controller['callsign']}** | {controller['name']}\n"
                    f"Frequency: {controller['frequency']}\n"
                    f"Position: {controller['facility']}\n"
                )
            controllers_info_str = "\n".join(controllers_info)
            embed = discord.Embed(title="Online Controllers", description=controllers_info_str, color=0x1e90ff)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No controllers currently online.")
    else:
        print(f"Error fetching controllers data: {response.text}")  # Log error details
        await interaction.response.send_message(f"Error fetching controllers data: {response.status_code}")

# Define the slash command to get VATSIM server information
@bot.tree.command(name="servers", description="Fetch VATSIM server information")
async def fetch_servers(interaction: discord.Interaction):
    # Fetch data from VATSIM API
    response = requests.get(VATSIM_API_URL)
    
    if response.status_code == 200):
        data = response.json()
        servers_list = data.get('servers', [])

        if servers_list:
            servers_info = []
            for server in servers_list:
                servers_info.append(
                    f"**{server['name']}** ({server['ident']})\n"
                    f"Location: {server['location']}\n"
                    f"Hostname/IP: {server['hostname_or_ip']}\n"
                )
            servers_info_str = "\n".join(servers_info)
            embed = discord.Embed(title="VATSIM Servers", description=servers_info_str, color=0x1e90ff)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No servers currently available.")
    else:
        print(f"Error fetching servers data: {response.text}")  # Log error details
        await interaction.response.send_message(f"Error fetching servers data: {response.status_code}")

# Define the slash command to search for a callsign
@bot.tree.command(name="search", description="Search for a specific callsign on VATSIM")
@app_commands.describe(callsign="The callsign to search for")
async def search_callsign(interaction: discord.Interaction, callsign: str):
    # Fetch data from VATSIM API
    response = requests.get(VATSIM_API_URL)
    
    if response.status_code == 200):
        data = response.json()
        callsign_upper = callsign.upper()
        
        # Search in pilots
        pilot_info = next((pilot for pilot in data.get('pilots', []) if pilot['callsign'].upper() == callsign_upper), None)
        controller_info = next((controller for controller in data.get('controllers', []) if controller['callsign'].upper() == callsign_upper), None)
        atis_info = next((atis for atis in data.get('atis', []) if atis['callsign'].upper() == callsign_upper), None)

        if pilot_info or controller_info or atis_info:
            embed = discord.Embed(title=f"Information for {callsign_upper}", color=0x1e90ff)

            if pilot_info:
                embed.add_field(
                    name="Pilot",
                    value=(
                        f"**Name**: {pilot_info['name']}\n"
                        f"**Callsign**: {pilot_info['callsign']}\n"
                        f"**Aircraft**: {pilot_info['flight_plan']['aircraft_faa'] if pilot_info.get('flight_plan') else 'N/A'}\n"
                        f"**Altitude**: {pilot_info['altitude']} ft\n"
                        f"**Ground Speed**: {pilot_info['groundspeed']} kts\n"
                        f"**Location**: {pilot_info['latitude']}, {pilot_info['longitude']}\n"
                        f"**Logon Time**: {pilot_info['logon_time']}\n"
                    ),
                    inline=False
                )
            
            if controller_info:
                embed.add_field(
                    name="Controller",
                    value=(
                        f"**Name**: {controller_info['name']}\n"
                        f"**Callsign**: {controller_info['callsign']}\n"
                        f"**Frequency**: {controller_info['frequency']}\n"
                        f"**Position**: {controller_info['facility']}\n"
                        f"**Logon Time**: {controller_info['logon_time']}\n"
                    ),
                    inline=False
                )

            if atis_info:
                atis_text = "\n".join(atis_info['text_atis'])
                embed.add_field(
                    name="ATIS",
                    value=(
                        f"**Callsign**: {atis_info['callsign']}\n"
                        f"**Frequency**: {atis_info['frequency']}\n"
                        f"**ATIS Code**: {atis_info.get('atis_code', 'N/A')}\n"
                        f"**ATIS Information**: {atis_text}\n"
                    ),
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No data found for the callsign '{callsign_upper}'.")
    else:
        print(f"Error fetching VATSIM data: {response.text}")  # Log error details
        await interaction.response.send_message(f"Error fetching VATSIM data: {response.status_code}")

# Define the slash command to search for real-life aircraft by callsign using Airplanes.live API
@bot.tree.command(name="irl_search", description="Search for a specific callsign using Airplanes.live API")
@app_commands.describe(callsign="The callsign to search for")
async def irl_search(interaction: discord.Interaction, callsign: str):
    # Fetch data from Airplanes.live API
    url = f"{AIRPLANES_LIVE_API_URL}callsign/{callsign.upper()}"
    response = requests.get(url)
    
    if response.status_code == 200):
        data = response.json()
        aircraft = data.get('ac', [])
        
        if aircraft:
            aircraft_info = aircraft[0]  # Assuming we take the first match
            last_position = aircraft_info.get('lastPosition', {})
            embed = discord.Embed(
                title=f"IRL Information for {callsign.upper()}",
                description=(
                    f"**Hex Code**: {aircraft_info.get('hex', 'N/A')}\n"
                    f"**Type**: {aircraft_info.get('t', 'N/A')} ({aircraft_info.get('desc', 'N/A')})\n"
                    f"**Registration**: {aircraft_info.get('r', 'N/A')}\n"
                    f"**Altitude**: {aircraft_info.get('alt_baro', 'N/A')} ft\n"
                    f"**Ground Speed**: {aircraft_info.get('gs', 'N/A')} kts\n"
                    f"**Track**: {aircraft_info.get('track', 'N/A')}°\n"
                    f"**Squawk**: {aircraft_info.get('squawk', 'N/A')}\n"
                    f"**Latitude**: {last_position.get('lat', 'N/A')}\n"
                    f"**Longitude**: {last_position.get('lon', 'N/A')}\n"
                    f"**Last Seen**: {aircraft_info.get('seen', 'N/A')} seconds ago"
                ),
                color=0x1e90ff
            )
            # Adding tracking link
            tracking_link = f"https://globe.airplanes.live/?icao={aircraft_info.get('hex', '')}"
            embed.add_field(name="Track on Airplanes.live", value=f"[Track here]({tracking_link})")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No aircraft found with callsign '{callsign.upper()}'.")
    else:
        print(f"Error fetching data from Airplanes.live API: {response.text}")  # Log error details
        await interaction.response.send_message(f"Error fetching data from Airplanes.live API: {response.status_code}")

# Function to decode a METAR string into human-readable information
def decode_metar(metar: str) -> dict:
    decoded = []

    # Extracting observation time (first group in METAR)
    observation_time_match = re.search(r'\b(\d{6}Z)\b', metar)
    observation_time = observation_time_match.group(1) if observation_time_match else "Unknown"

    # Parse METAR elements using regex
    wind_re = re.compile(r'(\d{3})(\d{2,3})(G\d{2,3})?KT')
    visibility_re = re.compile(r'(\d{4})')
    temp_dew_re = re.compile(r'(M?\d{2})/(M?\d{2})')
    pressure_re = re.compile(r'(QNH|A)(\d{4})')
    weather_re = re.compile(r'(\+|-|VC)?(MI|PR|BC|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP|HZ|BR|FG|FU|VA|DU|SA|SS|DS)?')
    cloud_re = re.compile(r'(FEW|SCT|BKN|OVC)(\d{3})')

    # Decode wind
    wind = wind_re.search(metar)
    if wind:
        direction, speed, gust = wind.groups()
        wind_text = f"Wind: {direction}° at {speed} KT"
        if gust:
            wind_text += f", gusting to {gust[1:]} KT"
        decoded.append(wind_text)

    # Decode visibility
    visibility = visibility_re.search(metar)
    if visibility:
        visibility_text = f"Visibility: {visibility.group(1)} meters"
        decoded.append(visibility_text)

    # Decode temperature and dew point
    temp_dew = temp_dew_re.search(metar)
    if temp_dew:
        temp, dew = temp_dew.groups()
        temp_text = f"Temperature: {temp.replace('M', '-') if 'M' in temp else temp}°C, Dew Point: {dew.replace('M', '-') if 'M' in dew else dew}°C"
        decoded.append(temp_text)

    # Decode pressure
    pressure = pressure_re.search(metar)
    if pressure:
        unit, value = pressure.groups()
        if unit == 'QNH':
            pressure_text = f"Pressure: {value} hPa"
        else:  # assuming 'A' is used for inHg
            pressure_text = f"Pressure: {value[:2]}.{value[2:]} inHg"
        decoded.append(pressure_text)

    # Decode weather phenomena
    weather = weather_re.search(metar)
    if weather and any(weather.groups()):
        intensity, descriptor, phenomenon = weather.groups()
        weather_text = "Weather: "
        if intensity:
            weather_text += f"{intensity} "
        if descriptor:
            weather_text += f"{descriptor} "
        if phenomenon:
            weather_text += f"{phenomenon}"
        decoded.append(weather_text.strip())

    # Decode cloud cover
    cloud_matches = cloud_re.findall(metar)
    if cloud_matches:
        cloud_text = "Clouds: " + ", ".join([f"{amount} at {int(height) * 100} feet" for amount, height in cloud_matches])
        decoded.append(cloud_text)

    decoded_str = "\n".join(decoded) if decoded else "No significant weather observed."
    return {"decoded": decoded_str, "observation_time": observation_time}

# Run the bot
bot.run(TOKEN)