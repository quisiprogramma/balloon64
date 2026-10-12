// BALLOON 64 - assembly MOS 6502/6510, sintassi Kick Assembler.
// Frame PAL 50 Hz; su NTSC si salta un aggiornamento ogni sei frame.
BasicUpstart2(entry)
.label screen=$0400
.label ptr=$fb

entry:
    sei
    lda #$37
    sta $01
    lda #$7f
    sta $dc0d
    sta $dd0d
    lda $dc0d
    lda $dd0d
    lda #0
    sta $d01a
    sta $d020
    sta $d015
    sta $d010
    sta $d017
    sta $d01d
    sta $d01c
    sta $d01b
    lda $dd00
    ora #3
    sta $dd00
    lda #$14
    sta $d018
    lda #$1b
    sta $d011
    lda #8
    sta $d016
    lda #6
    sta $d021
    lda #255
    sta $07f8
    lda balloon_color
    sta $d027
    ldx #24
    lda #0
!:  sta $d400,x
    dex
    bpl !-
    lda #15
    sta $d418
    lda #$00
    sta $d405
    sta $d40c
    jsr menu
main:
    jsr frame
    // KERNAL keyboard scan is called manually, with IRQ disabled.
    jsr $ff9f
    jsr $ffe4
    sta key
    lda #$7f
    sta $dc00
    lda $dc01
    and #$10
    eor #$10
    sta space
    lda #$ff
    sta $dc00
    jsr audio
    lda state
    beq menu_keys
    cmp #1
    beq play_dispatch
    cmp #3
    beq options_keys
    lda key
    cmp #77
    bne main
    jsr menu
    jmp main
play_dispatch:
    jsr game_tick
    jmp main
menu_keys:
    lda key
    cmp #83
    bne !+
    jsr start_game
    jmp main
!:  cmp #67
    bne !+
    jsr credits
    jmp main
!:  cmp #79
    bne main
    jsr options
    jmp main
options_keys:
    lda key
    cmp #77
    bne !+
    jsr menu
    jmp main
!:  cmp #49
    bne !+
    lda music_vol
    beq !+
    dec music_vol
!:  lda key
    cmp #50
    bne !+
    lda music_vol
    cmp #15
    beq !+
    inc music_vol
!:  lda key
    cmp #51
    bne !+
    lda sfx_vol
    beq !+
    dec sfx_vol
    jsr ping
!:  lda key
    cmp #52
    bne !+
    lda sfx_vol
    cmp #15
    beq !+
    inc sfx_vol
    jsr ping
!:  jsr color_input
    jsr volume_text
    jmp main

// 5/6 cycle through all 16 VIC-II colours, wrapping at either end.
color_input:
    lda key
    cmp #53
    bne !+
    dec balloon_color
!:  cmp #54
    bne !+
    inc balloon_color
!:  lda balloon_color
    and #15
    sta balloon_color
    sta $d027
    rts

// Raster 250, one update per frame, with NTSC compensation ($02a6).
frame:
!:  lda $d012
    cmp #250
    beq !-
!:  lda $d012
    cmp #250
    bne !-
    lda $02a6
    bne !+
    inc ntsc_count
    lda ntsc_count
    cmp #6
    bne !+
    lda #0
    sta ntsc_count
    jmp frame
!:  rts

// Clear text and colour RAM, preserving sprite pointers.
clear:
    // Restore text mode when leaving the bitmap title screen.
    lda #$1b
    sta $d011
    lda #8
    sta $d016
    lda #$14
    sta $d018
    lda #0
    sta $d015
    ldx #0
!:  lda #32
    sta screen,x
    sta screen+250,x
    sta screen+500,x
    sta screen+750,x
    lda #1
    sta $d800,x
    sta $d8fa,x
    sta $d9f4,x
    sta $daee,x
    inx
    cpx #250
    bne !-
    rts

.macro textAt(label, address) {
    ldx #0
!:  lda label,x
    beq !+
    sta address,x
    inx
    bne !-
!:
}
menu:
    jsr clear
    lda #0
    sta state
    ldx #0
    // Copy 1000 screen and colour cells, leaving sprite pointers intact.
!:  .for (var page=0; page<4; page++) {
        lda title_screen+page*250,x
        sta screen+page*250,x
        lda title_colors+page*250,x
        sta $d800+page*250,x
    }
    inx
    cpx #250
    bne !-
    lda #$18
    sta $d018
    sta $d016
    lda #$3b
    sta $d011
    rts
