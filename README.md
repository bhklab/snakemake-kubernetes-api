# snakemake-kubernetes-api
Flask API to issue snakemake command based on a request.
The API is to be used for the new data processing layer of ORCESTRA. 

The API is still under development and not complete.

Implemented so far: A GET request that 
1. Accepts git url for a repository containing a Snakefile and additional environment files, and data directory name.
2. Either clones or pulls the Snakefile repo.
3. Gets the latest commit sha. (To be used to reference the code used for data processing)
4. Submits a snakemake job to a Kubernetes cluster.
