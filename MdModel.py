from peewee import *

gDatabase = SqliteDatabase('Modan2.db')


class MdDataset(Model):
    dataset_name = CharField()
    dataset_desc = CharField()
    dimension = IntegerField()
    wireframe = CharField()
    baseline = CharField()
    polygons = CharField()
    created_at = DateTimeField()
    modified_at = DateTimeField()
    propertyname_list = CharField()

    class Meta:
        database = gDatabase
        
class MdObject(Model):
    object_name = CharField()
    object_desc = CharField()
    scale = FloatField()
    landmark_str = CharField()
    dataset = ForeignKeyField(MdDataset, backref='objects')
    created_at = DateTimeField()
    modified_at = DateTimeField()
    property_list = CharField()

    class Meta:
        database = gDatabase

class MdImage(Model):
    original_path = CharField()
    original_filename = CharField()
    name = CharField()
    md5hash = CharField()
    size = IntegerField()
    exifdatetime = DateTimeField()
    file_created = DateTimeField()
    file_modified = DateTimeField()
    created_at = DateTimeField()
    modified_at = DateTimeField()
    object = ForeignKeyField(MdObject, backref='images')
    class Meta:
        database = gDatabase
