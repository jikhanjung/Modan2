from peewee import *
import datetime
import os
import hashlib
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import io
from pathlib import Path
import time
import math
import numpy as np
import copy
import MdUtils as mu
#from MdUtils import *
import shutil
import copy

from MdLogger import setup_logger
logger = setup_logger(__name__)

LANDMARK_SEPARATOR = "\t"
LINE_SEPARATOR = "\n"
PROPERTY_SEPARATOR = ","
EDGE_SEPARATOR = "-"
WIREFRAME_SEPARATOR = ","
DATABASE_FILENAME = mu.PROGRAM_NAME + ".db"

database_path = os.path.join(mu.DEFAULT_DB_DIRECTORY, DATABASE_FILENAME)

gDatabase = SqliteDatabase(database_path,pragmas={'foreign_keys': 1})

def setup_database_location(database_dir):
    database_handle = SqliteDatabase(database_path,pragmas={'foreign_keys': 1})
    return database_handle


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
    propertyname_str = CharField(null=True)
    baseline_point_list = []
    edge_list = []
    polygon_list = []
    propertyname_list = []

    class Meta:
        database = gDatabase

    def get_valid_property_index_list(self):
        propertyname_list = self.get_propertyname_list()
        object_count = len(self.object_list)
        valid_property_index_list = []
        #print("object count:", object_count, "propertyname_list:", propertyname_list)
        for idx, propertyname in enumerate(propertyname_list):
            #print("propertyname:", propertyname, idx)
            unique_property_list = []
            for obj in self.object_list:
                property_list = obj.get_property_list()
                if idx < len(property_list) and property_list[idx] not in unique_property_list:
                    unique_property_list.append(property_list[idx])
            if len(unique_property_list) < 0.7 * object_count:
                valid_property_index_list.append(idx)
        return valid_property_index_list


    def get_propertyname_list(self):
        return self.unpack_propertyname_str(self.propertyname_str)

    def pack_propertyname_str(self, propertyname_list=None):
        if propertyname_list is None:
            propertyname_list = self.propertyname_list
        self.propertyname_str = PROPERTY_SEPARATOR.join(propertyname_list)
        return self.propertyname_str

    def unpack_propertyname_str(self, propertyname_str=''):
        if propertyname_str == '' and self.propertyname_str != '':
            propertyname_str = self.propertyname_str

        self.propertyname_list = []
        if propertyname_str is None or propertyname_str == '':
            return []

        self.propertyname_list = [x for x in propertyname_str.split(PROPERTY_SEPARATOR)]
        return self.propertyname_list

    def pack_wireframe(self, edge_list=None):
        if edge_list is None:
            edge_list = self.edge_list

        for points in edge_list:
            points.sort(key=int)
        edge_list.sort()

        new_edges = []
        for points in edge_list:
            # print points
            if len(points) != 2:
                continue
            new_edges.append(EDGE_SEPARATOR.join([str(x) for x in points]))
        self.wireframe = WIREFRAME_SEPARATOR.join(new_edges)
        return self.wireframe

    def unpack_wireframe(self, wireframe=''):
        if wireframe == '' and self.wireframe != '':
            wireframe = self.wireframe

        self.edge_list = []

        if wireframe is None or wireframe == '':
            return []

        # print wireframe
        for edge in wireframe.split(WIREFRAME_SEPARATOR):
            has_edge = True
            if edge != '':
                #print edge
                verts = edge.split(EDGE_SEPARATOR)
                int_edge = []
                for v in verts:
                    try:
                        v = int(v)
                    except:
                        has_edge = False
                        #print "Invalid landmark number [", v, "] in wireframe:", edge
                    int_edge.append(v)

                if has_edge:
                    if len(int_edge) != 2:
                        pass  #print "Invalid edge in wireframe:", edge
                    self.edge_list.append(int_edge)

        return self.edge_list

    def pack_polygons(self, polygon_list=None):
        # print polygon_list
        if polygon_list is None:
            polygon_list = self.polygon_list
        for polygon in polygon_list:
            # print polygon
            polygon.sort(key=int)
        polygon_list.sort()

        new_polygons = []
        for polygon in polygon_list:
            #print points
            new_polygons.append("-".join([str(x) for x in polygon]))
        self.polygons = ",".join(new_polygons)
        return self.polygons

    def unpack_polygons(self, polygons=''):
        if polygons == '' and self.polygons != '':
            polygons = self.polygons

        self.polygon_list = []
        if polygons is None or polygons == '':
            return []

        for polygon in polygons.split(","):
            if polygon != '':
                self.polygon_list.append([(int(x)) for x in polygon.split("-")])

        return self.polygon_list

    def get_polygon_list(self):
        return self.unpack_polygons()

    def get_edge_list(self):
        return self.unpack_wireframe()

    def pack_baseline(self, baseline_point_list=None):
        if baseline_point_list is None and len(self.baseline_point_list) > 0:
            baseline_point_list = self.baseline_point_list
        # print baseline_points
        self.baseline = ",".join([str(x) for x in baseline_point_list])
        #print self.baseline
        return self.baseline

    def unpack_baseline(self, baseline=''):
        if baseline == '' and self.baseline != '':
            baseline = self.baseline

        self.baseline_point_list = []
        if self.baseline is None or self.baseline == '':
            return []

        self.baseline_point_list = [(int(x)) for x in self.baseline.split(",")]
        return self.baseline_point_list

    def get_baseline_points(self):
        return self.baseline_point_list

    def add_object(self, object_name, object_desc=None, pixels_per_mm=None, landmark_str=None, property_str=None):
        obj = MdObject()
        obj.object_name=object_name
        obj.object_desc=object_desc
        obj.pixels_per_mm=pixels_per_mm
        obj.landmark_str=landmark_str
        obj.property_str=property_str
        obj.dataset=self
        return obj

    def add_propertyname(self, propertyname):
        self.propertyname_list.append(propertyname)
        self.pack_propertyname_str()
        self.save()
        return propertyname

