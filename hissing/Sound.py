from ctypes import byref
from warnings import warn
from threading import Thread

from openal.al import *
from openal.al import alDeleteBuffers as delBuff

from ._errorChecking import _checkError as _ckerr
from .ffmpeg_reader import FFMPEG_AudioReader


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


class SoundStatesEnum(object):
    Stopped = 'Stopped'
    Playing = 'Playing'
    Paused = 'Paused'
    Initial = 'Initial'


class Sound(object):
    def __init__(self, manager, filePath, isStream=False, bufferSize=48000, maxBufferNumber=3):
        self._filePath = filePath
        self._manager = manager
        self._isStream = isStream
        self._device = manager._device
        self._bufferSize = bufferSize
        self._ffmpegPath = manager._ffmpegPath
        manager._sounds.append(self)

        bufferSize = self._bufferSize

        # create the frames extactor
        reader = FFMPEG_AudioReader(self._ffmpegPath, filePath, bufferSize, nbytes=2)
        self._reader = reader

        # create a source
        sourceID = ALuint()
        alGenSources(1, byref(sourceID))
        self._checkError()
        self._sourceID = sourceID

        # read chunk or all file
        if isStream:
            self.filler = BufferFillingThread(manager._device, sourceID, bufferSize, maxBufferNumber, reader)
            self.filler.start()
        else:
            totalBytes = reader.read_chunk(bufferSize)
            while reader.pos < reader.nframes:
                totalBytes += reader.read_chunk(bufferSize)

            # create a buffer
            bufferID = ALuint()
            alGenBuffers(1, byref(bufferID))
            self._checkError()
            self._bufferID = bufferID

            # upload data to buffer
            alBufferData(bufferID, to_al_format(reader.nchannels, 8 * reader.nbytes), totalBytes, len(totalBytes),
                         reader.fps)
            self._checkError()

            # bind source
            alSourcei(sourceID, AL_BUFFER, bufferID.value)
            self._checkError()

    def play(self):
        alSourcePlay(self._sourceID)
        self._checkError()

    def pause(self):
        alSourcePause(self._sourceID)
        self._checkError()

    def stop(self):
        alSourceStop(self._sourceID)
        self._checkError()

    def rewind(self):
        alSourceRewind(self._sourceID)
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
    def time(self):
        # http://openal.996291.n3.nabble.com/Get-Audio-time-or-buffer-position-tp1874p1875.html
        sourceID = self._sourceID
        pos = ALint()
        alGetSourcei(sourceID, AL_SAMPLE_OFFSET, byref(pos))
        self._checkError()
        pos = pos.value
        if self._isStream:
            pos += self.filler.playedLength
        return pos / self._reader.fps

    @time.setter
    def time(self, value):
        raise NotImplementedError('')

    @property
    def length(self):
        reader = self._reader
        return reader.nframes / reader.fps

    @length.setter
    def length(self, value):
        raise NotImplementedError('')

    @property
    def position(self):
        raise NotImplementedError('')

    @position.setter
    def position(self, value):
        x, y, z = value
        alSource3f(sourceID, AL_POSITION, x, y, z)  # todo: change to handle vector
        self._checkError()

    @property
    def velocity(self):
        raise NotImplementedError('')

    @velocity.setter
    def velocity(self, value):
        x, y, z = value
        alSource3f(sourceID, AL_VELOCITY, x, y, z)  # todo: change to handle vector
        self._checkError()

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
            return SoundStatesEnum.Playing
        elif state == AL_STOPPED:
            return SoundStatesEnum.Stopped
        elif state == AL_PAUSED:
            return SoundStatesEnum.Paused
        elif state == AL_INITIAL:
            return SoundStatesEnum.Initial
        else:
            raise RuntimeError('unknown source state')

    @state.setter
    def state(self, state):
        if state == SoundStatesEnum.Playing:
            self.play()
        elif state == SoundStatesEnum.Stopped:
            self.stop()
        elif state == SoundStatesEnum.Paused:
            self.pause()
        else:
            raise RuntimeError('\'{}\' state not allowed to set'.format(state))

    def _checkError(self):
        _ckerr(self._device)

    def _terminate(self):
        self.__del__()

    def __del__(self):
        try:
            if hasattr(self, '_sourceID'):
                alDeleteSources(1, self._sourceID)
            if hasattr(self, '_bufferID'):
                # next raises 'NameError: name 'alDeleteBuffers' is not defined' when imported with *
                delBuff(1, self._bufferID)
            if self._isStream:
                self.filler.terminate()

        except Exception as err:
            warn(str(err))


class BufferFillingThread(Thread):
    def __init__(self, device, sourceID, bufferSize, maxBufferNumber, audioReader):
        super(BufferFillingThread, self).__init__()
        self.device = device
        self.sourceID = sourceID
        self.bufferSize = bufferSize
        self.maxBufferNumber = maxBufferNumber
        self.audioReader = audioReader
        self.buffers = []
        self._playedBuffersLenght = 0
        self.isFinished = False

        # create buffers
        buffers = (ALuint * maxBufferNumber)()
        alGenBuffers(maxBufferNumber, buffers)
        self._checkError()
        self.buffers.extend(buffers)
        for i in range(maxBufferNumber):
            availableBufferID = ALuint(buffers[i])
            chunk = audioReader.read_chunk(bufferSize)
            self.uploadData(availableBufferID, chunk)
            self.queueBuffer(availableBufferID)

    @property
    def playedLength(self):
        return self._playedBuffersLenght

    def run(self):
        processedBuffers = ALint()
        availableBufferID = ALuint()
        chunk = None
        reader = self.audioReader
        bufferSize = self.bufferSize
        sourceID = self.sourceID

        while not self.isFinished:
            if chunk is None and reader.pos < reader.nframes:
                # read audio chunk from file
                chunk = reader.read_chunk(bufferSize)

            # find out if there are free buffers
            alGetSourcei(sourceID, AL_BUFFERS_PROCESSED, byref(processedBuffers))
            self._checkError()

            if processedBuffers.value > 0 and chunk is not None:
                # new buffer available
                self._playedBuffersLenght += bufferSize

                # unqueue buffer from source to reuse it
                self.unQueueBuffer(availableBufferID)

                # upload data to buffer
                self.uploadData(availableBufferID, chunk)
                # queue buffer into source
                self.queueBuffer(availableBufferID)
                chunk = None

    def queueBuffer(self, availableBufferID):
        alSourceQueueBuffers(self.sourceID, 1, byref(availableBufferID))
        self._checkError()

    def unQueueBuffer(self, availableBufferID):
        alSourceUnqueueBuffers(self.sourceID, 1, byref(availableBufferID))
        self._checkError()

    def uploadData(self, availableBufferID, chunk):
        reader = self.audioReader
        alBufferData(availableBufferID, to_al_format(reader.nchannels, 8 * reader.nbytes), chunk, len(chunk),
                     reader.fps)
        self._checkError()

    def _checkError(self):
        _ckerr(self.device)

    def terminate(self):
        self.isFinished = True
        self.__del__()

    def __del__(self):
        while len(self.buffers) < 0:
            bufferID = ALuint(self.buffers.pop())
            delBuff(1, bufferID)
