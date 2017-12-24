from openal.al import *
from openal.alc import *

from .Sound import Sound
from ._errorChecking import _checkError as _ckerr


class Manager(object):
    def __init__(self, ffmpegPath='ffmpeg', bufferSize=44100, maxBufferNumber=3):
        self._ffmpegPath = ffmpegPath
        self._bufferSize = bufferSize
        self._device = None
        self._maxBufferNumber = maxBufferNumber
        self._sounds = []

        device = alcOpenDevice(None)
        self._checkError()
        if not device:
            raise RuntimeError('unknown error when opening device')
        self._device = device

        context = alcCreateContext(device, None)
        if not context:
            raise RuntimeError('unknown error when creating context')
        if not alcMakeContextCurrent(context):
            self._checkError()

        self._context = context

    def loadFile(self, filePath, isStream=False):
        sound = Sound(self, filePath, isStream, self._bufferSize, self._maxBufferNumber, self._ffmpegPath)
        self._sounds.append(sound)
        return sound

    @property
    def listenerPosition(self):
        return

    @listenerPosition.setter
    def listenerPosition(self, value):
        alListener3f(AL_POSITION, value)
        self._checkError()
        # alListener3f(AL_VELOCITY, 0, 0, 0);
        # // check for errors
        # alListenerfv(AL_ORIENTATION, listenerOri);
        # // check for errors

    def _checkError(self):
        _ckerr(self._device)

    def terminate(self):
        self.__del__()

    def __del__(self):

        for s in self._sounds:
            s._terminate()

        context = self._context
        device = alcGetContextsDevice(context)
        alcMakeContextCurrent(None)
        alcDestroyContext(context)
        alcCloseDevice(device)
    

