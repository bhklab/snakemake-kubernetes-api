from db import db
from enum import Enum
from db.models.snakemake_pipeline import SnakemakePipeline, DataRepo

class Status(Enum):
    PROCESSING='processing'
    COMPLETE='complete'
    UPLOADED='uploaded'
    ERROR='error'

class SnakemakeDataObject(db.Document):
    pipeline = db.ReferenceField(SnakemakePipeline)
    additional_data_repo = db.ListField(db.EmbeddedDocumentField(DataRepo))
    filename = db.StringField()
    commit_id = db.StringField()
    md5 = db.StringField()
    status = db.EnumField(Status, default=Status.PROCESSING)
    process_start_date = db.DateTimeField()
    process_end_date = db.DateTimeField()
    doi = db.StringField()
    download_link = db.StringField()
    error_message = db.StringField()

    def serialize(self):
        return({
            '_id': str(self.pk),
            'pipeline': {
                'name': self.pipeline.name,
                'repository_name': self.pipeline.repository_name,
                'git_url': self.pipeline.git_url,
                'object_name': self.pipeline.object_name
            },
            'additional_data_repo': list(map(lambda repo: {
                'repo_type': repo.repo_type,
                'git_url': repo.git_url,
                'commit_id': repo.commit_id
            }, self.additional_data_repo)),
            'commit_id': self.commit_id,
            'md5': self.md5 if self.md5 is not None else None,
            'status': self.status.value,
            'process_start_date': str(self.process_start_date) if self.process_start_date is not None else None,
            'process_end_date': str(self.process_end_date) if self.process_end_date is not None else None,
            'doi': self.doi if self.doi is not None else None,
            'download_link': self.download_link if self.download_link is not None else None
        })
    
    @staticmethod
    def serialize_list(obj_list):
        return([item.serialize() for item in obj_list])