"""Fast standalone cover and final export use exactly the same generator."""
from PIL import Image,ImageOps,ImageDraw,ImageFilter
from .models import Project
from .media import validate_project,ff,input_args,digest

def generate(db,payload,folder,cancel):
    from .render import text_card
    p=Project.model_validate(payload['project']);validate_project(db,p)
    frame=folder/'cover-source.png'
    try:
        if p.cover.image:
            with Image.open(db.path(p.cover.image)) as image:
                base=ImageOps.fit(ImageOps.exif_transpose(image).convert('RGB'),(1080,1920))
        else:
            at=p.cover.time
            for clip in p.clips:
                seconds=clip.end-clip.start
                if at<seconds:break
                at-=seconds
            filters=f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-1080)*{clip.focus_x}:(ih-1920)/2,setsar=1'
            if clip.zoom:
                zoom=1+.00015*round(at*30)
                filters+=f",zoompan=z={zoom}:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30"
            if p.template=='neon':filters+=',eq=saturation=1.18:contrast=1.04'
            if p.template=='arcade':filters+=',scale=270:480:flags=neighbor,scale=1080:1920:flags=neighbor,drawgrid=w=1080:h=8:t=1:c=black@0.16'
            if p.template=='cinema':filters+=',eq=saturation=0.82:contrast=1.08,vignette=PI/5'
            ff(['-ss',str(clip.start+at),*input_args(db.path(clip.asset)),'-frames:v','1','-vf',filters,str(frame)],cancel=cancel)
            with Image.open(frame) as image:base=image.convert('RGB')
        base=base.convert('RGBA')
        # Cover treatment is intentionally stronger than the in-video title.
        # Each template changes composition, texture and hierarchy—not just hue.
        overlay=Image.new('RGBA',base.size,(0,0,0,0));draw=ImageDraw.Draw(overlay)
        if p.template=='neon':
            draw.rectangle((0,0,1080,1920),fill=(18,3,35,38))
            draw.rectangle((0,1280,1080,1920),fill=(8,3,22,178))
            for x,color in [(24,'#FF007A'),(42,'#00E5FF')]:draw.rounded_rectangle((x,120,1080-x,1800),radius=38,outline=color,width=7)
            glow=overlay.filter(ImageFilter.GaussianBlur(18));base=Image.alpha_composite(base,glow);base=Image.alpha_composite(base,overlay)
        elif p.template=='arcade':
            draw.rectangle((0,0,1080,1920),outline='#FFC400',width=28)
            for y in range(0,1920,12):draw.line((0,y,1080,y),fill=(0,0,0,35),width=2)
            for x in range(35,1045,55):draw.rectangle((x,90,x+22,112),fill='#00E5FF')
            base=Image.alpha_composite(base,overlay)
        else:
            draw.rectangle((0,0,1080,175),fill=(0,0,0,210));draw.rectangle((0,1670,1080,1920),fill=(0,0,0,220))
            draw.line((75,1600,1005,1600),fill=p.cover.color,width=4)
            base=Image.alpha_composite(base,overlay)
        card=text_card(p.cover.title or p.title,p.template,p.cover.size,p.cover.color,font_name=p.cover.font)
        base.alpha_composite(card,(70,p.cover.y))
        brand=ImageDraw.Draw(base);from .fonts import load,available
        fonts=available();title_font='Bebas Neue' if 'Bebas Neue' in fonts else 'DejaVu Sans';body_font='Montserrat' if 'Montserrat' in fonts else 'DejaVu Sans'
        brand.text((75,82),'ATT DOS GAMES',font=load(title_font,44),fill='white',stroke_width=2,stroke_fill=p.cover.color)
        brand.text((75,142),'@attdosgames  •  SHORT ORIGINAL',font=load(body_font,22),fill=p.cover.color)
        base.convert('RGB').save(folder/'cover.png');base.convert('RGB').save(folder/'cover.jpg',quality=94)
        return {'hashes':{name:digest(folder/name) for name in ['cover.png','cover.jpg']},'publication_allowed':False}
    finally:frame.unlink(missing_ok=True)
