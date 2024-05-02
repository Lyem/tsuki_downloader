import os
import re
import math
import logging
import requests
from PIL import Image
from colorama import init
from colors import bcolors
from termcolor import cprint
import logging.handlers as handlers
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter, Retry

# Configuração de log
init()
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)
logHandler = handlers.RotatingFileHandler('app.log', maxBytes=500, backupCount=2)
logHandler.setLevel(logging.INFO)
logger.addHandler(logHandler)

# Configuração PIL
Image.MAX_IMAGE_PIXELS = 933120000

# Configuração requests
r = requests.session()
retries = Retry(total=5, backoff_factor=1)
r.mount('https://', HTTPAdapter(max_retries=retries))
base = 'https://tsuki-mangas.com'
cdns = ['https://cdn.tsuki-mangas.com/tsuki','https://cdn2.tsuki-mangas.com']
ua = UserAgent()
headers = {'referer': f'{base}', 'user-agent': ua.random}

# Função para baixar páginas do capítulo
def download_pages(chapters, ch, vol):
    for c in chapters:
        if float(ch) == float(c['number']):
            n = 1
            for version in c['versions']:
                if len(c['versions']) > 1:
                    print(f"{n} - Não tem como saber a scan kk")
                n += 1

            version = 1
            if len(c['versions']) > 1:
                cprint(f'{bcolors.OKBLUE}Selecione a versão: {bcolors.OKBLUE}')
                version = int(input())

            version_id = c['versions'][version - 1]['id']

            pages = r.get(f'{base}/api/v3/chapter/versions/{version_id}', headers=headers).json()

            manga_name = (pages['chapter']['manga']['title'][:20]) if len(pages['chapter']['manga']['title']) > 20 else pages['chapter']['manga']['title']
            manga_name = re.sub('[^a-zA-Z0-9&_áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ-]', '', manga_name)
            ch_title = ''
            if(pages['chapter']['title']):
                ch_title = " ({0})".format(re.sub('[^a-zA-Z0-9&_áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\.-]', '', pages['chapter']['title']))
            pages = pages['pages']
            ch = c['number']
            groups = f"v{version}"

            if(bool(re.search("^0{1}\d", ch))):
                ch = re.sub('0', '', ch)

            cprint(f'{bcolors.WARNING}baixando cap {ch}{bcolors.END}')
            if not os.path.isdir(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]')):
                os.makedirs(os.path.join('MangaDownloads', manga_name, f'{manga_name} [pt-br] - c{ch}{vol}{ch_title} [{groups}]'))

            page_number = 1
            for page in pages:
                try:
                    for index, cdn in enumerate(cdns):
                        response = r.get(f"{cdn}{page['url']}", stream=True, headers=headers)
                        if response.status_code == 200:
                            response.raw.decode_content = True
                            img = Image.open(response.raw)
                            icc = img.info.get('icc_profile')
                            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                            width, height = img.size
                            if(height > 10000):
                                top = 0
                                left = 0
                                slices = int(math.ceil(height / 5000))
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
                                logger.info(f"falha ao baixar pagina {page_number} do cap {c['number']} - {cdn}{page['url']}")
                                page_number += 1
                except Exception as e:
                    cprint(f'{bcolors.FAIL}falha ao baixar pagina {page_number} do cap {c["number"]}{bcolors.END}')
                    logger.info(f"falha ao baixar pagina {page_number} do cap {c['number']} - {cdn}{page['url']}")
                    page_number += 1

# Início do programa
if __name__ == "__main__":
    cprint(f"{bcolors.OKBLUE}Digite o id do manga: {bcolors.END}")
    id_manga = input()

    data = r.get(f'{base}/api/v3/chapters?manga_id={id_manga}', headers=headers).json()

    chapters = []
    for i in range(int(data['lastPage'])):
        response = r.get(f'{base}/api/v3/chapters?manga_id={id_manga}&order=desc&page={i + 1}', headers=headers).json()
        chapters.extend(response['data'])

    for ch in chapters:
        print(ch['number'])

    cprint(f'Selecione os caps \n{bcolors.BOLD}EXEMPLO: 1,2,3...{bcolors.END} \nou \n{bcolors.BOLD}EXEMPLO: 1-10{bcolors.END}')
    chs_selects = input()

    cprint(f'{bcolors.OKBLUE}Qual é o volume? (se não tiver é só apertar enter):{bcolors.END} ')
    vol = str(input() or '')
    if vol != '':
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
            chs.reverse()

    for ch in chs:
        download_pages(chapters, ch, vol)
