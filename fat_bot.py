import asyncio
import json
import os
from os import path
import discord
from discord.ext import commands, tasks
import configs
import youtube_scraper


intents = discord.Intents().default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix=".", intents=intents)

# Channel IDs
main_channel_id = 814202376068137013
test_channel_id = 814971629712572457

# Channel Names
vc_name = "General"

# User IDs
tiran_id = 477270012592259082
jamez_id = 477249470732697601
backup_id = 493043

# Global Variables
alert = False
alarm_control = False
absent_members = []
alert_counter = 0

# DIRECTORIES
image_dir = path.join(path.dirname(__file__), 'images')


# DESCRIPTIONS
with open("command_descriptions.json", "r") as file:
    descriptions = json.load(file)


# EVENT LISTENERS
@bot.event
async def on_ready():
    scraper = youtube_scraper.YoutubeScraper()
    latest_vid = scraper.get_video_url("Culinary Cam", latest=True)
    act = discord.Streaming(name="Being fat!",
                            url=latest_vid[0])
    await bot.change_presence(activity=act, status=discord.Status.online)
    print("Bot is ready!")


@bot.event
async def on_message(message):
    await bot.process_commands(message)  # Needs to be called because overriding the default on_message removes it!

    words = message.content.split()

    emoji_limit = 10
    banned_emojis = []#["twasok", "beegbrain", "WILDN", "femstobal"]

    member_blacklist = []#[jamez_id, backup_id]

    if message.author.id not in member_blacklist:
        try:
            if len(words) <= 2 and in_list(words[0], message.guild.emojis, use_id=False) and words[0] not in banned_emojis:
                await message.channel.purge(limit=1)
                sender_name = message.author.display_name
                sender_url = message.author.avatar_url
                image = get_item(words[0], message.guild.emojis, use_id=False).url
                main_embed = discord.Embed(color=discord.Color.from_rgb(54, 57, 63))
                main_embed.set_author(name=sender_name, icon_url=sender_url)
                main_embed.set_image(url=image)
                await message.channel.send(embed=main_embed)
                print(f"{message.author.display_name} sent the emoji {words[0]}!")
                if len(words) == 2:
                    if 1 < int(words[1]) < emoji_limit + 1:
                        spam_embed = discord.Embed(color=main_embed.colour)
                        spam_embed.set_image(url=main_embed.image.url)
                        for num in range(int(words[1])):
                            await message.channel.send(embed=spam_embed)
        except (IndexError, AttributeError):
            pass
    else:
        try:
            content = message.content
            await message.delete()
            with open("james.txt", "a") as stuff:
                stuff.write(content + "\n")
        except discord.errors.Forbidden:
            pass


@bot.event
async def on_voice_state_update(member, before, after):
    if not before.channel and after.channel:
        print(f"{member.display_name} joined voice channel!")
        joined_members = after.channel.members
        global alert
        global alert_counter
        global absent_members
        if len(joined_members) < 2:
            alert = True
            absent_members = []
            guild_members = bot.guilds[0].members
            for mem in guild_members:
                if mem.id != member.id and not mem.id == bot.user.id:
                    absent_members.append(mem)
        else:
            alert = False
            alert_counter = 0
        print(f"Alert: {alert}")
    elif before.channel and not after.channel:
        alert = False
        print(f"{member.display_name} left voice channel!")


@bot.event
async def on_command_error(ctx, error):
    error = getattr(error, "original", error)
    print(f"Error occurred!: {error} ... Type!: {type(error)}")
    if isinstance(error, commands.CheckFailure):
        await ctx.send("**NICE TRY BUSTER!**")
        print("Member warned!")
    if isinstance(error, commands.ExtensionAlreadyLoaded):
        await ctx.send("Extension already loaded!")
    elif isinstance(error, commands.ExtensionFailed):
        await ctx.send("Extension failed to load!")
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send("Extension doesn't exist!")
    elif isinstance(error, commands.ExtensionNotLoaded):
        await ctx.send("Extension isn't loaded!")
    elif isinstance(error, commands.NotOwner):
        await ctx.send("You ain't the owner, so you can't use this!")


# CHECKS
def is_not_james(ctx):
    return ctx.message.author.id != jamez_id


def is_not_dylan(ctx):
    return ctx.message.author.id != tiran_id


def is_not_second_acc(ctx):
    return ctx.message.author.id != backup_id


