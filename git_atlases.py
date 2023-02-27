import subprocess
import re

# clone repository from openneuro datasets
datasets_to_clone = ['ds004401']

# for set in sets to clone 
for dataset in datasets_to_clone:
    clone_cmd = f"git clone http://github.com/OpenNeuroDatasets/{dataset}.git"
    subprocess.run(clone_cmd, shell=True)

# generate s3 file manifest for each set of tags in each cloned repo
for dataset in datasets_to_clone:
    tags_cmd = f"pushd {dataset} && git tag"
    tags = subprocess.run(tags_cmd, shell=True, capture_output=True)
    for tag in tags.stdout.decode().splitlines():
        checkout_cmd = f"git checkout {tag} && git annex whereis | grep s3-PUBLIC > {dataset}_{tag}_url_list.txt"
        checkout = subprocess.run(checkout_cmd, shell=True)

        with open(f"{dataset}_{tag}_url_list.txt", 'r') as infile:
            lines = infile.readlines()

        with open(f"{dataset}_{tag}_url_list.txt", 'w') as outfile:
            for line in lines:
                url = re.search(r"https:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)", line)
                if url:
                    outfile.write(url)


