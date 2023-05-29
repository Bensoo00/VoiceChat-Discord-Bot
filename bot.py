import discord
import sqlite3
from discord.ext import commands
from datetime import datetime
from datetime import timedelta

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

DATABASE = 'voice_data.db'

# Create the database and table if they don't exist
def setup_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Drop the existing table if it exists
    c.execute('DROP TABLE IF EXISTS voice_data')

    # Create the table with the correct column structure
    c.execute('CREATE TABLE voice_data (user_id TEXT PRIMARY KEY, total_time INTEGER DEFAULT 0, session_start TEXT DEFAULT "")')

    conn.commit()
    conn.close()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    setup_database()

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        if before.channel is not None:
            await update_voice_time(member, before.channel)
        if after.channel is not None:
            await update_voice_time(member, after.channel)

async def update_voice_time(member, channel):
    if channel.type == discord.ChannelType.voice:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute('SELECT total_time, session_start FROM voice_data WHERE user_id = ?', (str(member.id),))
        result = c.fetchone()

        if result is not None:
            total_time, session_start = result
        else:
            total_time = 0
            session_start = ""

        if channel.id not in bot.voice_data:
            bot.voice_data[channel.id] = {}

        if member.id in bot.voice_data[channel.id]:
            start_time = bot.voice_data[channel.id][member.id]['start_time']
            total_time += int((datetime.now() - start_time).total_seconds())
            del bot.voice_data[channel.id][member.id]

        if member.voice is not None:
            bot.voice_data[channel.id][member.id] = {'start_time': datetime.now(), 'session_start': session_start or str(datetime.now())}

        c.execute('INSERT OR REPLACE INTO voice_data (user_id, total_time, session_start) VALUES (?, ?, ?)', (str(member.id), total_time, session_start or ""))
        conn.commit()
        conn.close()


@bot.command(name='voice_time')
async def voice_time(ctx):
    member = ctx.author
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('SELECT total_time FROM voice_data WHERE user_id = ?', (str(member.id),))
    result = c.fetchone()

    if result is not None:
        total_time = result[0]
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60
        seconds = total_time % 60

        await ctx.send(f'{member.mention}, your total voice chat time is: {hours} hours, {minutes} minutes, {seconds} seconds.')
    else:
        await ctx.send(f'{member.mention}, you have no recorded voice chat time.')

    conn.close()

bot.voice_data = {}
bot.run('MTA5OTQ5Nzc2Nzg2MjI4MDE5Mg.G8nvYc.Gs0y81iYbOReVybCFgemB_gpwr5puRc3CZxgP4')
