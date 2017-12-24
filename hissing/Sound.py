from ctypes import byref
from warnings import warn

from openal.al import *
from openal.al import alDeleteBuffers as delBuff

from ._errorChecking import _checkError as _ckerr
from .ffmpeg_reader import FFMPEG_AudioReader


class StatesEnum(object):
    Stopped = 'Stopped'
    Playing = 'Playing'
    Paused = 'Paused'
    Initial = 'Initial'


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
        self._sourceID = sourceID

        alSource3f(sourceID, AL_POSITION, 0, 0, 0)
        self._checkError()
        alSource3f(sourceID, AL_VELOCITY, 0, 0, 0)
        self._checkError()

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
                raise RuntimeError('unknown sound format')

        # upload data to buffer
        alBufferData(bufferID, to_al_format(ar.nchannels, 8 * ar.nbytes), totalBytes, len(totalBytes), ar.fps)
        self._checkError()

        # bind source
        if isStream:
            alSourceQueueBuffers(source, n, byref(buffers))  # for streaming
        else:
            alSourcei(sourceID, AL_BUFFER, bufferID.value)
        self._checkError()

    def play(self):
        alSourcePlay(self._sourceID)
        self._checkError()

    @property
    def looped(self):
        value = ALuint()
        alSourcei(self._sourceID, AL_LOOPING, byref(value))
        self._checkError()
        return bool(value.value)

    @looped.setter
    def looped(self, value):
        alSourcei(self._sourceID, AL_LOOPING, value)
        self._checkError()

    @property
    def position(self):
        # http://openal.996291.n3.nabble.com/Get-Audio-time-or-buffer-position-tp1874p1875.html
        sourceID = self._sourceID
        pos = ALint()
        alGetSourcei(sourceID, AL_SAMPLE_OFFSET, byref(pos))
        self._checkError()
        return pos.value

    @position.setter
    def position(self, value):
        pass

    @property
    def volume(self):
        val = ALuint()
        alGetSourcef(sourceID, AL_GAIN, byref(val))
        self._checkError()
        return val.value * 100

    @volume.setter
    def volume(self, value):
        alSourcef(sourceID, AL_GAIN, value / 100)
        self._checkError()

    @property
    def pitch(self):
        val = ALuint()
        alGetSourcef(sourceID, AL_PITCH, byref(val))
        self._checkError()
        return val.value * 100

    @pitch.setter
    def pitch(self, value):
        alSourcef(sourceID, AL_PITCH, value / 100)
        self._checkError()

    @property
    def state(self):
        state = ALint()
        alGetSourcei(self._sourceID, AL_SOURCE_STATE, byref(state))
        self._checkError()
        state = state.value
        if state == AL_PLAYING:
            return StatesEnum.Playing
        elif state == AL_STOPPED:
            return StatesEnum.Stopped
        elif state == AL_PAUSED:
            return StatesEnum.Paused
        elif state == AL_INITIAL:
            return StatesEnum.Initial
        else:
            raise RuntimeError('unknown source state')

    @state.setter
    def state(self, state):
        if state == StatesEnum.Playing:
            self.play()
        elif state == StatesEnum.Stopped:
            self.stop()
        elif state == StatesEnum.Paused:
            self.pause()
        else:
            raise RuntimeError('\'{}\' state not allowed to set'.format(state))

    def _checkError(self):
        _ckerr(self._device)

    def _terminate(self):
        self.__del__()

    def __del__(self):
        try:
            alDeleteSources(1, self._sourceID)
            # next raises 'NameError: name 'alDeleteBuffers' is not defined' when imported with *
            delBuff(1, self._bufferID)  # todo: handle multiple buffers (if managed locally)
        except Exception as err:
            warn(str(err))
