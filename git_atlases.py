import subprocess
import re
import shutil
from pathlib import Path
import json
import os


def remove_bids_path(url):
    if 'github' in url:
        dataset = re.search(r"ds\d+", url)[0]
        bids_path  = re.search(r"(\d+(?:\.\d+)+)\/(.*)", url)[2]
        full_path = os.path.join(dataset, bids_path)
        return {full_path : url}
    if 'openneuro.org':
        bids_path = re.search(r".org\/(.*)(.*)?\?", url)[1]
        return {bids_path: url}

url_regex = r"https:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)"

# clone repository from openneuro datasets
atlases = {
            'ds004401': 
                {
                    'OpenNeuroID': 'ds004401', 
                    'version': {},
                    'remote': ''
                }
        }
working_dir = Path(__file__).resolve().parent


# for set in sets to clone 
for atlas in atlases.keys():
    clone_cmd = f"git clone http://github.com/OpenNeuroDatasets/{atlases[atlas]['OpenNeuroID']}.git"
    # remove old dataset
    try:
        shutil.rmtree(atlas)
    except FileNotFoundError:
        pass

    subprocess.run(clone_cmd, shell=True)

    # collect remote origin of dataset git repo
    remote_origin_cmd = f"cd {atlas} && git remote -v | grep fetch | " + "awk '{print $2}'"
    remote_origin = subprocess.run(remote_origin_cmd, shell=True, capture_output=True)
    stdout = remote_origin.stdout.decode().rstrip().rstrip('.git')
    remote_origin = stdout
    atlases[atlas]['remote'] = remote_origin

# generate s3 file manifest for each set of tags in each cloned repo
for atlas in atlases.keys():
    tags_cmd = f"git tag"
    tags = subprocess.run(tags_cmd, shell=True, capture_output=True, cwd=working_dir / Path(atlas))
    print(f"Found tags: {tags.stdout.decode().splitlines()}")
    for tag in tags.stdout.decode().splitlines():
        # update dictionary
        versions = atlases[atlas].get('version', {}) 
        versions[tag] = {'urls': []}
        atlases[atlas]['version'].update(versions)

        checkout_cmd = f"git checkout {tag} && git annex whereis | grep s3-PUBLIC > {working_dir}/{atlas}_{tag}.manifest"
        checkout = subprocess.run(checkout_cmd, shell=True, cwd=working_dir / Path(atlas))

        with open(f"{working_dir}/{atlas}_{tag}.manifest", 'r') as infile:
            lines = infile.readlines()

        with open(f"{working_dir}/{atlas}_{tag}.manifest", 'w') as outfile:
            for line in lines:
                url = re.search(r"https:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)", line)
                if url:
                    # write to dictionary as well
                    atlases[atlas]['version'][tag]['urls'].append(remove_bids_path(url[0]))
                    outfile.write(url[0] + '\n')
                    print(remove_bids_path(url=url[0]))

        # check all version files for symlinks, if local paths resolve to remote url and add to url list
        with open(f"{working_dir}/{atlas}_{tag}.manifest", 'a') as outfile:
            for root, folders, files in os.walk(os.path.join(working_dir, atlas)):
                for f in files:
                    f_path = Path(os.path.join(root, f))
                    if f_path.is_symlink():
                        pass
                    else:
                        split_f_path = str(f_path).split(atlas, 1)[1]
                        remote_local_file = f"{atlases[atlas]['remote']}/blob/{tag}{split_f_path}"
                        atlases[atlas]['version'][tag]['urls'].append(remove_bids_path(remote_local_file))
                        outfile.write(remote_local_file + '\n')
                        print(remove_bids_path(url=remote_local_file))
    
pretty_json = json.dumps(atlases, indent=2)

with open(f"{working_dir}/atlases.json", 'w') as jsonfile:
    json.dump(atlases, jsonfile, indent=4)

