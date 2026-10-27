#!/usr/bin/env python3
"""param_ka: side-by-side Ka=100 vs Ka=300 montages (PIL) from renders/param_ka/*.clusters.png (or .slab.png)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
R='/scratch/sroy85/Github/dna/large_crystal/hand5/final_report/renders/param_ka'
FONT='/usr/share/fonts/dejavu/DejaVuSans.ttf'
try: F=ImageFont.truetype(FONT,44); Fs=ImageFont.truetype(FONT,34)
except Exception:
    import matplotlib; p=matplotlib.get_data_path()+'/fonts/ttf/DejaVuSans.ttf'; F=ImageFont.truetype(p,44); Fs=ImageFont.truetype(p,34)
SETS=[('a0.10_Kb100_s150','alpha=0.10, Kb=100, strength=150','a0.10_Ka{ka}_Kb100_s150'),
      ('a0.05_Kb100_s100','alpha=0.05, Kb=100, strength=100','a0.05_Ka{ka}_Kb100_s100'),
      ('a0.12_Kb300_s100','alpha=0.12, Kb=300, strength=100','a0.12_Ka{ka}_Kb300_s100'),
      ('a0.03_Kb300_s10','alpha=0.03, Kb=300, strength=10','a0.03_Ka{ka}_Kb300_s10')]
W=1600; H=900
def tile(path,label):
    im=Image.open(path).convert('RGB').resize((W,H),Image.LANCZOS); d=ImageDraw.Draw(im); d.text((20,H-60),label,fill=(40,40,40),font=Fs); return im
for kind in ('clusters','slab'):
    for key,title,pat in SETS:
        rows=(('pre','before the splice (~1e8 steps or last clean frame)'),('final','final last_conf.dat'))
        canvas=Image.new('RGB',(2*W,100+2*(H+60)),'white'); d=ImageDraw.Draw(canvas)
        d.text((20,20),f'{title}   [{kind}; colour = connected cluster, grey = unbonded]',fill='black',font=F)
        for i,(st,lab) in enumerate(rows):
            for j,ka in enumerate((100,300)):
                p=f'{R}/param_ka_{st}__{pat.format(ka=ka)}.{kind}.png'
                if not os.path.exists(p): continue
                y=100+i*(H+60)
                d.text((j*W+20,y),f'Ka={ka}   {lab}',fill=(0,60,140) if ka==100 else (170,100,0),font=Fs)
                canvas.paste(tile(p,''),(j*W,y+50))
        out=f'{R}/param_ka_montage_Ka100_vs_Ka300__{key}.{kind}.png'; canvas.save(out); print(out)
# overview: all four settings, pre-splice, Ka100|Ka300 pairs in one sheet (4 rows x 2)
canvas=Image.new('RGB',(2*W,100+4*(H+60)),'white'); d=ImageDraw.Draw(canvas)
d.text((20,20),'Ka=100 (left) vs Ka=300 (right), final conformations, four settings (cluster colours)',fill='black',font=F)
for i,(key,title,pat) in enumerate(SETS):
    for j,ka in enumerate((100,300)):
        p=f'{R}/param_ka_final__{pat.format(ka=ka)}.clusters.png'
        if os.path.exists(p):
            y=100+i*(H+60); d.text((j*W+20,y),f'{title}, Ka={ka}',fill='black',font=Fs); canvas.paste(tile(p,''),(j*W,y+50))
canvas.save(f'{R}/param_ka_montage_Ka100_vs_Ka300__all_final.png'); print('ok')
