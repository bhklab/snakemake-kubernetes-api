from db import db
from enum import Enum

class Status(Enum):
    PROCESSING='processing'
    COMPLETE='complete'
    UPLOADED='uploaded'

class SnakemakeDataObject(db.Document):
    pipeline_name = db.StringField()
    repository_name = db.StringField()
    filename = db.StringField()
    git_url = db.StringField()
    commit_id = db.StringField()
    md5 = db.StringField()
    status = db.EnumField(Status, default=Status.PROCESSING)
    process_start_date = db.DateTimeField()
    process_end_date = db.DateTimeField()
    data_object_id = db.StringField()
    doi = db.StringField()
    download_link = db.StringField()

    def serialize(self):
        return({
            '_id': str(self.pk),
            'pipeline_name': self.pipeline_name,
            'repository_name': self.repository_name,
            'filename': self.filename,
            'git_url': self.git_url,
            'commit_id': self.commit_id,
            'md5': self.md5 if self.md5 is not None else None,
            'status': self.status.value,
            'process_start_date': str(self.process_start_date) if self.process_start_date is not None else None,
            'process_end_date': str(self.process_end_date) if self.process_end_date is not None else None,
            'data_object_id': self.data_object_id if self.data_object_id is not None else None,
            'doi': self.doi if self.doi is not None else None,
            'download_link': self.download_link if self.download_link is not None else None
        })
    
    @staticmethod
    def serialize_list(obj_list):
        return([item.serialize() for item in obj_list])