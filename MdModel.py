from peewee import *
import datetime
import os
import hashlib
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import io
from pathlib import Path
import time
gDatabase = SqliteDatabase('Modan2.db',pragmas={'foreign_keys': 1})


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
    def __str__(self):
        return self.object_name
    def count_landmarks(self):
        if self.landmark_str is None or self.landmark_str == '':
            return 0
        return len(self.landmark_str.strip().split('\n'))

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

    def load_file_info(self, fullpath):

        file_info = {}

        ''' file stat '''
        stat_result = os.stat(fullpath)
        file_info['mtime'] = stat_result.st_mtime
        file_info['ctime'] = stat_result.st_ctime

        if os.path.isdir(fullpath):
            file_info['type'] = 'dir'
        else:
            file_info['type'] = 'file'

        if os.path.isdir( fullpath ):
            return file_info

        file_info['size'] = stat_result.st_size

        ''' md5 hash value '''
        file_info['md5hash'], image_data = self.get_md5hash_info(fullpath)

        ''' exif info '''
        exif_info = self.get_exif_info(fullpath, image_data)
        file_info['exifdatetime'] = exif_info['datetime']
        file_info['latitude'] = exif_info['latitude']
        file_info['longitude'] = exif_info['longitude']
        file_info['map_datum'] = exif_info['map_datum']

        self.original_path = fullpath
        self.original_filename = Path(fullpath).name
        self.md5hash = file_info['md5hash']
        self.size = file_info['size']
        self.exifdatetime = file_info['exifdatetime']
        self.file_created = file_info['ctime']
        self.file_modified = file_info['mtime']

    def get_md5hash_info(self,filepath):
        afile = open(filepath, 'rb')
        hasher = hashlib.md5()
        image_data = afile.read()
        hasher.update(image_data)
        afile.close()
        md5hash = hasher.hexdigest()
        return md5hash, image_data

    def get_exif_info(self, fullpath, image_data=None):
        image_info = {'date':'','time':'','latitude':'','longitude':'','map_datum':''}
        img = None
        if image_data:
            #img = Image.open()
            img = Image.open(io.BytesIO(image_data))
        else:
            img = Image.open(fullpath)
        ret = {}
        #print(filename)
        try:
            info = img._getexif()
            for tag, value in info.items():
                decoded=TAGS.get(tag, tag)
                ret[decoded]= value
                #print("exif:", decoded, value)
            try:
                if ret['GPSInfo'] != None:
                    gps_info = ret['GPSInfo']
                    #print("gps info:", gps_info)
                degree_symbol = "°"
                minute_symbol = "'"
                longitude = str(int(gps_info[4][0])) + degree_symbol + str(gps_info[4][1]) + minute_symbol + gps_info[3]
                latitude = str(int(gps_info[2][0])) + degree_symbol + str(gps_info[2][1]) + minute_symbol + gps_info[1]
                map_datum = gps_info[18]
                image_info['latitude'] = latitude
                image_info['longitude'] = longitude
                image_info['map_datum'] = map_datum

            except KeyError:
                pass
                #print( "GPS Data Don't Exist for", Path(filename).name)


            try:
                if ret['DateTimeOriginal'] is not None:
                    exif_timestamp = ret['DateTimeOriginal']
                    #print("original:", exifTimestamp)
                    image_info['date'], image_info['time'] = exif_timestamp.split()
            except KeyError:
                pass
                #print( "DateTimeOriginal Don't Exist")
            try:
                if ret['DateTimeDigitized'] is not None:
                    exif_timestamp = ret['DateTimeDigitized']
                    image_info['date'], image_info['time'] = exif_timestamp.split()
            except KeyError:
                pass
                #print( "DateTimeDigitized Don't Exist")
            try:
                if ret['DateTime'] is not None:
                    exif_timestamp = ret['DateTime']
                    image_info['date'], image_info['time'] = exif_timestamp.split()
            except KeyError:
                pass
                #print( "DateTime Don't Exist")

        except Exception as e:
            pass
            #print(e)

        if image_info['date'] == '':
            str1 = time.ctime(os.path.getmtime(fullpath))
            datetime_object = datetime.datetime.strptime(str1, '%a %b %d %H:%M:%S %Y')
            image_info['date'] = datetime_object.strftime("%Y-%m-%d")
            image_info['time'] = datetime_object.strftime("%H:%M:%S")
        else:
            image_info['date'] = "-".join( image_info['date'].split(":") )
        image_info['datetime'] = image_info['date'] + ' ' + image_info['time']
        return image_info

