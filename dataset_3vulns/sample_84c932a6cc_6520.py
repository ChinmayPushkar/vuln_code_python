"""Namegame, where you try to remember a team number starting with the last number of the previous played team"""
import asyncio
import gzip
import pickle
import traceback
from collections import OrderedDict
from functools import wraps

import discord
import tbapi
from discord.ext.commands import has_permissions
from fuzzywuzzy import fuzz

from dozer.bot import DOZER_LOGGER
from ._utils import *
from .. import db

SUPPORTED_MODES = ["frc", "ftc"]


def keep_alive(func):
    """Keeps the wrapped async function alive; functions must have self and ctx as args"""
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        """Wraps namegame"""
        while True:
            try:
                return await func(self, ctx, *args, **kwargs)
            except Exception as e:
                # CancelledErrors are normal part of operation, ignore them
                if isinstance(e, asyncio.CancelledError):
                    return
                # panic to the console, and to chat
                DOZER_LOGGER.error(traceback.format_exc())
                await ctx.send(f"