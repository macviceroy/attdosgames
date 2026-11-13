import asyncio
import pytest
from attstudio.voice import VoiceLabsAdapter,request_for,PROFILE

class Session:
    def __init__(self,valid=True,fail=False):self.calls=[];self.valid=valid;self.fail=fail
    async def call_tool(self,name,arguments):
        self.calls.append((name,arguments))
        if name=='list_voice_profiles':return {'profiles':[{'id':'approved-voice','name':PROFILE if self.valid else 'Outra voz','language':'pt'}]}
        if name=='speak':
            if self.fail:raise ConnectionError('Resposta incerta')
            return {'profile':PROFILE,'generationId':'a4e3a4d8-2eb4-48da-9c6e-03c9d4bbe598','status':'generating'}
        return {'profile':PROFILE,'status':'completed','audioUrl':'https://example.invalid/simulated-audio'}

def test_exact_profile_and_deterministic_request():
    assert request_for('Olá, Brasil!')==request_for('Olá, Brasil!')
    assert request_for('Olá, Brasil!')['locale_required']=='pt-BR'
    s=Session();r=asyncio.run(VoiceLabsAdapter(s).generate('Olá, Brasil!'))
    assert r['generation_id'] and s.calls[1][1]['profileName']==PROFILE
    assert s.calls[1][1]['language']=='pt'

def test_no_fallback_and_no_blind_retry():
    s=Session(valid=False)
    with pytest.raises(ValueError):asyncio.run(VoiceLabsAdapter(s).generate('Texto'))
    assert len(s.calls)==1
    s=Session(fail=True)
    with pytest.raises(ConnectionError):asyncio.run(VoiceLabsAdapter(s).generate('Texto'))
    assert len([x for x in s.calls if x[0]=='speak'])==1
