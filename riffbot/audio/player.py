import asyncio
from enum import Enum
import logging
import os
import threading
import typing

import discord

from .endpoint import Endpoint

_logger = logging.getLogger("riffbot." + __name__)


class PlayState(Enum):
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


class PlayerStoppedError(Exception):
    pass


class Player:
    def __init__(self, endpoint: Endpoint, voice_client: discord.VoiceClient,
                 after: typing.Callable[[Exception], typing.Awaitable[None]]):
        _logger.debug(f"Initializing with after={after.__name__}, \"{endpoint.get_song_description()}\"")
        self._endpoint = endpoint
        self._voice_client = voice_client

        # Create pipe for ffmpeg
        pipe_read, pipe_write = os.pipe()

        # Create and start thread that loads chunks and fills the pipe
        _logger.debug("Preparing thread for downloader")
        self._halt_event = threading.Event()
        self._downloader = threading.Thread(target=_downloader, args=(endpoint, pipe_write, self._halt_event))
        self._downloader.start()

        # Set up callback to execute in the Player's thread when playing finishes
        event_loop = asyncio.get_event_loop()

        def callback(error: Exception):
            _logger.debug(f"Audio source exhausted")
            if error is not None:
                _logger.error(f"Error occurred during playback: {error}")
            os.close(pipe_read)
            self._audio_source.cleanup()
            asyncio.run_coroutine_threadsafe(after(error), event_loop)

        # Set up audio source and start playing
        _logger.debug("Setting up audio source")
        self._audio_source = discord.FFmpegPCMAudio(pipe_read, pipe=True)
        self._voice_client.play(self._audio_source, after=callback)
        self._play_state = PlayState.PLAYING
        _logger.debug("Constructor finished, player fully initialized")

    def __del__(self):
        self.stop()

    def resume(self):
        if self._play_state == PlayState.STOPPED:
            raise PlayerStoppedError()

        if self._play_state == PlayState.PAUSED:
            _logger.debug("Resuming playback")
            self._play_state = PlayState.PLAYING
            self._voice_client.resume()

    def pause(self):
        if self._play_state == PlayState.STOPPED:
            raise PlayerStoppedError()

        if self._play_state == PlayState.PLAYING:
            _logger.debug("Pausing playback")
            self._play_state = PlayState.PAUSED
            self._voice_client.pause()

    def stop(self):
        if self._play_state != PlayState.STOPPED:
            _logger.debug("Stopping playback")
            self._play_state = PlayState.STOPPED
            self._halt_event.set()
            self._voice_client.stop()

    def get_endpoint(self):
        return self._endpoint


def _downloader(endpoint: Endpoint, pipe_write: int, halt_event: threading.Event):
    _logger.debug(f"Downloader thread starting for \"{endpoint.get_song_description()}\"")
    try:
        for chunk in endpoint.stream_chunks(endpoint.get_preferred_chunk_size()):
            if halt_event.is_set():
                _logger.debug("Downloader received halt event")
                break
            os.write(pipe_write, chunk)
            if halt_event.is_set():
                _logger.debug("Downloader received halt event")
                break
    except BrokenPipeError:
        pass
    finally:
        os.close(pipe_write)
        _logger.debug(f"Downloader thread finished for \"{endpoint.get_song_description()}\"")
