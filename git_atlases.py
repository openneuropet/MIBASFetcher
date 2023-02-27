import subprocess
import re
import shutil
from pathlib import Path

# clone repository from openneuro datasets
datasets_to_clone = ['ds004401']
working_dir = Path(__file__).resolve().parent


# for set in sets to clone 
for dataset in datasets_to_clone:
    clone_cmd = f"git clone http://github.com/OpenNeuroDatasets/{dataset}.git"
    # remove old dataset
    try:
        shutil.rmtree(dataset)
    except FileNotFoundError:
        pass

    subprocess.run(clone_cmd, shell=True)
 

# generate s3 file manifest for each set of tags in each cloned repo
for dataset in datasets_to_clone:
    tags_cmd = f"git tag"
    tags = subprocess.run(tags_cmd, shell=True, capture_output=True, cwd=working_dir / Path(dataset))
    print(f"Found tags: {tags}")
    for tag in tags.stdout.decode().splitlines():
        checkout_cmd = f"git checkout {tag} && git annex whereis | grep s3-PUBLIC > {working_dir}/{dataset}_{tag}_url_list.txt"
        checkout = subprocess.run(checkout_cmd, shell=True, cwd=working_dir / Path(dataset))

        with open(f"{working_dir}/{dataset}_{tag}_url_list.txt", 'r') as infile:
            lines = infile.readlines()

        with open(f"{working_dir}/{dataset}_{tag}_url_list.txt", 'w') as outfile:
            for line in lines:
                url = re.search(r"https:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)", line)
                if url:
                    outfile.write(url[0] + '\n')


