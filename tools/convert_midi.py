"""Convert this project's 120 BPM melody + percussion MIDI to SID tables.
Requires mido. Reject unsupported arrangements instead of dropping notes.
"""
from pathlib import Path
import mido
ROOT=Path(__file__).resolve().parents[1]
m=mido.MidiFile(ROOT/'music/source.mid')
assert m.ticks_per_beat>0
onsets={1:[],9:[]}; seconds=0; programs={}; tempos=[]
for msg in m:
    seconds+=msg.time
    if msg.type=='set_tempo': tempos.append(msg.tempo)
    if msg.type=='program_change': programs[msg.channel]=msg.program
    if msg.type=='note_on' and msg.velocity:
        assert msg.channel in onsets, 'Unexpected instrument'
        onsets[msg.channel].append((seconds,msg.note,msg.velocity))
assert tempos==[500000] and programs=={1:82}
assert abs(seconds-8)<1e-6
for events in onsets.values():
    assert len(events)==32
    assert all(abs(t-i*.25)<1e-6 and v==127 for i,(t,n,v) in enumerate(events))
melody=[n for t,n,v in onsets[1]]
drums=[n for t,n,v in onsets[9]]
assert set(drums)<={35,39}
lines=['// Generated from music/source.mid. 32 eighth notes, 120 BPM, 8 seconds.',
       '// Source note-on order is preserved, including repeated notes.',
       '// 13/12-frame alternation avoids accumulated 50 Hz tempo rounding.']
def table(name,values):
    lines.append(name+':')
    lines.append('    .byte '+','.join(map(str,values)))
table('song_duration',[13,12]*16)
table('song_midi_notes',melody)
table('song_drums',drums)
for name,clock in [('pal',985248),('ntsc',1022727)]:
    freqs=[round(440*2**((n-69)/12)*2**24/clock) for n in melody]
    table('song_'+name+'_lo',[f&255 for f in freqs])
    table('song_'+name+'_hi',[f>>8 for f in freqs])
(ROOT/'src/song.asm').write_text('\n'.join(lines)+'\n')
print('Converted all 32 melody notes + 32 drum hits; 120 BPM, 400 updates / 8 s.')
