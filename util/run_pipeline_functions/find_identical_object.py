from db.models.snakemake_data_object import SnakemakeDataObject

# Find a data object that matches the following criteria:
# 1. The data object that used the same pipeline as the parameter.
# 2. The commit id of the pipeline is the same as the parameter.
# 3. All the additional parameters are the same as the parameter.
# If all of the above are true, return the data object, else return None
def find_identical_object(pipeline, git_sha):
    data_object = SnakemakeDataObject.objects(
        pipeline=pipeline, commit_id=git_sha).first()
    if (data_object is None):
        data_object = SnakemakeDataObject.objects.filter(
            pipeline=pipeline, status='processing').first()
    if(data_object is None):
        return None
    
    # Compare the input additional parameters and the additional parameters in the existing data object with same pipeline and git commit id.
    if pipeline.additional_parameters:
        data_obj_params = data_object.additional_parameters
        for key in pipeline.additional_parameters.keys():
            if data_obj_params.get(key) is None or data_obj_params.get(key) != pipeline.additional_parameters.get(key):
                return None

    return data_object