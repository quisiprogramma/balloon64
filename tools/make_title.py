"""Generate native VIC-II multicolour bitmap assets and a decoded preview.
Requires Pillow. No external artwork or fonts are embedded in the game.
"""
from pathlib import Path
from PIL import Image, ImageDraw
from collections import Counter
import math, random
ROOT=Path(__file__).resolve().parents[1]
PAL=[(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(46,44,155),(191,206,114),(139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
im=Image.new('RGB',(320,200),PAL[6]); d=ImageDraw.Draw(im)
random.seed(64)
for _ in range(50):
    x,y=random.randrange(8,312),random.randrange(5,127)
    d.rectangle((x,y,x+1,y+1),fill=PAL[random.choice([1,3,14])])
# Scalloped golden cloud behind the lettering.
cloud=Image.new('1',im.size); cd=ImageDraw.Draw(cloud)
cd.rounded_rectangle((27,24,293,105),radius=23,fill=1)
for x,y,r in [(39,52,19),(62,30,19),(93,24,18),(129,28,21),(169,25,20),(207,25,18),(244,30,21),(278,48,20),(275,84,20),(240,102,18),(202,106,17),(157,105,20),(112,104,18),(65,100,21),(35,83,17)]:
    cd.ellipse((x-r,y-r,x+r,y+r),fill=1)
from PIL import ImageFilter
im.paste(PAL[8],(0,0),cloud.filter(ImageFilter.MaxFilter(9)))
im.paste(PAL[7],(0,0),cloud)
d=ImageDraw.Draw(im)
# Hand-drawn rounded letter paths; heavy outline and inset shine.
paths={
'B':[[(0,0),(0,36)],[(0,0),(12,0),(19,5),(19,11),(12,17),(0,17)],[(8,17),(19,21),(20,28),(15,36),(0,36)]],
'A':[[(0,36),(3,10),(10,0),(15,0),(22,10),(24,36)],[(3,23),(21,23)]],
'L':[[(0,0),(0,35),(20,35)]],
'O':[[(10,0),(3,3),(0,12),(0,26),(4,34),(13,36),(21,31),(23,22),(23,9),(18,1),(10,0)]],
'N':[[(0,36),(0,0),(22,36),(22,0)]],
'6':[[(19,0),(7,1),(0,12),(0,28),(6,35),(17,35),(22,29),(22,22),(17,17),(2,17)]],
'4':[[(16,36),(16,0),(0,23),(23,23)]]}
def stroke(points,width,col):
    d.line(points,fill=PAL[col],width=width,joint='curve')
    r=width//2
    for x,y in points: d.ellipse((x-r,y-r,x+r,y+r),fill=PAL[col])
letters=[]
for i,c in enumerate('BALLOON'):
    x=43+i*34; y=37+[0,-3,1,-2,0,-3,0][i]
    letters += [[(x+px,y+py) for px,py in p] for p in paths[c]]
for p in letters: stroke([(x+2,y+4) for x,y in p],15,0)
for p in letters: stroke(p,13,0)
for p in letters: stroke(p,9,4)
for p in letters: stroke([(x,y-1) for x,y in p],5,10)
for p in letters:
    x,y=p[0]; stroke([(x-1,y-1),(x+1,y-3)],2,1)
# Lower badge with rounded 64.
for i,c in enumerate('64'):
    for p in paths[c]:
        q=[(141+i*24+int(x*.65),84+int(y*.65)) for x,y in p]
        stroke(q,9,0); stroke(q,5,3)
# Encode actual 160x200 multicolour pixels: shared background + 3/cell.
im=im.resize((160,200),Image.Resampling.NEAREST)
# Pixel font drawn at native resolution keeps every control readable.
glyphs={
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','11001','10101','10011','10011','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'Y':['10001','10001','01010','00100','00100','00100','00100']}
d=ImageDraw.Draw(im)
def centered(text,y,color):
    x=(160-(len(text)*6-1))//2
    for c in text:
        if c!=' ':
            for gy,row in enumerate(glyphs[c]):
                for gx,v in enumerate(row):
                    if v=='1': d.point((x+gx,y+gy),fill=PAL[color])
        x+=6
centered('SKY RUN',128,3)
d.rounded_rectangle((45,140,114,156),radius=4,fill=PAL[4])
centered('S START',145,1)
centered('C CREDITS  O OPTIONS',164,7)
centered('HOLD SPACE TO BOOST',180,1)
centered('RELEASE TO REARM',191,3)
palette=Image.new('P',(1,1))
palette.putpalette([v for c in PAL for v in c]+[0]*(768-48))
im=im.quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB')
pix=im.load(); bitmap=bytearray(); screen=bytearray(); colors=bytearray()
preview=Image.new('RGB',im.size)
for cy in range(25):
    for cx in range(40):
        cell=[pix[cx*4+x,cy*8+y] for y in range(8) for x in range(4)]
        common=[c for c,n in Counter(cell).most_common() if c!=PAL[6]][:3]
        ids=[6]+[PAL.index(c) for c in common]
        ids += [6]*(4-len(ids))
        screen.append(ids[1]*16+ids[2]); colors.append(ids[3])
        for y in range(8):
            b=0
            for x in range(4):
                rgb=pix[cx*4+x,cy*8+y]
                k=min(range(4),key=lambda k:sum((rgb[i]-PAL[ids[k]][i])**2 for i in range(3)))
                b=(b<<2)|k
                preview.putpixel((cx*4+x,cy*8+y),PAL[ids[k]])
            bitmap.append(b)
assets=ROOT/'src'/'assets'; assets.mkdir(exist_ok=True)
(assets/'title-bitmap.bin').write_bytes(bitmap)
(assets/'title-screen.bin').write_bytes(screen)
(assets/'title-colors.bin').write_bytes(colors)
preview.resize((960,600),Image.Resampling.NEAREST).save(ROOT/'title-preview.png')
print('Generated VIC-II bitmap (8000 bytes), screen (1000), colours (1000).')
