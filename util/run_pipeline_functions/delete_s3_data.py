from decouple import config

# Delete all pipeline data in snakemake object storage if run_all flag is true
def delete_s3_data(s3_client, pipeline_name, run_all, preserved_data):
  s3_response = s3_client.list_objects_v2(
    Bucket=config('S3_BUCKET'), 
    Prefix='snakemake/{0}/'.format(pipeline_name)
  )
  if s3_response.get('Contents') is not None:
      for obj in s3_response.get('Contents'):
          key = obj.get('Key')
          if run_all or not any(map(key.__contains__, preserved_data)):
              print('Deleting: ' + key)
              s3_client.delete_object(
                  Bucket=config('S3_BUCKET'), 
                  Key=key
              )