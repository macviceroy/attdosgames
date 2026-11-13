# Motion HTML opcional

HyperFrames **0.9.41**, Apache-2.0, lock npm incluído. Não é necessário para o editor.
Node >=22 e Chrome/Chromium precisam estar instalados. Não executamos scripts de
instalação de terceiros. O pacote tem dependências com licenças próprias.

```powershell
cd integrations\hyperframes
npm ci --ignore-scripts
cd ..\..
# Se o Chrome não for detectado automaticamente:
$env:HYPERFRAMES_BROWSER_PATH = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
uv run python -m attstudio.motion --title 'Seu próximo Short' --output 'studio-data\intro.mp4'
```

O adaptador desativa telemetria e verificação de atualização, escapa o título,
copia a fonte licenciada e renderiza **somente o template confiável do pacote**.
Não recebe JavaScript/HTML pelo frontend. Sem serviços HeyGen/Pro.

Na Biblioteca do Studio, importe o MP4 gerado e adicione-o à montagem. O intro
não contém narração. Adicione música/voz autorizada e renderize pelo FFmpeg.
O teste real gerou3s/90frames1080×1920 e verificou importação/concatenação na
mesma pipeline; veja docs/STUDIO_TESTES.md. Windows não foi executado aqui.

O template usa animações CSS nativas e fonte local; sem CDN/GSAP. HyperFrames
inclui GSAP em seu pacote, com licença própria, mas não copiamos esse código.
Uma distribuição embutindo node_modules/binários precisa revisar e preservar
os avisos transitivos. Nesta entrega npm baixa o pacote separado.
