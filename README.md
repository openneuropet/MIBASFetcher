# MIBASFetcher
Small Script/Tool That Gets MIBAS (And maybe versions of MIBAS)

## Usage

### git_atlases.py

Update atlases with `mibasfetcher/git_atlases.py`, requires git and git annex to be installed.

### fetch_atlases.py

Downloads atlas files from remote urls via curl, to update url list to the latest pet atlas run this script with the `-u/--update` flag.

Requires python3 and curl.


```bash
usage: fetch_atlases [-h] [-m MANIFEST] [-d DESTINATION] [-n DATASET_NAME] [-v DATASET_VERSION] [-s] [-u]

options:
  -h, --help            show this help message and exit
  -m MANIFEST, --manifest MANIFEST
                        Manifest file containing url's of atlases, default file is located at:
                        /Users/galassiae/Projects/MIBASFetcher/mibasfetcher/atlases.json
  -d DESTINATION, --destination DESTINATION
                        Destination path to download atlas files to
                        defaults to curent working directory if left blank, e.g.
                        /Users/galassiae/Projects/MIBASFetcher
  -n DATASET_NAME, --dataset-name DATASET_NAME
                        Name of the atlas/dataset to collect files from
                        to see available atlases use the -s/--show-atlases argument e.g.
                        --dataset-name ds004401
  -v DATASET_VERSION, --dataset-version DATASET_VERSION
                        The version of the atlas to download,
                        to list available versions use the -s argument with the atlas name to show.
                        --dataset-name <name> -s
  -s, --show-atlases    Include this flag to list available atlases and atlas versions
  -u, --update          Include this flag to update the manifest file with the latest version from github
```
