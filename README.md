# snakemake-kubernetes-api
Flask API to issue snakemake command based on a request.
The API is to be used for the new data processing layer of ORCESTRA. 

Tested with a sample snakemake pipeline used in the official Snakemake tutorial: [Auto-scaling Azure Kubernetes cluster without shared filesystem](https://snakemake.readthedocs.io/en/stable/executor_tutorial/azure_aks.html), which was based on [this article](https://andreas-wilm.github.io/2020-06-08-snakemake-on-ask/#) which has a [link to the Snakefile](https://github.com/andreas-wilm/andreas-wilm.github.io/tree/master/data/2020-06-08) used in the example.

## Set up
All commands should be executed from the user's top level directory.

### Initial set up
'''
sudo apt-get update
sudo apt upgrade
'''

### Install git (if not already installed) and clone the API repository
'''
sudo apt install git
git clone https://github.com/bhklab/snakemake-kubernetes-api.git
scp -i path_to_the_key path_to_the_.env_file username>@hostname:/path_to_the_app's_root_dir
'''

### Install kubectl
Install kubectl to be used by Python's kubernetes client package by using the instructions available here: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/.

Once the kubectl installation is verified, connect the kubectl to Compute Canada's kubernetes cluster:
1. Create .kube directory in the user root. '''mkdir .kube'''
2. Obtain the 'config' file for the kubernetes cluster and add it to the .kube directory.
3. Ensure that kubectl is now pointing to the lab's kubernetes cluster. '''kubectl version'''

### Install Miniconda and set up python environment
To get started with setup you can install miniconda3 using the instructions available here: https://docs.conda.io/en/latest/miniconda.html.
Installation Guide: https://conda.io/projects/conda/en/latest/user-guide/install/linux.html#install-linux-silent





