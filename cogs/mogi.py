import math, random
import discord
from discord import ApplicationContext, Interaction, slash_command, Option, InputTextStyle
from discord.ui import View, Modal, InputText
from discord.utils import get
from discord.ext import commands

class mogi(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.mogi = {"status": 0, "running": 0, "players": ["player1", "player2", "player3", "player4", "player5", "player6", "player7", "player8", "player9", "player10", "player11"], "teams": [], "calc": [], "points": []}

    @slash_command(name="open", description="Start a new mogi")
    async def open(self, ctx: ApplicationContext):
        if self.mogi['status']:
            return await ctx.respond("A mogi is already open")
        self.mogi['status'] = 1
        await ctx.respond("# Started a new mogi! Use /join to participate!")

    @slash_command(name="join", description="Join the current mogi")
    async def join(self, ctx: ApplicationContext):
        if not self.mogi['status']:
            return await ctx.respond("Currently no mogi open")
        if ctx.author.name in self.mogi['players']:
            return await ctx.respond("You are already in the mogi")
        if len(self.mogi['players']) >= 12:
            return await ctx.respond("The mogi is already full")
        self.mogi['players'].append(ctx.author.name)
        await ctx.user.add_roles(get(ctx.guild.roles, name="InMogi"))
        await ctx.respond(f"{ctx.author.name} joined the mogi!\n{len(self.mogi['players'])} players are in!")

    @slash_command(name="leave", description="Leave the current mogi")
    async def leave(self, ctx: ApplicationContext):
        if ctx.author.name not in self.mogi['players']:
            return await ctx.respond("You are not in the mogi")
        self.mogi['players'].remove(ctx.author.name)
        await ctx.user.remove_roles(get(ctx.guild.roles, name="InMogi"))
        await ctx.respond(f"{ctx.author.name} left the mogi!\n{len(self.mogi['players'])} players are in!")

    @slash_command(name="l", description="List all players in the current mogi")
    async def l(self, ctx: ApplicationContext):
        if not self.mogi['status']:
            return await ctx.respond("Currently no open mogi")
        if not self.mogi['players']:
            return await ctx.respond("Current mogi: \n No players")
        list = "Current mogi:\n"
        for index, player in enumerate(self.mogi['players']):
            list += f"*{index+1}.* {player}\n"
        await ctx.respond(list)

    @slash_command(name="close", description="Stop the current Mogi if running")
    async def close(self, ctx: ApplicationContext):
        self.mogi = {"status": 0, "running": 0, "players": [], "teams": [], "calc": []}
        for member in ctx.guild.members:
            try:
                await member.remove_roles(get(ctx.guild.roles, name="InMogi"))
            except:
                pass
        await ctx.respond("# The mogi has been closed")

    @slash_command(name="status", description="See current state of mogi")
    async def status(self, ctx: ApplicationContext):
        if not self.mogi['status']:
            return await ctx.respond("No running mogi")
        await ctx.respond(f"Currently open mogi: {len(self.mogi['players'])} players")

    @commands.slash_command(name="play", description="Randomize teams, vote format and start playing")
    async def play(self, ctx: ApplicationContext):
        if not any(role.name == "InMogi" for role in ctx.author.roles):
            return await ctx.respond("You can't start a mogi you aren't in", ephemeral=True)
        if self.mogi['running']:
            return await ctx.respond("Mogi is already in play")
        
        players = len(self.mogi['players'])
        options = []
        options.append(discord.SelectOption(label=f"FFA", value=f"ffa"))
        if players % 2 == 0:
            for size in range(2, players // 2 + 1):
                options.append(discord.SelectOption(label=f"{size}v{size}", value=f"{size}v{size}"))

        class FormatView(View):
            def __init__(self, mogi):
                super().__init__()
                self.mogi = mogi
                self.voters = []
                self.votes = {"ffa": 0, "2v2": 5, "3v3": 0, "4v4": 0, "5v5": 0, "6v6": 0}

            @discord.ui.select(options=options)
            async def select_callback(self, select, interaction: discord.Interaction):
                select.disabled = True
                await interaction.response.defer()
                if self.mogi['running']:
                    return await ctx.send("Mogi already decided, voting is closed")
                if not any(role.name == "InMogi" for role in ctx.author.roles):
                    return await ctx.send("You can't vote if you aren't in the mogi", ephemeral=True)
                selected_option = select.values[0]
                if interaction.user.name in self.voters:
                    return await interaction.response.send_message("You already voted", ephemeral=True)
                self.voters.append(interaction.user.name)
                self.votes[selected_option] += 1
                await interaction.followup.send(f"+1 vote for *{selected_option}*")
                if self.votes[max(self.votes, key=self.votes.get)] >= math.ceil(len(self.mogi['players'])/2):
                    format = max(self.votes, key=self.votes.get)
                    lineup_str = ""
                    if players % 2 != 0:
                        for player in self.mogi['players']:
                            lineup_str += f"{player}\n"
                    else:
                        random.shuffle(self.mogi['players'])
                        teams = []
                        for i in range(0, len(self.mogi['players']), int(format[0])):
                            teams.append(self.mogi['players'][i:i + int(format[0])])
                        self.mogi['teams'] = teams
                        for i, item in enumerate(teams):
                            lineup_str += f"\n `{i+1}`. {', '.join(item)}"

                    await ctx.send(f"""
                        # Mogi starting!
                        ## Format: {format}
                        ### Lineup:
                        \n{lineup_str}
                    """)
                    self.votes = {key: 0 for key in self.votes}
                    self.mogi['running'] = 1
                        
        view = FormatView(self.mogi)
        await ctx.respond(f"{get(ctx.guild.roles, name='InMogi').mention} \nBeginning Mogi\nVote for a format:", view=view)

    @discord.slash_command(name="calc", description="Input player points, calculate new mmr and make tables")
    async def calc(self, ctx: discord.ApplicationContext):
        if not self.mogi['running']:
            return await ctx.respond("No running mogi")
        class MogiModal(discord.ui.Modal):
            def __init__(self, mogi, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.mogi = mogi

                subset = mogi['players'][len(mogi['calc']):][:4]
                if not len(mogi['calc']):
                    subset = mogi['players'][:4]

                for player in subset:
                    mogi['calc'].append(player)
                    self.add_item(discord.ui.InputText(label=player))

            async def callback(self: Modal = Modal, interaction: Interaction = Interaction, mogi=self.mogi):
                mogi["points"].append(self.children)
                await interaction.response.send_message(f"use this command again until you put all players' points\nresults: {self.children[0].value}", ephemeral=True)
                
        if len(self.mogi['players']) > len(self.mogi['calc']):
            modal = MogiModal(self.mogi, title="Input player points after match")
            await ctx.send_modal(modal)
        else: 
            return await ctx.respond("Already got all calcs")
        
    @discord.slash_command(name="table", description="Input player points, calculate new mmr and make tables")
    async def table(self, ctx: discord.ApplicationContext):
        await ctx.respond(self.mogi)

def setup(bot: commands.Bot):
    bot.add_cog(mogi(bot))