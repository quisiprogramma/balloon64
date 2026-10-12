"""Execute the PRG's 6502 routines and render their video RAM to PNG.
This is a software video reconstruction, NOT a VICE screenshot.
Usage: python tools/capture_screens.py /path/to/chargen-901225-01.bin
ROM is read from a local emulator installation, never copied into the repo.
"""
from pathlib import Path
import re, sys
from PIL import Image
from py65.devices.mpu6502 import MPU
root=Path(__file__).resolve().parents[1]
rom=Path(sys.argv[1]).read_bytes()
assert len(rom)==4096
sym={n:int(a,16) for n,a in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(root/'src/main.sym').read_text())}
cpu=MPU(); ram=cpu.memory
blob=(root/'balloon64.prg').read_bytes(); base=int.from_bytes(blob[:2],'little')
ram[base:base+len(blob)-2]=blob[2:]
palette=[(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(46,44,155),(191,206,114),(139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
def call(name):
    cpu.sp=255; cpu.stPushWord(0x2ff); cpu.pc=sym[name]
    for _ in range(50000):
        cpu.step()
        if cpu.pc==0x300: return
    raise RuntimeError(name)
def get(name): return ram[sym[name]]
def put(name,value): ram[sym[name]]=value
def snapshot(name):
    im=Image.new('RGB',(384,272),palette[ram[0xd020]&15])
    for y in range(200):
        for x in range(320):
            cell=(y//8)*40+x//8
            if ram[0xd011]&32:
                bits=ram[0x2000+cell*8+y%8]
                code=(bits>>(6-2*((x%8)//2)))&3
                colors=[ram[0xd021],ram[0x400+cell]>>4,ram[0x400+cell]&15,ram[0xd800+cell]]
                color=colors[code]&15
            else:
                bits=rom[ram[0x400+cell]*8+y%8]
                color=(ram[0xd800+cell] if bits&(128>>(x%8)) else ram[0xd021])&15
            im.putpixel((x+32,y+36),palette[color])
    if ram[0xd015]&1:
        address=ram[0x7f8]*64
        sx=ram[0xd000]+256*(ram[0xd010]&1)-24+32
        sy=ram[0xd001]-50+36
        for y in range(21):
            for x in range(24):
                if ram[address+y*3+x//8]&(128>>(x%8)):
                    im.putpixel((sx+x,sy+y),palette[ram[0xd027]&15])
    im.resize((768,544),Image.Resampling.NEAREST).save(root/'docs/screenshots'/f'{name}.png')
# Hardware setup corresponding to entry, without calling KERNAL/IRQ routines.
ram[0xd021]=6; ram[0xd020]=0; ram[0x7f8]=255
call('menu'); snapshot('title')
call('options'); snapshot('options')
call('start_game'); put('key',0)
# Feed space presses to the original physics; no score/position patching.
for frame in range(3000):
    target=get('gap_top')+17
    velocity=get('velocity'); velocity=velocity if velocity<128 else velocity-256
    y=(get('ypos')+256*ram[sym['ypos']+1])/16
    hold=get('held')
    pressed=(hold>0 and hold<3) or (hold==0 and y>target+3 and velocity>=0)
    put('space',16 if pressed else 0)
    call('game_tick')
    if get('state')!=1: raise RuntimeError(f'Autopilot collided at frame {frame}')
    if ram[sym['score']+3]>=1 and get('column')==13:
        snapshot('gameplay'); print('Gameplay captured after',frame+1,'updates; score',ram[sym['score']+3]); break
else: raise RuntimeError('Gameplay capture point not reached')
print('Three PNGs reconstructed from the PRG video memory.')
