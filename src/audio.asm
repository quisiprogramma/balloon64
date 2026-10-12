// MIDI arrangement: voice 1 calliope-like square lead; voice 2 kick/clap.
// Voice 3 reserved for gameplay SFX. No note stealing from the song.
// Step tables retain every MIDI onset, including identical repeated notes.
audio:
    lda music_vol
    asl
    asl
    asl
    asl
    sta $d406
    lda sfx_vol
    asl
    asl
    asl
    asl
    sta $d414
    lda song_wait
    bne music_running
    ldx song_step
    lda song_duration,x
    sta song_wait
    lda song_drums,x
    sta drum_type
    lda #0
    sta drum_age
    lda $02a6
    beq music_ntsc
    lda song_pal_lo,x
    sta $d400
    lda song_pal_hi,x
    jmp music_pitch
music_ntsc:
    lda song_ntsc_lo,x
    sta $d400
    lda song_ntsc_hi,x
music_pitch:
    sta $d401
    lda #0
    sta $d402
    sta $d405
    sta $d40c
    lda #8
    sta $d403
    inc song_step
    lda song_step
    and #31
    sta song_step
music_running:
    lda #$41
    sta $d404
    // Retrigger repeated notes with a single release frame before next step.
    lda song_wait
    cmp #1
    bne !+
    lda #$40
    sta $d404
!:  dec song_wait
    lda drum_type
    cmp #35
    bne clap
    ldx drum_age
    cpx #6
    bcs drum_silent
    lda kick_pitch,x
    sta $d408
    lda #0
    sta $d407
    lda #$11
    sta $d40b
    jmp drum_volume
clap:
    // Three short noise bursts followed by a short tail.
    ldx drum_age
    cpx #7
    bcs drum_silent
    lda #$80
    sta $d408
    lda #0
    sta $d407
    lda clap_gate,x
    sta $d40b
drum_volume:
    lda music_vol
    asl
    asl
    asl
    asl
    sta $d40d
    jmp drum_done
drum_silent:
    lda #0
    sta $d40b
drum_done:
    inc drum_age
    lda music_vol
    bne effects
    // Waveform off as well as gate: volume zero silences even attack peaks.
    lda #0
    sta $d404
    sta $d40b
effects:
    lda effect
    beq silence
    dec effect
    lda effect
    asl
    clc
    adc #8
    sta $d40f
    lda #$21
    sta $d412
    lda sfx_vol
    bne audio_done
silence:
    lda #0
    sta $d412
audio_done:
    rts
ping:
    lda #0
    sta $d412
    lda #10
    sta effect
    rts

song_step: .byte 0
song_wait: .byte 0
drum_type: .byte 35
drum_age: .byte 0
kick_pitch: .byte 9,6,4,3,2,1
clap_gate: .byte $81,0,$81,0,$81,$81,$81
#import "song.asm"