credits:
    jsr clear
    lda #2
    sta state
    :textAt(credits_title, screen+5*40+13)
    :textAt(credits1, screen+9*40+6)
    :textAt(credits2, screen+11*40+4)
    :textAt(credits3, screen+13*40+7)
    :textAt(credits4, screen+15*40+15)
    :textAt(back, screen+21*40+13)
    rts
options:
    jsr clear
    lda #3
    sta state
    :textAt(options_title, screen+5*40+13)
    :textAt(music_text, screen+10*40+5)
    :textAt(sfx_text, screen+13*40+5)
    :textAt(color_text, screen+16*40+5)
    :textAt(back, screen+21*40+13)
    // Split black/white swatch makes even blue, black and white visible.
    ldx #3
!:  lda #160
    sta screen+18*40+16,x
    sta screen+19*40+16,x
    sta screen+20*40+16,x
    txa
    lsr
    sta $d800+18*40+16,x
    sta $d800+19*40+16,x
    sta $d800+20*40+16,x
    dex
    bpl !-
    lda #156
    sta $d000
    lda #194
    sta $d001
    lda #1
    sta $d015
volume_text:
    ldx music_vol
    lda digits,x
    sta screen+10*40+32
    ldx sfx_vol
    lda digits,x
    sta screen+13*40+32
    ldx balloon_color
    stx $d027
    lda digits,x
    sta screen+16*40+32
    rts

start_game:
    jsr clear
    lda balloon_color
    sta $d027
    lda #1
    sta state
    sta $d015
    lda #0
    sta ypos
    sta velocity
    sta held
    sta scroll_count
    sta score
    sta score+1
    sta score+2
    sta score+3
    lda #8
    sta ypos+1
    lda #128
    sta $d001
    lda #96
    sta $d000
    lda #36
    sta column
    jsr new_gap
    lda #160
    sta tile
    jsr draw_pipe
    :textAt(score_text, screen+4)
    jsr show_score
    ldx #39
    lda #160
!:  sta screen+24*40,x
    dex
    bpl !-
    rts

// Signed velocity in 1/16 pixel; 16-bit y uses the same scale.
// Boost curve is 70% of the original, rounded to 1/16 pixel.
// First active frame: -1.375 px/frame; maximum: -2.625 px/frame.
// After 18 frames the burner must be released before rearming.
game_tick:
    lda key
    cmp #77
    bne !+
    jmp menu
!:  lda space
    bne thrust
    lda #0
    sta held
    jmp gravity
thrust:
    lda held
    bne holding
    jsr ping
holding:
    lda held
    cmp #18
    bcs gravity
    tax
    inc held
    lda boost_velocity,x
    sta velocity
    jmp integrate
gravity:
    lda velocity
    bmi !+
    cmp #48
    bcs integrate
!:  clc
    adc #2
    sta velocity
integrate:
    ldx #0
    lda velocity
    bpl !+
    dex
!:  clc
    adc ypos
    sta ypos
    txa
    adc ypos+1
    sta ypos+1
    // Convert fixed point position into VIC sprite Y.
    lda ypos
    lsr
    lsr
    lsr
    lsr
    sta temp
    lda ypos+1
    asl
    asl
    asl
    asl
    ora temp
    sta bird_y
    sta $d001
    cmp #60
    bcc die_jump
    cmp #222
    bcs die_jump
    inc scroll_count
    lda scroll_count
    cmp #5
    bcc collision
    lda #0
    sta scroll_count
    lda #32
    sta tile
    jsr draw_pipe
    dec column
    lda column
    cmp #$ff
    bne !+
    lda #36
    sta column
    jsr new_gap
!:  lda #160
    sta tile
    jsr draw_pipe
    lda column
    cmp #5
    bne collision
    jsr add_score
    jsr ping
collision:
    // Sprite bbox x=96..119. Pipe x=24+column*8, width 24.
    lda column
    cmp #7
    bcc alive
    cmp #12
    bcs alive
    lda bird_y
    cmp gap_top
    bcc die_jump
    clc
    adc #21
    cmp gap_bottom
    bcc alive
    beq alive
die_jump:
    jmp game_over
alive:
    rts
.const sixty=60
game_over:
    lda #4
    sta state
    lda #40
    sta effect
    :textAt(over_text, screen+11*40+13)
    :textAt(back, screen+14*40+13)
    rts

