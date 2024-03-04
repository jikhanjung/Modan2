from peewee import *
database_path = "D:/Dropbox/My Pet Projects/Modan/modan.moa"
gDatabase = SqliteDatabase(database_path,pragmas={'foreign_keys': 1})
class MdDataset(Model):
    dsname = CharField()
    dsdesc = CharField()
    dimension = IntegerField()
    groupname = CharField()
    wireframe = CharField()
    baseline = CharField()
    polygons = CharField()
    created_at = DateTimeField()
    class Meta:
        database = gDatabase

class MdObject(Model):
    dataset = ForeignKeyField(MdDataset, backref='objects')
    objname = CharField()
    objdesc = CharField()
    scale = CharField()
    group1 = CharField()
    group2 = CharField()
    group3 = CharField()
    group4 = CharField()
    group5 = CharField()
    group6 = CharField()
    group7 = CharField()
    group8 = CharField()
    group9 = CharField()
    group10 = CharField()
    created_at = DateTimeField()
    class Meta:
        database = gDatabase

class MdLandmark(Model):
    object = ForeignKeyField(MdObject, backref='landmarks')
    dataset = ForeignKeyField(MdDataset, backref='landmarks')
    lmseq = IntegerField()
    xcoord = FloatField()
    ycoord = FloatField()
    zcoord = FloatField()
    created_at = DateTimeField()
    class Meta:
        database = gDatabase


