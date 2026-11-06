"""Generate high-DPI friendly original cartographic interface assets with Pillow."""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import math, random
ASSETS=Path(__file__).with_name('assets'); ASSETS.mkdir(exist_ok=True)
R=random.Random(41)
W,H=2600,240
im=Image.new('RGB',(W,H))
p=im.load()
for y in range(H):
 for x in range(W):
  n=R.gauss(0,2.6)
  edge=min(x,W-x,y,H-y)
  shading= min(16, 450/(edge+40))
  p[x,y]=(int(232+n-shading), int(216+n-shading), int(180+n-shading))
d=ImageDraw.Draw(im,'RGBA')
for z in range(37):
 x0=z*86-250
 pts=[]
 for y in range(-20,H+30,4):
  x=x0+36*math.sin(y/47+z/2)+10*math.cos(y/21+z/4)
  pts.append((x,y))
 d.line(pts,fill=(98,79,48,43),width=2)
for z in range(3):
 pts=[]
 for x in range(400,W+40,6):
  pts.append((x,112+32*math.sin(x/91+z/6)+z*28+12*math.sin(x/23)))
 d.line(pts,fill=(104,80,42,38),width=2)
for i in range(11):
 x=450+i*189
 d.line((x,0,x+120,240),fill=(86,75,54,17),width=2)
d.rounded_rectangle((15,13,W-15,H-12),radius=18,outline=(107,78,43,90),width=3)
d.rounded_rectangle((24,22,W-24,H-21),radius=14,outline=(153,119,67,63),width=2)
im.save(ASSETS/'weathered_map_header.png', optimize=True)
# 3x raster oversampling makes the icons read like vector strokes at UI size.
S=4
for name in ['atlas','chronicles','cartography','oracle','book']:
 w=34*S
 icon=Image.new('RGBA',(w,w),(0,0,0,0)); q=ImageDraw.Draw(icon)
 green=(50,78,59,255); gold=(210,174,105,255)
 q.rounded_rectangle((2*S,2*S,32*S,32*S),radius=9*S,fill=green)
 q.rounded_rectangle((5*S,5*S,29*S,29*S),radius=7*S,outline=gold,width=2*S)
 if name=='atlas':
  q.polygon([(17*S,7*S),(21*S,17*S),(17*S,27*S),(13*S,17*S)],fill=gold)
  q.line([(17*S,7*S),(17*S,27*S)],fill=(250,239,210),width=S)
 elif name=='chronicles':
  q.rounded_rectangle((9*S,8*S,25*S,26*S),radius=S,outline=gold,width=2*S)
  for yy in (12,17,22): q.line([(12*S,yy*S),(22*S,yy*S)],fill=gold,width=S)
 elif name=='cartography':
  q.line([(8*S,10*S),(14*S,8*S),(20*S,10*S),(26*S,8*S),(26*S,25*S),(20*S,27*S),(14*S,25*S),(8*S,27*S),(8*S,10*S)],fill=gold,width=2*S)
  q.line([(14*S,8*S),(14*S,25*S)],fill=gold,width=S)
  q.line([(20*S,10*S),(20*S,27*S)],fill=gold,width=S)
 elif name=='oracle':
  q.ellipse((11*S,11*S,23*S,23*S),outline=gold,width=2*S)
  q.line([(17*S,7*S),(17*S,10*S)],fill=gold,width=2*S)
  q.line([(17*S,24*S),(17*S,27*S)],fill=gold,width=2*S)
  q.line([(7*S,17*S),(10*S,17*S)],fill=gold,width=2*S)
  q.line([(24*S,17*S),(27*S,17*S)],fill=gold,width=2*S)
 elif name=='book':
  q.line([(17*S,11*S),(17*S,25*S)],fill=gold,width=2*S)
  q.arc((7*S,10*S,17*S,27*S),90,280,fill=gold,width=2*S)
  q.arc((17*S,10*S,27*S,27*S),260,90,fill=gold,width=2*S)
 icon.resize((34,34),Image.Resampling.LANCZOS).save(ASSETS/f'nav_{name if name!="book" else "book"}.png')
print('Generated full-resolution banner and antialiased navigation icons')
