from openal.al import *
from openal.alc import *


def _checkError(device):
    _ERRMAP = {AL_NO_ERROR        : "No Error", AL_INVALID_NAME: "Invalid name", AL_INVALID_ENUM: "Invalid enum",
               AL_INVALID_VALUE   : "Invalid value", AL_INVALID_OPERATION: "Invalid operation",
               AL_OUT_OF_MEMORY   : "Out of memory", ALC_NO_ERROR: "No Error", ALC_INVALID_DEVICE: "Invalid device",
               ALC_INVALID_CONTEXT: "Invalid context", ALC_INVALID_ENUM: "Invalid ALC enum",
               ALC_INVALID_VALUE  : "Invalid ALC value", ALC_OUT_OF_MEMORY: "Out of memory"}

    def get_error_message(x):
        return _ERRMAP.get(x, "Unknown Error " + str(x))

    if device:
        err = alcGetError(device)
    else:
        err = alGetError()
    if err != AL_NO_ERROR:
        raise RuntimeError(get_error_message(err))
