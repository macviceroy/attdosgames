from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator

ID = Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
Color = Annotated[str, Field(pattern=r'^#[0-9a-fA-F]{6}$')]
FontName = Literal['DejaVu Sans','Bebas Neue','Montserrat']

class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Clip(Model):
    asset: ID
    start: float = Field(default=0, ge=0, le=14400)
    end: float = Field(gt=0, le=14400)
    focus_x: float = Field(default=.5, ge=0, le=1)
    zoom: bool = False
    @model_validator(mode='after')
    def interval(self):
        if self.end - self.start < .2:
            raise ValueError('Trecho deve ter pelo menos 0,2 s')
        return self

class Cue(Model):
    start: float = Field(ge=0, le=180)
    end: float = Field(gt=0, le=180)
    text: str = Field(min_length=1, max_length=120)
    @model_validator(mode='after')
    def interval(self):
        if self.end <= self.start or any(c in self.text for c in ['{', '}', '\\']):
            raise ValueError('Legenda inválida: intervalo ou caracteres ASS reservados')
        return self

class Track(Model):
    asset: ID
    volume: float = Field(default=1, ge=0, le=2)
    offset: float = Field(default=0, ge=0, le=179)

class Captions(Model):
    font: FontName = 'DejaVu Sans'
    style: Literal['minimal','neon','karaoke','bounce','word'] = 'neon'
    size: int = Field(default=56, ge=28, le=80)
    color: Color = '#FFFFFF'
    y: int = Field(default=1460, ge=350, le=1500)
    cues: list[Cue] = Field(default_factory=list, max_length=1800)

class Cover(Model):
    font: FontName = 'DejaVu Sans'
    time: float = Field(default=0, ge=0, le=180)
    image: ID | None = None
    title: str = Field(default='', max_length=100)
    color: Color = '#FF007A'
    y: int = Field(default=1050, ge=400, le=1250)
    size: int = Field(default=80, ge=40, le=110)

class Project(Model):
    schema_version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=100)
    title: str = Field(default='Meu novo Short', max_length=100)
    description: str = Field(default='', max_length=5000)
    hashtags: list[str] = Field(default_factory=lambda: ['#ATTDOSGAMES'], max_length=30)
    script: str = Field(default='', max_length=10000)
    template: Literal['neon','arcade','cinema'] = 'neon'
    clips: list[Clip] = Field(min_length=1, max_length=60)
    narration: Track | None = None
    music: Track | None = None
    original_volume: float = Field(default=1, ge=0, le=2)
    ducking: bool = True
    transition: Literal['cut','fade'] = 'fade'
    captions: Captions = Field(default_factory=Captions)
    cover: Cover = Field(default_factory=Cover)
    encoder: Literal['cpu','amd'] = 'cpu'
    @property
    def duration(self):
        return sum(c.end-c.start for c in self.clips)
    @model_validator(mode='after')
    def timeline(self):
        if not .5 <= self.duration <= 180:
            raise ValueError('Duração total: 0,5 a 180 s')
        previous=0
        for cue in self.captions.cues:
            if cue.start < previous or cue.end > self.duration + .001:
                raise ValueError('Legendas sobrepostas ou fora da linha do tempo')
            previous=cue.end
        if self.cover.time >= self.duration:
            raise ValueError('Frame da capa fora da linha do tempo')
        if any(len(h)>60 or not h.startswith('#') or any(c.isspace() for c in h) for h in self.hashtags):
            raise ValueError('Hashtags inválidas')
        return self

class Save(Model):
    revision: int = Field(ge=1)
    project: Project

class Analyze(Model):
    asset: ID
    seconds: float = Field(default=20, ge=3, le=60)

class Transcribe(Model):
    asset: ID

class Command(Model):
    text: str = Field(min_length=1, max_length=200)
