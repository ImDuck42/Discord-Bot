import discord
from discord.ext import commands
import requests

# Configuration
BOT_TOKEN = 'YOUR_BOT_TOKEN'
BOT_NAME = 'YOUR_BOT_NAME'
YOUR_BOT_OWNER_USER_ID = YOUR_BOT_OWNER_USER_ID     # Replace with the actual bot owner's user ID

# Set up Discord bot with command prefix and intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Dictionary to store user-channel mappings for DMs
current_channels = {}

# Dictionary to store whitelisted user IDs
whitelisted_users = set()

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

    if str(bot.user.id) in message.content:
        if isinstance(message.channel, discord.DMChannel):
            await message.author.send("```Discord\nUse !help to show info on how to use this bot```")
        elif isinstance(message.channel, discord.TextChannel):
            await message.delete()
            await message.channel.send("```Discord\n# Planned: Type /waifu [nsfw] to generate a waifu using https://waifu.pics's API```")

    if isinstance(message.channel, discord.DMChannel):
        await process_dm(message)

    if message.author.id == YOUR_BOT_OWNER_USER_ID:
        # Allow the bot owner to use the bot
        await bot.process_commands(message)
    elif message.content.startswith('!whitelist'):
        # Allow processing of !whitelist command for everyone
        await bot.process_commands(message)
    elif message.author.id not in whitelisted_users:
        # Show "no permission" message for non-whitelisted users
        await message.author.send("```Discord\nYou have no permission to use this Bot.```")
    else:
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

# Command to print contents of a URL into a code block
@bot.command(name='planed')
async def print_planed(ctx):
    try:
        url = 'https://raw.githubusercontent.com/ImDuck42/Discord-Bot/main/Planed.txt'
        response = requests.get(url)

        if response.status_code == 200:
            planed_content = response.text
            await ctx.send(f'```plaintext\n{planed_content}\n```')
        else:
            await ctx.send(f'```Discord\nError: Unable to fetch content from {url}. Status code: {response.status_code}\n```')
    except Exception as e:
        print(f"Error: An unexpected error occurred - {type(e).__name__}: {e}")
        await ctx.send("```Discord\nAn unexpected error occurred while processing the command.```")

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

# Command to manage bot whitelisting (Bot owner only)
@bot.command(name='whitelist')
async def whitelist_command(ctx, action: str, user_id: int = None):
    if ctx.author.id != YOUR_BOT_OWNER_USER_ID:
        await ctx.send("```Discord\nYou have no permission to use this command.```")
        return

    if action.lower() == 'add':
        if user_id:
            user = await bot.fetch_user(user_id)
            whitelisted_users.add(user_id)
            await ctx.send(f"```Discord\nUser with ID {user_id} ({user.display_name} [{user.name}#{user.discriminator}]) added to the whitelist.```")
        else:
            await ctx.send("```Discord\nPlease provide a user ID to add to the whitelist.```")
    elif action.lower() == 'remove':
        if user_id:
            user = await bot.fetch_user(user_id)
            whitelisted_users.discard(user_id)
            await ctx.send(f"```Discord\nUser with ID {user_id} ({user.display_name} [{user.name}#{user.discriminator}]) removed from the whitelist.```")
        else:
            await ctx.send("```Discord\nPlease provide a user ID to remove from the whitelist.```")
    elif action.lower() == 'list':
        if whitelisted_users:
            users_formatted = []
            for user_id in whitelisted_users:
                user = await bot.fetch_user(user_id)
                users_formatted.append(f'{user.display_name} ({user.name}#{user.discriminator}) (ID: {user.id})')

            user_list_message = '```Discord\nWhitelisted Users:\n```\n'
            chunks = [users_formatted[i:i + 10] for i in range(0, len(users_formatted), 10)]

            for i, chunk in enumerate(chunks, start=1):
                formatted_chunk = '\n'.join(f'- {user}' for user in chunk)
                user_list_message += f'```Discord\n{formatted_chunk}\n```\n'

                if len(chunks) > 1:
                    user_list_message += f'(Part {i})\n'

        else:
            user_list_message = '```Discord\nWhitelisted Users: (none)```'

        await ctx.send(user_list_message)
    else:
        await ctx.send("```Discord\nInvalid action. Use 'add', 'remove', or 'list'.```")

