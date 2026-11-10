from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Platform = Literal['instagram', 'youtube']
SCOPES = {
    'instagram': {'instagram_business_basic', 'instagram_business_content_publish'},
    'youtube': {'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube.readonly'},
}


class PublicationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class FixtureAuth(BaseModel):
    """A test assertion, NEVER a credential or proof of actual account access."""
    model_config = ConfigDict(extra='forbid', frozen=True)
    simulated: Literal[True]
    subject: str = Field(pattern=r'^sim_[A-Za-z0-9_-]{1,60}$')
    scopes: frozenset[str]
    expires_at: datetime
    thumbnail_capability: Literal['available', 'unavailable', 'unknown'] = 'unknown'

    def validate_for(self, platform):
        if self.expires_at.tzinfo is None or self.expires_at <= datetime.now(timezone.utc):
            raise PublicationError('simulated_auth_expired', 'Fixture de autenticação expirada ou sem timezone')
        if not SCOPES[platform] <= self.scopes:
            raise PublicationError('simulated_scope_missing', f'Permissões simuladas insuficientes para {platform}')
        return {'mode': 'simulated_fixture', 'subject': self.subject,
                'scopes': sorted(self.scopes), 'real_authentication_verified': False}


class Submission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    mode: Literal['dry-run'] = 'dry-run'
    video: Path
    cover: Path
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=5000)
    hashtags: list[str] = Field(default_factory=list, max_length=5)
    platforms: list[Platform] = Field(default_factory=lambda: ['instagram', 'youtube'], min_length=1, max_length=2)
    authentication: dict[Platform, FixtureAuth]
    made_for_kids: bool | None = None

    @field_validator('title', 'description')
    @classmethod
    def text(cls, value):
        if '<' in value or '>' in value or any(ord(c) < 32 and c not in '\n\r\t' for c in value):
            raise ValueError('Metadados contêm caracteres não aceitos')
        return value.strip()

    @field_validator('title')
    @classmethod
    def nonblank(cls, value):
        if not value:
            raise ValueError('Título vazio')
        return value

    @field_validator('hashtags')
    @classmethod
    def tags(cls, values):
        normalized = []
        for value in values:
            tag = value.strip().removeprefix('#')
            if not re.fullmatch(r'\w{1,60}', tag, flags=re.UNICODE):
                raise ValueError('Hashtag inválida: use letras, números ou underscore')
            if tag.casefold() not in {t.casefold() for t in normalized}:
                normalized.append(tag)
        return normalized

    @model_validator(mode='after')
    def metadata(self):
        if len(set(self.platforms)) != len(self.platforms):
            raise ValueError('Plataforma repetida')
        if set(self.authentication) != set(self.platforms):
            raise ValueError('Forneça uma fixture explícita para cada plataforma selecionada')
        if 'instagram' in self.platforms and len(self.instagram_caption()) > 2200:
            raise ValueError('Legenda completa do Instagram excede 2200 caracteres')
        if 'youtube' in self.platforms and len(self.youtube_description().encode('utf-8')) > 5000:
            raise ValueError('Descrição completa do YouTube excede 5000 bytes UTF-8')
        return self

    def hashtag_line(self):
        return ' '.join('#' + t for t in self.hashtags)

    def instagram_caption(self):
        return '\n\n'.join(s for s in [self.title, self.description, self.hashtag_line()] if s)

    def youtube_description(self):
        return '\n\n'.join(s for s in [self.description, self.hashtag_line()] if s)