class MdObject(Model):
    object_name = CharField()
    object_desc = CharField(null=True)
    pixels_per_mm = DoubleField(null=True)
    landmark_str = CharField(null=True)
    dataset = ForeignKeyField(MdDataset, backref='object_list', on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)
    property_str = CharField(null=True)
    landmark_list = []
    property_list = []
    centroid_size = -1

    class Meta:
        database = gDatabase

    def copy_object(self, new_dataset):
        new_object = MdObject()
        new_object.object_name = self.object_name
        new_object.object_desc = self.object_desc
        new_object.pixels_per_mm = self.pixels_per_mm
        new_object.landmark_str = self.landmark_str
        new_object.dataset = new_dataset
        new_object.property_str = self.property_str
        #new_object.save()
        return new_object

    def get_name(self):
        if self.object_name is None or self.object_name == '':
            return str(self.id)
        return self.object_name

    def __str__(self):
        return self.object_name or ''
    def __repr__(self):
        return self.object_name
    
    def count_landmarks(self):
        if self.landmark_str is None or self.landmark_str == '':
            return 0
        return len(self.landmark_str.strip().split(LINE_SEPARATOR))
    #def get_image_file_path(self):

    def add_image(self, file_name):
        img = MdImage()
        img.object = self
        img.add_file(file_name)
        return img

    def update_image(self, file_name):
        #print("update image:", file_name)
        img = self.get_image()
        if img is None:
            img = MdImage()
            #img.object = self
        else:
            img.delete_instance()
            img = MdImage()
        img.object = self
        img2 = img.add_file(file_name)
        #print("update image:", img, img2)
        return img

    def add_threed_model(self, file_name):
        model = MdThreeDModel()
        model.object = self
        model.add_file(file_name)
        return model
    
    def has_image(self):
        return self.image.count() > 0

    def get_image(self):
        return self.image[0]

    def has_threed_model(self):
        return self.threed_model.count() > 0

    def get_threed_model(self):
        return self.threed_model[0]

    def change_dataset(self, dataset):
        if self.has_image():
            source_path = self.get_image().get_file_path()
        if self.has_threed_model():
            source_path = self.get_threed_model().get_file_path()

        self.dataset = dataset
        self.save()

        if self.has_image():
            target_path = self.get_image().get_file_path()
        if self.has_threed_model():
            target_path = self.get_threed_model().get_file_path()

        if os.path.exists(source_path):
            if not os.path.exists(os.path.dirname(target_path)):
                os.makedirs(os.path.dirname(target_path))

            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(source_path, target_path)

    def pack_landmark(self):
        # error check
        self.landmark_str = LINE_SEPARATOR.join([LANDMARK_SEPARATOR.join([str(x) for x in lm[:self.dataset.dimension]]) for lm in self.landmark_list])

    def unpack_landmark(self):
        self.landmark_list = []
        #print "[", self.landmark_str,"]"
        if self.landmark_str is None or self.landmark_str == '':
            return self.landmark_list
        lm_list = self.landmark_str.split(LINE_SEPARATOR)
        for lm in lm_list:
            if lm != "":
                #self.landmark_list.append([float(x) for x in lm.split(LANDMARK_SEPARATOR)])
                #self.landmark_list.append([float(x) if x.replace('.', '', 1).isdigit() else 0.0 for x in lm.split(LANDMARK_SEPARATOR)])
                self.landmark_list.append([float(x) if self.is_float(x) else None for x in lm.split(LANDMARK_SEPARATOR)])
        return self.landmark_list
    def is_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
    def get_landmark_list(self):
        return self.unpack_landmark()

    def pack_property(self, property_list=None):
        if property_list is None:
            property_list = self.property_list
        self.property_str = PROPERTY_SEPARATOR.join(property_list)

    def unpack_property(self):
        self.property_list = []
        if self.property_str is None or self.property_str == '':
            return []
        self.property_list = [x for x in self.property_str.split(PROPERTY_SEPARATOR)]
        return self.property_list
    def get_property_list(self):
        return self.unpack_property()

    def get_centroid_size(self, refresh=False):

        #if len(self.landmark_list) == 0 and self.landmark_str != "":
        #    self.unpack_landmark()

        if len(self.landmark_list) == 0:
            if self.landmark_str is not None and self.landmark_str != "":
                self.unpack_landmark()
            if len(self.landmark_list) == 0:
                return -1
        elif len(self.landmark_list)== 1:
            return 1
        if ( self.centroid_size > 0 ) and ( refresh == False ):
            return self.centroid_size

        centroid = self.get_centroid_coord()
        # print "centroid:", centroid.xcoord, centroid.ycoord, centroid.zcoord
        sum_of_x_squared = 0
        sum_of_y_squared = 0
        sum_of_z_squared = 0
        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        lm_count = len(self.landmark_list)
        for lm in self.landmark_list:
            sum_of_x_squared += ( lm[0] - centroid[0]) ** 2
            sum_of_y_squared += ( lm[1] - centroid[1]) ** 2
            if len(lm) == 3:
                sum_of_z_squared += ( lm[2] - centroid[2]) ** 2
            sum_of_x += lm[0] - centroid[0]
            sum_of_y += lm[1] - centroid[1]
            if len(lm) == 3:
                sum_of_z += lm[2] - centroid[2]
        centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared
        #centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared \
        #              - sum_of_x * sum_of_x / lm_count \
        #              - sum_of_y * sum_of_y / lm_count \
        #              - sum_of_z * sum_of_z / lm_count
        #print centroid_size
        centroid_size = math.sqrt(centroid_size)
        self.centroid_size = centroid_size
        if self.pixels_per_mm is not None:
            centroid_size = centroid_size / self.pixels_per_mm
        #centroid_size = float( int(  * 100 ) ) / 100
        return centroid_size

    def get_centroid_coord(self):
        c = [0, 0, 0]

        #if len(self.landmark_list) == 0 and self.landmark_str != "":
        #    self.unpack_landmark()

        if len(self.landmark_list) == 0:
            return c
        
        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        lm_dim = 2
        for lm in ( self.landmark_list ):
            sum_of_x += lm[0]
            sum_of_y += lm[1]
            if len(lm) == 3:
                lm_dim = 3
                sum_of_z += lm[2]
        lm_count = len(self.landmark_list)
        c[0] = sum_of_x / lm_count
        c[1] = sum_of_y / lm_count
        if lm_dim == 3:
            c[2] = sum_of_z / lm_count
        return c

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

    def copy_image(self, new_object):
        new_image = MdImage()
        new_image.object = new_object
        new_image.original_path = self.original_path
        new_image.original_filename = self.original_filename
        new_image.name = self.name
        new_image.md5hash = self.md5hash
        new_image.size = self.size
        new_image.exifdatetime = self.exifdatetime
        new_image.file_created = self.file_created
        new_image.file_modified = self.file_modified
        new_image.add_file(self.get_file_path())
        return new_image

    def add_file(self, file_name):
        #print("add file:", file_name)
        self.load_file_info(file_name)
        new_filepath = self.get_file_path()
        if not os.path.exists(os.path.dirname(new_filepath)):
            os.makedirs(os.path.dirname(new_filepath))
        #print("new file:", new_filepath)
        ret = shutil.copyfile(file_name, new_filepath)
        #print("ret:", ret)
        return self

    def get_file_path(self, base_path =  mu.DEFAULT_STORAGE_DIRECTORY ):
        return os.path.join( base_path, str(self.object.dataset.id), str(self.object.id) + "." + self.original_path.split('.')[-1])

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

