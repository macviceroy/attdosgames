# Retomar o trabalho

Branch: `feat/studio-local-editor`; base original `b2318582529033f70c5a16ee7ccc576f64ebf61c`.
Checkpoint inicial salvo no commit `b96876e`. Após esclarecer sua intenção,
o usuário pediu continuidade da implementação; o pedido anterior de encerrar
foi revogado. Não declarar todos os requisitos completos.

## Estado salvo

Editor local e todos os controles visíveis ligados a projeto/ações reais. Mídia,
revisões, jobs e logs em SQLite separado. Render FFmpeg real; análise CPU,
SRT/ASS, capas, volumes/ducking, três templates e música procedural.
Adaptador ASR local opcional, HyperFrames CLI opcional. Nenhuma publicação.
`docs/STUDIO_TESTES.md` distingue testes técnicos, falhas e itens não testados.

## Próximos passos prioritários

1. Executar instalação, importação, cancelamento e render em Windows10/11;
   verificar AMD AMF com a GPU do usuário. O ambiente atual é Linux/CPU.
2. VoiceLabs Alex já foi gerado via conector oficial e testado no fluxo local.
   Concluir revisão auditiva e termos de uso; manter tokens fora do aplicativo/Git.
   A UI exporta pedidos para Work e aceita áudio importado. Autenticação direta
   do Python ainda exige configuração externa oficial; não pedir tokens no chat.
3. Melhorar ASR com modelo local maior e corpus pt-BR autorizado; medir erros,
   revisar palavras e considerar alinhamento WhisperX em ambiente separado.
4. Camadas temporizadas já implementadas. Expandir timeline com keyframes e drag-and-drop multipista,
   preview de baixa resolução, xfade; manter um contrato Project e FFmpeg único.
5. Integrar beat grid opcional por sugestões, respeitando silêncio/contexto.
6. Avaliar semântica local/LLM com memória e licença adequadas. A heurística
   atual não entende eventos de gameplay; jamais alegar viralização garantida.
7. Integrar motion HTML ao fluxo visual, depois de revisar dependências/licenças;
   nunca aceitar HTML/JS arbitrário do frontend. CLI já gera um asset importável.
8. ZIP já implementado. Melhorar gestão de disco (limpeza/remoção/backup) e isolamento caso
   haja futura hospedagem. Servidor atual é apenas loopback e um usuário.

As 22 decisões/licenças/commits estão em `STUDIO_REPOSITORIOS.md` e JSON de auditoria.
Não incorporar o restante dos projetos indiscriminadamente nem remover módulos
existentes. Nenhum serviço vidIQ/Descript é necessário ou usado.
