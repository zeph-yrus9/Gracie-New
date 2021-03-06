import disnake 
from disnake import Button, ButtonStyle, MessageInteraction, SlashCommand
from disnake.ext import commands

from typing import Optional
import logging as log

from Assets import constants


class LeftMostButton(disnake.ui.Button):
    def __init__(self, *, paginator):
        self.paginator = paginator
        super().__init__(
            disabled=(True if paginator.on_page==1 else False),
            label="<<",
            style=ButtonStyle.blurple 
        )

    async def callback(self, interaction: MessageInteraction, /):
        await self.paginator.to_first()
        await interaction.response.defer()
        
        
class LeftButton(disnake.ui.Button):
    def __init__(self,*, paginator) -> None:
        self.paginator = paginator
        super().__init__(
            disabled=(True if paginator.on_page==1 else False),
            label="<",
            style=ButtonStyle.red
        )

    async def callback(self, interaction: MessageInteraction, /):
        await self.paginator.prev_embed()
        await interaction.response.defer()   


class MiddleButton(disnake.ui.Button):
    def __init__(self, *, paginator):
        self.paginator = paginator
        super().__init__(
            disabled=True,
            label=f"{paginator.on_page}/{paginator.total_embeds}",
            style=ButtonStyle.gray
        )

class RightButton(disnake.ui.Button):
    def __init__(self, *, paginator):
        self.paginator = paginator
        super().__init__(
            disabled=(True if paginator.on_page == paginator.total_embeds else False),
            label=f">",
            style=ButtonStyle.green
        )

    async def callback(self, interaction: MessageInteraction, /):
        await self.paginator.next_embed()
        await interaction.response.defer()   

class RightMostButton(disnake.ui.Button):
    def __init__(self, *, paginator):
        self.paginator = paginator
        super().__init__(
            disabled=(True if paginator.on_page == paginator.total_embeds else False),
            label=">>",
            style=ButtonStyle.blurple 
        )

    async def callback(self, interaction: MessageInteraction, /):
        await self.paginator.to_last()
        await interaction.response.defer()

class paginator_view(disnake.ui.View):
    def __init__(self, *,paginator , timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.add_item(LeftMostButton(paginator=paginator))
        self.add_item(LeftButton(paginator=paginator))
        self.add_item(MiddleButton(paginator=paginator))
        self.add_item(RightButton(paginator=paginator))
        self.add_item(RightMostButton(paginator=paginator))

class MyPaginator():
    def __init__(self, embeds: list[disnake.Embed]) -> None:
        self.embeds = dict(enumerate(embeds, 1)) 
        self.total_embeds = len(embeds)
        self.on_page = 1
        self.message: disnake.Message= None

    async def to_first(self):
        """Edits the message to first page."""
        msg = self.message
        if self.on_page == 1:
            return 
        else:
            self.on_page = 1
            view = paginator_view(paginator=self)
            await msg.edit(embed=self.embeds[self.on_page], view=view)

    async def to_last(self):
        msg = self.message
        if self.on_page == self.total_embeds:
            return 
        else:
            self.on_page = self.total_embeds
            view = paginator_view(paginator=self)
            await msg.edit(embed=self.embeds[self.on_page], view=view)

    async def prev_embed(self):
        msg = self.message
        if self.on_page == 1:
            return 
        else:
            self.on_page -= 1
            view = paginator_view(paginator=self)
            await msg.edit(embed=self.embeds[self.on_page], view=view)

    async def next_embed(self):
        msg = self.message
        if self.on_page == self.total_embeds:
            return
        else:
            self.on_page += 1
            view = paginator_view(paginator=self)
            await msg.edit(embed=self.embeds[self.on_page], view=view)

    async def send(self, target: disnake.TextChannel):
        view = paginator_view(paginator=self)
        self.message = await target.send(embed=self.embeds[self.on_page], view=view)
        

class customhelpcommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs = {"help":"Shows this command"})

    Command = commands.Command
    Cog = commands.Cog
    
    def make_embeds(
        self, 
        cmdlist, 
        max_commands :int=7, 
        embed_color=disnake.Colour.blurple()
    ):
        """
        Gets list of pages from command list, 
        having specified no. of max commands(default=7) per embed per page.
        """
        help_embeds = []
        embed = disnake.Embed(title="Help")
        for no, command in enumerate(cmdlist,start=1):
            command: commands.Command
            embed.add_field(
                name=f"{command.usename}",
                value=f"*{command.help}*",
                inline=False
            )
            if no%max_commands==0 or no==len(cmdlist):
                embed.color=embed_color
                help_embeds.append(embed)
                embed = disnake.Embed(title="Help")    
    
        return help_embeds

    def get_public_commands(self):
        """Returns list of  text commands which are not hidden."""
        bot :commands.Bot = self.context.bot
        public_commands = []
        for cog in bot.cogs.values():
            for cog_command in cog.get_commands():
                if hasattr(cog, "prefix"):
                    cog_command.usename = f"{cog.prefix}{cog_command.name}"
                else:
                    cog_command.usename = f"{constants.BOT_PREFIX}{cog_command.name}"
                public_commands.append(cog_command)
        return public_commands

    async def send_bot_help(self, mapping :dict):
        log.info("calling bot help")
        commands = self.get_public_commands()
        commands = await self.filter_commands(
            commands=commands, 
            sort=True, 
            key=lambda a: a.usename
        )

        help_embeds = self.make_embeds(commands)

        paginator = MyPaginator(embeds=help_embeds)

        channel = self.get_destination()
        await paginator.send(target=channel)
        log.info("Sent paginator")
        return await super().send_bot_help(mapping)


class Help(commands.Cog):
    def __init__(self, bot :commands.Bot) -> None:
        self.bot = bot 
        self.oldhelpcommand = self.bot.help_command
        bot.help_command = customhelpcommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.oldhelpcommand


def setup(bot):
    bot.add_cog(Help(bot))
    log.info(f"loaded {Help.__name__}")