class MdThreeDModel(Model):
    original_path = CharField(null=True)
    original_filename = CharField(null=True)
    name = CharField(null=True)
    md5hash = CharField(null=True)
    size = IntegerField(null=True)
    file_created = DateTimeField(null=True)
    file_modified = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)
    object = ForeignKeyField(MdObject, backref='threed_model', on_delete="CASCADE")

    class Meta:
        database = gDatabase

    def copy_threed_model(self, new_object):
        new_model = MdThreeDModel()
        new_model.object = new_object
        new_model.original_path = self.original_path
        new_model.original_filename = self.original_filename
        new_model.name = self.name
        new_model.md5hash = self.md5hash
        new_model.size = self.size
        new_model.file_created = self.file_created
        new_model.file_modified = self.file_modified
        new_model.add_file(self.get_file_path())
        return new_model

    def add_file(self, file_name):
        file_name = mu.process_3d_file(file_name)
        self.load_file_info(file_name)
        new_filepath = self.get_file_path()
        if not os.path.exists(os.path.dirname(new_filepath)):
            os.makedirs(os.path.dirname(new_filepath))
        shutil.copyfile(file_name, new_filepath)
        return self

    def get_file_path(self, base_path =  mu.DEFAULT_STORAGE_DIRECTORY ):
        return os.path.join( base_path, str(self.object.dataset.id), str(self.object.id) + "." + self.original_path.split('.')[-1])

    def load_file_info(self, fullpath):

        file_info = {}

        ''' file stat '''
        stat_result = os.stat(fullpath)
        file_info['mtime'] = stat_result.st_mtime
        file_info['ctime'] = stat_result.st_ctime
        file_info['type'] = 'file'
        file_info['size'] = stat_result.st_size

        ''' md5 hash value '''
        file_info['md5hash'], image_data = self.get_md5hash_info(fullpath)

        self.original_path = fullpath
        self.original_filename = Path(fullpath).name
        self.md5hash = file_info['md5hash']
        self.size = file_info['size']
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

