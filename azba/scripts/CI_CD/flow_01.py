import os
import time
import json
from git import Repo
from datetime import datetime
# from docker import DockerClient

# Initialize Docker client
# client = DockerClient.from_env()

# Define the path to your repository
repo_path = r'd:\odoo_15\odoo\addons_azba'

# Initialize the repository
repo = Repo(repo_path)

# Define the paths for production and staging
paths = {
    'production': 'odoo/addons_azba/',
    'staging': 'beta/addons_azba/'
}

# Define the docker-compose paths for production and staging
docker_compose_paths = {
    'production': 'odoo/scripts',
    'staging': 'beta'
}

while True:
    # Check for new commits every 30 seconds
    time.sleep(3)
    repo.remotes.origin.fetch()

    # Check if there are new commits
    if repo.head.commit.hexsha != repo.remotes.origin.refs.master.commit.hexsha:
        print ('New commits detected ...')
        input("Please enter to continue ...")
        # Read the .update file
        with open('~/odoo/addons_azba/.update', 'r') as file:
            data = json.load(file)

        # Get the current date/time stamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        print (f"""Will create a new branch for {data["target"]} with name {'master_' + {timestamp}} ...""")
        input("Please enter to continue ...")

        # Create a new branch without checking it out
        new_branch = repo.create_head('master_' + timestamp, 'origin/master')

        print(f"""Will Pull the changes into {paths[data['target']]} ...""")
        input("Please enter to continue ...")

        # Pull the changes in the selected target
        os.chdir(paths[data['target']])
        os.system('git pull')



        # Update the docker-compose file
        print(f"""Will Update the docker-compose file {paths[data['target']]} ...""")
        print(f"odoo -d {data['target']} -u {','.join(data['addons'])}")
        input("Please enter to continue ...")

        with open('docker-compose.yml', 'r') as file:
            docker_compose = yaml.safe_load(file)

        docker_compose['services']['odoo']['command'] = f"odoo -d {data['target']} -u {','.join(data['addons'])}"

        with open('docker-compose.yml', 'w') as file:
            yaml.dump(docker_compose, file)

        # Restart the selected installations
        os.chdir(docker_compose_paths[data['target']])
        os.system('docker-compose restart')
