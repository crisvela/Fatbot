import asyncio

from discord.ext import commands
from discord.ext import tasks
import discord
import aiohttp
import os
import youtube_dl
import youtube_scraper
import cogs.quickpoll as quickpoll
from fat_bot import is_not_james
from fat_bot import is_not_dylan


# Channel IDs
main_channel_id = 814202376068137013
test_channel_id = 814971629712572457


class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emb_color = discord.Color.from_rgb(44, 47, 51)
        self.scraper = youtube_scraper.YoutubeScraper()
        self.poller = quickpoll.QuickPoll
        self.queue = []
        self.auto_play = True
        self.is_not_playing.start()
        self.last_channel = None
        self.current_caller = None
        self.current_song = None
        self.skipping = False

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'match_title': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    @commands.command()
    async def tstt(self, ctx):
        await ctx.send("Tstted!")
        print("Tstted!")

    @commands.command(aliases=['l'])
    async def lyrics(self, ctx, artist, *, title):
        title = title.replace("\"", "").title()
        print(f"Getting lyrics for \"{title}\" by {artist}!")
        async with aiohttp.ClientSession() as session:
            print(f"In session!: https://api.lyrics.ovh/v1/{artist}/{title}")
            async with session.get(f"https://api.lyrics.ovh/v1/{artist}/{title}") as response:
                print("Getting response!")
                try:
                    data = await response.json()
                except aiohttp.ContentTypeError:
                    await ctx.send("Song not found! Please enter correct Artist and Song title")
                    await session.close()
                lyric = data['lyrics']
                lyric = lyric.replace("\n\n\n\n", "\n").replace("\n\n\n", "\n").replace("\n\n", "\n")
                print(len(lyric))
                if len(lyric) > 2048:
                    step = 2048
                    offset = 0
                    last_i = None
                    for i in range(0, len(lyric), step):
                        last_i = i
                    for i in range(0, len(lyric), step):
                        curr_pos = i - offset
                        if i == last_i and curr_pos <= (len(lyric) - step):
                            print("Last 2 embeds!")
                            last_end = lyric[0: curr_pos + step].rfind("\n")
                            lyric_sect = lyric[curr_pos: last_end]
                            offset += curr_pos + step - last_end
                            emb = discord.Embed(title=f"{title}", description=f"{lyric_sect}", color=self.emb_color)
                            await ctx.send(embed=emb)
                            curr_pos = i + step - offset
                            lyric_sect = lyric[curr_pos:]
                        elif i == last_i:
                            lyric_sect = lyric[curr_pos:]
                        elif lyric[curr_pos + step] == "\n":
                            lyric_sect = lyric[curr_pos: curr_pos + step]
                        else:
                            last_end = lyric[0: curr_pos + step].rfind("\n")
                            lyric_sect = lyric[curr_pos: last_end]
                            offset += curr_pos + step - last_end
                        if i == 0:
                            emb = discord.Embed(title=f"{title}", description=f"{lyric_sect}", color=self.emb_color)
                        else:
                            emb = discord.Embed(description=f"{lyric_sect}", color=self.emb_color)
                        await ctx.send(embed=emb)
                else:
                    emb = discord.Embed(title=f"{title}", description=f"{lyric}", color=self.emb_color)
                    await ctx.send(embed=emb)
                await session.close()

    @commands.command()
    async def play(self, ctx, *, title):
        song_there = os.path.isfile("song.mp3")
        try:
            if not self.queue:
                if song_there:
                    os.remove("song.mp3")
        except PermissionError:
            await ctx.send("Wait for the current song to end or use the 'stop' command!")
            return

        song_details = None
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            if isinstance(title, list):
                song_details = [self.scraper.base + title[1], title[0]]
            else:
                song_details = self.scraper.get_video_url(query=title)
            ydl.download([song_details[0]])
            self.current_song = song_details[0]

        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            await ctx.send("Wait for the current song to end or use the 'stop' command!")
            return

        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, "song.mp3")

        await ctx.send(f"**PLAYING {song_details[1]}:** {song_details[0]}")

        voice_channel = discord.utils.get(ctx.guild.voice_channels, name='fat-phone')
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            pass
        else:
            voice = await voice_channel.connect()

        try:
            if self.skipping:
                self.current_caller = self.queue[0][1]
            else:
                self.current_caller = ctx.author.id
        except AttributeError:
            self.current_caller = self.queue[0][1]
        print(ctx.guild.get_member(self.current_caller).display_name + " is playing a song!")

        voice.play(discord.FFmpegPCMAudio("song.mp3"))

    @commands.command()
    async def add_playlist(self, ctx, url):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            for song in info["entries"]:
                self.queue.append([[song["title"], song["id"]], ctx.author.id])
        await ctx.send(f"**Added {url} to the queue!**")

    @commands.command()
    async def add(self, ctx, *, title):
        self.queue.append([title, ctx.author.id])
        await ctx.send(f"**{title}** was added to the queue!")

    @commands.command(aliases=["ls"])
    async def queue(self, ctx, clear="Not"):
        if clear.lower() == "force":
            if ctx.author.id == 387334819232874498:
                self.queue = []
                await ctx.send("Queue cleared!")
            else:
                await ctx.send("**NICE TRY BUSTER!** You ain't the owner")
        elif clear.lower() == "clear":
            index = len(self.queue) - 1
            for i in range(index + 1):
                if self.queue[index][1] == ctx.author.id:
                    self.queue.pop(index)
                index -= 1
            await ctx.send(ctx.guild.get_member(ctx.author.id).display_name + " cleared their songs!")
        else:
            try:
                songs = ""
                counter = 1
                for song in self.queue:
                    if isinstance(song[0], list):
                        songs += str(song[0][0] + f" - {ctx.guild.get_member(song[1]).display_name}" +
                                     f" - {str(counter)}" + "\n")
                    else:
                        songs += str(song[0] + f" - {ctx.guild.get_member(song[1]).display_name}" +
                                     f" - {str(counter)}" + "\n")
                    counter += 1
                songs = songs[:len(songs) - 1]
                emb = discord.Embed(title="Queue", description=f"{songs}", color=self.emb_color)
                await ctx.send(embed=emb)
            except IndexError:
                ctx.send("No songs in queue!")

    @commands.command()
    async def pop(self, ctx, index: int):
        try:
            if self.queue[index-1][1] == ctx.author.id:
                removed_song = self.queue[index-1][0]
                self.queue.pop(index-1)
                if isinstance(removed_song, list):
                    await ctx.send(f"**{removed_song[0]}** removed from queue!")
                else:
                    await ctx.send(f"**{removed_song}** removed from queue!")
            else:
                await ctx.send(f"**NICE TRY BUSTER!** You didn't add this song!")
        except IndexError:
            await ctx.send("Not a valid song position!")

    @commands.command()
    async def song_info(self, ctx):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(self.current_song, download=False)
            print(info)

    @commands.command()
    async def play_last(self, ctx):
        voice_channel = discord.utils.get(ctx.guild.voice_channels, name='fat-phone')
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            pass
        else:
            voice = await voice_channel.connect()

        song_there = os.path.isfile("song.mp3")
        if song_there:
            voice.play(discord.FFmpegPCMAudio("song.mp3"))
        else:
            await ctx.send("Can't get last song!")

    @commands.is_owner()
    @commands.command()
    async def stop(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            voice.stop()
        else:
            await ctx.send("Not connected to a voice channel!")
        print("Stopped song!")

    @commands.command()
    async def skip(self, ctx):
        self.skipping = True
        if ctx.author.id == self.current_caller:
            print("Skipping!")
            await self.stop(ctx)
            try:
                print(self.queue[0])
                await self.play(ctx=ctx, title=self.queue[0][0])
                self.queue.pop(0)
                print(self.queue)
            except IndexError:
                await ctx.send("Nothing in queue!")
        else:
            await ctx.send(f"**NICE TRY BUSTER!** You didn't play this song!")
        self.skipping = False

    async def _auto_skip(self, ctx):
        self.skipping = True
        print("Autoplay is skipping!")
        await self.stop(ctx)
        try:
            print(self.queue[0])
            await self.play(ctx=ctx, title=self.queue[0][0])
            self.queue.pop(0)
        except IndexError:
            await ctx.send("Nothing in queue!")
        self.skipping = False

    @commands.command()
    async def pause(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            if voice.is_playing():
                voice.pause()
            else:
                await ctx.send("No audio is playing!")
        else:
            await ctx.send("Not connected to a voice channel!")

    @commands.command()
    async def resume(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            if voice.is_paused():
                voice.resume()
            else:
                await ctx.send("The audio is not paused!")
        else:
            await ctx.send("Not connected to a voice channel!")

    @commands.is_owner()
    @commands.command()
    async def leave(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            if voice.is_connected():
                await voice.disconnect()
            else:
                await ctx.send("The bot is not connected to a voice channel!")
        else:
            await ctx.send("Not connected to a voice channel!")

    @commands.command(aliasese=["vs"])
    async def vote_skip(self, ctx):
        question = "**Skip song?** You have **10** seconds to vote!"
        await self.poller.quickpoll(self.poller, ctx, question, "yes", "no")
        await asyncio.sleep(10)
        await self.poller.tally(self.poller, ctx, self.poller.last_poll)
        print(self.poller.last_results)
        if self.poller.last_results["✅"] > self.poller.last_results["❌"]:
            await self._auto_skip(ctx)
            await ctx.send("Song skipped by vote skip!")
        else:
            await ctx.send("Not enough votes to skip!")


    @commands.command()
    async def switch_autoplay(self, ctx):
        self.auto_play = not self.auto_play
        if self.auto_play:
            await ctx.send("Autoplay is now on!")
        else:
            await ctx.send("Autoplay is now off!")

    # TASKS
    @tasks.loop(seconds=10)
    async def is_not_playing(self):
        if self.queue and self.auto_play:
            server = self.bot.guilds[0]
            voice = discord.utils.get(self.bot.voice_clients, guild=server)
            if voice:
                if voice.is_playing() or voice.is_paused() or self.skipping:
                    pass
                else:
                    ctx = FakeContext(server)
                    await self._auto_skip(ctx=ctx)
            else:
                voice_channel = discord.utils.get(server.voice_channels, name='fat-phone')
                await voice_channel.connect()
                ctx = FakeContext(server)
                await self._auto_skip(ctx=ctx)

    # CHECKS
    async def cog_check(self, ctx):
        return True  # is_not_james(ctx)


class FakeContext:
    def __init__(self, guild):
        self.guild = guild
        self.channel = guild.get_channel(main_channel_id)

    async def send(self, message):
        await self.channel.send(message)


def setup(bot):
    bot.add_cog(MusicBot(bot))