# Function to send a long message, splitting it into parts if needed
async def send_long_message(ctx, header, items, code_block=False):
    if not items:
        await ctx.send(f'{header}\n```Discord\nNo items to display.```')
        return

    chunks = [items[i:i + 20] for i in range(0, len(items), 20)]

    for i, chunk in enumerate(chunks, start=1):
        formatted_chunk = '\n'.join(f'- {item}' for item in chunk)

        if len(chunks) > 1:
            if code_block:
                if i == 1:
                    await ctx.send(f'{header} (Part {i})```Discord\n{formatted_chunk}\n```')
                else:
                    await ctx.send(f'(Part {i})```Discord\n{formatted_chunk}\n```')
            else:
                if i == 1:
                    await ctx.send(f'{header} (Part {i})\n{formatted_chunk}')
                else:
                    await ctx.send(f'(Part {i})\n{formatted_chunk}')
        else:
            if code_block:
                await ctx.send(f'{header}```Discord\n{formatted_chunk}\n```')
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
- !planed: Prints contents of https://raw.githubusercontent.com/ImDuck42/Discord-Bot/main/Planed.txt in a code block.
- !whitelist <add/remove/list>: Manage bot whitelisting. (Bot owner only)
- !help <subcategory>: Show detailed help for a specific subcategory.

For example:
- !connect 123456789: Set the channel to send messages to the channel with ID 123456789.
- !delete 987654321: Delete the message with ID 987654321 in the specified channel.
- !list users 987654321 10: List the first 10 users in the server with ID 987654321.
- !list channels 987654321: List channels in the server with ID 987654321.
- !list servers: List connected servers.
- !planed: Prints contents of Planed.txt.
- !whitelist add 123456789: Add user with ID 123456789 to the whitelist. (Bot owner only)
- !whitelist remove 123456789: Remove user with ID 123456789 from the whitelist. (Bot owner only)
- !whitelist list: List whitelisted users. (Bot owner only)
- !help connect: Show detailed help for the connect command.
```'''
            await ctx.send(f'{help_message}')
        elif subcategory.lower() == 'connect':
            detailed_help = '''```Discord\nHELP PAGE
Command: !connect

Description: Set the channel to send messages. Use 'null' to disconnect the channel.

Usage:
- !connect <channel_id>: Set the channel to send messages to the specified channel.
- !connect null: Disconnect the channel to stop receiving messages.

Examples:
- !connect 123456789: Set the channel to send messages to the channel with ID 123456789.
- !connect null: Disconnect the channel.

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
        elif subcategory.lower() == 'planed':
            detailed_help = '''```Discord\nHELP PAGE
Command: !planed

Description: Prints contents of Planed.txt in a code block.

Usage:
- !planed

Note: This command fetches content from https://raw.githubusercontent.com/ImDuck42/Discord-Bot/main/Planed.txt.
```'''
            await ctx.send(f'{detailed_help}')
        elif subcategory.lower() == 'whitelist':
            detailed_help = '''```Discord\nHELP PAGE
Command: !whitelist

Description: Manage bot whitelisting. (Bot owner only)

Usage:
- !whitelist add <user_id>: Add user with ID to the whitelist.
- !whitelist remove <user_id>: Remove user with ID from the whitelist.
- !whitelist list: List whitelisted users.

Examples:
- !whitelist add 123456789: Add user with ID 123456789 to the whitelist. (Bot owner only)
- !whitelist remove 123456789: Remove user with ID 123456789 from the whitelist. (Bot owner only)
- !whitelist list: List whitelisted users. (Bot owner only)
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
