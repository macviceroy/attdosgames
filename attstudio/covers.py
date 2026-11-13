"""Fast standalone cover and final export use exactly the same generator."""
from PIL import Image,ImageOps
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
        card=text_card(p.cover.title or p.title,p.template,p.cover.size,p.cover.color,font_name=p.cover.font)
        base.alpha_composite(card,(70,p.cover.y))
        base.convert('RGB').save(folder/'cover.png');base.convert('RGB').save(folder/'cover.jpg',quality=94)
        return {'hashes':{name:digest(folder/name) for name in ['cover.png','cover.jpg']},'publication_allowed':False}
    finally:frame.unlink(missing_ok=True)
