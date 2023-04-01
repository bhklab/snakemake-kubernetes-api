from db import db
from enum import Enum
from db.models.snakemake_pipeline import SnakemakePipeline, DataRepo


class Status(Enum):
    PROCESSING = 'processing'
    COMPLETE = 'complete'
    UPLOADED = 'uploaded'
    ERROR = 'error'

# Used to store object file info if there is more than one file.
class ObjFile(db.EmbeddedDocument):
    filename = db.StringField()
    md5 = db.StringField()
    download_link = db.StringField()


class SnakemakeDataObject(db.Document):
    pipeline = db.ReferenceField(SnakemakePipeline)
    additional_repo = db.ListField(db.EmbeddedDocumentField(DataRepo))
    filename = db.StringField()
    object_files = db.ListField(db.EmbeddedDocumentField(ObjFile), default=None)
    commit_id = db.StringField()
    md5 = db.StringField()
    status = db.EnumField(Status, default=Status.PROCESSING)
    process_start_date = db.DateTimeField()
    process_end_date = db.DateTimeField()
    doi = db.StringField()
    download_link = db.StringField()
    additional_parameters = db.DictField()
    error_messages = db.ListField(db.DictField(), default=None)

    def serialize(self):
        return ({
            '_id': str(self.pk),
            'pipeline': {
                'name': self.pipeline.name,
                'git_url': self.pipeline.git_url,
                'object_name': self.pipeline.object_name if self.pipeline.object_name is not None else None,
                'object_names': self.pipeline.object_names if self.pipeline.object_names is not None else None,
                'dvc_git': self.pipeline.dvc_git
            },
            'additional_repo': list(map(lambda repo: {
                'repo_type': repo.repo_type,
                'git_url': repo.git_url,
                'commit_id': repo.commit_id
            }, self.additional_repo)),
            'object_files': list(map(lambda file: {
                'filename': file.filename,
                'md5': file.md5,
                'download_link': file.download_link
            }, self.object_files)) if self.object_files is not None else None,
            'additional_parameters': self.additional_parameters if self.additional_parameters else None,
            'commit_id': self.commit_id,
            'md5': self.md5 if self.md5 is not None else None,
            'status': self.status.value,
            'process_start_date': str(self.process_start_date) if self.process_start_date is not None else None,
            'process_end_date': str(self.process_end_date) if self.process_end_date is not None else None,
            'doi': self.doi,
            'download_link': self.download_link,
            'error': self.error_messages if self.error_messages is not None else None
        })

    @staticmethod
    def serialize_list(obj_list):
        return ([item.serialize() for item in obj_list])
