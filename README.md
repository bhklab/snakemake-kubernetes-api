# snakemake-kubernetes-api
Flask API to issue snakemake command based on a request.
The API is to be used for the new data processing layer of ORCESTRA. 

The API is still under development and not complete.

Implemented so far: A GET request that 
1. Accepts git url for a repository containing a Snakefile and additional environment files, and data directory name.
2. Either clones or pulls the Snakefile repo.
3. Gets the latest commit sha. (To be used to reference the code used for data processing)
4. Submits a snakemake job to a Kubernetes cluster.

Tested with a sample snakemake pipeline used in the official Snakemake tutorial: [Auto-scaling Azure Kubernetes cluster without shared filesystem](https://snakemake.readthedocs.io/en/stable/executor_tutorial/azure_aks.html), which was based on [this article](https://andreas-wilm.github.io/2020-06-08-snakemake-on-ask/#) which has a [link to the Snakefile](https://github.com/andreas-wilm/andreas-wilm.github.io/tree/master/data/2020-06-08) used in the example.
