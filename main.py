import requests
from PIL import Image
import os
Image.MAX_IMAGE_PIXELS = 933120000

id_manga = input("Digite o id do manga: ")

chapters = requests.get(f'https://tsukimangas.com/api/v2/chapters/{id_manga}/all').json()

for ch in chapters:
    print(ch['number'])

chs_selects = input('Selecione os caps separanco com virgula \nEXEMPLO: 1,2,3... \n:')

chs = chs_selects.split(',')

for ch in chs:
    for c in chapters:
        if(float(ch) == float(c['number'])):
            n = 1
            for version in c['versions']:
                for scan in version['scans']:
                    print(f"{n} - {scan['scan']['name']}")
                n = n + 1

            version = int(input('Selecione a versão: '))

            version_id = c['versions'][version-1]['scans'][0]['chapter_version_id']

            pages = requests.get(f'https://tsukimangas.com/api/v2/chapter/versions/{version_id}').json()

            manga_name = pages['chapter']['manga']['title']
            pages = pages['pages']

            if not os.path.isdir(os.path.join('MangaDownloads', manga_name, c['number'])):
                os.makedirs(os.path.join('MangaDownloads', manga_name, c['number']))

            page_number = 1
            for page in pages:
                r = requests.get(f"https://cdn{page['server']}.tsukimangas.com/{page['url']}", stream=True)
                if r.status_code == 200:
                    r.raw.decode_content = True
                    img = Image.open(r.raw)
                    icc = img.info.get('icc_profile')
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    img.save(os.path.join('MangaDownloads', manga_name, c['number'], f"%03d.jpg" % page_number), quality=80, dpi=(72, 72), icc_profile=icc)
                    page_number = page_number + 1
                else:
                    print(f'falha ao baixar pagina {page_number}')
                    page_number = page_number + 1
