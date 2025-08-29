#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

import MdModel

# Test landmark unpacking
test_db = MdModel.SqliteDatabase(':memory:', pragmas={'foreign_keys': 1})
MdModel.gDatabase = test_db

# Update model metadata
models = [MdModel.MdDataset, MdModel.MdObject, MdModel.MdImage, MdModel.MdThreeDModel, MdModel.MdAnalysis]
for model in models:
    model._meta.database = test_db

# Create tables
test_db.connect()
test_db.create_tables(models, safe=True)

# Create dataset
dataset = MdModel.MdDataset.create(
    dataset_name="Test Dataset",
    dimension=2,
    landmark_count=5
)

# Create object with landmarks
obj = MdModel.MdObject.create(
    dataset=dataset,
    object_name="Test Object",
    sequence=1
)

# Set landmark data
landmark_str = "\n".join([f"{j}.0\t{j+1}.0" for j in range(5)])
print(f"Setting landmark_str: {repr(landmark_str)}")
obj.landmark_str = landmark_str
obj.save()

# Test unpacking
print(f"Before unpack - landmark_str: {repr(obj.landmark_str)}")
result = obj.unpack_landmark()
print(f"After unpack - landmark_list: {obj.landmark_list}")
print(f"Unpack result: {result}")

test_db.close()