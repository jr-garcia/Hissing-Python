from ctypes import byref
from warnings import warn

from openal.al import *
from openal.al import alDeleteBuffers as delBuff

from ._errorChecking import _checkError as _ckerr
from .ffmpeg_reader import FFMPEG_AudioReader


class Sound(object):
    def __init__(self, manager, filePath, isStream, bufferSize, ffmpegPath='ffmpeg'):
        self._filePath = filePath
        self._manager = manager
        self._isStream = isStream
        self._bufferSize = bufferSize
        self._ffmpegPath = ffmpegPath
        self._device = manager._device

        bufferSize = self._bufferSize

        # create the frames extactor
        ar = FFMPEG_AudioReader(ffmpegPath, filePath, bufferSize, nbytes=2)

        # create a source
        sourceID = ALuint()
        alGenSources(1, byref(sourceID))
        self._checkError()

        alSourcef(sourceID, AL_PITCH, 1)
        self._checkError()
        alSourcef(sourceID, AL_GAIN, 1)
        self._checkError()
        alSource3f(sourceID, AL_POSITION, 0, 0, 0)
        self._checkError()
        alSource3f(sourceID, AL_VELOCITY, 0, 0, 0)
        self._checkError()
        alSourcei(sourceID, AL_LOOPING, AL_FALSE)
        self._checkError()
        self._sourceID = sourceID

        # read chunk or all file
        totalBytes = ar.buffer
        if isStream:
            raise NotImplemented('! no streaming')
        else:
            while ar.pos <= ar.nframes:
                totalBytes += ar.read_chunk(bufferSize)

        # create a buffer
        bufferID = ALuint()
        alGenBuffers(1, byref(bufferID))  # todo: change to MAXBUFFERCOUNT
        self._checkError()
        self._bufferID = bufferID

        def to_al_format(channels, samples):
            stereo = channels > 1
            if samples == 16:
                if stereo:
                    return AL_FORMAT_STEREO16
                else:
                    return AL_FORMAT_MONO16
            elif samples == 8:
                if stereo:
                    return AL_FORMAT_STEREO8
                else:
                    return AL_FORMAT_MONO8
            else:
                return -1

        # upload data to buffer
        alBufferData(bufferID, to_al_format(ar.nchannels, ar.nbytes), totalBytes, len(totalBytes), ar.fps)
        self._checkError()

    def _checkError(self):
        _ckerr(self._device)

    def _terminate(self):
        self.__del__()

    def __del__(self):
        alDeleteSources(1, self._sourceID)
        # next raises NameError: name 'alDeleteBuffers' is not defined when imported with *
        try:
            delBuff(1, self._bufferID)  # todo: handle multiple buffers (if managed locally)
        except NameError as err:
            warn(str(err))
