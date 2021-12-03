import discord
from discord.ext import commands
import gatherer
import aiohttp
import io
import os
import json


# Descriptions
file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'command_descriptions.json')
with open(file_path, "r") as file:
    descriptions = json.load(file)


class RedditBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help=descriptions["tst"])
    async def tst(self, ctx):
        await ctx.send("Tsted!")
        print("Tsted!")

    @commands.command(aliases=['gp'], help=descriptions["get_posts"])
    async def get_posts(self, ctx, *, sub=None):
        print("Getting posts!")
        getter = gatherer.Gatherer()
        async with aiohttp.ClientSession() as session:
            async with session.get(await getter.get_sub_images(sub)) as response:
                if response.status != 200:
                    return await ctx.send('Could not download file!')
                data = io.BytesIO(await response.read())
                if getter.no_img_flag:
                    await ctx.send(f"{str(sub)} probably doesn't contain images, so here is a random subreddit post!")
                elif getter.error_flag:
                    await ctx.send(f"{str(sub)} nonexistent or private, so here is a random subreddit post!")

                emb = discord.Embed(title=f"From **r/{getter.sub_name}**:")
                fl = discord.File(data, 'your_face.png')
                emb.set_image(url="attachment://your_face.png")
                await ctx.send(file=fl, embed=emb)
                print("Post sent!")
                await session.close()


def setup(bot):
    bot.add_cog(RedditBot(bot))
