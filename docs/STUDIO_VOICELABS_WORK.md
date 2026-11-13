# VoiceLabs e ChatGPT Work: conexão real, limites explícitos

Em13/11/2026, a conexão oficial VoiceLabs desta sessão passou a estar disponível.
Foram consultados o perfil **ATT DOS GAMES - Brasileiro Alex** e os escopos
`voice:read`/`voice:generate`. Foram geradas quatro falas reais com `speak`,
acompanhadas com `get_generation` e baixadas pelas URLs assinadas retornadas.
Não foi criada outra voz, não foi feita clonagem e não houve fallback eSpeak.
O serviço informou franquia gratuita disponível; não foi contratada assinatura.

Isso **não** fornece tokens ao Python instalado no seu Windows. O Studio local
continua funcionando sem contas e pode importar o áudio retornado pelo Work.

## Caminho disponível agora

1. Escreva o roteiro no Studio e salve o projeto.
2. Em Roteiro e legendas, clique **Preparar pedido VoiceLabs**. Baixe o JSON.
3. Entregue o JSON a um agente no Work com o aplicativo VoiceLabs autorizado.
4. Peça para verificar o perfil exato, executar os argumentos de `speak_arguments`
   com o conector oficial, guardar o `generationId` e consultar `get_generation`.
5. Baixe o WAV/MP3 concluído e importe em **Narração** no Studio.
6. Ajuste duração e legendas, escute a voz e renderize. Não publique automaticamente.

O JSON contém roteiro, hash, perfil aprovado, idioma e instruções; nenhum token.
O idioma oficial da ferramenta é `pt`; `locale_required: pt-BR` e o perfil aprovado
registram a intenção brasileira. Isso não é validação acústica do sotaque.
O Work em nuvem não acessa automaticamente `localhost` do seu Windows. Sem uma
ponte local explicitamente autorizada, a transferência é por download/importação.

## Adaptador para hosts MCP

`attstudio.voice.VoiceLabsAdapter` aceita uma sessão MCP autenticada fornecida
pelo host e usa exclusivamente os nomes oficiais `list_voice_profiles`, `speak`
e `get_generation`. É compatível com a interface `ClientSession.call_tool` do
SDK MCP. Não cria endpoint REST nem inventa OAuth. O host deve cuidar de:

- Autenticação oficial e armazenamento de segredos fora do Git.
- Registro da intenção antes da geração e persistência do ID retornado.
- Reconciliação se a resposta de `speak` for incerta: não repetir cegamente.
- Download seguro do áudio e transferência ao Studio autorizado.

O adaptador não tenta autenticar usando a conexão do ChatGPT. Testes de unidade
validam perfil exato, argumentos e ausência de retentativa/fallback com cliente
simulado; as quatro gerações reais foram testadas separadamente pelo conector
desta sessão, não pelo Python local autenticado.

URLs assinadas, tokens e informações de conta não são salvos em exemplos públicos.
A consulta web aos termos do provedor retornou403 nesta sessão. Por isso os testes
não declaram licença comercial verificada nem publicam os novos áudios no GitHub.
Os resultados técnicos e hashes estão em `studio-evidence/voicelabs-live.json`.
Sotaque, pronúncia e qualidade editorial ainda precisam de revisão auditiva humana.