# USER COMMANDS
@commands.check(is_not_james)
@commands.check(is_not_second_acc)
@bot.command(help=descriptions["clear"])
async def clear(ctx, num=1):
    if not isinstance(ctx, discord.TextChannel):
        await ctx.channel.purge(limit=num + 1)
        print(f"{num} messages cleared from {ctx.channel.name}!")
    else:
        await ctx.purge(limit=num + 1)
        print(f"{num} messages cleared from {ctx.name}!")


@bot.command(aliases=["moji", "em", "m"], help=descriptions["send_emoji"])
async def send_emoji(ctx, emoji_name: str, count=1):
    await ctx.channel.purge(limit=1)
    sender_name = ctx.author.display_name
    sender_url = ctx.author.avatar_url
    image = get_item(emoji_name, ctx.guild.emojis, use_id=False).url
    main_embed = discord.Embed(color=discord.Color.from_rgb(44, 47, 51))
    main_embed.set_author(name=sender_name, icon_url=sender_url)
    main_embed.set_image(url=image)
    await ctx.send(embed=main_embed)
    print(f"{ctx.author.display_name} sent the emoji {emoji_name}!")
    if 1 < count < 11:
        spam_embed = discord.Embed(color=main_embed.colour)
        spam_embed.set_image(url=main_embed.image.url)
        for num in range(count):
            await ctx.send(embed=spam_embed)


@bot.command(help=descriptions["pog"])
@commands.is_owner()
async def pog(ctx, num=1):
    await ctx.channel.purge(limit=1)
    for nm in range(num):
        with open("pog.png", "rb") as img:
            await ctx.send(file=discord.File(img, "pog.png"))


@bot.command(help=descriptions["dm"])
async def dm(ctx, user: str, message: str = None):
    await ctx.channel.purge(limit=1)
    member_id = get_item(user, ctx.guild.members, use_id=False).id
    if message:
        await ctx.guild.get_member(member_id).send(message)
    else:
        await ctx.guild.get_member(member_id).send("Hey sugar. You. Me. Skin to skin. Love that feeling")


@bot.command(help=descriptions["switch_alarm"], aliases=["alarm"])
async def switch_alarm(ctx):
    global alarm_control
    alarm_control = not alarm_control
    if alarm_control:
        await ctx.send("The call alarm is now on!")
    else:
        await ctx.send("The call alarm is now off!")


@bot.command(help=descriptions["test"])
async def test(message):
    print(message)


@commands.is_owner()
@bot.command(aliases=["lo"])
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f"{extension} loaded!")
    print(f"{extension} loaded!")


@commands.is_owner()
@bot.command(aliases=["ulo"])
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send(f"{extension} unloaded!")
    print(f"{extension} unloaded!")


# TASKS
@tasks.loop(seconds=4)
async def alert_members():
    if alert and alarm_control:
        server = bot.guilds[0]
        channel = server.get_channel(main_channel_id)
        call_emoji = str(get_item("slay", server.emojis, False))
        sad_emoji = str(get_item("creep", server.emojis, False))
        absentees = ""
        counter = 1
        for member in absent_members:
            if counter < len(absent_members):
                absentees += member.mention + " and "
            else:
                absentees += member.mention
            counter += 1
        global alert_counter
        if alert_counter < 10:
            await channel.send(f"Ring ring ring, {absentees}, Fat Phone calling! {call_emoji}")
            alert_counter += 1
        else:
            await channel.send(f"please, {absentees}, join. i'm lonely {sad_emoji}")
        await asyncio.sleep(2)
        await channel.purge(limit=1)


@tasks.loop(seconds=4)
async def auto_leave():
    server = bot.guilds[0]
    voice_channel = discord.utils.get(server.voice_channels, name=vc_name)
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice and voice.is_connected():
        if len(voice_channel.members) == 1:
            await voice.disconnect()
    else:
        pass


@auto_leave.before_loop
async def before_auto_leave():
    print('waiting...')
    await bot.wait_until_ready()


# UTILITY FUNCTIONS
def get_item(item_identifier, item_list, use_id=True):
    for item in item_list:
        if use_id:
            if item.id == item_identifier:
                return item
        else:
            if item.name.lower() == item_identifier.lower():
                return item
    return None


def in_list(item_identifier, item_list, use_id=True):
    for item in item_list:
        if use_id:
            if item.id == item_identifier:
                return True
        else:
            if item.name.lower() == item_identifier.lower():
                return True
    return False


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

alert_members.start()
auto_leave.start()
bot.run(configs.token)
