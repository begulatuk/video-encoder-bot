import os
import sys
import json
import time
import ffmpeg
import subprocess
import asyncio
from subprocess import call, check_output
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import logging
LOGGER = logging.getLogger(__name__)

def get_codec(filepath, channel='v:0'):
    output = check_output(['ffprobe', '-v', 'error', '-select_streams', channel,
                            '-show_entries', 'stream=codec_name,codec_tag_string', '-of', 
                            'default=nokey=1:noprint_wrappers=1', filepath])
    return output.decode('utf-8').split()

async def encode(filepath):
    basefilepath, extension = os.path.splitext(filepath)
    LOGGER.info(f"basefilepath: {basefilepath}")
    output_filepath = basefilepath + '.HEVC' + '.mp4'
    LOGGER.info(f"output_filepath: {output_filepath}")
    assert(output_filepath != filepath)
    if os.path.isfile(output_filepath):
        print('Skipping "{}": file already exists'.format(output_filepath))
        return None
    print(filepath)
    # Get the video channel codec
    video_codec = get_codec(filepath, channel='v:0')
    if video_codec == []:
        print('Skipping: no video codec reported')
        return None
    # Video transcode options
    if video_codec[0] == 'hevc':
        if video_codec[1] == 'hvc1':
            print('Skipping: already h265 / hvc1')
            return None
        else:
            # Copy stream to hvc1
            video_opts = '-c:v copy -tag:v hvc1'
    else:
        # Transcode to h265 / hvc1
        video_opts = '-c:v libx265 -preset ultrafast -pix_fmt yuv420p10le -threads 0'
    # Get the audio channel codec
    audio_codec = get_codec(filepath, channel='a:0')
    LOGGER.info(f"video_opts: {video_opts}")
    
    if audio_codec == []:
        audio_opts = ''
    elif audio_codec[0] == 'aac':
        audio_opts = '-c:a copy'
    else:
        audio_opts = '-c:a aac -b:a 128k'
    LOGGER.info(f"audio_opts: {audio_opts}")    
    #call(['ffmpeg', '-i', filepath] + video_opts.split() + audio_opts.split() + [output_filepath])
    #process = subprocess.Popen(
    #    ['ffmpeg', '-i', filepath] + video_opts.split() + audio_opts.split() + [output_filepath],
    #    stdout=subprocess.PIPE,
    #    stderr=subprocess.PIPE,
    #)
    #cmd = ['ffmpeg', '-i', filepath] + video_opts.split() + audio_opts.split() + [output_filepath]
    cmd = [
      "ffmpeg",
      "-hide_banner",
      "-loglevel",
      "quiet",
      "-i",
      filepath,
      "-c:v", 
      "libx265",
      "-preset", 
      "veryslow",
      "-crf",
      "28",
      "-c:a",
      "copy",
      output_filepath
    ]    
    LOGGER.debug(cmd)
    process = await asyncio.create_subprocess_exec(
        *cmd,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )    
    #LOGGER.debug(cmd)
    #process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)    
    stdout, stderr = await process.communicate()    
    LOGGER.debug("[stdout] " + stdout.decode())
    LOGGER.debug("[stderr] " + stderr.decode())
    LOGGER.info(f"filepath: {filepath}")
    LOGGER.info(f"output_filepath: {output_filepath}")
    
    os.remove(filepath)
    return output_filepath

def get_thumbnail(in_filename, path, ttl):
    out_filename = os.path.join(path, str(time.time()) + ".jpg")
    open(out_filename, 'a').close()
    try:
        (
            ffmpeg
            .input(in_filename, ss=ttl)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return out_filename
    except ffmpeg.Error as e:
      return None

def get_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
      return metadata.get('duration').seconds
    else:
      return 0

def get_width_height(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("width") and metadata.has("height"):
      return metadata.get("width"), metadata.get("height")
    else:
      return 1280, 720
