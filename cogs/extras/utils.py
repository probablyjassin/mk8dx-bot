import discord
from discord import Option, ApplicationContext
from discord.ext import commands
from discord.utils import get

def is_allowed_server(server_id: int):
    return server_id in [1084911987626094654, 1056713663714693241]

def is_mogi_manager():
    async def predicate(ctx: ApplicationContext):
        if is_allowed_server(ctx.guild_id) and (ctx.user.guild_permissions.administrator or get(ctx.guild.roles, name="Mogi Manager") in ctx.user.roles):
            return True
        else:
            await ctx.respond("You're not allowed to use this command.")
            return False
    return commands.check(predicate)

def is_admin():
    async def predicate(ctx: ApplicationContext):
        if is_allowed_server(ctx.guild_id) and ctx.user.guild_permissions.administrator:
            return True
        else:
            await ctx.respond("You're not allowed to use this command.")
            return False
    return commands.check(predicate)