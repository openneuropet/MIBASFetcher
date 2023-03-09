#! /usr/bin/env python
import urllib.request
import json
import argparse
import sys
import time
import hashlib
import tempfile
import shutil
import subprocess
from typing import Union
from pathlib import Path
from os import getcwd, devnull


cwd = getcwd()
this_files_directory = Path(__file__).parent.absolute()

def curl(url: str, destination: Union[Path, str]):
    """
    Download the file from the given url.
    """
    curl_call = subprocess.run(f"curl -L {url} -o {destination}", shell=True, check=True)
    if curl_call.returncode != 0:
        print(f"curl call failed with return code {curl_call.returncode}")
    else:
        return destination


def md5(file_path: Path):
    """
    Calculate the md5 hash of a file.
    """
    hash_md5 = hashlib.md5()
    hash_md5.update(open(file_path, 'rb').read())
    return hash_md5.hexdigest()


def check_atlas_md5(
        file_path: Union[Path,str]=this_files_directory / Path('atlases.json'), 
        atlases_url: str='https://raw.githubusercontent.com/openneuropet/MIBASFetcher/main/mibasfetcher/atlases.json'):
    """
    Check the md5 hash of a file and download a new version if the hash does not match.
    """
    atlas_changed = False
    
    if not Path(file_path).exists():
        print(f"File {file_path} does not exist. Downloading from {atlases_url}")
        curl(atlases_url, file_path)
        atlas_changed = True

    atlases_json_md5 = md5(file_path)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = Path(tmpdir) / 'atlases.json'
        try:
            atlases_json = curl(atlases_url, tmpfile)
            #atlases_json = urllib.request.urlopen(atlases_url, timeout=10)
            #open(tmpfile, 'wb').write(atlases_json.read())
            # get hash of new file
            new_atlases_json_md5 = md5(tmpfile)
        except urllib.error.HTTPError as err:
            print(f"Unable to download {file_path} from {atlases_url}")
            print(f"Keeping local version of {file_path} with md5 hash: {atlases_json_md5}")
            print(err)
            sys.exit(1)

        if new_atlases_json_md5 != atlases_json_md5:
            print(f"New version of {file_path} found. Updating from {atlases_url}")
            shutil.copy(tmpfile, file_path)
            atlas_changed = True
        else:
            print(f"Local version of {file_path} is up to date.")
    
    return atlas_changed

def load_manifest_urls(file_path: Union[Path, str]='atlases.json', dataset_name: str='', version: str='') -> list:
    """
    Loads urls from a manifest json file or text file. Json file must be formatted with dataset name,
    version, and list of urls made up of file paths to files and urls to download the files from.

    {
    "datasetname": {
        "OpenNeuroID": "ds004401",
        "version": {
            "1.0.0": {
                "urls": [
                    {
                        "datasetname/derivatives/freesurfer/mni152/label/BA_exvivo.thresh.ctab": 
                        "https://s3.amazonaws.com/openneuro.org/ds004401/derivatives/freesurfer/mni152/label/BA_exvivo.thresh.ctab?versionId=34yjpvQZT2qwhTp72jOo8Acvd4Rcc53g"
                    },
                    {
                        "ds004401/derivatives/freesurfer/mni152/label/BA_exvivo.ctab": 
                        "https://s3.amazonaws.com/openneuro.org/ds004401/derivatives/freesurfer/mni152/label/BA_exvivo.ctab?versionId=KjHKLOsShW3qdSOVufFIv6ITGGrMcl.v"
                    }
                ]
            }
        }
    }

    Additionally, this function can load urls from a text file with the following format:

    BA_exvivo.thresh.ctab https://s3.amazonaws.com/openneuro.org/ds004401/derivatives/freesurfer/mni152/label/BA_exvivo.thresh.ctab?versionId=34yjpvQZT2qwhTp72jOo8Acvd4Rcc53g
    BA_exvivo.ctab https://s3.amazonaws.com/openneuro.org/ds004401/derivatives/freesurfer/mni152/label/BA_exvivo.ctab?versionId=KjHKLOsShW3qdSOVufFIv6ITGGrMcl.v

    Parameters
    ----------
    file_path : Union[Path, str], optional
        path to the manifest file, by default 'atlases.json'
    dataset_name : str, optional
        name of the dataset to download/collect urls from, by default ''
    version : str, optional
        version number of the dataset to collect urls from corresponds to
        git/git annex tag, by default ''

    Returns
    -------
    list
        list of dictionaries with file names and urls to download from

    Raises
    ------
    KeyError
        If no dataset name or version is provided for a json input file, this function will raise a KeyError.
    """
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
    """
    download files from a list of urls and file paths and saves them to the destination directory.

    Parameters
    ----------
    manifest_urls : list
        list of urls and file paths to download from
    destination : Union[Path, str], optional
        destination path to download files to, will be overwritten if existing, by default Path('downloads/')
    """
    url_list = manifest_urls
    for entry in url_list:
        for name, url in entry.items():
            try:
                #data = urllib.request.urlopen(url=url, timeout=20)
                file_path = Path(destination) / Path(name)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                #open(file_path, 'wb').write(data.read())
                curl(url=url, destination=file_path)
                print(f"Collected {name} at {url}")
            except urllib.error.HTTPError as err:
                print(f"Unable to download {name} from {url}")
                print(err)

