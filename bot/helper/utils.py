import os
from pySmartDL import SmartDL
from bot import data, download_dir
from pyrogram.types import Message
from .ffmpeg_utils import encode, get_thumbnail, get_duration, get_width_height
from urllib.parse import unquote_plus
import logging
import asyncio


LOGGER = logging.getLogger(__name__)

ROOT = os.getcwd()
def on_task_complete():
    del data[0]
    if len(data) > 0:
      add_task(data[0])

async def add_task(message: Message):
    try:
      msg = await message.reply_text("```Downloading video...```", quote=True)
      custom_file_name = unquote_plus(os.path.basename(message.text))
      filepath = os.path.join(ROOT, download_dir, custom_file_name)  
      downloader = SmartDL(message.text, filepath, progress_bar=False)
      await asyncio.sleep(2)
      downloader.start()
      await asyncio.sleep(1)  
      print(downloader.isSuccessful())
      path = downloader.get_dest()          
      LOGGER.info(f"filepath: {filepath}")
      LOGGER.info(f"path: {path}")
      await asyncio.sleep(5)
      await msg.edit("```Encoding video...```")
      new_file = await encode(filepath)
      if new_file:
        await asyncio.sleep(2)
        await msg.edit("```Video Encoded, getting metadata...```")
        duration = get_duration(new_file)
        thumb = get_thumbnail(new_file, download_dir, duration / 4)
        width, height = get_width_height(new_file)
        await msg.edit("```Uploading video...```")
        await asyncio.sleep(5)
        await message.reply_video(new_file, quote=True, supports_streaming=True, thumb=thumb, duration=duration, width=width, height=height)
        os.remove(new_file)
        os.remove(thumb)
        await asyncio.sleep(2)
        await msg.edit("```Video Encoded to x265```")
      else:
        await msg.edit("```Something wents wrong while encoding your file. Make sure it is not already in HEVC format.```")
        os.remove(filepath)
    except Exception as e:
        await msg.edit(f"```{e}```")
      
    on_task_complete()
