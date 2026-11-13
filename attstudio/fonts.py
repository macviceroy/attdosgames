from pathlib import Path
from PIL import ImageFont
from attgames.editor import PROJECT

FILES={'DejaVu Sans':'DejaVuSans-Bold.ttf','Bebas Neue':'BebasNeue-Regular.ttf','Montserrat':'Montserrat-Regular.ttf'}
def available():
    return [name for name,file in FILES.items() if (PROJECT/'brand'/file).is_file() and (name=='DejaVu Sans' or (PROJECT/'brand'/file).with_suffix('.LICENSE.txt').is_file())]
def path(name):
    if name not in available():raise ValueError('Fonte indisponível ou sem licença em brand/')
    return PROJECT/'brand'/FILES[name]
def load(name,size):return ImageFont.truetype(str(path(name)),size)
