import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import argparse, zipfile
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8765');parser.add_argument('--fixtures',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--browser',default=None);args=parser.parse_args()
root=args.output.resolve();root.mkdir(parents=True,exist_ok=True);errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path=args.browser)
 page=browser.new_page(viewport={'width':1600,'height':1100},device_scale_factor=1)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(args.url)
 page.locator('#rightsCheck').check();page.locator('#rightsText').fill('CC0 — mídia de teste original ATT DOS GAMES')
 page.locator('#desired').fill('5')
 page.locator('#videoUpload').set_input_files(str(args.fixtures/'source.mp4'))
 expect(page.locator('#clips .clip')).to_have_count(1)
 page.locator('#name').fill('Short criado pelo navegador');page.locator('#title').fill('Seu próximo Short começa aqui');page.locator('#title').blur()
 page.locator('[data-template="arcade"]').click();page.locator('#undo').click()
 assert page.locator('[data-template="neon"]').get_attribute('class').endswith('selected')
 page.locator('#musicUpload').set_input_files(str(args.fixtures/'music.wav'))
 expect(page.locator('#music')).not_to_have_value('')
 page.locator('#layersPanel summary').click();page.locator('#addTextLayer').click();page.locator('#textLayers input[type=text]').fill('Camada criada no navegador');page.locator('#textLayers input[type=text]').blur()
 page.get_by_text('Capa e metadados',exact=True).click();page.locator('#coverTitle').fill('Capa independente');page.locator('#coverTitle').blur();page.locator('#previewCover').click();page.locator('#coverPreview a').wait_for(timeout=30000)
 page.locator('#save').click();expect(page.locator('#revision')).to_contain_text('SALVA')
 page.locator('#render').click()
 page.locator('#downloads a').first.wait_for(timeout=180000)
 assert 'aprovado' in page.locator('#qc').inner_text(),page.locator('#qc').inner_text()
 with page.expect_download() as downloaded:
  page.get_by_text('↓ Baixar todos os arquivos (ZIP)',exact=True).click()
 downloaded.value.save_as(root/'browser-export.zip')
 with zipfile.ZipFile(root/'browser-export.zip') as archive:
  assert len(archive.namelist())==8
  assert json.loads(archive.read('project.json'))['text_layers'][0]['text']=='Camada criada no navegador'
 page.locator('#preview').evaluate('(v)=>v.play()')
 page.wait_for_timeout(800)
 assert page.locator('#preview').evaluate('(v)=>v.currentTime')>0.1
 page.locator('#preview').evaluate('(v)=>v.pause()')
 page.screenshot(path=str(root/'studio-desktop.png'),full_page=True)
 page.locator('[data-tab="variations"]').click();page.locator('#analysisDuration').fill('10');page.locator('#analyze').click()
 page.locator('#candidates .candidate').nth(2).wait_for(timeout=90000)
 page.screenshot(path=str(root/'studio-variations.png'),full_page=True)
 page.locator('#candidates .candidate').first.locator('input').first.fill('1')
 page.locator('#candidates .candidate').first.get_by_role('button',name='Editar este Short').click()
 assert page.locator('#clips input').first.input_value()=='1'
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(root/'studio-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'mobile overflow'
 browser.close()
assert not errors, errors
(root/'browser-evidence.json').write_text(json.dumps({'upload':True,'project_save':True,'undo':True,'render':True,'playback':True,'variations':True,'adjust_start':True,'mobile_no_horizontal_overflow':True,'text_layer':True,'cover_preview':True,'zip_download':True,'console_errors':errors},indent=2))
print('BROWSER PASS')
