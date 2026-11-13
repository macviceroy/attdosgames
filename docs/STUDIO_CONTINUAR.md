# Retomar o trabalho

Branch: `feat/studio-local-editor`; base original `b2318582529033f70c5a16ee7ccc576f64ebf61c`.
A pedido do usuário, a implementação foi encerrada para salvar uma entrega
funcional antes de esgotar o orçamento. Não declarar todos os requisitos completos.

## Estado salvo

Editor local e todos os controles visíveis ligados a projeto/ações reais. Mídia,
revisões, jobs e logs em SQLite separado. Render FFmpeg real; análise CPU,
SRT/ASS, capas, volumes/ducking, três templates e música procedural.
Adaptador ASR local opcional, HyperFrames CLI opcional. Nenhuma publicação.
`docs/STUDIO_TESTES.md` distingue testes técnicos, falhas e itens não testados.

## Próximos passos prioritários

1. Executar instalação, importação, cancelamento e render em Windows10/11;
   verificar AMD AMF com a GPU do usuário. O ambiente atual é Linux/CPU.
2. Testar WAV/MP3 da voz Alex autorizado e SRT revisado. Conectar VoiceLabs
   somente com API/MCP oficialmente suportado, acesso à voz e autenticação
   explícita; nenhuma credencial está disponível aqui. Não pedir tokens no chat.
3. Melhorar ASR com modelo local maior e corpus pt-BR autorizado; medir erros,
   revisar palavras e considerar alinhamento WhisperX em ambiente separado.
4. Expandir timeline: camadas de texto e keyframes, drag-and-drop multipista,
   preview de baixa resolução, xfade; manter um contrato Project e FFmpeg único.
5. Integrar beat grid opcional por sugestões, respeitando silêncio/contexto.
6. Avaliar semântica local/LLM com memória e licença adequadas. A heurística
   atual não entende eventos de gameplay; jamais alegar viralização garantida.
7. Integrar motion HTML ao fluxo visual, depois de revisar dependências/licenças;
   nunca aceitar HTML/JS arbitrário do frontend. CLI já gera um asset importável.
8. Melhorar gestão de disco (limpeza/remoção/backup/export ZIP) e isolamento caso
   haja futura hospedagem. Servidor atual é apenas loopback e um usuário.

As 22 decisões/licenças/commits estão em `STUDIO_REPOSITORIOS.md` e JSON de auditoria.
Não incorporar o restante dos projetos indiscriminadamente nem remover módulos
existentes. Nenhum serviço vidIQ/Descript é necessário ou usado.
