import discord
from discord.ext import commands

# Configuration
BOT_TOKEN = 'MTE3NjE0NDk3MDUxNjgwMzYxNg.GfO9QX.qbpeeBsCHaKW1jUeKchQ1_ZCnUDZF1SXhOhZQA'
BOT_NAME = 'SCROT'

# Set up Discord bot with command prefix and intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Dictionary to store user-channel mappings for DMs
current_channels = {}

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Connected to servers:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')

# Event handler for processing incoming messages
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if str(bot.user.id) in message.content:  # Convert bot.user.id to string
        if isinstance(message.channel, discord.DMChannel):
            await message.author.send("```Discord\nUse !help to show info on how to use this bot```")
        elif isinstance(message.channel, discord.TextChannel):
            await message.delete()
            await message.channel.send("```Discord\n# Planned: Type /waifu [nsfw] to generate a waifu using https://waifu.pics's API```")

    if isinstance(message.channel, discord.DMChannel):
        await process_dm(message)

    await bot.process_commands(message)

# Function to process direct messages
async def process_dm(message):
    user_id = message.author.id

    if user_id in current_channels:
        channel_id = current_channels[user_id]
        channel = bot.get_channel(channel_id)

        if channel:
            try:
                await channel.send(f"{message.content}")
                print(f"Message sent to channel {channel_id} from DM by {user_id}")
            except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                print(f"Error: Could not send message to channel {channel_id}. {type(e).__name__}: {e}")
        else:
            print(f"Warning: Channel with ID {channel_id} not found.")

# Command to set or disconnect the channel for receiving messages
@bot.command(name='connect')
async def set_channel(ctx, channel_id: str = None):
    user_id = ctx.author.id

    if channel_id.lower() == 'null':
        if user_id in current_channels:
            channel_id = current_channels[user_id]
            channel = bot.get_channel(channel_id)

            if channel:
                del current_channels[user_id]
                await ctx.author.send(f'```Discord\nChannel disconnected. You will no longer transmit messages to {channel.name} (ID: {channel_id})```')
            else:
                await ctx.author.send(f'```Discord\nError: Channel with ID {channel_id} not found.```')
        else:
            await ctx.author.send("```Discord\nYou don't have a channel set.```")
        return

    try:
        channel_id = int(channel_id)
    except ValueError:
        await ctx.author.send("```Discord\nInvalid channel ID. Please provide a valid channel ID or use 'null' to disconnect the channel.```")
        return

    channel = bot.get_channel(channel_id)

    if not channel or channel.guild not in bot.guilds:
        await ctx.author.send("```Discord\nInvalid channel ID or bot is not a member of the server associated with the provided channel ID.```")
        return

    current_channels[user_id] = channel_id
    await ctx.author.send(f'```Discord\nChannel ID set to {channel.name} (ID: {channel_id})```')


# Command to delete a specific message in the set channel
@bot.command(name='delete')
async def delete_specific_message(ctx, message_id: int):
    if ctx.author.id not in current_channels:
        await ctx.send("```Discord\nPlease use !connect <channel_id> to set the channel first.```")
        return

    channel_id = current_channels[ctx.author.id]
    channel = bot.get_channel(channel_id)

    if channel:
        try:
            specific_message = await channel.fetch_message(message_id)
            await specific_message.delete()
            await ctx.send("```Discord\nMessage deleted.```")
        except discord.errors.NotFound:
            await ctx.send("```Discord\nMessage not found.```")
        except discord.errors.Forbidden:
            await ctx.send("```Discord\nMissing permissions to delete the message.```")
    else:
        print(f"Warning: Channel with ID {channel_id} not found.")

# Command to list information about users, channels, or servers
@bot.command(name='list')
async def list_info(ctx, category: str = 'all', target_id: int = None, num_users: int = None):
    try:
        if category.lower() == 'users':
            if target_id:
                target_guild = bot.get_guild(target_id)
                if target_guild:
                    users_list = [f'{member.display_name} ({member.name}#{member.discriminator}) (ID: {member.id})' for member in target_guild.members]

                    if num_users:
                        users_list = users_list[:num_users]

                    await send_long_message(ctx, f'```Discord\nUsers in the server (ID: {target_guild.id}):```', users_list, code_block=True)
                else:
                    await ctx.send(f'```Discord\nServer with ID {target_id} not found.```')
            else:
                await ctx.send('```Discord\nPlease provide a server ID to list users in that server.```')
        elif category.lower() == 'channels':
            if target_id:
                target_guild = bot.get_guild(target_id)
                if target_guild:
                    channels_list = [f'{channel.name} (ID: {channel.id})' for channel in target_guild.channels]
                    await send_long_message(ctx, f'```Discord\nChannels in the server (ID: {target_guild.id}):```', channels_list, code_block=True)
                else:
                    await ctx.send(f'```Discord\nServer with ID {target_id} not found.```')
            else:
                await ctx.send('```Discord\nPlease provide a server ID to list channels in that server.```')
        elif category.lower() == 'servers':
            servers_list = [f'{guild.name} (ID: {guild.id})' for guild in bot.guilds]
            await send_long_message(ctx, '```Discord\nConnected servers:```', servers_list, code_block=True)
        else:
            await ctx.send('```Discord\nInvalid category. Use !list users <server_id>, !list channels <server_id>, !list servers.```')
    except Exception as e:
        print(f"Error: An unexpected error occurred - {type(e).__name__}: {e}")
        await ctx.send("```Discord\nAn unexpected error occurred while processing the command.```")

