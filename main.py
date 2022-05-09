import requests
from PIL import Image
import os
import re
from colors import bcolors

Image.MAX_IMAGE_PIXELS = 933120000

id_manga = input(f"{bcolors.OKBLUE}Digite o id do manga: {bcolors.END}")

chapters = requests.get(f'https://tsukimangas.com/api/v2/chapters/{id_manga}/all').json()

for ch in chapters:
    print(ch['number'])

chs_selects = input(f'Selecione os caps \n{bcolors.BOLD}EXEMPLO: 1,2,3...{bcolors.END} \nou \n{bcolors.BOLD}EXEMPLO: 1-10{bcolors.END} \n:')
vol = str(input(f'{bcolors.OKBLUE}Qual é o volume? (se não tiver é só apertar enter):{bcolors.END} ') or '')
if(vol != ''):
    vol = f' (v{vol})'
chs = chs_selects.split(',')
if len(chs) == 1:
    chs = chs_selects.split('-')
    if len(chs) > 1:
        chs = sorted(chs)
        nmin = chs[0]
        nmax = chs[1]
        chs = []
        for ch in chapters:
            if float(ch['number']) >= float(nmin) and float(ch['number']) <= float(nmax):
                chs.append(ch['number'])

for ch in chs:
    for c in chapters:
        if(float(ch) == float(c['number'])):
            n = 1
            for version in c['versions']:
                for scan in version['scans']:
                    if len(c['versions']) > 1:
                        print(f"{n} - {scan['scan']['name']}")
                n = n + 1

            version = 1
            if len(c['versions']) > 1:
                version = int(input(f'{bcolors.OKBLUE}Selecione a versão: {bcolors.OKBLUE}'))

            version_id = c['versions'][version-1]['scans'][0]['chapter_version_id']

            pages = requests.get(f'https://tsukimangas.com/api/v2/chapter/versions/{version_id}').json()

            manga_name = pages['chapter']['manga']['title']
            ch_title = ''
            if(pages['chapter']['title']): 
                ch_title = " ({0})".format(re.sub('[^a-zA-Z0-9&_áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\.-]','', pages['chapter']['title']))
            pages = pages['pages']
            ch = c['number']
            g = []
            for scan in c['versions'][version-1]['scans']:
                g.append(re.sub(' ', '', scan['scan']['name']))
                g.append('+')
            g.pop()
            groups = "".join(g)

            if(bool(re.search("^0{1}\d", ch))):
                ch = re.sub('0','',ch)

            print(f'{bcolors.WARNING}baixando cap {ch}{bcolors.END}')
            if not os.path.isdir(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]')):
                os.makedirs(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]'))

            page_number = 1
            for page in pages:
                r = requests.get(f"https://cdn{page['server']}.tsukimangas.com/{page['url']}", stream=True)
                if r.status_code == 200:
                    r.raw.decode_content = True
                    img = Image.open(r.raw)
                    icc = img.info.get('icc_profile')
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    img.save(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]', f"%03d.jpg" % page_number), quality=80, dpi=(72, 72), icc_profile=icc)
                    print(f'{bcolors.OK}pagina {page_number} baixada com sucesso{bcolors.END}')
                    page_number = page_number + 1
                else:
                    print(f'{bcolors.FAIL}falha ao baixar pagina {page_number} do cap {c["number"]}{bcolors.END}')
                    page_number = page_number + 1
