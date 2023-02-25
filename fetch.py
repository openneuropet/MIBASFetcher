import subprocess
import re
import requests
from pathlib import Path

# generate list of urls
url_list_cmd = "cd ds004401 && git annex whereis | grep s3-PUBLIC > ../url_list.txt"
url_list = subprocess.run(url_list_cmd, shell=True) 

# load urllist into lines
with open('url_list.txt', 'r') as infile:
    lines = infile.readlines()

# collect just urls
urls = []
for l in lines:
    url = re.search(r"https:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)", l)
    if url:
        urls.append(url[0])

# download files from web
for url in urls:
    r = requests.get(url, allow_redirects=True)
    # collect filepath from url
    filepath =  Path('downloads/') / Path(re.search(r"\.org\/(.*)(.*)?\?", url)[1])
    filepath.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {url} to {filepath}")
    
    open(filepath, 'wb').write(r.content)
