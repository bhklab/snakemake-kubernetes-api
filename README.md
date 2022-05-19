# snakemake-kubernetes-api
Flask API used as the new data processing layer of ORCESTRA.

Refer to [this wiki page](https://github.com/bhklab/snakemake-kubernetes-api/wiki/Set-up-on-Compute-Canada-VM) for setting up and configuring the application.

## API End-points

**GET /api/pipeline/list** 
Lists all pipelines.

Example: 
```
curl http://Host_URL/api/pipeline/list
```

**POST /api/pipeline/create** 
Creates a pipeline based on json object.

Example: 
```
curl -X POST http://Host_URL/api/pipeline/create \
   -H "Content-Type: application/json" \
   -d SEE EXAMPLE JSON FILE (examples/create_pipeline_example.json) 
```

**POST /api/pipeline/run** 
Triggers a data object curation pipeline run.

Example: 
```
curl -X POST http://Host_URL/api/pipeline/run \
   -H "Content-Type: application/json" \
   -d SEE EXAMPLE JSON FILE (examples/run_pipeline_example.json) 
```

**GET /api/data_object/list**
Lists data objects. 
Accepted parameters:
```
status (optional, by default it returns 'complete' and 'uploaded' data objects): processing, complete or uploaded
pipeline_name (optional): string value for pipeline name
latest (optional, defaults to 'false'): boolean, if true, returns the latest pipeline run filtered with other parameters.
```

Example:
```
curl http://Host_URL/api/data_object/list
```

**GET /api/data_object/download**
Downloads a data object to local storage.

Example: 
```
curl 'http://Host_URL/api/data_object/download?data_obj_id=Data_Object_ID' --output File_Name
```

**POST /api/data_object/upload**
Uploads a data object to Zenodo.

Example:
```
curl -X POST http://Host_URL/api/data_object/upload \
   -H "Content-Type: application/json" \
   -d '{"data_obj_id": Data_Object_ID}' 
```

**GET /api/log/list**
Returns a list of log files for a pipeline.

Example:
```
curl http://Host_URL/api/logs?pipeline=Pipeline_Name
```

**GET /api/log/download**
Downloads a specified log file for a pipeline.

Example:
```
curl http://Host_URL/api/log/download?pipeline=Pipeline_Name&filename=Log_File_Name --output Log_File_Name
```

**GET /api/k8/error_pods**
If there is an error, Kubernetes pod will not be deleted. This API route gets a list of pods in error status.

Example:
```
curl http://Host_URL/api/k8/error_pods
```

**GET /api/k8/pod_log**
Returns Kubernetes log of a specified pod.

Example:
```
curl http://Host_URL/api/k8/pod_log?podname=Pod_Name_From_Snakemake_Log_Or_List_Of_K8_Error_Pods
```
