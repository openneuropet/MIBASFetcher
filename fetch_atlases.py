#! /usr/bin/env python
import urllib.request
import json
import argparse
import sys
from typing import Union
from pathlib import Path
from argparse import RawTextHelpFormatter
from os import getcwd

cwd = getcwd()


def load_manifest_urls(file_path: Union[Path, str]='atlases.json', dataset_name: str='', version: str='') -> list:
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

def list_atlases(file_path, dataset_name: str=""):
    if Path(file_path).exists() and Path(file_path).is_file():
        with open(file_path, 'r') as infile:
            atlases = json.load(infile)
            if not dataset_name:
                for atlas in atlases.keys():
                    print(atlas)
            elif dataset_name:
                versions = atlases[dataset_name]['version'].keys()
                for version in versions:
                    print(version)
    else:
        raise FileNotFoundError(f"No manifest file found at {file_path}.")
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser('fetch_atlases', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-m', '--manifest', default='atlases.json', help=f"Manifest file containing url's of atlases, default file is located at:\n{str(Path(__file__).parent.resolve())}/atlases.json")
    parser.add_argument('-d', '--destination', default=cwd, help=f"Destination path to download atlas files to\ndefaults to curent working directory if left blank, e.g.\n{cwd}")
    parser.add_argument('-n', '--dataset-name', default='', help=f"Name of the atlas/dataset to collect files from\nto see available atlases use the -s/--show-atlases argument e.g.\n--dataset-name ds004401\n")
    parser.add_argument('-v', '--dataset-version', default='', help=f"The version of the atlas to download,\nto list available versions use the -s argument with the atlas name to show.\n--dataset-name <name> -s\n")
    parser.add_argument('-s', '--show-atlases', action='store_true', help="Include this flag to list available atlases and atlas versions")

    args = parser.parse_args()

    if not args.dataset_name and not args.dataset_version and args.show_atlases:
        list_atlases(args.manifest)
    elif args.dataset_name and not args.dataset_version and args.show_atlases:
        list_atlases(args.manifest, args.dataset_name)

    elif args.dataset_name:
        if not args.dataset_version:
            print(f"Specify a dataset version to download with the --dataset-version flag\n"
                  f"To view available versions re-run previous command with -s or --show-atlases flag "
                  f"e.g.\n\n./{' '.join(sys.argv)} -s\n", 
                  file=sys.stderr)
            sys.exit(1)
        else:
            urls = load_manifest_urls(args.manifest, dataset_name=args.dataset_name, version=args.dataset_version)

            # set up destination path
            if args.dataset_name not in str(args.destination) and args.dataset_name:
                args.destination = Path(args.destination) / Path(args.dataset_name)
            if args.dataset_version not in str(args.destination) and args.dataset_version:
                args.destination = Path(args.destination) / Path(args.dataset_version)
            
            download_files(urls, destination=args.destination)
    elif len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

