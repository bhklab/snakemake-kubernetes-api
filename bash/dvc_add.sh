# Script used to add data to DVC remote.
while getopts r:d:f: flag
do
    case "${flag}" in
        r) repodir=${OPTARG};;
        d) dataname=${OPTARG};;
        f) filename=${OPTARG};;
    esac
done

cd $repodir && 
/home/ubuntu/miniconda3/envs/orcestra-snakemake/bin/dvc add --to-remote --remote ${dataname} ${filename} && 
git add "${filename}.dvc" && 
git commit -m 'Added data' && 
/home/ubuntu/miniconda3/envs/orcestra-snakemake/bin/dvc push -r ${dataname} && 
git push 