# Function to send a long message, splitting it into parts if needed
async def send_long_message(ctx, header, items, code_block=False):
    chunks = [items[i:i + 20] for i in range(0, len(items), 20)]
    
    for i, chunk in enumerate(chunks, start=1):
        formatted_chunk = '\n'.join(f'- {item}' for item in chunk)
        
        if len(chunks) > 1:  # Check if there are multiple blocks
            if code_block:
                if i == 1:
                    await ctx.send(f'{header} (Part {i})\n```Discord\n{formatted_chunk}\n```')
                else:
                    await ctx.send(f'(Part {i})\n```Discord\n{formatted_chunk}\n```')
            else:
                if i == 1:
                    await ctx.send(f'{header} (Part {i})\n{formatted_chunk}')
                else:
                    await ctx.send(f'(Part {i})\n{formatted_chunk}')
        else:
            if code_block:
                await ctx.send(f'{header}\n```Discord\n{formatted_chunk}\n```')
            else:
                await ctx.send(f'{header}\n{formatted_chunk}')

# Command to display help messages
@bot.command(name='help')
async def show_help(ctx, subcategory: str = None):
    try:
        if not subcategory:
            help_message = '''```Discord\nHELP PAGE
Here are the available commands:

- !connect <channel_id>: Set the channel to send messages. Use 'null' to disconnect the channel.
- !delete <message_id>: Delete a specific message in the specified channel.
- !list <category> <target_id> [num_users]: List information about users, channels, or servers.
- !help <subcategory>: Show detailed help for a specific subcategory.

For example:
- !connect 123456789: Set the channel to send messages to the channel with ID 123456789.
- !delete 987654321: Delete the message with ID 987654321 in the specified channel.
- !list users 987654321 10: List the first 10 users in the server with ID 987654321.
- !list channels 987654321: List channels in the server with ID 987654321.
- !list servers: List connected servers.
- !help connect: Show detailed help for the connect command.
```'''
            await ctx.send(f'{help_message}')
        elif subcategory.lower() == 'connect':
            detailed_help = '''```Discord\nHELP PAGE
Command: !connect

Description: Set the channel to send messages. Use 'null' to disconnect the channel.

Usage:
- !connect <channel_id>: Set the channel to send messages to the specified channel.
- !connect null: disconnect the channel to stop receiving messages.

Examples:
- !connect 123456789: Set the channel to send messages to the channel with ID 123456789.
- !connect null: disconnect the channel.

Note: If you disconnect the channel, you will no longer transmit messages.
```'''
            await ctx.send(f'{detailed_help}')
        elif subcategory.lower() == 'delete':
            detailed_help = '''```Discord\nHELP PAGE
Command: !delete

Description: Delete a specific message in the specified channel.

Usage:
- !delete <message_id>: Delete the message with the specified ID.

Examples:
- !delete 987654321: Delete the message with ID 987654321 in the specified channel.
```'''
            await ctx.send(f'{detailed_help}')
        elif subcategory.lower() == 'list':
            detailed_help = '''```Discord\nHELP PAGE
Command: !list

Description: List information about users, channels, or servers.

Usage:
- !list users <server_id> [num_users]: List users in the specified server. Optional: specify the number of users to display.
- !list channels <server_id>: List channels in the specified server.
- !list servers: List connected servers.

Examples:
- !list users 987654321 10: List the first 10 users in the server with ID 987654321.
- !list channels 987654321: List channels in the server with ID 987654321.
- !list servers: List connected servers.
```'''
            await ctx.send(f'{detailed_help}')
        else:
            await ctx.send('```Discord\nInvalid subcategory. Use !help to see the list of available commands and subcategories.```')
    except Exception as e:
        print(f"Error: An unexpected error occurred - {type(e).__name__}: {e}")
        await ctx.send("```Discord\nAn unexpected error occurred while processing the command.```")

# Event handler for handling command errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('```Discord\nInvalid command. Use !help to see the list of available commands.```')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Discord\nMissing required arguments. Please check the command usage with !help.```')
    elif isinstance(error, commands.BadArgument):
        await ctx.send('```Discord\nInvalid arguments. Please provide valid arguments.```')
    elif isinstance(error, commands.CommandInvokeError):
        original_error = error.original
        print(f"Error: {type(original_error).__name__}: {original_error}")
        await ctx.send(f'```Discord\nAn error occurred while processing the command: {type(original_error).__name__}.```')
    else:
        print(f"Error: {type(error).__name__}: {error}")
        await ctx.send(f'```Discord\nAn error occurred: {type(error).__name__}.```')

# Run the bot with the provided token
bot.run(BOT_TOKEN)
