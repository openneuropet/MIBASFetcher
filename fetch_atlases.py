import urllib.request
import json
import argparse
from typing import Union
from pathlib import Path


def load_manifest_urls(file_path: Union[Path, str], dataset_name: str='', version: str='') -> list:
    url_list = []
    if Path(file_path).suffix == '.json':
        if not dataset_name and not version:
            raise KeyError(f"dataset and version arguments must included to extract url list from json file.\nYou provided dataset: {dataset}, version: {version}.")
        with open(file_path, 'r') as jsonfile:
            json_contents = json.load(jsonfile)
            dataset = json_contents.get(dataset_name, {})
            version = dataset['version'].get(version, {})
        return version['urls']
    else:
        with open(file_path, 'r') as infile:
            lines = infile.readlines()
            lines = [l.strip() for l in lines]
        for line in lines:
            filename, url = line.split(' ')
            url_list.append({filename: url})
        return url_list

def download_files(manifest_urls: list, destination: Union[Path, str]=Path('downloads/')) -> None:
    url_list = manifest_urls
    for entry in url_list:
        for name, url in entry.items():
            try:
                data = urllib.request.urlopen(url=url, timeout=20)
                file_path = Path(destination) / Path(name)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                open(file_path, 'wb').write(data.read())
                print(f"Collected {name} at {url}")
            except urllib.error.HTTPError as err:
                print(f"Unable to download {name} from {url}")
                print(err)

if __name__ == "__main__":

    parser = argparse.ArgumentParser('fetch_atlases')
    parser.add_argument('manifest')
    parser.add_argument('destination')
    parser.add_argument('-n', '--dataset-name', default='')
    parser.add_argument('-v', '--dataset-version', default='')
    args = parser.parse_args()

    urls = load_manifest_urls(args.manifest, dataset_name=args.dataset_name, version=args.dataset_version)

    # set up destination path
    if args.dataset_name not in str(args.destination) and args.dataset_name:
        args.destination = Path(args.destination) / Path(args.dataset_name)
    if args.dataset_version not in str(args.destination) and args.dataset_version:
        args.destination = Path(args.destination) / Path(args.dataset_version)
    
    download_files(urls, destination=args.destination)