class MdObjectOps:
    def __init__(self,mdobject):
        self.id = mdobject.id
        self.object_name = mdobject.object_name
        self.object_desc = mdobject.object_desc
        self.pixel_per_mm = mdobject.pixels_per_mm
        #self.dataset_id = mdobject.dataset
        #self.scale = mdobject.scale
        self.landmark_str = mdobject.landmark_str
        self.property_str = mdobject.property_str
        if self.landmark_str is not None and self.landmark_str != "":
            mdobject.unpack_landmark()
        self.landmark_list = copy.deepcopy(mdobject.landmark_list)
        #if mdobject.polygons is not None and mdobject.polygons != "":
        #    mdobject.unpack_polygons()
        #self.polygon_list = copy.deepcopy(mdobject.polygon_list)
        #print("landmark list:", self.landmark_list)
        #for lm in mdobject.landmark_list:
        #    self.landmark_list.append(lm)
        self.property_list = []
        if self.property_str is not None and self.property_str != "":
            mdobject.unpack_property()
        self.property_list = copy.deepcopy(mdobject.property_list)

        self.centroid_size = -1
        self.polygon_color = None
        self.edge_color = None
        self.landmark_color = None
        self.visible = True
        self.show_landmark = True
        self.show_polygon = True
        self.show_wireframe = True
        self.opacity = 1.0
        if self.pixel_per_mm is None:
            self.pixel_per_mm = 1.0
        self.scale_applied = False
        #self.apply_scale()
    
    def apply_scale(self):
        if self.pixel_per_mm is not None:
            for lm in self.landmark_list:
                lm[0] = lm[0] / self.pixel_per_mm
                lm[1] = lm[1] / self.pixel_per_mm
                if len(lm) == 3:
                    lm[2] = lm[2] / self.pixel_per_mm
        self.scale_applied = True


    def get_centroid_coord(self):
        c = [0, 0, 0]

        #if len(self.landmark_list) == 0 and self.landmark_str != "":
        #    self.unpack_landmark()

        if len(self.landmark_list) == 0:
            return c
        
        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        lm_dim = 2
        for lm in ( self.landmark_list ):
            sum_of_x += lm[0]
            sum_of_y += lm[1]
            if len(lm) == 3:
                lm_dim = 3
                sum_of_z += lm[2]
        lm_count = len(self.landmark_list)
        c[0] = sum_of_x / lm_count
        c[1] = sum_of_y / lm_count
        if lm_dim == 3:
            c[2] = sum_of_z / lm_count
        return c

    def get_centroid_size(self, refresh=False):

        #if len(self.landmark_list) == 0 and self.landmark_str != "":
        #    self.unpack_landmark()

        if len(self.landmark_list) == 0:
            return -1
        elif len(self.landmark_list)== 1:
            return 1
        if ( self.centroid_size > 0 ) and ( refresh == False ):
            return self.centroid_size

        centroid = self.get_centroid_coord()
        # print "centroid:", centroid.xcoord, centroid.ycoord, centroid.zcoord
        sum_of_x_squared = 0
        sum_of_y_squared = 0
        sum_of_z_squared = 0
        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        lm_count = len(self.landmark_list)
        for lm in self.landmark_list:
            sum_of_x_squared += ( lm[0] - centroid[0]) ** 2
            sum_of_y_squared += ( lm[1] - centroid[1]) ** 2
            if len(lm) == 3:
                sum_of_z_squared += ( lm[2] - centroid[2]) ** 2
            sum_of_x += lm[0] - centroid[0]
            sum_of_y += lm[1] - centroid[1]
            if len(lm) == 3:
                sum_of_z += lm[2] - centroid[2]
        centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared
        #centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared \
        #              - sum_of_x * sum_of_x / lm_count \
        #              - sum_of_y * sum_of_y / lm_count \
        #              - sum_of_z * sum_of_z / lm_count
        #print centroid_size
        centroid_size = math.sqrt(centroid_size)
        self.centroid_size = centroid_size
        #centroid_size = float( int(  * 100 ) ) / 100
        return centroid_size

    def move(self, x, y, z=0):
        new_landmark_list = []
        #print("move 1:", id(self.landmark_list), self.landmark_list[0])
        for lm in self.landmark_list:
            lm[0] = lm[0] + x
            lm[1] = lm[1] + y
            if len(lm) == 3:
                lm[2] = lm[2] + z
            new_landmark_list.append(lm)
        self.landmark_list = new_landmark_list
        #print("move 2:", id(self.landmark_list), self.landmark_list[0])

    def move_to_center(self):
        centroid = self.get_centroid_coord()
        #print("centroid:", centroid[0], centroid[1], centroid[2])
        self.move(-1 * centroid[0], -1 * centroid[1], -1 * centroid[2])

    def rescale(self, factor):
        #print("rescale:", factor, self.landmark_list[:5])
        new_landmark_list = []
        for lm in self.landmark_list:
            lm = [x * factor for x in lm]
            new_landmark_list.append(lm)
        self.landmark_list = new_landmark_list
        #print("rescale:", factor, self.objname, self.landmark_list[:5])

    def rescale_to_unitsize(self):
        centroid_size = self.get_centroid_size(True)
        
        self.rescale(( 1 / centroid_size ))

    def apply_rotation_matrix(self, rotation_matrix):
        #print("obj_ops apply rotation", rotation_matrix)
        if len(self.landmark_list)>0:
            ones_column = np.ones((np.array(self.landmark_list).shape[0], 1))
            vertices_with_ones = np.hstack((self.landmark_list, ones_column))
            new_vertices = np.dot(vertices_with_ones, rotation_matrix.T)
            self.landmark_list = new_vertices[:, 0:3].tolist()


    def rotate_2d(self, theta):
        self.rotate_3d(theta, 'Z')
        return

    def rotate_3d(self, theta, axis):
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        r_mx = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if ( axis == 'Z' ):
            r_mx[0][0] = cos_theta
            r_mx[0][1] = sin_theta
            r_mx[1][0] = -1 * sin_theta
            r_mx[1][1] = cos_theta
        elif ( axis == 'Y' ):
            r_mx[0][0] = cos_theta
            r_mx[0][2] = sin_theta
            r_mx[2][0] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        elif ( axis == 'X' ):
            r_mx[1][1] = cos_theta
            r_mx[1][2] = sin_theta
            r_mx[2][1] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        # print "rotation matrix", r_mx

        for i, lm in enumerate(self.landmark_list):
            coords = [0,0,0]
            for j in range(len(lm)):
                coords[j] = lm[j]
            x_rotated = coords[0] * r_mx[0][0] + coords[1] * r_mx[1][0] + coords[2] * r_mx[2][0]
            y_rotated = coords[0] * r_mx[0][1] + coords[1] * r_mx[1][1] + coords[2] * r_mx[2][1]
            z_rotated = coords[0] * r_mx[0][2] + coords[1] * r_mx[1][2] + coords[2] * r_mx[2][2]
            self.landmark_list[i] = [ x_rotated, y_rotated, z_rotated ]

    def trim_decimal(self, dec=4):
        factor = math.pow(10, dec)

        for lm in self.landmark_list:
            lm = [float(round(x * factor)) / factor for x in lm]

    def print_landmarks(self, text=''):
        print("[", text, "] [", str(self.get_centroid_size()), "]")
        # lm= self.landmarks[0]
        print(self.landmark_list[:5])
        #for lm in self.landmark_list:
        #    print(lm)
            #break
            #lm= self.landmarks[1]
            #print lm.xcoord, ", ", lm.ycoord, ", ", lm.zcoord

    def align(self, baseline):
        if len(baseline) == 3:
            point1 = baseline[0]
            point2 = baseline[1]
            point3 = baseline[2]
        elif len(baseline) == 2:
            point1 = baseline[0]
            point2 = baseline[1]
            point3 = baseline[0]
        else:
            return
        #print("baseline:",baseline)

        #print(self.landmark_list)

        #print(self.landmark_list[point2 - 1], self.landmark_list[point1 - 1])

        curr_vector1 = np.array(self.landmark_list[point2 - 1]) - np.array(self.landmark_list[point1 - 1])

        if len(curr_vector1) == 2:
            to_vector1 = np.array([1, 0])
        else:        
            to_vector1 = np.array([1, 0, 0])


        #print("curr_vector1:", curr_vector1)
        #print("to_vector1:", to_vector1)
        v1_norm = curr_vector1 / np.linalg.norm(curr_vector1)
        to_norm = to_vector1 / np.linalg.norm(to_vector1)



        if np.allclose(v1_norm, to_norm):
            if len(curr_vector1) == 2:
                return
            # do nothing
            pass
        else:
            if len(curr_vector1) == 2:
                #print("2D rotation", curr_vector1, to_vector1)
                #print
                cos_theta = np.dot(curr_vector1, to_vector1) / (np.linalg.norm(curr_vector1) * np.linalg.norm(to_vector1))
                sin_theta = np.sqrt(1 - cos_theta ** 2)

                rotation_matrix = [ [ cos_theta, -1 * sin_theta], [sin_theta, cos_theta] ]
                # apply rotation matrix to landmarks
                #print("landmarks before rotation", self.landmark_list)
                #print("rotation matrix", rotation_matrix)
                for i, lm in enumerate(self.landmark_list):
                    coords = [0,0]
                    for j in range(len(lm)):
                        coords[j] = lm[j]
                    x_rotated = coords[0] * rotation_matrix[0][0] + coords[1] * rotation_matrix[1][0]
                    y_rotated = coords[0] * rotation_matrix[0][1] + coords[1] * rotation_matrix[1][1]
                    self.landmark_list[i] = [ x_rotated, y_rotated ]
                #print("landmarks after rotation", self.landmark_list)
                return
            else:
                # calculate cosine and sine of rotation angle
                cos_theta = np.dot(curr_vector1, to_vector1) / (np.linalg.norm(curr_vector1) * np.linalg.norm(to_vector1))
                sin_theta = np.sqrt(1 - cos_theta ** 2)

                #calculate rotation axis
                rotation_axis = np.cross(curr_vector1, to_vector1)
                rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)

                # calculate rotation matrix to align vector1 to x-axis - Rodrigues' rotation formula
                # https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
                r_mx = [[1, 0, 0,0], [0, 1, 0,0], [0, 0, 1,0],[0,0,0,1]]
                r_mx[0][0] = cos_theta + rotation_axis[0] * rotation_axis[0] * (1 - cos_theta)
                r_mx[0][1] = rotation_axis[0] * rotation_axis[1] * (1 - cos_theta) - rotation_axis[2] * sin_theta
                r_mx[0][2] = rotation_axis[0] * rotation_axis[2] * (1 - cos_theta) + rotation_axis[1] * sin_theta
                r_mx[1][0] = rotation_axis[1] * rotation_axis[0] * (1 - cos_theta) + rotation_axis[2] * sin_theta
                r_mx[1][1] = cos_theta + rotation_axis[1] * rotation_axis[1] * (1 - cos_theta)
                r_mx[1][2] = rotation_axis[1] * rotation_axis[2] * (1 - cos_theta) - rotation_axis[0] * sin_theta
                r_mx[2][0] = rotation_axis[2] * rotation_axis[0] * (1 - cos_theta) - rotation_axis[1] * sin_theta
                r_mx[2][1] = rotation_axis[2] * rotation_axis[1] * (1 - cos_theta) + rotation_axis[0] * sin_theta
                r_mx[2][2] = cos_theta + rotation_axis[2] * rotation_axis[2] * (1 - cos_theta)

                #r_mx = [[1, 0, 0,0], [0, 1, 0,0], [0, 0, 1,0],[0,0,0,1]]
                #r_mx[1][1] = cos_theta
                #r_mx[1][2] = sin_theta
                #r_mx[2][1] = -1 * sin_theta
                #r_mx[2][2] = cos_theta

                #print("rotation matrix:", r_mx)

                # apply rotation matrix to all landmarks
                self.apply_rotation_matrix(np.array(r_mx))

                curr_vector1 = np.array(self.landmark_list[point2 - 1]) - np.array(self.landmark_list[point1 - 1])
                #print("curr_vector1 after rotation:", curr_vector1)
                #print(self.landmark_list[point2 - 1], self.landmark_list[point1 - 1])

        mid_point12 = np.array(self.landmark_list[point1 - 1]) + curr_vector1 / 2
        curr_vector2 = np.array(self.landmark_list[point3 - 1]) - np.array(mid_point12)
        #projection_vector2 = np.dot(curr_vector2, curr_vector1) / np.linalg.norm(curr_vector1) * curr_vector1
        projection_vector2 = (np.dot(curr_vector2, curr_vector1) / np.linalg.norm(curr_vector1)**2) * curr_vector1



        curr_vector2 = curr_vector2 - projection_vector2
        to_vector2 = np.array([0, 1, 0])
        #print("curr_vector2:", curr_vector2)
        #print("to_vector2:", to_vector2)

        v2_norm = curr_vector2 / np.linalg.norm(curr_vector2)
        to_norm = to_vector2 / np.linalg.norm(to_vector2)


        if np.allclose(v2_norm, to_norm):
            # do nothing
            pass
        else:

            # calculate cosine and sine of rotation angle
            cos_theta = np.dot(curr_vector2, to_vector2) / (np.linalg.norm(curr_vector2) * np.linalg.norm(to_vector2))
            sin_theta = np.sqrt(1 - cos_theta ** 2)
            #print("cos_theta:", cos_theta, "sin_theta:", sin_theta)

            #calculate rotation axis
            rotation_axis = np.cross(curr_vector2, to_vector2)
            rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
            #print("rotation axis", rotation_axis)

            # calculate rotation matrix to align vector1 to x-axis - Rodrigues' rotation formula
            # https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
            r_mx = [[1, 0, 0,0], [0, 1, 0,0], [0, 0, 1,0],[0,0,0,1]]
            r_mx[0][0] = cos_theta + rotation_axis[0] * rotation_axis[0] * (1 - cos_theta)
            r_mx[0][1] = rotation_axis[0] * rotation_axis[1] * (1 - cos_theta) - rotation_axis[2] * sin_theta
            r_mx[0][2] = rotation_axis[0] * rotation_axis[2] * (1 - cos_theta) + rotation_axis[1] * sin_theta
            r_mx[1][0] = rotation_axis[1] * rotation_axis[0] * (1 - cos_theta) + rotation_axis[2] * sin_theta
            r_mx[1][1] = cos_theta + rotation_axis[1] * rotation_axis[1] * (1 - cos_theta)
            r_mx[1][2] = rotation_axis[1] * rotation_axis[2] * (1 - cos_theta) - rotation_axis[0] * sin_theta
            r_mx[2][0] = rotation_axis[2] * rotation_axis[0] * (1 - cos_theta) - rotation_axis[1] * sin_theta
            r_mx[2][1] = rotation_axis[2] * rotation_axis[1] * (1 - cos_theta) + rotation_axis[0] * sin_theta
            r_mx[2][2] = cos_theta + rotation_axis[2] * rotation_axis[2] * (1 - cos_theta)

            # apply rotation matrix to all landmarks
            self.apply_rotation_matrix(np.array(r_mx))

    def sliding_baseline_registration(self, baseline):
        csize = self.get_centroid_size()
        self.bookstein_registration(baseline, csize)

    def bookstein_registration(self, baseline, rescale=-1):
        # c = self.get_centroid_coord()
        #print "centroid:", c.xcoord, ", ", c.ycoord, ", ", c.zcoord
        point1 = point2 = point3 = -1
        if len(baseline) == 3:
            point1 = baseline[0]
            point2 = baseline[1]
            point3 = baseline[2]
        elif len(baseline) == 2:
            point1 = baseline[0]
            point2 = baseline[1]
            point3 = None
        point1 = point1 - 1
        point2 = point2 - 1
        if ( point3 != None ):
            point3 = point3 - 1

        #self.print_landmarks("before any processing");

        center = [0, 0, 0]
        center[0] = ( self.landmark_list[point1][0] + self.landmark_list[point2][0] ) / 2
        center[1] = ( self.landmark_list[point1][1] + self.landmark_list[point2][1] ) / 2
        center[2] = ( self.landmark_list[point1][2] + self.landmark_list[point2][2] ) / 2
        self.move(-1 * center[0], -1 * center[1], -1 * center[2])

        #self.print_landmarks("translation");
        #self.scale_to_univsize()
        xdiff = self.landmark_list[point1][0] - self.landmark_list[point2][0]
        ydiff = self.landmark_list[point1][1] - self.landmark_list[point2][1]
        zdiff = self.landmark_list[point1][2] - self.landmark_list[point2][2]
        #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff

        size = math.sqrt(xdiff * xdiff + ydiff * ydiff + zdiff * zdiff)
        #print "size: ", size
        #print "rescale: ", rescale
        if ( rescale < 0 ):
            self.rescale(( 1 / size ))
        elif ( rescale > 0 ):
            self.rescale(( 1 / rescale ))

        #self.print_landmarks("rescaling");

        if ( point3 != None ):
            xdiff = self.landmark_list[point1][0] - self.landmark_list[point2][0]
            ydiff = self.landmark_list[point1][1] - self.landmark_list[point2][1]
            zdiff = self.landmark_list[point1][2] - self.landmark_list[point2][2]
            cos_val = xdiff / math.sqrt(xdiff * xdiff + zdiff * zdiff)
            #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
            #print "cos val: ", cos_val
            theta = math.acos(cos_val)
            #print "theta: ", theta, ", ", theta * 180/math.pi
            if ( zdiff < 0 ):
                theta = theta * -1
            self.rotate_3d(-1 * theta, 'Y')

        #self.print_landmarks("rotate along xz plane");

        xdiff = self.landmark_list[point1][0] - self.landmark_list[point2][0]
        ydiff = self.landmark_list[point1][1] - self.landmark_list[point2][1]
        zdiff = self.landmark_list[point1][2] - self.landmark_list[point2][2]

        size = math.sqrt(xdiff * xdiff + ydiff * ydiff)
        cos_val = xdiff / size
        #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
        #print "cos val: ", cos_val
        theta = math.acos(cos_val)
        #print "theta: ", theta, ", ", theta * 180/math.pi
        if ( ydiff < 0 ):
            theta = theta * -1
        self.rotate_2d(-1 * theta)

        if ( point3 != None ):
            xdiff = self.landmark_list[point3][0]
            ydiff = self.landmark_list[point3][1]
            zdiff = self.landmark_list[point3][2]
            size = math.sqrt(ydiff ** 2 + zdiff ** 2)
            cos_val = ydiff / size
            theta = math.acos(cos_val)
            if ( zdiff < 0 ):
                theta = theta * -1
            self.rotate_3d(-1 * theta, 'X')

