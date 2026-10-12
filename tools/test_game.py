"""CPU-level regression checks. Requires py65 (pip install py65).
VIC/SID and KERNAL are not emulated: this is not a VICE integration test.
"""
from pathlib import Path
import re
from py65.devices.mpu6502 import MPU

root = Path(__file__).resolve().parents[1]
symbols = dict((n, int(a,16)) for n,a in re.findall(r'\.label (\w+)=\$([0-9a-f]+)', (root/'src/main.sym').read_text()))
blob=(root/'balloon64.prg').read_bytes()
base=int.from_bytes(blob[:2], 'little')
cpu=MPU()
cpu.memory[base:base+len(blob)-2]=blob[2:]
def setv(name, value): cpu.memory[symbols[name]]=value
def get(name): return cpu.memory[symbols[name]]
def call(name):
    cpu.sp=0xff
    cpu.stPushWord(0x02ff)
    cpu.pc=symbols[name]
    for _ in range(30000):
        cpu.step()
        if cpu.pc==0x0300: return
    raise AssertionError('Routine did not return: '+name)
def start():
    call('start_game'); setv('key',0); setv('space',0)
call('menu'); assert get('state')==0
assert cpu.memory[0xd011]==0x3b and cpu.memory[0xd016]==0x18
assert cpu.memory[0xd018]==0x18
assert cpu.memory[0x400:0x7e8]==cpu.memory[symbols['title_screen']:symbols['title_screen']+1000]
assert cpu.memory[0xd800:0xdbe8]==cpu.memory[symbols['title_colors']:symbols['title_colors']+1000]
call('credits'); assert get('state')==2
assert cpu.memory[0xd011]==0x1b and cpu.memory[0xd018]==0x14
credit_lines=[(9,6,"GIOCO PER COMMODORE 64 CREATO"),
              (11,4,"CON L'INTELLIGENZA ARTIFICIALE CON"),
              (13,7,"L'INTENTO DI INNERVOSIRE IL"),(15,15,"GIOCATORE")]
for row,col,text in credit_lines:
    address=0x400+row*40+col
    assert cpu.memory[address:address+len(text)]==[ord(c)&63 for c in text]
call('options'); assert get('state')==3
assert cpu.memory[0xd015]==1 and cpu.memory[0xd027]==7
expected_sprite=[0,127,0,1,255,192,3,255,224,3,231,224,
    7,217,240,7,223,240,7,217,240,3,231,224,
    3,255,224,3,255,224,2,255,160,1,127,64,
    1,62,64,0,156,128,0,156,128,0,73,0,0,73,0,
    0,62,0,0,62,0,0,62,0,0,28,0]
assert len(expected_sprite)==63
assert cpu.memory[0x3fc0:0x4000]==expected_sprite+[0]
for key,step in [(54,1),(53,-1)]:
    setv('key',key)
    for _ in range(16):
        previous=get('balloon_color')
        call('color_input'); call('volume_text')
        chosen=(previous+step)&15
        assert get('balloon_color')==chosen and cpu.memory[0xd027]==chosen
        assert cpu.memory[0x400+16*40+32]==cpu.memory[symbols['digits']+chosen]
setv('key',54); call('color_input')
call('menu')
start(); assert get('state')==1 and cpu.memory[0xd015]==1
assert get('balloon_color')==8 and cpu.memory[0xd027]==8, 'Colour persists into gameplay'
assert cpu.memory[0xd016]==8 and cpu.memory[0xd018]==0x14
setv('space',16); call('game_tick'); first=get('velocity')
assert first==234, 'First boost is 70% of original, rounded: -22/16 px'
call('game_tick'); assert get('velocity') < first, 'Hold increases lift'
assert get('velocity')==231, 'Second boost: -25/16 px'
setv('space',0); call('game_tick'); assert get('held')==0
start(); setv('ypos',0)
cpu.memory[symbols['ypos']+1]=3
call('game_tick'); assert get('state')==4, 'Ceiling collision'
start(); setv('column',9); setv('gap_top',140); setv('gap_bottom',196)
call('game_tick'); assert get('state')==4, 'Pipe collision'
start(); setv('column',9); setv('gap_top',110); setv('gap_bottom',166)
call('game_tick'); assert get('state')==1, 'Safe opening'
start(); setv('column',6); setv('scroll_count',4)
call('game_tick'); assert cpu.memory[symbols['score']+3]==1
for _ in range(998): call('add_score')
assert cpu.memory[symbols['score']:symbols['score']+4]==[0,9,9,9]
call('add_score'); assert cpu.memory[symbols['score']:symbols['score']+4]==[1,0,0,0]
start(); setv('column',0); setv('scroll_count',4)
call('game_tick'); assert get('column')==36 and 5<=get('gap')<=12
setv('music_vol',0); setv('sfx_vol',0); call('ping'); call('audio')
assert cpu.memory[0xd404]&1==0 and cpu.memory[0xd40b]&1==0
assert cpu.memory[0xd412]==0
# Compare a full loop of machine-code playback with all source MIDI onsets.
import mido
source=mido.MidiFile(root/'music/source.mid')
melody=[]; drums=[]
for msg in source:
    if msg.type=='note_on' and msg.velocity:
        (drums if msg.channel==9 else melody).append(msg.note)
for video,clock in [(1,985248),(0,1022727)]:
    cpu.memory[0x02a6]=video
    setv('song_step',0); setv('song_wait',0); setv('music_vol',8)
    onsets=[]
    for frame in range(401):
        onset=get('song_wait')==0
        # Trigger SFX during music; it must not steal either music voice.
        if frame==100: setv('sfx_vol',12); call('ping')
        call('audio')
        if onset:
            index=len(onsets)%32
            freq=cpu.memory[0xd400]+256*cpu.memory[0xd401]
            expected=round(440*2**((melody[index]-69)/12)*2**24/clock)
            assert freq==expected and get('drum_type')==drums[index]
            onsets.append(frame)
        if frame==100: assert cpu.memory[0xd412]==0x21
    assert onsets==[25*(i//2)+13*(i%2) for i in range(33)]
    assert onsets[-1]==400, 'Eight-second loop without accumulated rounding'
print('PASS: screens, credits text, exact sprite data, all 16 colours and wrap/persistence, variable lift, release, collisions, scoring/carry, obstacle recycling, audio mute')
print('PASS: MIDI melody/percussion, full loop timing, PAL/NTSC tuning, independent SFX')
