import asyncio
import logging
import os
import threading
from typing import Optional

from blinker import signal
import discord

from riffbot.endpoints.endpoint import Endpoint
from .songqueue import SongQueue

_logger = logging.getLogger(__name__)


class Player:
    def __init__(self, voice_client: discord.VoiceClient):
        _logger.debug(f"Initializing")
        self._voice_client = voice_client
        self._song_queue = SongQueue()
        self._current = None

    def __del__(self):
        _logger.debug("Destroying")
        self.stop()

    def play(self):
        if self._voice_client.is_paused():
            _logger.debug("Resuming playback")
            self._voice_client.resume()
        elif not self._voice_client.is_playing():
            _logger.debug("Starting playback")
            if self._song_queue.size() > 0:
                self._init_playback(self._song_queue.get_next())

    def pause(self):
        if self._voice_client.is_playing():
            _logger.debug("Pausing playback")
            self._voice_client.pause()

    def stop(self):
        if self._voice_client.is_playing() or self._voice_client.is_paused():
            _logger.debug("Stopping playback")
            self._voice_client.stop()

    def get_current(self) -> Optional[Endpoint]:
        return self._current

    def get_queue(self) -> SongQueue:
        return self._song_queue

    def _init_playback(self, endpoint: Endpoint):
        self._current = endpoint

        # Create pipe for ffmpeg
        pipe_read, pipe_write = os.pipe()

        # Create and start thread that loads chunks and fills the pipe
        _logger.debug("Preparing thread for downloader")
        halt_event = threading.Event()
        downloader_thread = threading.Thread(target=_downloader, args=(endpoint, pipe_write, halt_event))
        downloader_thread.start()

        _logger.debug("Setting up audio source")
        audio_source = discord.FFmpegPCMAudio(pipe_read, pipe=True)

        # Set up callback to execute in the Player's thread when playing finishes
        event_loop = asyncio.get_event_loop()

        def callback(error: Exception):
            _logger.debug(f"Audio source exhausted")
            if error is not None:
                _logger.error(f"Error occurred during playback: {error}")

            # Clean up resources
            self._current = None
            halt_event.set()
            os.close(pipe_read)
            self._voice_client.stop()
            audio_source.cleanup()

            # Dispatch callback in main thread
            asyncio.run_coroutine_threadsafe(self._on_song_over(), event_loop)

        # Set up audio source and start playing
        self._voice_client.play(audio_source, after=callback)
        _logger.debug("Playback initialized")

    async def _on_song_over(self):
        _logger.debug("Song is over")

        # Emit event that a song finished
        signal("player_song_over").send(self)

        # Play next song if there is one in the queue
        if self._song_queue.size() > 0:
            _logger.debug("Playing next song in queue")
            self._init_playback(self._song_queue.get_next())


def _downloader(endpoint: Endpoint, pipe_write: int, halt_event: threading.Event):
    _logger.debug(f"Downloader thread started for \"{endpoint.get_song_description()}\"")
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
        # The read end may be closed at any point in time, if this happens ignore it and clean up
        pass
    finally:
        os.close(pipe_write)
        _logger.debug(f"Downloader thread finished for \"{endpoint.get_song_description()}\"")
