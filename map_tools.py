"""Portable layered battlemaps: tile paint, imported background and vector props.

No proprietary assets or network requests. PNG output can be scaled for VTT use.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PALETTE = {
    'floor':(214,205,186),'wall':(52,63,71),'water':(69,122,153),
    'door':(155,107,69),'forest':(93,136,99),'hazard':(157,78,71),
}
TILE_NAMES=tuple(PALETTE)
PROP_NAMES=('Crate','Barrel','Tree','Stairs','Table','Doorway','Marker')
COLORS={'Crate':(148,95,58),'Barrel':(124,83,51),'Tree':(49,115,73),
        'Stairs':(131,141,151),'Table':(162,127,85),'Doorway':(173,123,76),'Marker':(204,131,68)}


def render_map(map_data,size=64,grid=True,background=None,asset_resolver=None):
    cols,rows=map_data['cols'],map_data['rows']
    if not (4<=cols<=60 and 4<=rows<=60 and 8<=size<=128):raise ValueError('Unsupported map size')
    w,h=cols*size,rows*size
    if background is not None:
        if isinstance(background,(str,Path)):
            with Image.open(background) as img:base=img.convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
        else:base=background.convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
    else:base=Image.new('RGB',(w,h),PALETTE['floor'])
    draw=ImageDraw.Draw(base)
    for y,row in enumerate(map_data['tiles']):
        for x,name in enumerate(row):
            # Floor is transparent when a user-provided background is present.
            if background is None or name!='floor':
                draw.rectangle((x*size,y*size,(x+1)*size-1,(y+1)*size-1),fill=PALETTE.get(name,PALETTE['floor']))
    for prop in map_data.get('objects',[]):
        try:
            x,y=int(prop['x']),int(prop['y']);kind=str(prop.get('kind','Marker'))
            if not (0<=x<cols and 0<=y<rows):continue
        except (ValueError,TypeError,KeyError):continue
        ww=max(1,min(12,int(prop.get('w',1) or 1)))
        hh=max(1,min(12,int(prop.get('h',1) or 1)))
        ww=min(ww,cols-x);hh=min(hh,rows-y)
        degrees=int(prop.get('rotation',0) or 0)%360
        asset=prop.get('asset_archive_id')
        if asset and asset_resolver:
            try:
                path=asset_resolver(asset)
                with Image.open(path) as opened:
                    pic=opened.convert('RGBA')
                    pic.thumbnail((4096,4096))
                    pic=pic.resize((max(1,ww*size),max(1,hh*size)),Image.Resampling.LANCZOS)
                    if degrees:pic=pic.rotate(-degrees,Image.Resampling.BICUBIC,expand=True)
                    dest_x=round((x+ww/2)*size-pic.width/2)
                    dest_y=round((y+hh/2)*size-pic.height/2)
                    base.paste(pic,(dest_x,dest_y),pic)
                continue
            except (OSError,ValueError,TypeError):
                pass # missing image: draw a visible placeholder rather than losing the map
        cx=(x+ww/2)*size;cy=(y+hh/2)*size
        rw=max(3,ww*size*.42);rh=max(3,hh*size*.42)
        color=COLORS.get(kind,COLORS['Marker']);border=(24,39,43)
        # Draw regular props in a transparent layer so rotation is useful.
        layer=Image.new('RGBA',(max(3,ww*size),max(3,hh*size)),(0,0,0,0))
        ld=ImageDraw.Draw(layer)
        lx,ly=layer.width/2,layer.height/2
        radius=min(layer.width,layer.height)*.1
        if kind in ('Crate','Stairs'):
            ld.rectangle((lx-rw,ly-rh,lx+rw,ly+rh),fill=color,outline=border,width=max(1,size//22))
            if kind=='Crate':
                ld.line((lx-rw,ly-rh,lx+rw,ly+rh),fill=border,width=max(1,size//30))
                ld.line((lx+rw,ly-rh,lx-rw,ly+rh),fill=border,width=max(1,size//30))
            else:
                for step in range(1,5):
                    ty=ly-rh+step*2*rh/5
                    ld.line((lx-rw,ty,lx+rw,ty),fill=border,width=max(1,size//30))
        elif kind=='Table':
            ld.rounded_rectangle((lx-rw,ly-rh*.75,lx+rw,ly+rh*.75),radius=max(1,radius),fill=color,outline=border,width=2)
        elif kind=='Doorway':
            ld.rectangle((lx-rw*.3,ly-rh,lx+rw*.3,ly+rh),fill=color,outline=border,width=2)
        else:
            ld.ellipse((lx-rw,ly-rh,lx+rw,ly+rh),fill=color,outline=border,width=2)
            if kind=='Tree':ld.ellipse((lx-rw*.55,ly-rh*.55,lx+rw*.55,ly+rh*.55),outline=(192,224,176),width=2)
            elif kind=='Marker':ld.ellipse((lx-3,ly-3,lx+3,ly+3),fill=(245,234,207))
        if degrees:layer=layer.rotate(-degrees,Image.Resampling.BICUBIC,expand=True)
        base.paste(layer,(round(cx-layer.width/2),round(cy-layer.height/2)),layer)
    if grid:
        grid_color=(113,125,130) if background is None else (91,94,91)
        for x in range(cols+1):draw.line((x*size,0,x*size,h),fill=grid_color,width=max(1,size//70))
        for y in range(rows+1):draw.line((0,y*size,w,y*size),fill=grid_color,width=max(1,size//70))
    return base


def export_map(map_data,path,grid=True,background=None,asset_resolver=None):
    render_map(map_data,grid=grid,background=background,asset_resolver=asset_resolver).save(path,'PNG')
