from db import db


class DataRepo(db.EmbeddedDocument):
    repo_type = db.StringField()
    git_url = db.StringField()
    commit_id = db.StringField()


class SnakemakePipeline(db.Document):
    name = db.StringField()
    snakefile = db.StringField()
    git_url = db.StringField()
    dvc_git = db.StringField()
    object_name = db.StringField(default=None)
    object_names = db.ListField(db.StringField(), default=None)
    additional_repo = db.ListField(db.EmbeddedDocumentField(DataRepo))
    additional_parameters = db.DictField(default=None)

    def serialize(self):
        return ({
            '_id': str(self.pk),
            'name': self.name,
            'snakefile': self.snakefile if self.snakefile else 'Snakefile',
            'object_name': self.object_name if self.object_name is not None else None,
            'object_names': self.object_names if self.object_names is not None else None,
            'git_url': self.git_url,
            'dvc_git': self.dvc_git,
            'additional_repo': list(map(lambda repo: {
                'repo_type': repo.repo_type,
                'git_url': repo.git_url
            }, self.additional_repo)),
            'additional_parameters': self.additional_parameters if self.additional_parameters else None
        })

    @staticmethod
    def serialize_list(obj_list):
        return ([item.serialize() for item in obj_list])
