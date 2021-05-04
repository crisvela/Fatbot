import asyncio
import json
from discord.ext import commands
from discord.ext import tasks
import discord
import os
import youtube_dl
import lyricsgenius
import random

import db_manager
from configs import genius_token
import youtube_scraper
import cogs.quickpoll as quickpoll


# Channel IDs
main_channel_id = 814202376068137013
test_channel_id = 814971629712572457

# Descriptions
file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'command_descriptions.json')
with open(file_path, "r") as file:
    descriptions = json.load(file)


class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emb_color = discord.Color.from_rgb(44, 47, 51)
        self.scraper = youtube_scraper.YoutubeScraper()
        self.poller = quickpoll.QuickPoll(bot)
        self.database = db_manager.Database()
        self.genius = lyricsgenius.Genius(genius_token, timeout=15)
        self.queue = []
        self.auto_play = True
        self.is_not_playing.start()
        self.last_channel = None
        self.current_caller = None
        self.current_song = None
        self.current_song_title = None
        self.skipping = False

        self.codes = {"&#39;": "'", "&quot;": "\"", "&amp;": "&"}

        self.sql_codes = {"'": "''"}

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'match_title': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    @commands.command(help=descriptions["tstt"])
    async def tstt(self, ctx):
        await ctx.send("Tstted!")
        print("Tstted!")

    @commands.command(aliases=['l'], help=descriptions["lyrics"])
    async def lyrics(self, ctx, *, title):
        title = title.replace("\"", "").title()
        print(f"Getting lyrics for \"{title}\"")
        # musician = self.genius.search_artist(artist, max_songs=0, sort="title")
        song = self.genius.search_song(title)
        if not song:
            await ctx.send("**No lyrics were found!**")
            return
        lyric = song.lyrics
        lyric = lyric.replace("\n\n\n\n", "\n").replace("\n\n\n", "\n").replace("\n\n", "\n")
        print(len(lyric))
        await self.parse_and_send(ctx, lyric, f"**{song.title}**")

    @commands.command(aliases=["p"], help=descriptions["play"])
    async def play(self, ctx, *, title):
        song_there = os.path.isfile("song.mp3")
        try:
            if not self.queue:
                if song_there:
                    os.remove("song.mp3")
        except PermissionError:
            await ctx.send("Wait for the current song to end or use the 'stop' command!")
            return

        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            if isinstance(title, list):
                song_details = [self.scraper.base + title[1], title[0]]
            else:
                song_details = self.scraper.get_video_url(query=title)
            ydl.download([song_details[0]])
            song_details[1] = self.partial_decode(song_details[1])

        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            await ctx.send("Wait for the current song to end or use the 'stop' command!")
            return

        song_name = song_details[1].lower()

        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                file_title = file.title().lower()
                if self.matching_strings(song_name, file_title):
                    os.rename(file, "song.mp3")
                    print("File renamed!")

        self.current_song = song_details[0]
        self.current_song_title = song_details[1]

        await ctx.send(f"**PLAYING {song_details[1]}:** {song_details[0]}")
        await self.all_ratings(ctx)

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

    @commands.command(help=descriptions["add_playlist"])
    async def add_playlist(self, ctx, url):
        self.auto_play = False
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            for song in info["entries"]:
                self.queue.append([[song["title"], song["id"]], ctx.author.id])
        await ctx.send(f"**Added {url} to the queue!**")
        self.auto_play = True

    @commands.command(help=descriptions["add"])
    async def add(self, ctx, *, title):
        self.queue.append([title, ctx.author.id])
        await ctx.send(f"**{title}** was added to the queue!")

    @commands.command(aliases=["ls", "queue"], help=descriptions["queue"])
    async def queued_songs(self, ctx, shuffle=None):
        if not shuffle:
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
                await self.parse_and_send(ctx, songs, "Queue")
            except IndexError:
                ctx.send("No songs in queue!")
        elif shuffle == "shuffle":
            indexes = []
            index = 0
            for song in self.queue:
                if ctx.guild.get_member(song[1]).id == ctx.author.id:
                    indexes.append(index)
                index += 1
            if indexes:
                shuffled_indexes = random.sample(indexes, len(indexes))
            else:
                await ctx.send("You have no songs in the queue!")
                return
            trans_list = self.queue.copy()
            index = 0
            for ind in indexes:
                self.queue[ind] = trans_list[shuffled_indexes[index]]
                index += 1
            await ctx.send("Songs shuffled")
            await self.queued_songs(ctx)

    @commands.command(help=descriptions["rem"])
    async def rem(self, ctx, index):
        try:
            index = int(index)
            if index:
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
        except ValueError:
            if index.lower() == "force":
                if ctx.author.id == 387334819232874498:
                    self.queue = []
                    await ctx.send("Queue cleared!")
                else:
                    await ctx.send("**NICE TRY BUSTER!** You ain't the owner")
            elif index.lower() == "clear":
                index = len(self.queue) - 1
                for i in range(index + 1):
                    if self.queue[index][1] == ctx.author.id:
                        self.queue.pop(index)
                    index -= 1
                await ctx.send(ctx.guild.get_member(ctx.author.id).display_name + " cleared their songs!")
            else:
                await ctx.send("Not a valid song position or command!")

    @commands.command(help=descriptions["song_info"])
    async def song_info(self, ctx):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(self.current_song, download=False)
            print(info)

    @commands.command(help=descriptions["play_last"])
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

    @commands.command(help=descriptions["skip"])
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

    @commands.command(help=descriptions["pause"])
    async def pause(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            if voice.is_playing():
                voice.pause()
            else:
                await ctx.send("No audio is playing!")
        else:
            await ctx.send("Not connected to a voice channel!")

    @commands.command(help=descriptions["resume"])
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
                self.auto_play = False
            else:
                await ctx.send("The bot is not connected to a voice channel!")
        else:
            await ctx.send("Not connected to a voice channel!")

    @commands.command(aliasese=["vs"], help=descriptions["vote_skip"])
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

    @commands.command(help=descriptions["switch_autoplay"])
    async def switch_autoplay(self, ctx):
        self.auto_play = not self.auto_play
        print(self.auto_play)
        if self.auto_play:
            await ctx.send("Autoplay is now on!")
        else:
            await ctx.send("Autoplay is now off!")

    # SONG RATING
    @commands.command()
    @commands.is_owner()
    async def make_tables(self, ctx):
        await self.database.create_tables()

    @commands.command()
    @commands.is_owner()
    async def drop_tables(self, ctx):
        await self.database.drop_tables()

    @commands.is_owner()
    @commands.command()
    async def print_ratings(self, ctx):
        await self.database.print_all_ratings()

    @commands.command(help=descriptions["all_ratings"])
    async def all_ratings(self, ctx, *, title: str = None):
        if not title:
            if self.current_song_title:
                title = self.current_song_title
        if title:
            ratings = await self.database.get_all_ratings(self.sql_encode(title))
            if ratings:
                rating_message = ""
                for rating in ratings:
                    rating_message += f"""**{ctx.guild.get_member(rating[0]).display_name}** \
                                      rated this a: **{rating[1]}/10**\n"""
                rating_message = rating_message[:len(rating_message) - 1]
                await self.parse_and_send(ctx, rating_message, f"\"{title}\" Ratings")
            else:
                await ctx.send(f"**{title}** not rated by anyone yet!")
        else:
            await ctx.send("No song has been played and song wasn't specified!")

    @commands.command(help=descriptions["songs_scored"])
    async def songs_scored(self, ctx, score: int):
        songs = await self.database.get_songs(score)
        if songs:
            song_message = ""
            for song in songs:
                song_message += f"""**{song[1]}**: rated by **{ctx.guild.get_member(song[0]).display_name}**\n"""
            song_message = song_message[:len(song_message) - 1]
            await self.parse_and_send(ctx, song_message, f"**{score}/10** Songs")
        else:
            await ctx.send(f"No songs have been rated: **{score}/10**")

    @commands.command(help=descriptions["rate"])
    async def rate(self, ctx, score: int, *, title: str = None):
        if not title:
            if self.current_song_title:
                title = self.current_song_title
        if title:
            await self.database.rate_song(title=self.sql_encode(title), score=score, critic=ctx.author.id)
            emb = discord.Embed(description=f"""{ctx.author.display_name} rated **_{title}_**: **{score}/10**""",
                                color=self.emb_color)
            await ctx.send(embed=emb)
        else:
            await ctx.send("No song has been played and song wasn't specified!")

    @commands.command(help=descriptions["is_rated"])
    async def is_rated(self, ctx, *, title: str = None):
        if not title:
            if self.current_song_title:
                title = self.current_song_title
        if title:
            rating = await self.database.get_rating(self.sql_encode(title), ctx.author.id)
            if rating:
                await ctx.send(f"{ctx.author.display_name} rated **{title}**: **{rating}/10**!")
            else:
                await ctx.send(f"{ctx.author.display_name} has not rated **{title}**!")
        else:
            await ctx.send("No song has been played and song wasn't specified!")

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

    # UTILS
    async def parse_and_send(self, ctx, message, title):
        if len(message) > 2048:
            step = 2048
            offset = 0
            last_i = None
            for i in range(0, len(message), step):
                last_i = i
            for i in range(0, len(message), step):
                curr_pos = i - offset
                if i == last_i and curr_pos <= (len(message) - step):
                    print("Last 2 embeds!")
                    last_end = message[0: curr_pos + step].rfind("\n")
                    string_sect = message[curr_pos: last_end]
                    offset += curr_pos + step - last_end
                    emb = discord.Embed(title=f"{title}", description=f"{string_sect}", color=self.emb_color)
                    await ctx.send(embed=emb)
                    curr_pos = i + step - offset
                    string_sect = message[curr_pos:]
                elif i == last_i:
                    string_sect = message[curr_pos:]
                elif message[curr_pos + step] == "\n":
                    string_sect = message[curr_pos: curr_pos + step]
                else:
                    last_end = message[0: curr_pos + step].rfind("\n")
                    string_sect = message[curr_pos: last_end]
                    offset += curr_pos + step - last_end
                if i == 0:
                    emb = discord.Embed(title=f"{title}", description=f"{string_sect}", color=self.emb_color)
                else:
                    emb = discord.Embed(description=f"{string_sect}", color=self.emb_color)
                await ctx.send(embed=emb)
        else:
            emb = discord.Embed(title=f"{title}", description=f"{message}", color=self.emb_color)
            await ctx.send(embed=emb)

    def partial_decode(self, string):
        for key, value in self.codes.items():
            string = string.replace(key, value)
        return string

    def sql_encode(self, string):
        for key, value in self.sql_codes.items():
            string = string.replace(key, value)
        return string

    def matching_strings(self, str1, str2):
        length = len(str1) if len(str1) <= len(str2) else len(str2)
        matching_chars = 0
        for i in range(0, length):
            if str1[i] == str2[i]:
                matching_chars += 1
        match_percent = matching_chars * 1.0 / length
        if match_percent > 0.8:
            return True
        return False


class FakeContext:
    def __init__(self, guild):
        self.guild = guild
        self.channel = guild.get_channel(main_channel_id)

    async def send(self, *message, embed=None):
        if embed:
            await self.channel.send(embed=embed)
        else:
            await self.channel.send(message[0])


def setup(bot):
    bot.add_cog(MusicBot(bot))
