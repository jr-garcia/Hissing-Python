from __future__ import print_function
from hissing import Manager, StatesEnum, Sound

sm = Manager()

file = './sounds/ice_cubes_glass/ice_cube.mp3'
'''
Ice sound by Daniel Simion
Dowmloaded from http://soundbible.com/2182-Ice-Cubes-Glass.html
'''

sound = Sound(sm, file)
sound.play()

state = sound.state
print(state, end='')
while state == StatesEnum.Playing:
    pos = sound.time
    print('\r' + state + '... Position: ' + str(pos) + ' of ' + str(sound.length), end='')
    state = sound.state

print('\rFinished')
sm.terminate()
