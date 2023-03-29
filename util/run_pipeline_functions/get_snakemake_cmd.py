from decouple import config

# Builds a snakemake command based on the pipeline configuration
def get_snakemake_cmd(pipeline, work_dir):
  snakefile_name = pipeline.snakefile if pipeline.snakefile is not None else 'Snakefile'
  print(config('SNAKEMAKE_DOCKER_IMG'))
  snakemake_cmd = [
      '/home/ubuntu/miniconda3/envs/orcestra-snakemake/bin/snakemake',
      '--snakefile', work_dir + '/' + snakefile_name,
      '--directory', work_dir,
      '--kubernetes',
      '--container-image', config('SNAKEMAKE_DOCKER_IMG'),
      '--default-remote-prefix', config('S3_BUCKET'),
      '--default-remote-provider', 'S3',
      '--jobs', '1',
      '--config',
      'prefix={0}/snakemake/{1}/'.format(
          config('S3_BUCKET'), pipeline.name),
      'key={0}'.format(config('S3_ACCESS_KEY_ID')),
      'secret={0}'.format(config('S3_SECRET_ACCESS_KEY')),
      'host={0}'.format(config('S3_URL')),
      'filename={0}'.format(pipeline.object_name),
  ]

  # Add additional config values if additional parameters are available.
  if pipeline.additional_parameters:
      print(pipeline.additional_parameters)
      for key in pipeline.additional_parameters.keys():
          snakemake_cmd.append('{0}={1}'.format(key, pipeline.additional_parameters[key]))
  
  return(snakemake_cmd)
