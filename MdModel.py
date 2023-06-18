from peewee import *
import datetime

gDatabase = SqliteDatabase('Modan2.db')


class MdDataset(Model):
    dataset_name = CharField()
    dataset_desc = CharField(null=True)
    dimension = IntegerField(default=2)
    wireframe = CharField(null=True)
    baseline = CharField(null=True)
    polygons = CharField(null=True)
    parent = ForeignKeyField('self', backref='children', null=True,on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)
    propertyname_list = CharField(null=True)

    class Meta:
        database = gDatabase

class MdObject(Model):
    object_name = CharField()
    object_desc = CharField(null=True)
    scale = FloatField(null=True)
    landmark_str = CharField(null=True)
    dataset = ForeignKeyField(MdDataset, backref='objects', on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)
    property_list = CharField(null=True)

    class Meta:
        database = gDatabase

class MdImage(Model):
    original_path = CharField(null=True)
    original_filename = CharField(null=True)
    name = CharField(null=True)
    md5hash = CharField(null=True)
    size = IntegerField(null=True)
    exifdatetime = DateTimeField(null=True)
    file_created = DateTimeField(null=True)
    file_modified = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)
    object = ForeignKeyField(MdObject, backref='image', on_delete="CASCADE")
    class Meta:
        database = gDatabase
