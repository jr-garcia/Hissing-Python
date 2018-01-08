from openal.al import *
from openal.alc import *
import ctypes

from .Sound import Sound
from ._errorChecking import _checkError as _ckerr


class Listener(object):
    def __init__(self, device):
        self._pos = [0, 0, 0]
        self._up = [0, 1, 0]
        self.orientation = [0, 0, 0]
        self._device = device

    @property
    def position(self):
        return

    @position.setter
    def position(self, value):
        valLen = len(value)
        if valLen != 3:
            raise ValueError('wrong number of elements. Expected 3, got '+ str(valLen))
        arr = (ctypes.c_float * 3)(*value)
        alListenerfv(AL_POSITION, arr)
        self._checkError()

        # alListener3f(AL_VELOCITY, 0, 0, 0);
        # // check for errors
        # alListenerfv(AL_ORIENTATION, listenerOri);
        # // check for errors

    def _checkError(self):
        _ckerr(self._device)


class Manager(object):
    def __init__(self, ffmpegPath='ffmpeg'):
        self._ffmpegPath = ffmpegPath
        self._device = None
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

        self._listener = Listener(device)

    @property
    def listener(self):
        return self._listener

    def _checkError(self):
        _ckerr(self._device)

    def terminate(self):
        self.__del__()

    def __del__(self):

        for s in self._sounds:
            s._terminate()
        if hasattr(self, '_context'):
            context = self._context
            device = alcGetContextsDevice(context)
            alcMakeContextCurrent(None)
            alcDestroyContext(context)
            alcCloseDevice(device)
        else:
            if hasattr(self, '_device'):
                device = self._device
                alcCloseDevice(device)
    

