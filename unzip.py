import os
import zipfile
import platform
import requests

system = platform.system()
if system == 'Linux':
    chrome = requests.get('https://download-chromium.appspot.com/dl/Linux_x64')
    chrome_zip = 'Linux_x64'
elif system == 'Windowns':
    chrome = requests.get('https://download-chromium.appspot.com/dl/Win_x64')
    chrome_zip = 'Win_x64'
else:
    chrome = requests.get('https://download-chromium.appspot.com/dl/Mac')
    chrome_zip = 'Mac'


with open(os.path.join('./', chrome_zip), 'wb') as archive:
    archive.write(chrome.content)

with zipfile.ZipFile(chrome_zip, 'r') as zip_ref:
    zip_ref.extractall('.')

os.remove(os.path.join('./', chrome_zip))