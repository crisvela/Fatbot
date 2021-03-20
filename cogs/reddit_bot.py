import discord
from discord.ext import commands
import Gatherer
import aiohttp
import io
from fat_bot import is_not_james


class RedditBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tst(self, ctx):
        await ctx.send("Tsted!")
        print("Tsted!")

    @commands.command(aliases=['gp'], help="Gets top image post from specified subreddit, or random if not specified")
    async def get_posts(self, ctx, *, sub=None):
        print("Getting posts!")
        getter = Gatherer.Gatherer()
        async with aiohttp.ClientSession() as session:
            async with session.get(await getter.get_sub_images(sub)) as response:
                if response.status != 200:
                    return await ctx.send('Could not download file!')
                data = io.BytesIO(await response.read())
                if getter.no_img_flag:
                    await ctx.send(f"{str(sub)} probably doesn't contain images, so here is a random subreddit post!")
                elif getter.error_flag:
                    await ctx.send(f"{str(sub)} nonexistent or private, so here is a random subreddit post!")
                await ctx.send(f"From {getter.sub_name}:")
                await ctx.send(file=discord.File(data, 'your_face.png'))
                print("Post sent!")
                await session.close()


def setup(bot):
    bot.add_cog(RedditBot(bot))
