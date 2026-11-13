# Avaliação dos 22 repositórios — 13/11/2026

Consulta real de metadados, README e licença em commits fixos. Datas indicam atividade observada, não garantia de qualidade/manutenção futura. Apenas componentes explicitamente integrados foram instalados/testados; compatibilidade dos demais é documental, não um teste executado. Nenhum script de instalação upstream foi executado.

## FFmpeg/FFmpeg

- Referência: [634e00732ada](https://github.com/FFmpeg/FFmpeg/tree/634e00732ada6717191aca88cfb0b47bf89a73c9); último commit observado: 2026-11-13T04:29:28Z; arquivado: False.

- Licença lida: NOASSERTION (`LICENSE.md`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Integrado: motor único.** Cortes, concatenação, scale/crop, fades, zoom, libass, sidechaincompress, H.264/AAC, FFprobe. CPU padrão; AMF validado por codificação real antes de usar.

- Instalação, Windows, CPU/AMD, custos e conflitos: Executável Windows disponível externamente; não distribuímos binários. Sem API. Build Linux 7.1.5 com GPL/libx264; licença efetiva depende da configuração.

## Zulko/moviepy

- Referência: [211e4b15f6ce](https://github.com/Zulko/moviepy/tree/211e4b15f6ce4f34a6a9efbfff40590e43a68f77); último commit observado: 2026-08-26T06:17:07Z; arquivado: False.

- Licença lida: MIT (`LICENCE.txt`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Não instalado.** Composição Python v2, clipes, efeitos e texto. Oferece a mesma função do FFmpeg já utilizado; evitar conversão de frames em arrays e motor concorrente.

- Instalação, Windows, CPU/AMD, custos e conflitos: Windows/CPU documentados; Python/pip/FFmpeg. Sem API necessária. MIT, preservar aviso caso incorporado no futuro.

## mifi/editly

- Referência: [dc46674052ea](https://github.com/mifi/editly/tree/dc46674052eacd15ef6e0f563a58eb378b3804ad); último commit observado: 2025-02-20T13:19:17Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Não instalado.** Montagem JSON/Node e transições GLSL. Acrescenta runtime e dependências gráficas para duplicar o render existente.

- Instalação, Windows, CPU/AMD, custos e conflitos: Windows declarado; Node/npm/FFmpeg, possíveis dificuldades de módulos GL nativos. CPU possível; nenhuma aceleração AMD verificada. Sem API obrigatória.

## heygen-com/hyperframes

- Referência: [ff687fed9900](https://github.com/heygen-com/hyperframes/tree/ff687fed9900ed6a531057f2ebbed7ad43e801c6); último commit observado: 2026-11-13T05:30:01Z; arquivado: False.

- Licença lida: Apache-2.0 (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Integrado opcionalmente: 0.9.41.** HTML/CSS → MP4 via Chrome e FFmpeg. Template neon próprio e CLI attstudio.motion; saída importável no mesmo editor. Não aceita HTML enviado pelo frontend.

- Instalação, Windows, CPU/AMD, custos e conflitos: Node >=22, Chrome/Chromium, npm ci --ignore-scripts. Render local testado em software; Windows documentado upstream, não executado aqui. Sem Pro/HeyGen/API. Telemetria e update check desativados no adaptador.

## mehbul/chopify

- Referência: [d576927bf3b7](https://github.com/mehbul/chopify/tree/d576927bf3b764733c97ac1ad324aa9957b0885d); último commit observado: 2026-11-06T07:08:02Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Conceitos avaliados; sem código copiado.** Dashboard local, sugestões, legendas, projetos retomáveis e revisão antes de exportar. Inspira separação entre candidatos e decisões, sem incorporar aplicação inteira.

- Instalação, Windows, CPU/AMD, custos e conflitos: Windows é alvo primário, Python3.11+/FFmpeg, CPU. Sem assinatura/API obrigatória. Não executar instalador remoto nem habilitar download de vídeos.

## Breakthrough/PySceneDetect

- Referência: [78992833b282](https://github.com/Breakthrough/PySceneDetect/tree/78992833b28266e35eb56343d701ad24d9b505de); último commit observado: 2026-11-13T05:33:59Z; arquivado: False.

- Licença lida: BSD-3-Clause (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Integrado: scenedetect 0.6.7.1.** ContentDetector real, lista de cenas e miniaturas; ranking adicional próprio de atividade visual e RMS.

- Instalação, Windows, CPU/AMD, custos e conflitos: BSD-3-Clause. Python/OpenCV/numpy, CPU e Windows; sem CUDA/API. opencv-python-headless 4.11.0.86 e numpy 2.2.6 fixados.

## WyattBlue/auto-editor

- Referência: [98d0328ac8a6](https://github.com/WyattBlue/auto-editor/tree/98d0328ac8a67a3f943f824fb76a2f0af8c6be5b); último commit observado: 2026-11-13T05:03:30Z; arquivado: False.

- Licença lida: Unlicense (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Avaliado; não instalado.** Versão atual em Nim, análise de intensidade e remoção de espaços. Evitar motor paralelo e cortes automáticos de silêncios narrativos.

- Instalação, Windows, CPU/AMD, custos e conflitos: Repositório Unlicense; binários e app podem ter outras licenças. Instalação própria upstream; não assumir antigo pacote Python. Alternativa: RMS apenas como sugestão, sem remover cenas.

## Anil-matcha/AI-Youtube-Shorts-Generator

- Referência: [1142a747b005](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator/tree/1142a747b0056da5551970e88ca9f1ec85deafc5); último commit observado: 2026-11-12T13:36:12Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Não integrado.** Transcrição, ranking LLM e reenquadramento. Modo API padrão MuAPI; modo local ainda solicita OpenAI/Gemini no passo de ranking.

- Instalação, Windows, CPU/AMD, custos e conflitos: Python/FFmpeg/OpenCV/faster-whisper CPU disponíveis; chaves e custos no fluxo semântico. Substituído por análise heurística local explícita, sem download de terceiros.

## zhouxiaoka/autoclip

- Referência: [cd8e6bed18d8](https://github.com/zhouxiaoka/autoclip/tree/cd8e6bed18d87a81273d48bcd165751708ac715c); último commit observado: 2026-11-03T15:32:13Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Conceitos avaliados; não incorporado.** Aplicação Tauri/React/Python com edição, export kits, MCP e modelos locais ou cloud. Sobrepõe quase todo o Studio.

- Instalação, Windows, CPU/AMD, custos e conflitos: Windows x64 com instalador, CPU/local Whisper e Ollama/LM Studio; cloud cobra por uso. Documenta estatísticas/erros opcionais. Não importar telemetria, publicadores ou segunda aplicação.

## divyaprakash0426/autoshorts

- Referência: [64b75936e567](https://github.com/divyaprakash0426/autoshorts/tree/64b75936e567f74a6b9d1326f0ba154b64dc20b9); último commit observado: 2026-11-05T08:47:47Z; arquivado: False.

- Licença lida: Apache-2.0 (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Não incorporado.** Gameplay: movimento, ação, categorias e ranking; fallback libx264 existe, mas instalação exige NVIDIA, nvcc, CUDA Decord e stack FFmpeg4.

- Instalação, Windows, CPU/AMD, custos e conflitos: Apache-2.0. Dependências CUDA/PyTorch/TorchCodec conflitam com alvo AMD/CPU simples. Alternativa implementada: PySceneDetect+atividade visual+RMS; sem alegar semântica de gameplay.

## SYSTRAN/faster-whisper

- Referência: [6cb639e70786](https://github.com/SYSTRAN/faster-whisper/tree/6cb639e70786aea42b9233006ae60eaf07190bdb); último commit observado: 2026-11-12T09:05:55Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Integrado opcionalmente: 1.1.1.** Reconhecimento local language=pt, timestamps por palavra, VAD, CPU int8. Modelo local explicitamente configurado; sem download implícito.

- Instalação, Windows, CPU/AMD, custos e conflitos: MIT, CTranslate2/PyAV/ONNX. CPU funciona em Windows; GPU upstream é CUDA, portanto não usado para AMD. PyAV 14.2.0 fixado após erro real com 19.0.2. Pesos têm licença própria; tiny MIT foi testado, com erros de transcrição.

## m-bain/whisperX

- Referência: [b904f02b7e1f](https://github.com/m-bain/whisperX/tree/b904f02b7e1f26fd10fb04840d655ff27e88e464); último commit observado: 2026-11-12T17:34:05Z; arquivado: False.

- Licença lida: BSD-2-Clause (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Adiado.** Alinhamento por fonemas e diarização; pode melhorar palavras, mas PyTorch/modelos adicionais ampliam memória e instalação.

- Instalação, Windows, CPU/AMD, custos e conflitos: BSD-2-Clause no commit auditado. CPU int8 documentado, GPU CUDA opcional; alguns modelos de diarização exigem aceite/token e licença própria. Não instalado. Revisão SRT/manual como alternativa atual.

## nicolaigaina/ai-video-captions

- Referência: [bd87ac7ff104](https://github.com/nicolaigaina/ai-video-captions/tree/bd87ac7ff1040f1364ab0d162bd59cb92fcdcc9c); último commit observado: 2026-03-27T08:19:51Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Inspiração funcional; implementação própria.** Flask/faster-whisper/FFmpeg, seis estilos de legendas. Implementados em ASS: karaoke por intervalo, bounce, destaque, minimal, neon; sem copiar código.

- Instalação, Windows, CPU/AMD, custos e conflitos: MIT. Python3.11+/Node20+/Docker na aplicação original; CPU via Whisper. Evita Flask/React/segundo backend. Sem necessidade de API paga para o caminho local.

## Merserk/BeatSync-Engine

- Referência: [73a94c1be756](https://github.com/Merserk/BeatSync-Engine/tree/73a94c1be7563f15254948fcaa2b85524149435c); último commit observado: 2026-11-09T20:02:50Z; arquivado: False.

- Licença lida: GPL-3.0 (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Não incorporado.** Beat grid, energia, seleção de momentos e render musical. GPL-3.0 exigiria resolver distribuição derivada.

- Instalação, Windows, CPU/AMD, custos e conflitos: Windows portátil Python3.13, Gradio, CuPy/CUDA opcional, Qwen3-VL/Vulkan e CPU H.264. Não assumir NVIDIA necessária para todas funções. Alternativa: trilhas procedurais próprias e ducking FFmpeg; sincronização automática de cortes por batidas permanece pendente.

## browser-use/video-use

- Referência: [43cfc5668335](https://github.com/browser-use/video-use/tree/43cfc566833548093455c9d4a46bd69913b7e552); último commit observado: 2026-10-08T22:16:59Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Conceito EDL e revisão; sem código copiado.** Agente: transcrever, planejar EDL, renderizar e autoavaliar cortes. Setup documentado exige ElevenLabs e agente/LLM.

- Instalação, Windows, CPU/AMD, custos e conflitos: MIT. Instalação documentada com brew/uv; Windows não validado. API/LLM pode ter custo. Studio usa gramática local limitada que só propõe alterações verificáveis, sem eval e sem chave.

## OpenMontageInc/OpenMontage

- Referência: [fecb9a1e3cc2](https://github.com/OpenMontageInc/OpenMontage/tree/fecb9a1e3cc23ef84de30b272059457a427f16f8); último commit observado: 2026-11-09T06:23:54Z; arquivado: False.

- Licença lida: AGPL-3.0 (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Não incorporado.** Orquestração por storyboard, aprovação de assets, render e QC; aplicação ampla com múltiplos provedores e compositor.

- Instalação, Windows, CPU/AMD, custos e conflitos: AGPL-3.0: modificação/distribuição e disponibilização por rede têm obrigações de código-fonte; não copiar sem decisão jurídica. Windows PowerShell documentado, CPU/FFmpeg; serviços opcionais podem custar. Arquitetura própria mantém fases/QC sem copiar.

## harry0703/MoneyPrinterTurbo

- Referência: [82216ccbad2f](https://github.com/harry0703/MoneyPrinterTurbo/tree/82216ccbad2ff20d9c51a0cd8472e6ee6cda3f45); último commit observado: 2026-11-12T12:32:53Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Padrão de fluxo avaliado; sem código copiado.** Tema→roteiro→mídia→voz→legendas→música→exportação. WebUI/CLI/API e muitos provedores.

- Instalação, Windows, CPU/AMD, custos e conflitos: MIT. Windows10/CPU/pip/FFmpeg, Ollama local possível; TTS/mídia/LLMs cloud podem custar e precisam de credenciais. Não herdar vozes Edge/eSpeak nem downloads/licenças por suposição.

## opencut-app/opencut-classic

- Referência: [cf5e79e91914](https://github.com/opencut-app/opencut-classic/tree/cf5e79e919144200294fb9fed22a222592a0aeea); último commit observado: 2026-05-17T16:07:21Z; arquivado: True.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Descartado para integração.** Editor legado com timeline; README informa arquivado e sem manutenção; exportação em refatoração.

- Instalação, Windows, CPU/AMD, custos e conflitos: MIT. Bun/Docker/Rust/WASM aumentam stack; instruções Windows não equivalem a validação. Alternativa: frontend estático ligado ao backend real existente.

## OpenCut-app/OpenCut

- Referência: [e66801077856](https://github.com/OpenCut-app/OpenCut/tree/e668010778568641babef2cc40be4703ae6916d6); último commit observado: 2026-09-24T08:58:46Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Avaliado; não instalado.** Reescrita ativa com Editor API e headless, monorepo de ferramentas fixadas por proto/moon.

- Instalação, Windows, CPU/AMD, custos e conflitos: MIT. Windows PowerShell documentado; implica outro runtime/editor e testes de exportação próprios. Sem necessidade desta substituição; conceitos de timeline/revisões aproveitados de forma independente.

## remotion-dev/remotion

- Referência: [88cf869fa8b2](https://github.com/remotion-dev/remotion/tree/88cf869fa8b2b0bf5b6867f81a4543c03a864e98); último commit observado: 2026-11-12T19:12:20Z; arquivado: False.

- Licença lida: NOASSERTION (`LICENSE.md`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Não incorporado.** Composição React, preview e render em Chrome, batch e serviços de cloud opcionais.

- Instalação, Windows, CPU/AMD, custos e conflitos: Licença especial, não MIT/Apache: gratuita para pessoa física, entidade sem fins lucrativos ou empresa até3 empregados; demais exigem Company License. Proíbe certas redistribuições derivadas. Sem enquadramento jurídico confirmado; HyperFrames opcional como alternativa.

## Prekzursil/Reframe

- Referência: [a0ba357af9db](https://github.com/Prekzursil/Reframe/tree/a0ba357af9dbd9619e4b83005cec7fc8158f063b); último commit observado: 2026-11-04T21:08:45Z; arquivado: False.

- Licença lida: MIT (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Avaliado; não incorporado.** Editor local Electron/React/Python, JSON-RPC, modelos locais, ducking, legendas e reenquadramento.

- Instalação, Windows, CPU/AMD, custos e conflitos: MIT. Windows x64 é alvo; CPU fallback, aceleração CUDA opcional; verthor/WSL2 no reenquadramento. Integrar aplicação inteira duplicaria backend/frontend/modelos. Studio implementa crop manual e mesma representação preview/export.

## mifi/lossless-cut

- Referência: [4c7ab1cb0c9a](https://github.com/mifi/lossless-cut/tree/4c7ab1cb0c9acaefabb48e997bc909562dc3624d); último commit observado: 2026-11-03T14:13:43Z; arquivado: False.

- Licença lida: GPL-2.0 (`LICENSE`). FFmpeg/Remotion têm termos além de SPDX genérico.

- **Ferramenta auxiliar externa, opcional.** Cortes rápidos e extração sem recodificar, excelente para preparar gravações; cortes keyframe podem não ser exatos.

- Instalação, Windows, CPU/AMD, custos e conflitos: GPL-2.0 (ver termos da versão), Electron/FFmpeg, Windows/CPU; builds de lojas podem ser pagos, código fonte disponível. Não embutido, sem obrigar instalação. Exportação final precisa reencodar para efeitos/9:16.


## Escopo jurídico e dependências

Nenhum código dos projetos avaliados foi copiado para os módulos Python/JS novos. Bibliotecas são instaladas via gerenciador com lock; os avisos das distribuições integradas estão em `docs/licenses/`. HyperFrames tem `package-lock.json` próprio, Apache-2.0 na revisão npm `20084cbe67f37e2a9386402165f66233d2824baa`; não empacotamos node_modules. Seu pacote contém dependências com termos próprios (incluindo GSAP); o template usa CSS nativo, sem importar GSAP. Redistribuição completa de binários/dependências exige preservar todos os avisos e conferir licenças transitivas.

FFmpeg é executado como programa externo, não distribuído. A build usada contém libx264/GPL; o instalador Windows apenas verifica PATH. A licença de software não autoriza músicas, jogos, vídeos, vozes nem marcas. Declarações de upload são registradas, mas não constituem verificação jurídica independente.

Não há necessidade de vidIQ, Descript, cartão ou API paga. VoiceLabs continua desconectado; não se usa voz substituta no Studio.
