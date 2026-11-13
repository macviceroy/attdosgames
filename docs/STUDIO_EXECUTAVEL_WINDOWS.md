# Executável Windows

O workflow `Windows executable` compila e testa o Studio em um runner Windows
x64. Ele produz dois arquivos:

- `ATT-DOS-GAMES-Studio-Setup-x64.exe`: instalador por usuário, sem privilégio
  de administrador, com atalhos no menu Iniciar e opcionalmente na área de trabalho.
- `ATT-DOS-GAMES-Studio-Portable-x64.zip`: pasta portátil; extraia tudo e abra
  `ATT-DOS-GAMES-Studio.exe`. Não execute o `.exe` de dentro do ZIP.

O pacote inclui Python congelado, frontend, fontes licenciadas, FFmpeg e FFprobe.
Não precisa instalar Python, uv ou FFmpeg. A primeira abertura inicia o servidor
somente em `127.0.0.1` e abre o navegador. Projetos ficam em:

```text
%LOCALAPPDATA%\ATT DOS GAMES Studio\data
```

Desinstalar o programa não apaga automaticamente essa pasta de projetos.

## Como baixar

1. Abra a aba **Actions** do repositório.
2. Selecione **Windows executable** e a execução verde mais recente da branch
   `feat/studio-local-editor`.
3. Em **Artifacts**, baixe `ATT-DOS-GAMES-Studio-Windows-x64`.
4. Extraia o artifact. Confira `SHA256SUMS.txt` antes de abrir o instalador.

Artifacts do GitHub expiram após 30 dias e exigem login no GitHub. O arquivo
`SHA256SUMS.txt` contém o hash do instalador e do ZIP portátil. O Windows pode
mostrar SmartScreen porque o executável ainda não possui assinatura Authenticode;
isso não significa que o build falhou. Verifique o hash e a origem da execução.

## O que o build testa

- 82 testes Python da branch.
- Hash SHA-256 do ZIP oficial do FFmpeg antes de extrair.
- Execução do `.exe` congelado em modo self-test.
- Criação de vídeo de entrada com FFmpeg incluído.
- Worker iniciado como um segundo processo do próprio `.exe`.
- Renderização real H.264/AAC em 1080×1920 e FFprobe do resultado.
- Inicialização do servidor empacotado e leitura de `/api/capabilities`.
- Confirmação de que publicação continua desativada.

O runner testa Windows Server 2025 x64. Isso dá evidência real do pacote, mas
não substitui o teste final em Windows 10/11 e na GPU AMD do usuário. AMF só é
usado depois do botão **Verificar AMD AMF** passar na máquina de destino; CPU é
o padrão.

## Reproduzir o build

O workflow fixa PyInstaller 6.16.0, uv 0.9.11 e FFmpeg 9.0.2. O FFmpeg é aceito
somente se o arquivo tiver SHA-256:

```text
60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba
```

O instalador é produzido pelo Inno Setup 6.4.3. Avisos e licenças de terceiros
são copiados para o pacote. `node_modules`, bancos, tokens, mídia do usuário,
modelos Whisper e credenciais VoiceLabs não entram no executável.

## Limitações

- O executável não contém modelo faster-whisper; transcrição automática continua
  opcional. SRT importado funciona sem modelo.
- VoiceLabs conectado ao ChatGPT não fornece credenciais ao `.exe`. Use o pedido
  para Work ou importe WAV/MP3.
- HyperFrames/Node é uma integração opcional de desenvolvimento e não entra no
  pacote principal. O editor e o render FFmpeg funcionam sem ela.
- Não há assinatura digital paga nem atualização automática nesta versão.
- Nenhuma publicação para YouTube ou Instagram é habilitada.
