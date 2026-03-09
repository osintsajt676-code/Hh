"""
Handlers - registers all bot commands.
"""
from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from config import Config
from commands.nick import cmd_nick
from commands.email_cmd import cmd_email
from commands.domain import cmd_domain
from commands.ip_cmd import cmd_ip
from commands.social import cmd_social
from commands.help_cmd import cmd_help, cmd_start

def register_handlers(dp: Dispatcher, config: Config):
    router = Router()

    @router.message(Command("start"))
    async def start(msg: Message): await cmd_start(msg)

    @router.message(Command("help"))
    async def help_(msg: Message): await cmd_help(msg)

    @router.message(Command("nick"))
    async def nick(msg: Message): await cmd_nick(msg, config)

    @router.message(Command("email"))
    async def email(msg: Message): await cmd_email(msg, config)

    @router.message(Command("domain"))
    async def domain(msg: Message): await cmd_domain(msg, config)

    @router.message(Command("ip"))
    async def ip(msg: Message): await cmd_ip(msg, config)

    @router.message(Command("social"))
    async def social(msg: Message): await cmd_social(msg, config)

    dp.include_router(router)