// LFSR changes the opening at every wrap. Seven character rows = 56px.
new_gap:
    lda random
    asl
    bcc !+
    eor #$1d
!:  sta random
    and #7
    clc
    adc #5
    sta gap
    asl
    asl
    asl
    clc
    adc #50
    sta gap_top
    clc
    adc #56
    sta gap_bottom
    rts

// Draw or erase 3 columns, rows 2..23; no full-screen redraw in game.
draw_pipe:
    lda #<(screen+80)
    clc
    adc column
    sta ptr
    lda #>(screen+80)
    adc #0
    sta ptr+1
    ldx #2
row_loop:
    cpx gap
    bcc solid
    txa
    sec
    sbc gap
    cmp #7
    bcc next_row
solid:
    ldy #2
    lda tile
!:  sta (ptr),y
    dey
    bpl !-
next_row:
    clc
    lda ptr
    adc #40
    sta ptr
    bcc !+
    inc ptr+1
!:  inx
    cpx #24
    bne row_loop
    rts
add_score:
    ldx #3
!:  inc score,x
    lda score,x
    cmp #10
    bcc show_score
    lda #0
    sta score,x
    dex
    bpl !-
show_score:
    ldx #3
!:  lda score,x
    clc
    adc #48
    sta screen+11,x
    dex
    bpl !-
    rts

#import "audio.asm"

state: .byte 0
key: .byte 0
space: .byte 0
ntsc_count: .byte 0
ypos: .word 0
// round(0.70 * min(28 + 4 * held_frame, 60)), negated.
boost_velocity:
    .byte -22,-25,-28,-31,-34,-36,-39,-42,-42
    .byte -42,-42,-42,-42,-42,-42,-42,-42,-42
velocity: .byte 0
held: .byte 0
bird_y: .byte 0
temp: .byte 0
scroll_count: .byte 0
column: .byte 36
gap: .byte 8
gap_top: .byte 114
gap_bottom: .byte 170
tile: .byte 160
random: .byte $a7
score: .fill 4,0
music_vol: .byte 8
sfx_vol: .byte 12
balloon_color: .byte 7
beat: .byte 0
note: .byte 0
effect: .byte 0
.encoding "screencode_upper"
subtitle: .text "BALLOON 64 - SKY RUN"; .byte 0
menu_text: .text "S START    C CREDITS    O OPTIONS"; .byte 0
help1: .text "HOLD SPACE TO BOOST - RELEASE TO ARM"; .byte 0
help2: .text "FLY THROUGH THE GAPS. M RETURNS HOME"; .byte 0
credits_title: .text "C R E D I T S"; .byte 0
credits1: .text "GIOCO PER COMMODORE 64 CREATO"; .byte 0
credits2: .text "CON L'INTELLIGENZA ARTIFICIALE CON"; .byte 0
credits3: .text "L'INTENTO DI INNERVOSIRE IL"; .byte 0
credits4: .text "GIOCATORE"; .byte 0
back: .text "M - MAIN MENU"; .byte 0
options_title: .text "O P T I O N S"; .byte 0
music_text: .text "MUSIC   1 - / 2 +"; .byte 0
sfx_text: .text "SFX     3 - / 4 +"; .byte 0
color_text: .text "COLORE  5 - / 6 +"; .byte 0
digits: .text "0123456789ABCDEF"
score_text: .text "SCORE:"; .byte 0
over_text: .text "G A M E  O V E R"; .byte 0
*=$2000 "Title multicolour bitmap"
.import binary "assets/title-bitmap.bin"
*=$3fc0 "Balloon sprite"
// Exact 63 bitmap bytes supplied by the user (BASIC DATA lines 200-240).
// Last byte is alignment padding, not part of the 24x21 bitmap.
balloon:
.byte 0,127,0,1,255,192,3,255,224,3,231,224
.byte 7,217,240,7,223,240,7,217,240,3,231,224
.byte 3,255,224,3,255,224,2,255,160,1,127,64
.byte 1,62,64,0,156,128,0,156,128,0,73,0,0,73,0
.byte 0,62,0,0,62,0,0,62,0,0,28,0
.byte 0
*=$4000 "Title screen data"
title_screen:
.import binary "assets/title-screen.bin"
title_colors:
.import binary "assets/title-colors.bin"