class MdDatasetOps:
    def __init__(self,dataset):
        self.id = dataset.id
        self.dataset_name = dataset.dataset_name
        self.dataset_desc = dataset.dataset_desc
        self.dimension = dataset.dimension
        self.wireframe = dataset.wireframe
        self.baseline = dataset.baseline
        self.polygons = dataset.polygons
        self.object_list = []
        self.selected_object_id_list = []
        self.edge_list = []
        for mo in dataset.object_list:
            #self.object_list.append(mo.copy())
            self.object_list.append(MdObjectOps(mo))
        
        if dataset.wireframe is not None and dataset.wireframe != '':
            dataset.unpack_wireframe()
        if dataset.edge_list is not None and len(dataset.edge_list) > 0:
            self.edge_list = dataset.edge_list[:]
        #print("edge list in MdDatasetOps.__init__:", dataset.wireframe, dataset.edge_list, self.edge_list)
        self.propertyname_list = dataset.propertyname_list
        if dataset.polygons != '':
            dataset.unpack_polygons()
        if dataset.baseline != '':
            dataset.unpack_baseline()
        
        self.baseline_point_list = dataset.baseline_point_list
        #print self
    def reset_pose(self):
        pass

    def set_reference_shape(self, shape):
        self.reference_shape = shape

    def rotate_gls_to_reference_shape(self, object_index):
        num_obj = len(self.object_list)
        if ( num_obj == 0 or num_obj - 1 < object_index  ):
            return

        mo = self.object_list[object_index]
        nlandmarks = len(mo.landmark_list)
        target_shape = np.zeros((nlandmarks, self.dimension))
        reference_shape = np.zeros((nlandmarks, self.dimension))

        i = 0
        for lm in ( mo.landmark_list ):
            for j in range(self.dimension):
                target_shape[i,j] = lm[j]
            i += 1

        i = 0
        for lm in self.reference_shape.landmark_list:
            for j in range(self.dimension):
                reference_shape[i,j] = lm[j]
            i += 1

        rotation_matrix = self.rotation_matrix(reference_shape, target_shape)
        #print rotation_matrix
        #target_transposed = np.transpose( target_shape )
        #print target_transposed
        #print rotation_matrix.shape
        #print target_transposed.shape
        rotated_shape = np.transpose(np.dot(rotation_matrix, np.transpose(target_shape)))

        #print rotated_shape

        i = 0
        new_landmark_list = []
        for i in range( len(mo.landmark_list) ):
            lm = [0] * self.dimension
            #lm = [0,0,0]
            for j in range(self.dimension):
                lm[j] = rotated_shape[i,j]
            new_landmark_list.append(lm)
            #lm = [ rotated_shape[i, 0], rotated_shape[i, 1], rotated_shape[i, 2] ]
            #i += 1
        mo.landmark_list = new_landmark_list

    def apply_rotation_matrix(self, rotation_matrix):
        #print("obj_ops apply rotation", rotation_matrix)
        for mo in self.object_list:
            if len(mo.landmark_list)>0:
                ones_column = np.ones((np.array(mo.landmark_list).shape[0], 1))
                vertices_with_ones = np.hstack((mo.landmark_list, ones_column))
                new_vertices = np.dot(vertices_with_ones, rotation_matrix.T)
                mo.landmark_list = new_vertices[:, 0:3].tolist()

    def rotation_matrix(self, ref, target):
        #assert( ref[0] == 3 )
        #assert( ref.shape == target.shape )

        correlation_matrix = np.dot(np.transpose(ref), target)
        v, s, w = np.linalg.svd(correlation_matrix)
        is_reflection = ( np.linalg.det(v) * np.linalg.det(w) ) < 0.0
        if is_reflection:
            v[-1, :] = -v[-1, :]
        rot_mx = np.dot(v, w)
        #print("rotation_matrix:",rot_mx)
        return rot_mx

    def get_average_shape(self):

        object_count = len(self.object_list)

        average_shape = MdObjectOps(MdObject())
        average_shape.landmark_list = []

        sum_x = []
        sum_y = []
        sum_z = []

        for mo in self.object_list:
            i = 0
            for lm in mo.landmark_list:
                if len(sum_x) <= i:
                    sum_x.append(0)
                    sum_y.append(0)
                    sum_z.append(0)
                sum_x[i] += lm[0]
                sum_y[i] += lm[1]
                if self.dimension == 3:
                    sum_z[i] += lm[2]
                i += 1
        for i in range(len(sum_x)):
            if self.dimension == 2:
                lm = [ float(sum_x[i]) / object_count, float(sum_y[i]) / object_count ]
            else:
                lm = [ float(sum_x[i]) / object_count, float(sum_y[i]) / object_count, float(sum_z[i]) / object_count ]
            average_shape.landmark_list.append(lm)
        if self.id:
            average_shape.dataset_id = self.id
        return average_shape

    def check_object_list(self):
        min_number_of_landmarks = 999999
        max_number_of_landmarks = -999999
        sum_val = 0
        for mo in self.object_list:
            number_of_landmarks = len(mo.landmark_list)
            # print number_of_landmarks
            sum_val += number_of_landmarks
            min_number_of_landmarks = min(min_number_of_landmarks, number_of_landmarks)
            max_number_of_landmarks = max(max_number_of_landmarks, number_of_landmarks)
        #average_number_of_landmarks = float( sum_val ) / len( self.objects )
        #print min_number_of_landmarks, max_number_of_landmarks
        if sum_val > 0 and min_number_of_landmarks != max_number_of_landmarks:
            print("Inconsistent number of landmarks", min_number_of_landmarks, max_number_of_landmarks)
            return False
        return True

    def procrustes_superimposition(self):
        #print("begin_procrustes")
        if not self.check_object_list():
            print("check_object_list failed")
            return False

        for mo in self.object_list:
            #mo.set_landmarks()
            mo.move_to_center()
            mo.rescale_to_unitsize()
        #print("move_to_center and rescale_to_unitsize done")
        #print("object",self.object_list[0].landmark_list[:5])

        average_shape = None
        previous_average_shape = None
        i = 0
        while ( True ):
            i += 1
            #print("progressing...", i)
            previous_average_shape = average_shape
            average_shape = self.get_average_shape()

            #average_shape.print_landmarks("average_shape")

            if ( self.is_same_shape(previous_average_shape, average_shape) and previous_average_shape != None ):
                break
            self.set_reference_shape(average_shape)
            for j in range(len(self.object_list)):
                self.rotate_gls_to_reference_shape(j)
                #self.objects[0].print_landmarks('aa')
                #self.objects[1].print_landmarks('bb')
                #average_shape.print_landmarks('cc')
        #print("end procrustes")
        return True

    def is_same_shape(self, shape1, shape2):
        if ( shape1 == None or shape2 == None ):
            return False
        sum_coord = 0
        for i in range(len(shape1.landmark_list)):
            sum_coord += ( shape1.landmark_list[i][0] - shape2.landmark_list[i][0]) ** 2
            sum_coord += ( shape1.landmark_list[i][1] - shape2.landmark_list[i][1]) ** 2
            if self.dimension == 3:
                sum_coord += ( shape1.landmark_list[i][2] - shape2.landmark_list[i][2]) ** 2
        #shape1.print_landmarks("shape1")
        #shape2.print_landmarks("shape2")
        sum_coord = math.sqrt(sum_coord)
        #print "diff: ", sum
        if sum_coord < 10 ** -10:
            return True
        return False

    def resistant_fit_superimposition(self):
        if len(self.object_list) == 0:
            print( "No objects to transform!")
            raise 

        for mo in self.object_list:
            mo.move_to_center()
        average_shape = None
        previous_average_shape = None

        i = 0
        while True:
            i += 1
            #print "iteration: ", i
            previous_average_shape = average_shape
            average_shape = self.get_average_shape()
            average_shape.rescale_to_unitsize()
            if self.is_same_shape(previous_average_shape, average_shape) and previous_average_shape is not None:
                break
            self.set_reference_shape(average_shape)
            for j in range(len(self.object_list)):
                self.rotate_resistant_fit_to_reference_shape(j)

    def rotate_vector_2d(self, theta, vec):
        return self.rotate_vector_3d(theta, vec, 'Z')

    def rotate_vector_3d(self, theta, vec, axis):
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        r_mx = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if ( axis == 'Z' ):
            r_mx[0][0] = cos_theta
            r_mx[0][1] = sin_theta
            r_mx[1][0] = -1 * sin_theta
            r_mx[1][1] = cos_theta
        elif ( axis == 'Y' ):
            r_mx[0][0] = cos_theta
            r_mx[0][2] = sin_theta
            r_mx[2][0] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        elif ( axis == 'X' ):
            r_mx[1][1] = cos_theta
            r_mx[1][2] = sin_theta
            r_mx[2][1] = -1 * sin_theta
            r_mx[2][2] = cos_theta

        x_rotated = vec[0] * r_mx[0][0] + vec[1] * r_mx[1][0] + vec[2] * r_mx[2][0]
        y_rotated = vec[0] * r_mx[0][1] + vec[1] * r_mx[1][1] + vec[2] * r_mx[2][1]
        z_rotated = vec[0] * r_mx[0][2] + vec[1] * r_mx[1][2] + vec[2] * r_mx[2][2]
        vec[0] = x_rotated
        vec[1] = y_rotated
        vec[2] = z_rotated
        return vec

    def rotate_resistant_fit_to_reference_shape(self, object_index):
        num_obj = len(self.object_list)
        if num_obj == 0 or num_obj - 1 < object_index:
            return

        target_shape = self.object_list[object_index]
        nlandmarks = len(target_shape.landmark_list)
        #target_shape = np.zeros((nlandmarks,3))
        reference_shape = self.reference_shape

        #rotation_matrix = self.rotation_matrix( reference_shape, target_shape )

        #rotated_shape = np.transpose( np.dot( rotation_matrix, np.transpose( target_shape ) ) )

        # obtain scale factor using repeated median
        landmark_count = len(reference_shape.landmark_list)
        inner_tau_array = []
        outer_tau_array = []
        median_index = -1
        for i in range(landmark_count - 1):
            for j in range(i + 1, landmark_count):
                target_distance = math.sqrt(
                    ( target_shape.landmark_list[i][0] - target_shape.landmark_list[j][0] ) ** 2 + \
                    ( target_shape.landmark_list[i][1] - target_shape.landmark_list[j][1] ) ** 2 + \
                    ( target_shape.landmark_list[i][2] - target_shape.landmark_list[j][2] ) ** 2)
                reference_distance = math.sqrt(
                    ( reference_shape.landmark_list[i][0] - reference_shape.landmark_list[j][0] ) ** 2 + \
                    ( reference_shape.landmark_list[i][1] - reference_shape.landmark_list[j][1] ) ** 2 + \
                    ( reference_shape.landmark_list[i][2] - reference_shape.landmark_list[j][2] ) ** 2)
                tau = reference_distance / target_distance
                inner_tau_array.append(tau)
                median_index = self.get_median_index(inner_tau_array)
            #       print median_index
            #print "tau: ", inner_tau_array
            outer_tau_array.append(inner_tau_array[median_index])
            inner_tau_array = []
        median_index = self.get_median_index(outer_tau_array)
        #print "tau: ", outer_tau_array
        tau_final = outer_tau_array[median_index]

        # rescale to scale factor
        #print "index:", object_index
        #print "scale factor:", tau_final
        #target_shape.print_landmarks("before rescale")
        target_shape.rescale(tau_final)
        #target_shape.print_landmarks("after rescale")
        #exit

        # obtain rotation angle using repeated median
        inner_theta_array = []
        outer_theta_array = []
        inner_vector_array = []
        outer_vector_array = []
        for i in range(landmark_count - 1):
            for j in range(i + 1, landmark_count):
                # get vector
                target_vector = np.array([target_shape.landmark_list[i][0] - target_shape.landmark_list[j][0],
                                             target_shape.landmark_list[i][1] - target_shape.landmark_list[j][1],
                                             target_shape.landmark_list[i][2] - target_shape.landmark_list[j][2]])
                reference_vector = np.array([reference_shape.landmark_list[i][0] - reference_shape.landmark_list[j][0],
                                             reference_shape.landmark_list[i][1] - reference_shape.landmark_list[j][1],
                                             reference_shape.landmark_list[i][2] - reference_shape.landmark_list[j][2]])
                #       cos_val = ( target_vector[0] * reference_vector[0] + \
                #                   target_vector[1] * reference_vector[1] + \
                #                   target_vector[2] * reference_vector[2] ) \
                #                  / \
                #                  ( math.sqrt( target_vector[0] ** 2 + target_vector[1]**2 + target_vector[2]**2 ) * \
                #                    math.sqrt( reference_vector[0] ** 2 + reference_vector[1]**2 + reference_vector[2]**2 ) )
                #        if( cos_val > 1.0 ):
                #          print "cos_val 1: ", cos_val
                #          print target_vector
                #          print reference_vector
                #          print math.acos( cos_val )
                #          cos_val = 1.0
                cos_val = np.vdot(target_vector, reference_vector) / np.linalg.norm(
                    target_vector) * np.linalg.norm(reference_vector)
                #        if( cos_val > 1.0 ):
                #          print "cos_val 2: ", cos_val
                #          cos_val = 1.0
                #        try:
                #          if( cos_val == 1.0 ):
                #            theta = 0.0
                #          else:
                theta = math.acos(cos_val)
                #        except ValueError:
                #          print "acos value error"
                #          theta = 0.0
                inner_theta_array.append(theta)
                inner_vector_array.append(np.array([target_vector, reference_vector]))
                #print inner_vector_array[-1]
            median_index = self.get_median_index(inner_theta_array)
            #      print inner_vector_array[median_index]
            outer_theta_array.append(inner_theta_array[median_index])
            outer_vector_array.append(inner_vector_array[median_index])
            inner_theta_array = []
            inner_vector_array = []
        median_index = self.get_median_index(outer_theta_array)
        # theta_final = outer_theta_array[median_index]
        vector_final = outer_vector_array[median_index]
        #    print vector_final

        target_shape = np.zeros((1, 3))
        reference_shape = np.zeros((1, 3))
        #print vector_final
        target_shape[0] = vector_final[0]
        reference_shape[0] = vector_final[1]

        rotation_matrix = self.get_vector_rotation_matrix(vector_final[1], vector_final[0])

        #rotation_matrix = self.rotation_matrix( reference_shape, target_shape )
        #print reference_shape
        #print target_shape
        #rotated_shape = np.transpose( np.dot( rotation_matrix, np.transpose( target_shape ) ) )
        #print rotated_shape
        #exit
        target_shape = np.zeros((nlandmarks, 3))
        i = 0
        for lm in ( self.object_list[object_index].landmark_list ):
            target_shape[i] = lm
            i += 1

        reference_shape = np.zeros((nlandmarks, 3))
        i = 0
        for lm in ( self.reference_shape.landmark_list ):
            reference_shape[i] = lm
            i += 1

        rotated_shape = np.transpose(np.dot(rotation_matrix, np.transpose(target_shape)))

        #print "reference: ", reference_shape[0]
        #print "target: ", target_shape[0], np.linalg.norm(target_shape[0])
        #print "rotation: ", rotation_matrix
        #print "rotated: ", rotated_shape[0], np.linalg.norm(rotated_shape[0])
        #print "determinant: ", np.linalg.det( rotation_matrix )

        i = 0
        for lm in ( self.object_list[object_index].landmark_list ):
            lm = [ rotated_shape[i, 0], rotated_shape[i, 1], rotated_shape[i, 2] ]
            i += 1
        if ( object_index == 0 ):
            pass
            #self.reference_shape.print_landmarks("ref:")
            #self.objects[object_index].print_landmarks(str(object_index))
            #print "reference: ", reference_shape[0]
            #print "target: ", target_shape[0], np.linalg.norm(target_shape[0])
            #print "rotation: ", rotation_matrix
            #print "rotated: ", rotated_shape[0], np.linalg.norm(rotated_shape[0])
            #print "determinant: ", np.linalg.det( rotation_matrix )

    def get_vector_rotation_matrix(self, ref, target):
        ( x, y, z ) = ( 0, 1, 2 )
        #print ref
        #print target
        #print "0 ref", ref
        #print "0 target", target

        ref_1 = ref
        ref_1[z] = 0
        cos_val = ref[x] / math.sqrt(ref[x] ** 2 + ref[z] ** 2)
        theta1 = math.acos(cos_val)
        if ( ref[z] < 0 ):
            theta1 = theta1 * -1
        ref = self.rotate_vector_3d(-1 * theta1, ref, 'Y')
        target = self.rotate_vector_3d(-1 * theta1, target, 'Y')

        #print "1 ref", ref
        #print "1 target", target

        cos_val = ref[x] / math.sqrt(ref[x] ** 2 + ref[y] ** 2)
        theta2 = math.acos(cos_val)
        if ( ref[y] < 0 ):
            theta2 = theta2 * -1
        ref = self.rotate_vector_2d(-1 * theta2, ref)
        target = self.rotate_vector_2d(-1 * theta2, target)

        #print "2 ref", ref
        #print "2 target", target

        cos_val = target[x] / math.sqrt(( target[x] ** 2 + target[z] ** 2 ))
        theta1 = math.acos(cos_val)
        if ( target[z] < 0 ):
            theta1 = theta1 * -1
        target = self.rotate_vector_3d(-1 * theta1, target, 'Y')

        #print "3 ref", ref
        #print "3 target", target

        cos_val = target[x] / math.sqrt(( target[x] ** 2 + target[y] ** 2 ))
        theta2 = math.acos(cos_val)
        if ( target[y] < 0 ):
            theta2 = theta2 * -1
        target = self.rotate_vector_2d(-1 * theta2, target)

        #print "4 ref", ref
        #print "4 target", target

        r_mx1 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        r_mx2 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        #print "shape:", r_mx1.shape
        #print "r_mx1", r_mx1
        #print "theta1", theta1
        #print "cos theta1", math.cos( theta1 )
        #print "sin theta1", math.sin( theta1 )
        #print "r_mx2", r_mx2
        #print "theta2", theta2
        r_mx1[0][0] = math.cos(theta1)
        r_mx1[0][2] = math.sin(theta1)
        r_mx1[2][0] = math.sin(theta1) * -1
        r_mx1[2][2] = math.cos(theta1)

        #print "r_mx1", r_mx1
        #print "theta1", theta1
        #print "r_mx2", r_mx2
        #print "theta2", theta2

        r_mx2[0][0] = math.cos(theta2)
        r_mx2[0][1] = math.sin(theta2)
        r_mx2[1][0] = math.sin(theta2) * -1
        r_mx2[1][1] = math.cos(theta2)

        #print "r_mx1", r_mx1
        #print "theta1", theta1
        #print "r_mx2", r_mx2
        #print "theta2", theta2

        rotation_matrix = np.dot(r_mx1, r_mx2)
        return rotation_matrix


    def get_median_index(self, arr):
        arr.sort()
        len_arr = len(arr)
        if ( len_arr == 0 ):
            return -1
        half_len = int(math.floor(len_arr / 2.0))
        return half_len

