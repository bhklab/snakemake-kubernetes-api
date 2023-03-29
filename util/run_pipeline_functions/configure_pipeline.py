from db.models.snakemake_pipeline import SnakemakePipeline

# Find the pipeline and set request parameters
def configure_pipeline(pipeline_name, request_parameters):
    pipeline = None
    pipeline = SnakemakePipeline.objects(name=pipeline_name).first()
    if pipeline.additional_parameters:
        for key in pipeline.additional_parameters.keys():
            if request_parameters and request_parameters.get(key) is not None:
                pipeline.additional_parameters[key] = request_parameters[key]
    return(pipeline)