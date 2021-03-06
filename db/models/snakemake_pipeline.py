from db import db

class DataRepo(db.EmbeddedDocument):
    repo_type = db.StringField()
    git_url = db.StringField()
    commit_id = db.StringField()

class SnakemakePipeline(db.Document):
    name = db.StringField()
    git_url = db.StringField()
    dvc_git = db.StringField()
    object_name = db.StringField()
    additional_repo = db.ListField(db.EmbeddedDocumentField(DataRepo))

    def serialize(self):
        return({
            '_id': str(self.pk),
            'name': self.name,
            'object_name': self.object_name,
            'git_url': self.git_url,
            'dvc_git': self.dvc_git,
            'additional_repo': list(map(lambda repo: {
                'repo_type': repo.repo_type,
                'git_url': repo.git_url
            }, self.additional_repo))
        })
    
    @staticmethod
    def serialize_list(obj_list):
        return([item.serialize() for item in obj_list])