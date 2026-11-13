"""Official VoiceLabs MCP tool adapter; injected authenticated session, never inherited tokens.

The local UI exports a request for an external authorized agent. An MCP host can
also supply its own initialized official ClientSession to VoiceLabsAdapter.
No REST endpoint, OAuth client, token store or automatic retry is invented here.
"""
import hashlib
import json

PROFILE='ATT DOS GAMES - Brasileiro Alex'
TOOLS={'list_voice_profiles','speak','get_generation'}

def request_for(script):
    script=script.strip()
    if not 1<=len(script)<=5000:raise ValueError('Roteiro de voz deve ter entre 1 e 5000 caracteres')
    request_id=hashlib.sha256((PROFILE+'\npt-BR\n'+script).encode()).hexdigest()
    return {'schema_version':1,'request_id':request_id,'provider':'VoiceLabs','locale_required':'pt-BR',
            'profile_name':PROFILE,'script':script,'script_sha256':hashlib.sha256(script.encode()).hexdigest(),
            'official_mcp_tools':{'verify':'list_voice_profiles','generate':'speak','poll':'get_generation'},
            'speak_arguments':{'profileName':PROFILE,'language':'pt','text':script},
            'review_required':True,'publication_allowed':False,
            'instructions':['Verify the exact approved profile; never create or substitute a voice.',
                            'Persist generationId before polling; never repeat speak after an uncertain response.',
                            'Download the completed audio securely; do not place signed URLs or credentials in Git.',
                            'Import WAV/MP3 into the local Studio; pt does not automatically prove Brazilian accent.']}

def unpack(result):
    if getattr(result,'isError',False):raise RuntimeError('VoiceLabs recusou a operação; confira permissões no host MCP')
    if isinstance(result,dict):
        if result.get('isError'):raise RuntimeError('Erro retornado pelo VoiceLabs')
        return result.get('structuredContent',result)
    structured=getattr(result,'structuredContent',None)
    if structured is not None:return structured
    for item in getattr(result,'content',[]):
        if getattr(item,'type',None)=='text':return json.loads(item.text)
    raise ValueError('Resposta MCP sem dados estruturados')

class VoiceLabsAdapter:
    """Works with MCP ClientSession.call_tool; caller owns authentication and persistence."""
    def __init__(self,session):self.session=session
    async def verify(self):
        result=unpack(await self.session.call_tool('list_voice_profiles',arguments={}))
        voices=[p for p in result.get('profiles',[]) if p.get('name')==PROFILE and p.get('language')=='pt']
        if len(voices)!=1:raise ValueError('Perfil brasileiro aprovado indisponível; nenhum fallback permitido')
        return voices[0]
    async def generate(self,script):
        request=request_for(script);voice=await self.verify()
        # The caller must record an intent BEFORE this method and persist the result.
        # Deliberately no retry: an uncertain network response may have created audio.
        result=unpack(await self.session.call_tool('speak',arguments={**request['speak_arguments'],'profileId':voice['id']}))
        if not result.get('generationId') or result.get('profile')!=PROFILE:raise ValueError('Resposta de geração inválida; reconciliar no VoiceLabs antes de repetir')
        return {'request_id':request['request_id'],'generation_id':result['generationId'],'profile':PROFILE,'status':result['status']}
    async def poll(self,generation_id):
        import uuid
        uuid.UUID(generation_id)
        result=unpack(await self.session.call_tool('get_generation',arguments={'generationId':generation_id}))
        if result.get('profile')!=PROFILE:raise ValueError('A geração não pertence ao perfil aprovado')
        return result
