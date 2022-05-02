# snakemake-kubernetes-api
Flask API to issue snakemake command based on a request.
The API is to be used for the new data processing layer of ORCESTRA. 

## Set up
All commands should be executed from the user's top level directory.

### Update the package manager 
```
sudo apt-get update
sudo apt upgrade
```

### Set firewall with Uncomplicated Firewall (ufw) to allow only ssh, http and https connections to the server.
```
sudo ufw allow ssh http https
```

### Install git (if not already installed) and clone the API repository
```
sudo apt install git
git clone https://github.com/bhklab/snakemake-kubernetes-api.git
scp -i path_to_the_key path_to_the_.env_file username>@hostname:/path_to_the_app's_root_dir
```

### Install kubectl
Install kubectl to be used by Python's kubernetes client package by using the instructions available here: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/.

Once the kubectl installation is verified, connect the kubectl to Compute Canada's kubernetes cluster:
1. Create .kube directory in the user root. ```mkdir .kube```
2. Obtain the 'config' file for the kubernetes cluster and add it to the .kube directory.
3. Ensure that kubectl is now pointing to the lab's kubernetes cluster: ```kubectl version```

### Install Miniconda and set up python environment
To get started with setup you can install miniconda3 using the instructions available here: https://docs.conda.io/en/latest/miniconda.html.
Installation Guide: https://conda.io/projects/conda/en/latest/user-guide/install/linux.html#install-linux-silent.

1. Create orcestra-snakemake environment: ```conda env create --file snakemake-kubernetes-api/setup/orcestra-snakemake.yml```
2. If it is not automatically activated after installation please run ```conda activate orcestra-snakemake``` before proceeding to the next step.
3. Install additional dependencies used for the API: ```pip install -r snakemake-kubernetes-api/requirements.txt```

### Set up the API
Reference: https://blog.miguelgrinberg.com/post/how-to-deploy-a-react--flask-project

1. Create directories to host snakemake repos and DVC repos.
```
mkdir -p /home/ubuntu/{snakemake_workdir,dvc_workdir,tmp}
```

2. Set up nginx
```
sudo apt-get install -y nginx
```
Confirm that nginx is installed by going to ```http://IP_Address_of_the_VM```. The browser should display the defauly Nginx page.

Add orcestra.nginx file in the setup directory to nginx directory and activate the service.
```
sudo rm /etc/nginx/sites-enabled/default
sudo cp snakemake-kubernetes-api/setup/orcestra.nginx /etc/nginx/sites-available
sudo ln -s /etc/nginx/sites-available/orcestra.nginx /etc/nginx/sites-enabled
sudo systemctl reload nginx
```

3. Set up gunicorn
```
pip install gunicorn
```
Copy the service configuration to the system directory
'''
sudo cp snakemake-kubernetes-api/setup/orcestra.service /etc/systemd/system
'''
Start the service.
```
sudo systemctl daemon-reload
sudo systemctl start orcestra
sudo systemctl status orcestra 
```
You should see "Active: active (running)" around the third line of the output.

Confirm that the service is properly set up by going to ```http://IP_Address_of_the_VM/api/test```. You should see "ok" on the browser.

### Clone Snakemake and DVC repositories (work in progress)
Currently there is only one data object curation pipeline as a test: https://github.com/BHKLAB-Pachyderm/pdtx-snakemake.git.
The DVC repo for the data object is here: https://github.com/mnakano/pdtx-dvc.git
Clone the snakemake pipeline repo in ```/home/ubuntu/snakemake_workdir```.
Clone the DVC repo in ```/home/ubuntu/dvc_workdir```.

In the future, when there are large number of pipelines and dvc repositories, the cloning process needs to be automated.





