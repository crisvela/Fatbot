import discord
from discord.ext import commands
import os
import json


# Descriptions
file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'command_descriptions.json')
with open(file_path, "r") as file:
    descriptions = json.load(file)


class QuickPoll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_poll = None
        self.last_results = None
        self.multi_vote = True

    @commands.command(pass_context=True, help=descriptions["quickpoll"])
    async def quickpoll(self, ctx, question, *options: str):
        if len(options) <= 1:
            await ctx.send('You need more than one option to make a poll!')
            return
        if len(options) > 10:
            await ctx.send('You cannot make a poll for more than 10 things!')
            return

        if len(options) == 2 and options[0] == 'yes' and options[1] == 'no':
            reactions = ['✅', '❌']
        else:
            reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']

        description = []
        for x, option in enumerate(options):
            description += '\n {} {}'.format(reactions[x], option)
        embed = discord.Embed(title=question, description=''.join(description))
        react_message = await ctx.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text=f'Poll ID: {react_message.id}')
        self.last_poll = react_message.id
        await react_message.edit(embed=embed)

    @commands.command(pass_context=True, help=descriptions["tally"])
    async def tally(self, ctx, id):
        if id == "last":
            id = self.last_poll
        poll_message = await ctx.fetch_message(id)
        print("Got message!")
        if not poll_message.embeds:
            print("No embed!")
            return
        print("Getting embeds!")
        embed = poll_message.embeds[0]
        print("Got embeds!")
        print(embed.footer.text)
        if poll_message.author != ctx.guild.me:
            print("This poll wasn't made by me!")
            return
        if not embed.footer.text.startswith('Poll ID:'):
            print("This embed has no footer!")
            return
        unformatted_options = [x.strip() for x in embed.description.split('\n')]
        opt_dict = {x[:2].strip(): x[3:] for x in unformatted_options} if unformatted_options[0][0] == '1' \
            else {x[:1]: x[2:] for x in unformatted_options}

        print(f"Opt Dict: {opt_dict}")
        # check if we're using numbers for the poll, or x/checkmark, parse accordingly
        voters = [ctx.guild.me.id]  # add the bot's ID to the list of voters to exclude it's votes

        print("Tallying!")
        tally = {x: 0 for x in opt_dict.keys()}

        print([i for i in poll_message.reactions])
        for reaction in poll_message.reactions:
            if reaction.emoji in opt_dict.keys():
                reactors = await reaction.users().flatten()
                for reactor in reactors:
                    if reactor.id not in voters:
                        tally[reaction.emoji] += 1
                        if not self.multi_vote:
                            voters.append(reactor.id)

        output = 'Results of the poll for "{}":\n'.format(embed.title) + \
                 '\n'.join(['{}: {}'.format(opt_dict[key], tally[key]) for key in tally.keys()])
        self.last_results = tally
        await ctx.send(output)


def setup(bot):
    bot.add_cog(QuickPoll(bot))