def list_atlases(file_path, dataset_name: str="", display=sys.stdout):
    if Path(file_path).exists() and Path(file_path).is_file():
        with open(file_path, 'r') as infile:
            atlases = json.load(infile)
            if not dataset_name:
                for atlas in atlases.keys():
                    print(atlas, file=display)
                return []
            elif dataset_name:
                versions = atlases[dataset_name]['version'].keys()
                for version in versions:
                    print(version, file=display)
                return versions
    else:
        raise FileNotFoundError(f"No manifest file found at {file_path}.")


def main():
    parser = argparse.ArgumentParser('fetch_atlases', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-m', '--manifest', default=f"{this_files_directory}/atlases.json", help=f"Manifest file containing url's of atlases, default file is located at:\n{str(Path(__file__).parent.resolve())}/atlases.json")
    parser.add_argument('-d', '--destination', default=cwd, help=f"Destination path to download atlas files to\ndefaults to curent working directory if left blank, e.g.\n{cwd}")
    parser.add_argument('-n', '--dataset-name', default='', help=f"Name of the atlas/dataset to collect files from\nto see available atlases use the -s/--show-atlases argument e.g.\n--dataset-name ds004401\n")
    parser.add_argument('-v', '--dataset-version', default='', help=f"The version of the atlas to download,\nto list available versions use the -s argument with the atlas name to show.\n--dataset-name <name> -s\n")
    parser.add_argument('-s', '--show-atlases', action='store_true', help="Include this flag to list available atlases and atlas versions")
    parser.add_argument('-u', '--update', action='store_true', default=False, help="Include this flag to update the manifest file with the latest version from github")
    args = parser.parse_args()

    if args.update:
        # update manifest file
        check_atlas_md5(args.manifest)

    if not args.dataset_name and not args.dataset_version and args.show_atlases:
        list_atlases(args.manifest)
    elif args.dataset_name and not args.dataset_version and args.show_atlases:
        list_atlases(args.manifest, args.dataset_name)

    elif args.dataset_name:
        if not args.dataset_version:
            versions = list(list_atlases(args.manifest, args.dataset_name, display=open(devnull,'w')))
            print(f'versions = {versions}')
            # get latest version
            versions.sort(reverse=True)
            try:
                latest = versions[0]
            except IndexError:
                latest = None

            print(f"No argument provided for --dataset-version, using latest version from {args.dataset_name}, version = {latest}")
            print(f"Download will begin in 5 seconsd\nEnter ctrl c to cancel.")
            time.sleep(5)

            if latest:
                urls = load_manifest_urls(args.manifest, dataset_name=args.dataset_name, version=latest)
                # set up destination path
                if args.dataset_name not in str(args.destination) and args.dataset_name:
                    args.destination = Path(args.destination) / Path(args.dataset_name) / Path(latest)
                download_files(urls, destination=args.destination)
            else:
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


if __name__ == "__main__":
    main()