class MdAnalysis(Model):
    analysis_name = CharField()
    analysis_desc = CharField(null=True)
    ''' dataset info '''
    dataset = ForeignKeyField(MdDataset, related_name='analyses', null=True,on_delete="CASCADE")
    dimension = IntegerField(default=2)
    wireframe = CharField(null=True)
    baseline = CharField(null=True)
    polygons = CharField(null=True)
    propertyname_str = CharField(null=True)
    superimposition_method = CharField()
    #analysis_method = CharField() # PCA or CVA

    ''' object info '''
    object_info_json = CharField(null=True) # object name, id, properties and centroid size
    raw_landmark_json = CharField(null=True)    # raw landmark info in list of list format
    superimposed_landmark_json = CharField(null=True) # superimposed landmark info in list of list format

    ''' PCA result '''
    cva_group_by = CharField(null=True)
    pca_analysis_result_json = CharField(null=True) # PCA result in list of list format
    pca_rotation_matrix_json = CharField(null=True) # rotation matrix from PCA
    pca_eigenvalues_json = CharField(null=True) # PCA eigenvalues and percentages of variance explained

    ''' CVA result '''
    cva_group_by = CharField(null=True)
    cva_analysis_result_json = CharField(null=True) # CVA result in list of list format
    cva_rotation_matrix_json = CharField(null=True) # rotation matrix from CVA
    cva_eigenvalues_json = CharField(null=True) # CVA eigenvalues and percentages of variance explained

    ''' MANOVA result'''
    manova_group_by = CharField(null=True)
    manova_analysis_result_json = CharField(null=True) # MANOVA results

    #virtual_specimens_json = CharField(null=True) # list of virtual specimens

    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)
    class Meta:
        database = gDatabase
