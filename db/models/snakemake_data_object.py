from db import db

class SnakemakeDataObject(db.Document):
    dataset_name = db.StringField()
    repository_name = db.StringField()
    filename = db.StringField()
    git_url = db.StringField()
    commit_id = db.StringField()
    md5 = db.StringField()
    status = db.StringField()
    process_start_date = db.DateTimeField()
    process_end_date = db.DateTimeField()
    data_object_id = db.StringField()
    error = db.BooleanField()