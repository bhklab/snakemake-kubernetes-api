# Script used to add data to DVC remote.
while getopts r:d:f: flag
do
    case "${flag}" in
        r) root_dir=${OPTARG};;
        d) dataname=${OPTARG};;
        f) filename=${OPTARG};;
    esac
done

cd "${root_dir}/${dataname}-dvc" && 
dvc add --to-remote --remote ${dataname} ${filename} && 
git add "${filename}.dvc" && 
git commit -m 'Added data' && 
dvc push -r ${dataname} && 
git push 