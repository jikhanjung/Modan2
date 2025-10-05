import MdModel1

import MdModel as md2

ds_list = MdModel1.MdDataset.select()
for ds in ds_list:
    print(ds.dsname)
    ds2 = md2.MdDataset()
    ds2.dataset_name = ds.dsname
    ds2.dataset_description = ds.dsdesc
    ds2.dimension = ds.dimension
    ds2.group_name = ds.groupname
    if ds.wireframe:
        # new_wireframe = ""
        new_wire_list = []
        wire_list = ds.wireframe.split(",")

        for wire in wire_list:
            new_point_list = []
            point_list = wire.split("-")
            new_point_list = [int(x) - 1 for x in point_list]
            new_wire_list.append("-".join([str(x) for x in new_point_list]))
        ds2.wireframe = ",".join(new_wire_list)

        # ds2.wireframe = ",".join( [ int(x) - 1 for x in  ] )

    ds2.baseline = ds.baseline
    ds2.polygons = ds.polygons
    ds2.created_at = ds.created_at
    ds2.propertyname_str = ds.groupname
    ds2.save()

    for obj in ds.objects:
        print(obj.objname, len(obj.landmarks), obj.created_at)

        landmark_list = []
        for lm in obj.landmarks:
            landmark_list.append("\t".join([str(x) for x in [lm.xcoord, lm.ycoord, lm.zcoord]]))

        property_list = []
        for i in range(10):
            prop = getattr(obj, "group" + str(i + 1))
            if prop:
                property_list.append(prop)

        obj2 = md2.MdObject()
        obj2.object_name = obj.objname
        obj2.object_description = obj.objdesc
        obj2.scale = obj.scale
        obj2.property_str = ",".join(property_list)
        obj2.landmark_str = "\n".join([str(x) for x in landmark_list])
        obj2.created_at = obj.created_at
        obj2.dataset = ds2
        obj2.save()
        #    print(lm.lmseq, lm.xcoord, lm.ycoord, lm.zcoord)


# ds2.dsname = "test"
