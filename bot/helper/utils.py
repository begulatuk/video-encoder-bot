import os, aiohttp, asyncio 
from bot import data, download_dir
from pyrogram.types import Message
from .ffmpeg_utils import encode, get_thumbnail, get_duration, get_width_height
import logging

LOGGER = logging.getLogger(__name__)


def on_task_complete():
    del data[0]
    if len(data) > 0:
      add_task(data[0])

async def add_task(message: Message):
    try:
      msg = await message.reply_text("```Downloading video...```", quote=True)
      filepath = ""
      async with aiohttp.ClientSession() as sess:
        async with sess.get(message.text) as resp:
            if resp.status == 200:
                filepath = str(time.time())
                with open(filepath, "wb") as fi:
                    fi.write(await resp.read())
            else:
                await msg.edit("```Failed...```")
                return
      LOGGER.info(f"filepath: {filepath}")
      msg.edit("```Encoding video...```")
      new_file = encode(filepath)
      if new_file:
        msg.edit("```Video Encoded, getting metadata...```")
        duration = get_duration(new_file)
        thumb = get_thumbnail(new_file, download_dir, duration / 4)
        width, height = get_width_height(new_file)
        msg.edit("```Uploading video...```")
        message.reply_video(new_file, quote=True, supports_streaming=True, thumb=thumb, duration=duration, width=width, height=height)
        os.remove(new_file)
        os.remove(thumb)
        msg.edit("```Video Encoded to x265```")
      else:
        msg.edit("```Something wents wrong while encoding your file. Make sure it is not already in HEVC format.```")
        os.remove(filepath)
    except Exception as e:
      msg.edit(f"```{e}```")
    on_task_complete()
