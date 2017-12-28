from __future__ import print_function
from hissing import Manager, StatesEnum, Sound

sm = Manager()

file = './sounds/big_buck_bunny/bbb_stereo_0_8_3.ogg'
'''
Sound sample extracted from Big Buck Bunny short, at time 0:8:3.458
(c) copyright 2008, Blender Foundation / www.bigbuckbunny.org
'''

sound = Sound(sm, file, isStream=True)
sound.play()

state = sound.state
print(sound.state, end='')
while state == StatesEnum.Playing:
    pos = sound.time
    print('\r' + state + '... Position: ' + str(pos) + ' of ' + str(sound.length), end='')
    state = sound.state

print('\rFinished')
sm.terminate()
