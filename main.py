import requests
from PIL import Image
import os
import re
from colors import bcolors
from colorama import init
from termcolor import cprint
import math
from fake_useragent import UserAgent
init()
ua = UserAgent()

Image.MAX_IMAGE_PIXELS = 933120000

cprint(f"{bcolors.OKBLUE}Digite o id do manga: {bcolors.END}")
id_manga = input()

base = 'https://tsuki-mangas.com'
cdns = ['https://cdn.tsuki-mangas.com/tsuki','https://cdn2.tsuki-mangas.com']

headers = {'referer': f'{base}', 'user-agent': ua.random}

data = requests.get(f'https://tsuki-mangas.com/api/v3/chapters?manga_id={id_manga}', headers=headers).json()

chapters = []

for i in range(int(data['lastPage'])):
    r = requests.get(f'{base}/api/v3/chapters?manga_id={id_manga}&order=desc&page={i + 1}', headers=headers).json()
    chapters.extend(r['data'])

for ch in chapters:
    print(ch['number'])
cprint(f'Selecione os caps \n{bcolors.BOLD}EXEMPLO: 1,2,3...{bcolors.END} \nou \n{bcolors.BOLD}EXEMPLO: 1-10{bcolors.END}')
chs_selects = input()
cprint(f'{bcolors.OKBLUE}Qual é o volume? (se não tiver é só apertar enter):{bcolors.END} ')
vol = str(input() or '')
if(vol != ''):
    vol = f' (v{vol})'
chs = chs_selects.split(',')
if len(chs) == 1:
    chs = chs_selects.split('-')
    if len(chs) > 1:
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
                n += 1

            version = 1
            if len(c['versions']) > 1:
                cprint(f'{bcolors.OKBLUE}Selecione a versão: {bcolors.OKBLUE}')
                version = int(input())

            version_id = c['versions'][version-1]['id']

            pages = requests.get(f'{base}/api/v3/chapter/versions/{version_id}', headers=headers).json()

            manga_name = (pages['chapter']['manga']['title'][:20]) if len(pages['chapter']['manga']['title']) > 20 else pages['chapter']['manga']['title']
            manga_name = re.sub('[^a-zA-Z0-9&_áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ-]','', manga_name)
            ch_title = ''
            if(pages['chapter']['title']): 
                ch_title = " ({0})".format(re.sub('[^a-zA-Z0-9&_áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\.-]','', pages['chapter']['title']))
            pages = pages['pages']
            ch = c['number']
            g = []
            if(len(c['versions'][version-1]['scans']) > 0):
                for scan in c['versions'][version-1]['scans']:
                    g.append(re.sub(' ', '', scan['scan']['name']))
                    g.append('+')
                g.pop()
            groups = "".join(g)

            if(bool(re.search("^0{1}\d", ch))):
                ch = re.sub('0','',ch)

            cprint(f'{bcolors.WARNING}baixando cap {ch}{bcolors.END}')
            if not os.path.isdir(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]')):
                os.makedirs(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]'))

            page_number = 1
            for page in pages:
                try:
                    for index, cdn in enumerate(cdns):
                        r = requests.get(f"{cdn}{page['url']}", stream=True, headers=headers)
                        if r.status_code == 200:
                            r.raw.decode_content = True
                            img = Image.open(r.raw)
                            icc = img.info.get('icc_profile')
                            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                            width, height = img.size
                            if(height > 10000):
                                top = 0
                                left = 0
                                slices = int(math.ceil(height/5000))
                                count = 1
                                for slice in range(slices):
                                    if count == slices:
                                        bottom = height
                                    else:
                                        bottom = int(count * 5000)  

                                    box = (left, top, width, bottom)
                                    img_slice = img.crop(box)
                                    top += 5000
                                    img_slice.save(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]', f"%03d.jpg" % page_number), quality=80, dpi=(72, 72), icc_profile=icc)
                                    cprint(f'{bcolors.OK}pagina {page_number} baixada com sucesso{bcolors.END}')
                                    count += 1
                                    page_number += 1
                            else:
                                img.save(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]', f"%03d.jpg" % page_number), quality=80, dpi=(72, 72), icc_profile=icc)
                                cprint(f'{bcolors.OK}pagina {page_number} baixada com sucesso{bcolors.END}')
                                page_number += 1
                            break
                        else:
                            if len(cdns) == index + 1:
                                cprint(f'{bcolors.FAIL}falha ao baixar pagina {page_number} do cap {c["number"]}{bcolors.END}')
                                print(f"{cdn}{page['url']}")
                                page_number += 1
                except Exception as e:
                    cprint(f'{bcolors.FAIL}falha ao baixar pagina {page_number} do cap {c["number"]}{bcolors.END}')
                    print(f"{cdn}{page['url']}")
                    page_number += 1
