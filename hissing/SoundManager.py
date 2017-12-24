from openal.al import *
from openal.alc import *

from .Sound import Sound
from ._errorChecking import _checkError as _ckerr


class Manager(object):
    def __init__(self, ffmpegPath='ffmpeg', audioBuffer=44100):
        self.ffmpegPath = ffmpegPath
        self.audioBuffer = audioBuffer
        self._device = None
        device = alcOpenDevice(None)
        if not device:
            self._checkError()
        self._device = device

        self._sounds = []

        context = alcCreateContext(device, None)
        if not alcMakeContextCurrent(context):
            self._checkError()

        self._context = context

    def loadFile(self, filePath, isStream=False):
        sound = Sound(self, filePath, isStream, self.audioBuffer, self.ffmpegPath)
        self._sounds.append(sound)
        return sound

    def updateListener(self, position, lookFixed, rotMat):
        looklist = list(lookFixed)
        if self._lastListenerPosition != vec3(position):
            self.listenerPosition = list(position)
            self._lastListenerPosition = vec3(position)
        if self._lastListenerOrientation != looklist:
            # orien = list(lookFixed.normalize())
            orien = looklist
            # orien.extend([0, 1, 0])
            orien.extend(list(rotMat * vec3(0, 1, 0)))
            self.sink.listener.orientation = orien
            self._lastListenerOrientation = looklist
        self.sink.update()
        for sound in self._sounds.values():
            sound.update()

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
    

