# dvc set up
# only used to initialize a new DVC repository
while getopts d:f:u:i:s: flag
do
    case "${flag}" in
        d) dataname=${OPTARG};;
        f) filename=${OPTARG};;
        u) endpointurl=${OPTARG};;
        i) access_key_id=${OPTARG};;
        s) secret_access_key=${OPTARG};;
    esac
done

git clone "https://github.com/mnakano/${dataname}-dvc.git" && 
git clone "git@github.com:mnakano/${dataname}-dvc.git" && 
cd "${dataname}-dvc" && 
dvc init &&
touch .gitignore && echo $filename > .gitignore && 
dvc remote add ${dataname} --local "s3://bhklab_orcestra/dvc/${dataname}/" && 
dvc remote modify ${dataname} --local endpointurl $endpointurl && 
dvc remote modify ${dataname} --local access_key_id $access_key_id && 
dvc remote modify ${dataname} --local secret_access_key "${secret_access_key}" && 
git add . && git commit -m "Initialize dvc repo."

git push