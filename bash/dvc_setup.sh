# dvc set up
# used to modifed a cloned dvc repo
while getopts d:f:u:i:s: flag
do
    case "${flag}" in
        d) dataname=${OPTARG};;
        u) endpointurl=${OPTARG};;
        i) access_key_id=${OPTARG};;
        s) secret_access_key=${OPTARG};;
    esac
done
cd "/home/ubuntu/dvc_workdir/${dataname}-dvc" && 
dvc remote add ${dataname} --local "s3://bhklab_orcestra/dvc/${dataname}/" && 
dvc remote modify ${dataname} --local endpointurl $endpointurl && 
dvc remote modify ${dataname} --local access_key_id $access_key_id && 
dvc remote modify ${dataname} --local secret_access_key "${secret_access_key}"