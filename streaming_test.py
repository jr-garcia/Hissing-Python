from __future__ import print_function
from hissing import Manager, StatesEnum

sm = Manager()

file = './sounds/big_buck_bunny/bbb_stereo_0_8_3.ogg'
'''
Ice sound by Daniel Simion
Dowmloaded from http://soundbible.com/2182-Ice-Cubes-Glass.html
'''

sound = sm.loadFile(file, isStreaming=True)
sound.play()

state = sound.state
print(state, end='')
while state == StatesEnum.Playing:
    pos = sound.position
    print('\r' + state + '... Positon: ' + str(pos), end='')
    state = sound.state

print('\rFinished')
sm.terminate()
