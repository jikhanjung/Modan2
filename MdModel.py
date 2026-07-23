import copy
import datetime
import hashlib
import io
import json
import logging
import math
import os

# from MdUtils import *
import shutil
import time
import warnings
from pathlib import Path

import numpy as np
from peewee import CharField, DateTimeField, DoubleField, ForeignKeyField, IntegerField, Model, SqliteDatabase
from PIL import Image
from PIL.ExifTags import TAGS

import MdUtils as mu

logger = logging.getLogger(__name__)

LANDMARK_SEPARATOR = "\t"
LINE_SEPARATOR = "\n"
VARIABLE_SEPARATOR = ","
EDGE_SEPARATOR = "-"
WIREFRAME_SEPARATOR = ","
DATABASE_FILENAME = mu.PROGRAM_NAME + ".db"


def landmark_position_count(obj):
    """Number of landmark *positions* on an object, missing ones included.

    A missing landmark still occupies a position — Procrustes imputes it — so
    this, not ``count_landmarks()``, is the measure for consistency checks.
    Works for both ``MdObject`` (unpacking on demand) and ``MdObjectOps``.
    """
    if not getattr(obj, "landmark_list", None) and hasattr(obj, "unpack_landmark"):
        obj.unpack_landmark()
    return len(getattr(obj, "landmark_list", None) or [])


def find_landmark_count_mismatch(objects):
    """Find the first object whose landmark-position count differs from the first's.

    The single implementation of "do these objects agree on landmark count",
    shared by ``MdDatasetOps.check_object_list`` (the Procrustes gate) and the
    controller's pre-analysis validation. They used to answer this question
    separately, and disagreed: the controller compared a missing-*excluding*
    expected count against missing-*including* actuals, so any object with a
    missing landmark failed against itself.

    Returns:
        ``(object, expected, found)`` for the first offender, or ``None`` when
        the counts agree (including when there is nothing to compare).
    """
    objects = list(objects)
    if not objects:
        return None
    expected = landmark_position_count(objects[0])
    for obj in objects:
        found = landmark_position_count(obj)
        if found != expected:
            return obj, expected, found
    return None


# How many times Procrustes imputation may re-estimate the gaps. Each round
# re-aligns the (now complete) objects and re-fits the estimates to the improved
# mean; on synthetic data the estimates stop moving after two or three.
MAX_IMPUTATION_REFINEMENTS = 5


def impute_missing_landmarks(landmark_list, reference_landmarks, dimension=None):
    """Fill missing landmarks from a reference shape fitted onto the observed ones.

    The reference (normally a Procrustes mean) is mapped onto ``landmark_list``
    with a similarity transform — rotation via Kabsch with reflection excluded,
    plus scale and translation — fitted on the landmarks present in both, and
    the gaps are filled from the transformed reference.

    Fitting rather than copying the reference's coordinates straight across is
    what makes the estimate land in the right place whenever the object is not
    already sitting in the reference's frame. Two callers need exactly this:
    the object dialog's preview, where the specimen is in image coordinates and
    may have been photographed at any angle, and Procrustes imputation, where an
    object with gaps was centred and scaled on its observed subset while the
    mean comes from whole configurations.

    ``dimension`` defaults to the reference shape's own dimensionality, so a
    caller that has no dataset at hand does not have to guess.

    Returns a new landmark list. The input is returned (copied) unchanged when
    the reference is missing or too few landmarks are shared to fit.
    """
    result = [list(lm) for lm in (landmark_list or [])]
    if not result or not reference_landmarks:
        return result

    if dimension is None:
        dimension = max((len(lm) for lm in reference_landmarks if lm), default=2)
        dimension = min(max(dimension, 2), 3)

    def _complete(lm):
        return len(lm) >= dimension and all(c is not None for c in lm[:dimension])

    shared = [
        i
        for i in range(min(len(result), len(reference_landmarks)))
        if _complete(result[i]) and _complete(reference_landmarks[i])
    ]
    if len(shared) < dimension:
        logger.warning("Cannot fit reference shape: %d shared landmarks, need %d", len(shared), dimension)
        return result

    target = np.array([result[i][:dimension] for i in shared], dtype=float)
    source = np.array([reference_landmarks[i][:dimension] for i in shared], dtype=float)

    target_centroid = target.mean(axis=0)
    source_centroid = source.mean(axis=0)
    target_centered = target - target_centroid
    source_centered = source - source_centroid

    target_size = np.sqrt((target_centered**2).sum())
    source_size = np.sqrt((source_centered**2).sum())
    scale = target_size / source_size if source_size > 0 else 1.0

    rotation = np.eye(dimension)
    if source_size > 0 and target_size > 0:
        u, _, vt = np.linalg.svd(source_centered.T @ target_centered)
        reflection = np.sign(np.linalg.det(vt.T @ u.T)) or 1.0
        diagonal = np.ones(dimension)
        diagonal[-1] = reflection
        rotation = vt.T @ np.diag(diagonal) @ u.T

    filled = 0
    for i in range(len(result)):
        if _complete(result[i]):
            continue
        if i >= len(reference_landmarks) or not _complete(reference_landmarks[i]):
            continue  # nothing to estimate from (landmark absent everywhere)
        point = np.array(reference_landmarks[i][:dimension], dtype=float)
        transformed = rotation @ (point - source_centroid) * scale + target_centroid
        for d in range(dimension):
            if d < len(result[i]):
                result[i][d] = float(transformed[d])
        filled += 1

    logger.debug("Imputed %d landmark(s); fit scale=%.4f", filled, scale)
    return result


def find_unimputable_landmarks(objects):
    """Landmark positions that *no* object records.

    Procrustes fills a missing coordinate from the per-coordinate mean of the
    other objects. When every object is missing the same coordinate that mean is
    undefined (``nanmean`` of an all-NaN slice), the ``None`` survives
    superimposition and only surfaces much later, in the analysis matrix, as
    ``float() argument must be a string or a real number, not 'NoneType'``.

    Detection is per *coordinate* — a landmark whose X is everywhere present but
    whose Y is everywhere missing is just as unimputable — while the result is
    reported per landmark, which is what the user sees in the table.

    Returns:
        Sorted 0-based landmark indices with at least one such coordinate.
    """
    objects = list(objects)
    if not objects:
        return []

    for obj in objects:
        landmark_position_count(obj)  # force unpack

    row_count = max((len(obj.landmark_list) for obj in objects), default=0)
    unimputable = []
    for row in range(row_count):
        width = max((len(obj.landmark_list[row]) for obj in objects if row < len(obj.landmark_list)), default=0)
        for col in range(width):
            if all(
                row >= len(obj.landmark_list)
                or col >= len(obj.landmark_list[row])
                or obj.landmark_list[row][col] is None
                for obj in objects
            ):
                unimputable.append(row)
                break
    return unimputable


database_path = os.path.join(mu.DEFAULT_DB_DIRECTORY, DATABASE_FILENAME)

gDatabase = SqliteDatabase(database_path, pragmas={"foreign_keys": 1})


def set_database_path(path):
    """Point the application at a different database file.

    Every model binds to ``gDatabase`` at import time, so the file cannot be
    changed by reassigning ``database_path`` alone -- peewee has to be told, via
    ``init``, to reuse the same Database object against another file. Call this
    before anything queries the database (``--db`` does, at startup).
    """
    global database_path

    path = os.path.abspath(os.path.expanduser(path))
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    if not gDatabase.is_closed():
        gDatabase.close()
    gDatabase.init(path, pragmas={"foreign_keys": 1})
    database_path = path
    logger.info("database path set to %s", path)
    return path


class MdDataset(Model):
    dataset_name = CharField()
    dataset_desc = CharField(null=True)
    dimension = IntegerField(default=2)
    wireframe = CharField(null=True)
    baseline = CharField(null=True)
    polygons = CharField(null=True)
    parent = ForeignKeyField("self", backref="children", null=True, on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)
    propertyname_str = CharField(null=True)
    # Semi-landmark curve configuration (JSON). See get_curve_config(). Nullable,
    # so datasets without curves simply have none.
    curve_config_json = CharField(null=True)
    # Per-landmark name/abbreviation and description (JSON). See
    # get_landmark_names(). Dataset-wide, indexed by landmark position. Nullable.
    landmark_name_json = CharField(null=True)

    class Meta:
        database = gDatabase

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Per-instance scratch state populated by the unpack_*/pack_* helpers.
        # These are NOT DB fields; they were previously class-level mutable
        # defaults shared across every instance (R01 C2), which leaked data
        # between datasets when mutated in place.
        self.baseline_point_list = []
        self.edge_list = []
        self.polygon_list = []
        self.variablename_list = []

    def get_curve_config(self):
        """Semi-landmark curve configuration as a list, ``[]`` when unset or unreadable.

        Each entry describes one curve whose evenly-spaced semi-landmarks are
        appended to every object's landmark list:
        ``{"id": str, "n": int, "method": "equidistant"|"equal_angle", "start": int}``
        -- the target semi-landmark count, the resampling method, and the 0-based
        index in ``landmark_list`` where this curve's points begin. Never raises:
        a corrupt blob must not stop a dataset from opening.
        """
        if not self.curve_config_json:
            return []
        try:
            config = json.loads(self.curve_config_json)
        except (ValueError, TypeError) as e:
            logger.warning("Ignoring unreadable curve config for dataset %s: %s", self.id, e)
            return []
        return config if isinstance(config, list) else []

    def set_curve_config(self, config):
        """Store semi-landmark curve configuration (see :meth:`get_curve_config`)."""
        self.curve_config_json = json.dumps(config) if config else None

    def get_landmark_names(self):
        """Per-landmark names as a list, ``[]`` when unset or unreadable.

        Each entry is ``{"name": str, "desc": str}`` for the landmark at that
        index (an abbreviation like ``CR1`` plus a longer description). The list
        may be shorter than the landmark count; missing entries are unnamed.
        Never raises.
        """
        if not self.landmark_name_json:
            return []
        try:
            names = json.loads(self.landmark_name_json)
        except (ValueError, TypeError) as e:
            logger.warning("Ignoring unreadable landmark names for dataset %s: %s", self.id, e)
            return []
        return names if isinstance(names, list) else []

    def set_landmark_names(self, names):
        """Store per-landmark names (see :meth:`get_landmark_names`).

        Trailing fully-empty entries are dropped so an all-blank list clears the
        field rather than persisting noise.
        """
        trimmed = list(names or [])
        while trimmed and not (trimmed[-1].get("name") or trimmed[-1].get("desc")):
            trimmed.pop()
        self.landmark_name_json = json.dumps(trimmed) if trimmed else None

    def get_grouping_variable_index_list(self):
        variablename_list = self.get_variablename_list()
        object_count = len(self.object_list)
        valid_property_index_list = []
        # print("object count:", object_count, "propertyname_list:", propertyname_list)
        for idx, _variablename in enumerate(variablename_list):
            # print("propertyname:", propertyname, idx)
            unique_variable_list = []
            for obj in self.object_list:
                variable_list = obj.get_variable_list()
                if idx < len(variable_list) and variable_list[idx] not in unique_variable_list:
                    unique_variable_list.append(variable_list[idx])
            # print("unique_variable_list:", unique_variable_list, len(unique_variable_list))
            if len(unique_variable_list) <= 10 or len(unique_variable_list) < 0.5 * object_count:
                valid_property_index_list.append(idx)
        # print("valid_property_index_list:", valid_property_index_list)
        if len(valid_property_index_list) == 0:
            valid_property_index_list = list(range(len(variablename_list)))
        return valid_property_index_list

    def get_variablename_list(self):
        return self.unpack_variablename_str(self.propertyname_str)

    def pack_variablename_str(self, variablename_list=None):
        if variablename_list is None:
            variablename_list = self.variablename_list
        self.propertyname_str = VARIABLE_SEPARATOR.join(variablename_list)
        return self.propertyname_str

    def unpack_variablename_str(self, propertyname_str=""):
        if propertyname_str == "" and self.propertyname_str != "":
            propertyname_str = self.propertyname_str

        self.variablename_list = []
        if propertyname_str is None or propertyname_str == "":
            return []

        self.variablename_list = list(propertyname_str.split(VARIABLE_SEPARATOR))
        return self.variablename_list

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

    def unpack_wireframe(self, wireframe=""):
        if wireframe == "" and self.wireframe != "":
            wireframe = self.wireframe

        self.edge_list = []

        if wireframe is None or wireframe == "":
            return []

        # print wireframe
        for edge in wireframe.split(WIREFRAME_SEPARATOR):
            has_edge = True
            if edge != "":
                # print edge
                verts = edge.split(EDGE_SEPARATOR)
                int_edge = []
                for v in verts:
                    try:
                        v = int(v)
                    except (ValueError, TypeError) as e:
                        has_edge = False
                        logger.warning(f"Invalid landmark number '{v}' in wireframe edge '{edge}': {e}")
                    int_edge.append(v)

                if has_edge:
                    if len(int_edge) != 2:
                        pass  # print "Invalid edge in wireframe:", edge
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
            # print points
            new_polygons.append("-".join([str(x) for x in polygon]))
        self.polygons = ",".join(new_polygons)
        return self.polygons

    def unpack_polygons(self, polygons=""):
        if polygons == "" and self.polygons != "":
            polygons = self.polygons

        self.polygon_list = []
        if polygons is None or polygons == "":
            return []

        for polygon in polygons.split(","):
            if polygon != "":
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
        # print self.baseline
        return self.baseline

    def unpack_baseline(self, baseline=""):
        if baseline == "" and self.baseline != "":
            baseline = self.baseline

        self.baseline_point_list = []
        if self.baseline is None or self.baseline == "":
            return []

        self.baseline_point_list = [(int(x)) for x in self.baseline.split(",")]
        return self.baseline_point_list

    def get_baseline_points(self):
        return self.baseline_point_list

    def add_object(self, object_name, object_desc=None, pixels_per_mm=None, landmark_str=None, property_str=None):
        obj = MdObject()
        obj.object_name = object_name
        obj.object_desc = object_desc
        obj.pixels_per_mm = pixels_per_mm
        obj.landmark_str = landmark_str
        obj.property_str = property_str
        obj.dataset = self
        return obj

    def add_variablename(self, propertyname):
        self.variablename_list.append(propertyname)
        self.pack_variablename_str()
        self.save()
        return propertyname

    def refresh(self):
        """Refresh dataset from database"""
        return self.get_by_id(self.id)


class MdObject(Model):
    object_name = CharField()
    object_desc = CharField(null=True)
    pixels_per_mm = DoubleField(null=True)
    landmark_str = CharField(null=True)
    dataset = ForeignKeyField(MdDataset, backref="object_list", on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)
    property_str = CharField(null=True)
    sequence = IntegerField(null=True)
    # Raw digitized curve traces (JSON). See get_curve_raw(). Nullable and
    # optional -- absent for landmark-only or imported objects.
    curve_raw_json = CharField(null=True)
    # Sparse click anchors for edge-snapped (live-wire) curves (JSON). See
    # get_curve_anchors(). Present only for snap-traced curves; the dense
    # curve_raw_json is re-derived by snapping between these on edit.
    curve_anchor_json = CharField(null=True)

    class Meta:
        database = gDatabase

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Per-instance scratch state (not DB fields). Previously class-level
        # mutable defaults shared across all instances (R01 C2). centroid_size
        # is a cache sentinel: get_centroid_size() recomputes while it is <= 0.
        self.landmark_list = []
        self.variable_list = []
        self.centroid_size = -1

    def get_curve_raw(self):
        """Raw digitized curve traces as a dict, ``{}`` when unset or unreadable.

        Keyed by curve id -> list of ``[x, y(, z)]`` points: the dense polyline a
        user traced before it was resampled to evenly-spaced semi-landmarks
        (which live in ``landmark_list`` as ordinary landmarks). Optional --
        absent for imported/legacy objects, which then cannot be re-resampled but
        still analyze fine. Never raises.
        """
        if not self.curve_raw_json:
            return {}
        try:
            raw = json.loads(self.curve_raw_json)
        except (ValueError, TypeError) as e:
            logger.warning("Ignoring unreadable curve traces for object %s: %s", self.id, e)
            return {}
        return raw if isinstance(raw, dict) else {}

    def set_curve_raw(self, raw):
        """Store raw digitized curve traces (see :meth:`get_curve_raw`)."""
        self.curve_raw_json = json.dumps(raw) if raw else None

    def get_curve_anchors(self):
        """Sparse click anchors per snap-traced curve, ``{}`` when unset/unreadable.

        Keyed by curve id -> list of ``[x, y(, z)]`` -- the points the user
        actually clicked while edge-snapping. The dense trace in
        ``curve_raw_json`` is the live-wire path between them; editing an anchor
        re-snaps to rebuild it. Absent for hand-traced or imported curves, whose
        raw points are themselves the editable points. Never raises.
        """
        if not self.curve_anchor_json:
            return {}
        try:
            anchors = json.loads(self.curve_anchor_json)
        except (ValueError, TypeError) as e:
            logger.warning("Ignoring unreadable curve anchors for object %s: %s", self.id, e)
            return {}
        return anchors if isinstance(anchors, dict) else {}

    def set_curve_anchors(self, anchors):
        """Store sparse curve click anchors (see :meth:`get_curve_anchors`)."""
        self.curve_anchor_json = json.dumps(anchors) if anchors else None

    def copy_object(self, new_dataset):
        new_object = MdObject()
        new_object.object_name = self.object_name
        new_object.object_desc = self.object_desc
        new_object.pixels_per_mm = self.pixels_per_mm
        new_object.landmark_str = self.landmark_str
        new_object.dataset = new_dataset
        new_object.property_str = self.property_str
        new_object.curve_raw_json = self.curve_raw_json
        new_object.curve_anchor_json = self.curve_anchor_json
        # new_object.save()
        return new_object

    def get_name(self):
        if self.object_name is None or self.object_name == "":
            return str(self.id)
        return self.object_name

    def __str__(self):
        return self.object_name or ""

    def __repr__(self):
        return self.object_name

    def count_landmarks(self, exclude_missing=True):
        """Count landmarks.

        Note:
            This counts *recorded* landmarks by default, which is what the object
            table shows the user. It is the wrong measure for landmark-count
            consistency — use :func:`find_landmark_count_mismatch`, which counts
            positions.

        Args:
            exclude_missing: If True, exclude landmarks with None values (default: True)

        Returns:
            int: Number of landmarks (excluding missing if exclude_missing=True)
        """
        if self.landmark_str is None or self.landmark_str == "":
            return 0

        if not exclude_missing:
            # Simple count: just count lines
            return len(self.landmark_str.strip().split(LINE_SEPARATOR))

        # Unpack landmarks to check for missing values
        self.unpack_landmark()

        # Count only landmarks that are not missing
        count = 0
        for lm in self.landmark_list:
            # Check if landmark has valid coordinates
            if lm[0] is not None and lm[1] is not None:
                count += 1

        return count

    # def get_image_file_path(self):

    def add_image(self, file_name):
        img = MdImage()
        img.object = self
        img.add_file(file_name)
        return img

    def update_image(self, file_name):
        # print("update image:", file_name)
        img = self.get_image()
        if img is None:
            img = MdImage()
            # img.object = self
        else:
            # Files live at <storage>/<ds.id>/<obj.id>.<ext>: a replacement
            # with a different extension would not overwrite them, leaving the
            # old working copy and its originals/ archive orphaned on disk.
            for old_path in (img.get_file_path(), img.get_original_file_path()):
                try:
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except OSError as e:
                    logger.warning(f"Could not remove replaced image file {old_path}: {e}")
            img.delete_instance()
            img = MdImage()
        img.object = self
        img.add_file(file_name)
        # print("update image:", img, img2)
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
        # Fetch any linked media once. Previously this issued up to four queries
        # (has_image/has_threed_model COUNTs + get_image/get_threed_model indexed
        # fetches) before the save and four more after it.
        media = self.image.first() or self.threed_model.first()
        source_path = media.get_file_path() if media is not None else None

        if media is None:
            # No image or 3D file to relocate (e.g. a landmark-only object).
            self.dataset = dataset
            self.save()
            return

        # Reassign the dataset in memory (NOT yet persisted) so get_file_path()
        # resolves the new destination, then move the file *before* saving. If the
        # move fails, save() is never reached and the DB still points at the old
        # dataset -- the media stays consistent with the row instead of being
        # orphaned. get_file_path() resolves via media.object.dataset, so re-attach
        # this object first.
        self.dataset = dataset
        media.object = self
        target_path = media.get_file_path()

        if source_path and os.path.exists(source_path):
            if not os.path.exists(os.path.dirname(target_path)):
                os.makedirs(os.path.dirname(target_path))

            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(source_path, target_path)

        self.save()

    def pack_landmark(self):
        # error check - modified to handle None values as "Missing"
        landmark_strs = []
        for lm in self.landmark_list:
            coords = []
            for i in range(self.dataset.dimension):
                if i < len(lm) and lm[i] is not None:
                    coords.append(str(lm[i]))
                else:
                    coords.append("Missing")  # Store as "Missing" text
            landmark_strs.append(LANDMARK_SEPARATOR.join(coords))
        self.landmark_str = LINE_SEPARATOR.join(landmark_strs)

    def unpack_landmark(self):
        """Parse ``landmark_str`` into ``landmark_list``, blanks included.

        A field that is empty or non-numeric ("Missing", "NA", …) becomes
        ``None``. Blank fields delimited by tab/comma **keep their position**:
        clearing the Y cell of a landmark yields ``[x, None]``, not a short
        ``[x]``. Callers index ``lm[0]``/``lm[1]`` unconditionally, so a short
        row raises ``IndexError`` and takes the whole dataset's analysis down
        (``has_missing_landmarks``, ``procrustes_superimposition``,
        ``count_landmarks``). Runs of whitespace are padding, not position, so
        the blanks they produce are still dropped.
        """
        self.landmark_list = []
        # print "[", self.landmark_str,"]"
        if self.landmark_str is None or self.landmark_str == "":
            return self.landmark_list
        lm_list = self.landmark_str.split(LINE_SEPARATOR)
        for lm in lm_list:
            if lm != "":
                # Try to detect the separator used
                # Priority: tab > comma > multiple spaces > single space
                positional = True
                if "\t" in lm:
                    separator = "\t"
                elif "," in lm:
                    separator = ","
                elif "  " in lm:  # Multiple spaces
                    # Split by multiple spaces and filter empty strings
                    coords = [x for x in lm.split() if x]
                    self.landmark_list.append([float(x) if self.is_float(x) else None for x in coords])
                    continue
                elif " " in lm:
                    separator = " "
                    positional = False
                else:
                    # Single value or unknown format
                    separator = LANDMARK_SEPARATOR

                coords = [x.strip() for x in lm.split(separator)]
                if not positional:
                    # Space-separated: an empty field is just extra spacing.
                    coords = [x for x in coords if x]
                self.landmark_list.append([float(x) if self.is_float(x) else None for x in coords])
        self._normalize_landmark_widths()
        return self.landmark_list

    def _normalize_landmark_widths(self):
        """Give every landmark row one slot per dimension, padding with ``None``.

        Guards the ``lm[0]``/``lm[1]``/``lm[2]`` indexing that the rest of the
        codebase does unconditionally. Only *trailing* ``None``s are trimmed, so
        a row carrying more real numbers than the dataset's dimension keeps them
        rather than silently losing data.
        """
        if not self.landmark_list:
            return

        width = None
        try:
            if self.dataset is not None:
                width = self.dataset.dimension
        except Exception:
            # Unsaved/detached object: fall back to the widest row present.
            width = None
        if not width:
            width = max(len(lm) for lm in self.landmark_list)
        # Every landmark needs at least X and Y.
        width = max(width, 2)

        for lm in self.landmark_list:
            if len(lm) < width:
                lm.extend([None] * (width - len(lm)))
            while len(lm) > width and lm[-1] is None:
                lm.pop()

    def is_float(self, s):
        # Check for "Missing" text specifically
        if s == "Missing" or s == "missing" or s == "":
            return False
        try:
            float(s)
            return True
        except ValueError:
            return False

    def get_landmark_list(self):
        return self.unpack_landmark()

    def pack_variable(self, variable_list=None):
        if variable_list is None:
            variable_list = self.variable_list
        self.property_str = VARIABLE_SEPARATOR.join(variable_list)

    def unpack_variable(self):
        self.variable_list = []
        if self.property_str is None or self.property_str == "":
            return []
        self.variable_list = list(self.property_str.split(VARIABLE_SEPARATOR))
        return self.variable_list

    def get_variable_list(self):
        return self.unpack_variable()

    def get_centroid_size(self, refresh=False):
        # if len(self.landmark_list) == 0 and self.landmark_str != "":
        #    self.unpack_landmark()

        if len(self.landmark_list) == 0:
            if self.landmark_str is not None and self.landmark_str != "":
                self.unpack_landmark()
            if len(self.landmark_list) == 0:
                return -1
        elif len(self.landmark_list) == 1:
            return 1
        if (self.centroid_size > 0) and (not refresh):
            return self.centroid_size

        centroid = self.get_centroid_coord()
        # print "centroid:", centroid.xcoord, centroid.ycoord, centroid.zcoord
        sum_of_x_squared = 0
        sum_of_y_squared = 0
        sum_of_z_squared = 0
        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        valid_lm_count = 0
        for lm in self.landmark_list:
            # Skip landmarks with None values
            if lm[0] is None or lm[1] is None:
                continue
            valid_lm_count += 1
            sum_of_x_squared += (lm[0] - centroid[0]) ** 2
            sum_of_y_squared += (lm[1] - centroid[1]) ** 2
            if len(lm) == 3 and lm[2] is not None:
                sum_of_z_squared += (lm[2] - centroid[2]) ** 2
            sum_of_x += lm[0] - centroid[0]
            sum_of_y += lm[1] - centroid[1]
            if len(lm) == 3 and lm[2] is not None:
                sum_of_z += lm[2] - centroid[2]

        if valid_lm_count == 0:
            return 0

        centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared
        # centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared \
        #              - sum_of_x * sum_of_x / lm_count \
        #              - sum_of_y * sum_of_y / lm_count \
        #              - sum_of_z * sum_of_z / lm_count
        # print centroid_size
        try:
            if centroid_size < 0:
                logger.warning(f"Negative centroid size value: {centroid_size}")
                centroid_size = 0
            centroid_size = math.sqrt(centroid_size)
        except (ValueError, OverflowError) as e:
            logger.error(f"Math error calculating centroid size: {e}")
            centroid_size = 0

        self.centroid_size = centroid_size
        if self.pixels_per_mm is not None and self.pixels_per_mm != 0:
            try:
                centroid_size = centroid_size / self.pixels_per_mm
            except ZeroDivisionError:
                logger.error("Division by zero: pixels_per_mm is 0")
                centroid_size = 0
        # centroid_size = float( int(  * 100 ) ) / 100
        return centroid_size

    def get_centroid_coord(self):
        c = [0, 0, 0]

        # if len(self.landmark_list) == 0 and self.landmark_str != "":
        #    self.unpack_landmark()

        if len(self.landmark_list) == 0:
            return c

        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        count_x = 0
        count_y = 0
        count_z = 0
        lm_dim = 2
        for lm in self.landmark_list:
            # Skip None values when calculating centroid
            if lm[0] is not None:
                sum_of_x += lm[0]
                count_x += 1
            if lm[1] is not None:
                sum_of_y += lm[1]
                count_y += 1
            if len(lm) == 3:
                lm_dim = 3
                if lm[2] is not None:
                    sum_of_z += lm[2]
                    count_z += 1

        # Calculate average only for non-None values
        if count_x > 0:
            c[0] = sum_of_x / count_x
        if count_y > 0:
            c[1] = sum_of_y / count_y
        if lm_dim == 3 and count_z > 0:
            c[2] = sum_of_z / count_z
        return c

    def refresh(self):
        """Refresh object from database"""
        return self.get_by_id(self.id)


# Attached images whose longer side exceeds this are stored as a downscaled
# working copy (the pristine original is archived under originals/ next to it).
# Landmarks are digitized on the working copy, so it must never be regenerated
# with different parameters once landmarks exist. 2560 keeps fit-to-window and
# moderate zoom sharp on typical displays while cutting a 24 MP photo's decode
# cost and memory roughly 5x.
IMAGE_MAX_DIM = 2560
IMAGE_JPEG_QUALITY = 90


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
    object = ForeignKeyField(MdObject, backref="image", on_delete="CASCADE")

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

        # The working copy above is already downscaled (if the original was
        # oversized), so carry the archived pristine original along with it.
        source_original = self.get_original_file_path()
        if os.path.exists(source_original):
            target_original = new_image.get_original_file_path()
            os.makedirs(os.path.dirname(target_original), exist_ok=True)
            shutil.copyfile(source_original, target_original)
        return new_image

    def add_file(self, file_name, base_path=mu.DEFAULT_STORAGE_DIRECTORY):
        # print("add file:", file_name)
        try:
            self.load_file_info(file_name)
            new_filepath = self.get_file_path(base_path)

            # Create directory if it doesn't exist
            try:
                if not os.path.exists(os.path.dirname(new_filepath)):
                    os.makedirs(os.path.dirname(new_filepath))
            except OSError as e:
                logger.error(f"Failed to create directory for {new_filepath}: {e}")
                raise ValueError(f"Cannot create directory for file storage: {e}") from e

            if self._try_downscale(file_name, new_filepath):
                # Working copy is downscaled: archive the pristine original
                # alongside it so nothing is lost.
                original_filepath = self.get_original_file_path(base_path)
                try:
                    os.makedirs(os.path.dirname(original_filepath), exist_ok=True)
                    shutil.copyfile(file_name, original_filepath)
                except (OSError, shutil.Error) as e:
                    logger.error(f"Failed to archive original {file_name} to {original_filepath}: {e}")
                    raise ValueError(f"Cannot archive original file: {e}") from e
            else:
                # Small enough (or not downscalable): store verbatim
                try:
                    shutil.copyfile(file_name, new_filepath)
                except (OSError, shutil.Error) as e:
                    logger.error(f"Failed to copy file from {file_name} to {new_filepath}: {e}")
                    raise ValueError(f"Cannot copy file: {e}") from e

        except Exception as e:
            logger.error(f"Failed to add file {file_name}: {e}")
            raise

        return self

    def _try_downscale(self, source_path, target_path):
        """Write a downscaled working copy of ``source_path`` to ``target_path``.

        Returns True only when the source is oversized (longer side above
        ``IMAGE_MAX_DIM``) and the downscaled copy was written successfully.
        Returns False when no downscale is needed OR on any failure, so the
        caller falls back to copying the original verbatim — an attach must
        never fail or lose data because downscaling did.
        """
        try:
            with Image.open(source_path) as img:
                if max(img.size) <= IMAGE_MAX_DIM:
                    return False
                exif = img.info.get("exif")
                img.thumbnail((IMAGE_MAX_DIM, IMAGE_MAX_DIM), Image.LANCZOS)
                save_kwargs = {}
                if target_path.split(".")[-1].lower() in ("jpg", "jpeg"):
                    if img.mode not in ("RGB", "L", "CMYK"):
                        img = img.convert("RGB")
                    save_kwargs["quality"] = IMAGE_JPEG_QUALITY
                    save_kwargs["optimize"] = True
                    if exif:
                        save_kwargs["exif"] = exif
                img.save(target_path, **save_kwargs)
                logger.info(f"Stored downscaled working copy {img.size} of {source_path}")
                return True
        except Exception as e:
            logger.warning(f"Downscale of {source_path} failed, storing original verbatim: {e}")
            return False

    def get_file_path(self, base_path=mu.DEFAULT_STORAGE_DIRECTORY):
        return os.path.join(
            base_path, str(self.object.dataset.id), str(self.object.id) + "." + self.original_path.split(".")[-1]
        )

    def get_original_file_path(self, base_path=mu.DEFAULT_STORAGE_DIRECTORY):
        """Path of the archived pristine original for this image.

        Only oversized attachments are archived (small ones are stored verbatim
        as the working copy), so this path may not exist.
        """
        return os.path.join(
            base_path,
            str(self.object.dataset.id),
            "originals",
            str(self.object.id) + "." + self.original_path.split(".")[-1],
        )

    def has_archived_original(self, base_path=mu.DEFAULT_STORAGE_DIRECTORY):
        return os.path.exists(self.get_original_file_path(base_path))

    class Meta:
        database = gDatabase

    def load_file_info(self, fullpath):
        file_info = {}

        """ file stat """
        stat_result = os.stat(fullpath)
        file_info["mtime"] = stat_result.st_mtime
        file_info["ctime"] = stat_result.st_ctime

        if os.path.isdir(fullpath):
            file_info["type"] = "dir"
        else:
            file_info["type"] = "file"

        if os.path.isdir(fullpath):
            return file_info

        file_info["size"] = stat_result.st_size

        """ md5 hash value """
        file_info["md5hash"], image_data = self.get_md5hash_info(fullpath)

        """ exif info """
        exif_info = self.get_exif_info(fullpath, image_data)
        file_info["exifdatetime"] = exif_info["datetime"]
        file_info["latitude"] = exif_info["latitude"]
        file_info["longitude"] = exif_info["longitude"]
        file_info["map_datum"] = exif_info["map_datum"]

        self.original_path = fullpath
        self.original_filename = Path(fullpath).name
        self.md5hash = file_info["md5hash"]
        self.size = file_info["size"]
        self.exifdatetime = file_info["exifdatetime"]
        self.file_created = file_info["ctime"]
        self.file_modified = file_info["mtime"]

    def get_md5hash_info(self, filepath):
        try:
            hasher = hashlib.md5()
            with open(filepath, "rb") as afile:
                image_data = afile.read()
                hasher.update(image_data)
            md5hash = hasher.hexdigest()
            return md5hash, image_data
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error(f"Cannot read file for MD5 hash {filepath}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calculating MD5 for {filepath}: {e}")
            raise ValueError(f"Cannot calculate MD5 hash for {filepath}: {e}") from e

    def get_exif_info(self, fullpath, image_data=None):
        image_info = {"date": "", "time": "", "latitude": "", "longitude": "", "map_datum": ""}
        img = None

        try:
            if image_data:
                # img = Image.open()
                img = Image.open(io.BytesIO(image_data))
            else:
                img = Image.open(fullpath)
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Cannot open image file {fullpath}: {e}")
            raise
        except Exception as e:
            logger.warning(f"Cannot process image {fullpath}: {e}")
            # Return empty info if image cannot be processed
            return {"datetime": "", "latitude": "", "longitude": "", "map_datum": ""}
        ret = {}
        # print(filename)
        try:
            info = img._getexif()
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                ret[decoded] = value
                # print("exif:", decoded, value)
            try:
                if ret["GPSInfo"] is not None:
                    gps_info = ret["GPSInfo"]
                    # print("gps info:", gps_info)
                degree_symbol = "°"
                minute_symbol = "'"
                longitude = str(int(gps_info[4][0])) + degree_symbol + str(gps_info[4][1]) + minute_symbol + gps_info[3]
                latitude = str(int(gps_info[2][0])) + degree_symbol + str(gps_info[2][1]) + minute_symbol + gps_info[1]
                map_datum = gps_info[18]
                image_info["latitude"] = latitude
                image_info["longitude"] = longitude
                image_info["map_datum"] = map_datum

            except KeyError:
                pass
                # print( "GPS Data Don't Exist for", Path(filename).name)

            try:
                if ret["DateTimeOriginal"] is not None:
                    exif_timestamp = ret["DateTimeOriginal"]
                    # print("original:", exifTimestamp)
                    image_info["date"], image_info["time"] = exif_timestamp.split()
            except KeyError:
                pass
                # print( "DateTimeOriginal Don't Exist")
            try:
                if ret["DateTimeDigitized"] is not None:
                    exif_timestamp = ret["DateTimeDigitized"]
                    image_info["date"], image_info["time"] = exif_timestamp.split()
            except KeyError:
                pass
                # print( "DateTimeDigitized Don't Exist")
            try:
                if ret["DateTime"] is not None:
                    exif_timestamp = ret["DateTime"]
                    image_info["date"], image_info["time"] = exif_timestamp.split()
            except KeyError:
                pass
                # print( "DateTime Don't Exist")

        except Exception:
            pass
            # print(e)

        if image_info["date"] == "":
            str1 = time.ctime(os.path.getmtime(fullpath))
            datetime_object = datetime.datetime.strptime(str1, "%a %b %d %H:%M:%S %Y")
            image_info["date"] = datetime_object.strftime("%Y-%m-%d")
            image_info["time"] = datetime_object.strftime("%H:%M:%S")
        else:
            image_info["date"] = "-".join(image_info["date"].split(":"))
        image_info["datetime"] = image_info["date"] + " " + image_info["time"]
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
    object = ForeignKeyField(MdObject, backref="threed_model", on_delete="CASCADE")

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
        # Mirror MdImage.add_file: log + raise typed errors so a failure surfaces
        # instead of leaving a 3D-model row without its file (data loss).
        try:
            file_name = mu.process_3d_file(file_name)
            self.load_file_info(file_name)
            new_filepath = self.get_file_path()

            try:
                if not os.path.exists(os.path.dirname(new_filepath)):
                    os.makedirs(os.path.dirname(new_filepath))
            except OSError as e:
                logger.error(f"Failed to create directory for {new_filepath}: {e}")
                raise ValueError(f"Cannot create directory for file storage: {e}") from e

            try:
                shutil.copyfile(file_name, new_filepath)
            except (OSError, shutil.Error) as e:
                logger.error(f"Failed to copy file from {file_name} to {new_filepath}: {e}")
                raise ValueError(f"Cannot copy file: {e}") from e

        except Exception as e:
            logger.error(f"Failed to add 3D model file {file_name}: {e}")
            raise

        return self

    def get_file_path(self, base_path=mu.DEFAULT_STORAGE_DIRECTORY):
        return os.path.join(
            base_path, str(self.object.dataset.id), str(self.object.id) + "." + self.original_path.split(".")[-1]
        )

    def load_file_info(self, fullpath):
        file_info = {}

        """ file stat """
        stat_result = os.stat(fullpath)
        file_info["mtime"] = stat_result.st_mtime
        file_info["ctime"] = stat_result.st_ctime
        file_info["type"] = "file"
        file_info["size"] = stat_result.st_size

        """ md5 hash value """
        file_info["md5hash"], image_data = self.get_md5hash_info(fullpath)

        self.original_path = fullpath
        self.original_filename = Path(fullpath).name
        self.md5hash = file_info["md5hash"]
        self.size = file_info["size"]
        self.file_created = file_info["ctime"]
        self.file_modified = file_info["mtime"]

    def get_md5hash_info(self, filepath):
        try:
            hasher = hashlib.md5()
            with open(filepath, "rb") as afile:
                image_data = afile.read()
                hasher.update(image_data)
            md5hash = hasher.hexdigest()
            return md5hash, image_data
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error(f"Cannot read file for MD5 hash {filepath}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calculating MD5 for {filepath}: {e}")
            raise ValueError(f"Cannot calculate MD5 hash for {filepath}: {e}") from e


class MdObjectOps:
    def __init__(self, mdobject):
        self.id = mdobject.id
        self.object_name = mdobject.object_name
        self.object_desc = mdobject.object_desc
        self.pixel_per_mm = mdobject.pixels_per_mm
        self.sequence = mdobject.sequence
        # self.dataset_id = mdobject.dataset
        # self.scale = mdobject.scale
        self.landmark_str = mdobject.landmark_str
        self.property_str = mdobject.property_str
        if self.landmark_str is not None and self.landmark_str != "":
            mdobject.unpack_landmark()
        self.landmark_list = copy.deepcopy(mdobject.landmark_list)
        # if mdobject.polygons is not None and mdobject.polygons != "":
        #    mdobject.unpack_polygons()
        # self.polygon_list = copy.deepcopy(mdobject.polygon_list)
        # print("landmark list:", self.landmark_list)
        # for lm in mdobject.landmark_list:
        #    self.landmark_list.append(lm)
        self.variable_list = []
        if self.property_str is not None and self.property_str != "":
            mdobject.unpack_variable()
        self.variable_list = copy.deepcopy(mdobject.variable_list)

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
        # self.apply_scale()

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

        # if len(self.landmark_list) == 0 and self.landmark_str != "":
        #    self.unpack_landmark()

        if len(self.landmark_list) == 0:
            return c

        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        count_x = 0
        count_y = 0
        count_z = 0
        lm_dim = 2
        for lm in self.landmark_list:
            # Skip None values when calculating centroid
            if lm[0] is not None:
                sum_of_x += lm[0]
                count_x += 1
            if lm[1] is not None:
                sum_of_y += lm[1]
                count_y += 1
            if len(lm) == 3:
                lm_dim = 3
                if lm[2] is not None:
                    sum_of_z += lm[2]
                    count_z += 1

        # Calculate average only for non-None values
        if count_x > 0:
            c[0] = sum_of_x / count_x
        if count_y > 0:
            c[1] = sum_of_y / count_y
        if lm_dim == 3 and count_z > 0:
            c[2] = sum_of_z / count_z
        return c

    def get_centroid_size(self, refresh=False):
        # if len(self.landmark_list) == 0 and self.landmark_str != "":
        #    self.unpack_landmark()

        if len(self.landmark_list) == 0:
            return -1
        elif len(self.landmark_list) == 1:
            return 1
        if (self.centroid_size > 0) and (not refresh):
            return self.centroid_size

        centroid = self.get_centroid_coord()
        # print "centroid:", centroid.xcoord, centroid.ycoord, centroid.zcoord
        sum_of_x_squared = 0
        sum_of_y_squared = 0
        sum_of_z_squared = 0
        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        valid_lm_count = 0
        for lm in self.landmark_list:
            # Skip landmarks with None values
            if lm[0] is None or lm[1] is None:
                continue
            valid_lm_count += 1
            sum_of_x_squared += (lm[0] - centroid[0]) ** 2
            sum_of_y_squared += (lm[1] - centroid[1]) ** 2
            if len(lm) == 3 and lm[2] is not None:
                sum_of_z_squared += (lm[2] - centroid[2]) ** 2
            sum_of_x += lm[0] - centroid[0]
            sum_of_y += lm[1] - centroid[1]
            if len(lm) == 3 and lm[2] is not None:
                sum_of_z += lm[2] - centroid[2]

        if valid_lm_count == 0:
            return 0

        centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared
        # centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared \
        #              - sum_of_x * sum_of_x / lm_count \
        #              - sum_of_y * sum_of_y / lm_count \
        #              - sum_of_z * sum_of_z / lm_count
        # print centroid_size
        centroid_size = math.sqrt(centroid_size)
        self.centroid_size = centroid_size
        # centroid_size = float( int(  * 100 ) ) / 100
        return centroid_size

    def move(self, x, y, z=0):
        new_landmark_list = []
        # print("move 1:", id(self.landmark_list), self.landmark_list[0])
        for lm in self.landmark_list:
            new_lm = lm.copy()  # Create a copy to avoid modifying original
            # Only move non-None coordinates
            if new_lm[0] is not None:
                new_lm[0] = new_lm[0] + x
            if new_lm[1] is not None:
                new_lm[1] = new_lm[1] + y
            if len(new_lm) == 3 and new_lm[2] is not None:
                new_lm[2] = new_lm[2] + z
            new_landmark_list.append(new_lm)
        self.landmark_list = new_landmark_list
        # print("move 2:", id(self.landmark_list), self.landmark_list[0])

    def move_to_center(self):
        centroid = self.get_centroid_coord()
        # print("centroid:", centroid[0], centroid[1], centroid[2])
        self.move(-1 * centroid[0], -1 * centroid[1], -1 * centroid[2])

    def rescale(self, factor):
        # print("rescale:", factor, self.landmark_list[:5])
        new_landmark_list = []
        for lm in self.landmark_list:
            # Scale each coordinate individually, preserving None values
            new_lm = []
            for coord in lm:
                if coord is not None:
                    new_lm.append(coord * factor)
                else:
                    new_lm.append(None)
            new_landmark_list.append(new_lm)
        self.landmark_list = new_landmark_list
        # print("rescale:", factor, self.objname, self.landmark_list[:5])

    def rescale_to_unitsize(self):
        centroid_size = self.get_centroid_size(True)

        if not centroid_size:
            # A single coincident-point (or empty) shape has zero centroid size;
            # scaling by 1/0 would raise ZeroDivisionError. Leave it unscaled.
            logger.warning("rescale_to_unitsize: centroid size is 0; skipping rescale")
            return
        self.rescale(1 / centroid_size)

    def apply_rotation_matrix(self, rotation_matrix):
        # print("obj_ops apply rotation", rotation_matrix)
        if len(self.landmark_list) > 0:
            new_landmark_list = []
            for lm in self.landmark_list:
                # Check if all coordinates are valid (not None)
                if all(coord is not None for coord in lm):
                    # Prepare the landmark array based on dimension
                    if len(lm) == 2:
                        lm_array = np.array([lm[0], lm[1], 0, 1])  # 2D point with z=0 and homogeneous
                    else:  # 3D
                        lm_array = np.array(lm[:3] + [1])  # Add homogeneous coordinate

                    # Apply rotation
                    rotated = np.dot(rotation_matrix.T, lm_array)

                    # Return the appropriate dimension
                    if len(lm) == 2:
                        new_landmark_list.append([rotated[0], rotated[1]])
                    else:
                        new_landmark_list.append(rotated[:3].tolist())
                else:
                    # Keep None values as is
                    new_landmark_list.append(lm)
            self.landmark_list = new_landmark_list

    def rotate_2d(self, theta):
        self.rotate_3d(theta, "Z")
        return

    def rotate_3d(self, theta, axis):
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        r_mx = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if axis == "Z":
            r_mx[0][0] = cos_theta
            r_mx[0][1] = sin_theta
            r_mx[1][0] = -1 * sin_theta
            r_mx[1][1] = cos_theta
        elif axis == "Y":
            r_mx[0][0] = cos_theta
            r_mx[0][2] = sin_theta
            r_mx[2][0] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        elif axis == "X":
            r_mx[1][1] = cos_theta
            r_mx[1][2] = sin_theta
            r_mx[2][1] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        # print "rotation matrix", r_mx

        for i, lm in enumerate(self.landmark_list):
            coords = [0, 0, 0]
            for j, value in enumerate(lm):
                coords[j] = value
            x_rotated = coords[0] * r_mx[0][0] + coords[1] * r_mx[1][0] + coords[2] * r_mx[2][0]
            y_rotated = coords[0] * r_mx[0][1] + coords[1] * r_mx[1][1] + coords[2] * r_mx[2][1]
            z_rotated = coords[0] * r_mx[0][2] + coords[1] * r_mx[1][2] + coords[2] * r_mx[2][2]
            self.landmark_list[i] = [x_rotated, y_rotated, z_rotated]

    def trim_decimal(self, dec=4):
        factor = math.pow(10, dec)

        for lm in self.landmark_list:
            lm = [float(round(x * factor)) / factor for x in lm]

    def print_landmarks(self, text=""):
        print("[", text, "] [", str(self.get_centroid_size()), "]")
        # lm= self.landmarks[0]
        print(self.landmark_list[:5])
        # for lm in self.landmark_list:
        #    print(lm)
        # break
        # lm= self.landmarks[1]
        # print lm.xcoord, ", ", lm.ycoord, ", ", lm.zcoord

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
        # print("baseline:",baseline)
        # print(self.landmark_list)
        # print(self.landmark_list[point2 - 1], self.landmark_list[point1 - 1])

        curr_vector1 = np.array(self.landmark_list[point2 - 1]) - np.array(self.landmark_list[point1 - 1])

        if len(curr_vector1) == 2:
            to_vector1 = np.array([1, 0])
        else:
            to_vector1 = np.array([1, 0, 0])

        # print("curr_vector1:", curr_vector1)
        # print("to_vector1:", to_vector1)
        v1_norm = curr_vector1 / np.linalg.norm(curr_vector1)
        to_norm = to_vector1 / np.linalg.norm(to_vector1)

        if np.allclose(v1_norm, to_norm):
            if len(curr_vector1) == 2:
                return
            # do nothing
            pass
        else:
            if len(curr_vector1) == 2:
                # print("2D rotation", curr_vector1, to_vector1)

                curr_vector1 = curr_vector1 / np.linalg.norm(curr_vector1)
                to_vector1 = to_vector1 / np.linalg.norm(to_vector1)

                cos_theta = np.dot(curr_vector1, to_vector1)
                sin_theta = np.sqrt(1 - cos_theta**2)

                # print
                # cos_theta = np.dot(curr_vector1, to_vector1) / (np.linalg.norm(curr_vector1) * np.linalg.norm(to_vector1))
                # sin_theta = np.sqrt(1 - cos_theta ** 2)
                # print("cos_theta:", cos_theta, "sin_theta:", sin_theta)
                # calculate theta
                theta = math.acos(cos_theta)
                if sin_theta < 0:
                    theta = -1 * theta
                # print("theta:", theta)

                rotation_matrix = np.array([[cos_theta, -1 * sin_theta], [sin_theta, cos_theta]])

                # rotation_matrix = [ [ cos_theta, -1 * sin_theta], [sin_theta, cos_theta] ]
                # apply rotation matrix to landmarks
                # print("landmarks before rotation", self.landmark_list)
                # print("rotation matrix", rotation_matrix)

                rotated_landmarks = []
                for _i, lm in enumerate(self.landmark_list):
                    coords = np.array(lm)
                    rotated_coords = np.dot(rotation_matrix, coords)
                    rotated_landmarks.append(rotated_coords.tolist())

                    # coords = [0,0]
                    # for j in range(len(lm)):
                    #    coords[j] = lm[j]
                    # x_rotated = coords[0] * rotation_matrix[0][0] + coords[1] * rotation_matrix[1][0]
                    # y_rotated = coords[0] * rotation_matrix[0][1] + coords[1] * rotation_matrix[1][1]
                    # self.landmark_list[i] = [ x_rotated, y_rotated ]
                self.landmark_list = rotated_landmarks
                # print("landmarks after rotation", self.landmark_list)
                return
            else:
                # calculate cosine and sine of rotation angle
                cos_theta = np.dot(curr_vector1, to_vector1) / (
                    np.linalg.norm(curr_vector1) * np.linalg.norm(to_vector1)
                )
                sin_theta = np.sqrt(1 - cos_theta**2)

                # calculate rotation axis
                rotation_axis = np.cross(curr_vector1, to_vector1)
                rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)

                # calculate rotation matrix to align vector1 to x-axis - Rodrigues' rotation formula
                # https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
                r_mx = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
                r_mx[0][0] = cos_theta + rotation_axis[0] * rotation_axis[0] * (1 - cos_theta)
                r_mx[0][1] = rotation_axis[0] * rotation_axis[1] * (1 - cos_theta) - rotation_axis[2] * sin_theta
                r_mx[0][2] = rotation_axis[0] * rotation_axis[2] * (1 - cos_theta) + rotation_axis[1] * sin_theta
                r_mx[1][0] = rotation_axis[1] * rotation_axis[0] * (1 - cos_theta) + rotation_axis[2] * sin_theta
                r_mx[1][1] = cos_theta + rotation_axis[1] * rotation_axis[1] * (1 - cos_theta)
                r_mx[1][2] = rotation_axis[1] * rotation_axis[2] * (1 - cos_theta) - rotation_axis[0] * sin_theta
                r_mx[2][0] = rotation_axis[2] * rotation_axis[0] * (1 - cos_theta) - rotation_axis[1] * sin_theta
                r_mx[2][1] = rotation_axis[2] * rotation_axis[1] * (1 - cos_theta) + rotation_axis[0] * sin_theta
                r_mx[2][2] = cos_theta + rotation_axis[2] * rotation_axis[2] * (1 - cos_theta)

                # r_mx = [[1, 0, 0,0], [0, 1, 0,0], [0, 0, 1,0],[0,0,0,1]]
                # r_mx[1][1] = cos_theta
                # r_mx[1][2] = sin_theta
                # r_mx[2][1] = -1 * sin_theta
                # r_mx[2][2] = cos_theta

                # print("rotation matrix:", r_mx)

                # apply rotation matrix to all landmarks
                self.apply_rotation_matrix(np.array(r_mx))

                curr_vector1 = np.array(self.landmark_list[point2 - 1]) - np.array(self.landmark_list[point1 - 1])
                # print("curr_vector1 after rotation:", curr_vector1)
                # print(self.landmark_list[point2 - 1], self.landmark_list[point1 - 1])

        mid_point12 = np.array(self.landmark_list[point1 - 1]) + curr_vector1 / 2
        curr_vector2 = np.array(self.landmark_list[point3 - 1]) - np.array(mid_point12)
        # projection_vector2 = np.dot(curr_vector2, curr_vector1) / np.linalg.norm(curr_vector1) * curr_vector1
        projection_vector2 = (np.dot(curr_vector2, curr_vector1) / np.linalg.norm(curr_vector1) ** 2) * curr_vector1

        curr_vector2 = curr_vector2 - projection_vector2
        to_vector2 = np.array([0, 1, 0])
        # print("curr_vector2:", curr_vector2)
        # print("to_vector2:", to_vector2)

        v2_norm = curr_vector2 / np.linalg.norm(curr_vector2)
        to_norm = to_vector2 / np.linalg.norm(to_vector2)

        if np.allclose(v2_norm, to_norm):
            # do nothing
            pass
        else:
            # calculate cosine and sine of rotation angle
            cos_theta = np.dot(curr_vector2, to_vector2) / (np.linalg.norm(curr_vector2) * np.linalg.norm(to_vector2))
            sin_theta = np.sqrt(1 - cos_theta**2)
            # print("cos_theta:", cos_theta, "sin_theta:", sin_theta)

            # calculate rotation axis
            rotation_axis = np.cross(curr_vector2, to_vector2)
            rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
            # print("rotation axis", rotation_axis)

            # calculate rotation matrix to align vector1 to x-axis - Rodrigues' rotation formula
            # https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
            r_mx = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
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
        # print "centroid:", c.xcoord, ", ", c.ycoord, ", ", c.zcoord
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
        if point3 is not None:
            point3 = point3 - 1

        # self.print_landmarks("before any processing");

        center = [0, 0, 0]
        center[0] = (self.landmark_list[point1][0] + self.landmark_list[point2][0]) / 2
        center[1] = (self.landmark_list[point1][1] + self.landmark_list[point2][1]) / 2
        center[2] = (self.landmark_list[point1][2] + self.landmark_list[point2][2]) / 2
        self.move(-1 * center[0], -1 * center[1], -1 * center[2])

        # self.print_landmarks("translation");
        # self.scale_to_univsize()
        xdiff = self.landmark_list[point1][0] - self.landmark_list[point2][0]
        ydiff = self.landmark_list[point1][1] - self.landmark_list[point2][1]
        zdiff = self.landmark_list[point1][2] - self.landmark_list[point2][2]
        # print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff

        size = math.sqrt(xdiff * xdiff + ydiff * ydiff + zdiff * zdiff)
        # print "size: ", size
        # print "rescale: ", rescale
        if rescale < 0:
            self.rescale(1 / size)
        elif rescale > 0:
            self.rescale(1 / rescale)

        # self.print_landmarks("rescaling");

        if point3 is not None:
            xdiff = self.landmark_list[point1][0] - self.landmark_list[point2][0]
            ydiff = self.landmark_list[point1][1] - self.landmark_list[point2][1]
            zdiff = self.landmark_list[point1][2] - self.landmark_list[point2][2]
            cos_val = xdiff / math.sqrt(xdiff * xdiff + zdiff * zdiff)
            # print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
            # print "cos val: ", cos_val
            theta = math.acos(cos_val)
            # print "theta: ", theta, ", ", theta * 180/math.pi
            if zdiff < 0:
                theta = theta * -1
            self.rotate_3d(-1 * theta, "Y")

        # self.print_landmarks("rotate along xz plane");

        xdiff = self.landmark_list[point1][0] - self.landmark_list[point2][0]
        ydiff = self.landmark_list[point1][1] - self.landmark_list[point2][1]
        zdiff = self.landmark_list[point1][2] - self.landmark_list[point2][2]

        size = math.sqrt(xdiff * xdiff + ydiff * ydiff)
        cos_val = xdiff / size
        # print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
        # print "cos val: ", cos_val
        theta = math.acos(cos_val)
        # print "theta: ", theta, ", ", theta * 180/math.pi
        if ydiff < 0:
            theta = theta * -1
        self.rotate_2d(-1 * theta)

        if point3 is not None:
            xdiff = self.landmark_list[point3][0]
            ydiff = self.landmark_list[point3][1]
            zdiff = self.landmark_list[point3][2]
            size = math.sqrt(ydiff**2 + zdiff**2)
            cos_val = ydiff / size
            theta = math.acos(cos_val)
            if zdiff < 0:
                theta = theta * -1
            self.rotate_3d(-1 * theta, "X")


class MdDatasetOps:
    def __init__(self, dataset):
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
        object_list = dataset.object_list.order_by(MdObject.sequence)
        # Semi-landmark curves are stored per object as raw traces, not as
        # landmarks (merge-at-analysis model). Expand them here so analysis sees
        # each shape as fixed landmarks followed by the resampled semi-landmarks.
        curve_config = dataset.get_curve_config()
        n_dim = 3 if dataset.dimension == 3 else 2
        for mo in object_list:
            # self.object_list.append(mo.copy())
            # print(mo.id, mo.sequence)
            ops = MdObjectOps(mo)
            if curve_config:
                raw_map = mo.get_curve_raw()
                for curve in curve_config:
                    n = curve.get("n", 0)
                    raw = raw_map.get(curve.get("id"))
                    if raw and len(raw) >= 2:
                        ops.landmark_list.extend([list(p) for p in mu.resample_polyline(raw, n)])
                    else:
                        # Curve not traced on this object: keep the layout aligned
                        # with a block of missing landmarks for the imputation path.
                        ops.landmark_list.extend([[None] * n_dim for _ in range(n)])
            self.object_list.append(ops)

        if dataset.wireframe is not None and dataset.wireframe != "":
            dataset.unpack_wireframe()
        if dataset.edge_list is not None and len(dataset.edge_list) > 0:
            self.edge_list = dataset.edge_list[:]
        # print("edge list in MdDatasetOps.__init__:", dataset.wireframe, dataset.edge_list, self.edge_list)
        self.variablename_list = dataset.variablename_list
        if dataset.polygons != "":
            dataset.unpack_polygons()
        if dataset.baseline != "":
            dataset.unpack_baseline()

        self.baseline_point_list = dataset.baseline_point_list
        # print self

    def reset_pose(self):
        pass

    def set_reference_shape(self, shape):
        self.reference_shape = shape

    def rotate_gls_to_reference_shape(self, object_index):
        num_obj = len(self.object_list)
        if num_obj == 0 or num_obj - 1 < object_index:
            return

        mo = self.object_list[object_index]
        nlandmarks = len(mo.landmark_list)

        # Check if there are any None values
        has_missing = False
        for lm in mo.landmark_list:
            if any(coord is None for coord in lm[: self.dimension]):
                has_missing = True
                break

        if not has_missing:
            # Original implementation for complete data - rotate all landmarks
            target_shape = np.zeros((nlandmarks, self.dimension))
            reference_shape = np.zeros((nlandmarks, self.dimension))

            i = 0
            for lm in mo.landmark_list:
                for j in range(self.dimension):
                    target_shape[i, j] = lm[j]
                i += 1

            i = 0
            for lm in self.reference_shape.landmark_list:
                for j in range(self.dimension):
                    reference_shape[i, j] = lm[j]
                i += 1

            rotation_matrix = self.rotation_matrix(reference_shape, target_shape)
            rotated_shape = np.transpose(np.dot(rotation_matrix, np.transpose(target_shape)))

            i = 0
            for lm in mo.landmark_list:
                for j in range(self.dimension):
                    lm[j] = rotated_shape[i, j]
                i += 1
        else:
            # New implementation for missing data - use only valid landmarks
            valid_indices = []
            target_points = []
            reference_points = []

            for i in range(nlandmarks):
                obj_lm = mo.landmark_list[i]
                ref_lm = self.reference_shape.landmark_list[i] if i < len(self.reference_shape.landmark_list) else None

                if (
                    obj_lm
                    and ref_lm
                    and all(coord is not None for coord in obj_lm[: self.dimension])
                    and all(coord is not None for coord in ref_lm[: self.dimension])
                ):
                    valid_indices.append(i)
                    target_points.append(obj_lm[: self.dimension])
                    reference_points.append(ref_lm[: self.dimension])

            # Need at least 3 points for rotation in 2D, 4 in 3D
            min_points = 3 if self.dimension == 2 else 4
            if len(valid_indices) < min_points:
                return  # Not enough valid points for rotation

            # Create arrays for valid points only
            target_shape = np.array(target_points)
            reference_shape = np.array(reference_points)

            rotation_matrix = self.rotation_matrix(reference_shape, target_shape)
            rotated_shape = np.transpose(np.dot(rotation_matrix, np.transpose(target_shape)))

            # Apply rotation only to valid landmarks
            new_landmark_list = []
            valid_idx = 0
            for i in range(len(mo.landmark_list)):
                if i in valid_indices:
                    # This landmark was part of the rotation
                    lm = [0] * len(mo.landmark_list[i])
                    for j in range(self.dimension):
                        lm[j] = rotated_shape[valid_idx, j]
                    if len(mo.landmark_list[i]) > self.dimension:
                        # Preserve additional dimensions if any
                        for j in range(self.dimension, len(mo.landmark_list[i])):
                            lm[j] = mo.landmark_list[i][j]
                    new_landmark_list.append(lm)
                    valid_idx += 1
                else:
                    # This landmark has None values, keep it as is
                    new_landmark_list.append(mo.landmark_list[i])
            mo.landmark_list = new_landmark_list

    def apply_rotation_matrix(self, rotation_matrix):
        # print("obj_ops apply rotation", rotation_matrix)
        for mo in self.object_list:
            # Use the MdObjectOps apply_rotation_matrix which handles None values
            mo.apply_rotation_matrix(rotation_matrix)

    def rotation_matrix(self, ref, target):
        # assert( ref[0] == 3 )
        # assert( ref.shape == target.shape )

        correlation_matrix = np.dot(np.transpose(ref), target)
        try:
            v, s, w = np.linalg.svd(correlation_matrix)
        except np.linalg.LinAlgError as e:
            # Degenerate / non-finite landmark data (e.g. missing coords -> NaN)
            # makes the SVD fail to converge. Surface a clear cause.
            raise ValueError(
                "Cannot compute alignment rotation: landmark data is degenerate "
                f"or contains missing/invalid values ({e})"
            ) from e
        is_reflection = (np.linalg.det(v) * np.linalg.det(w)) < 0.0
        if is_reflection:
            v[-1, :] = -v[-1, :]
        rot_mx = np.dot(v, w)
        # print("rotation_matrix:",rot_mx)
        return rot_mx

    def get_average_shape(self):
        average_shape = MdObjectOps(MdObject())
        average_shape.landmark_list = []

        n_dim = 3 if self.dimension == 3 else 2
        # Landmark counts may differ between objects; pad ragged objects to the
        # maximum count seen so they can be stacked into one array.
        n_landmarks = max((len(mo.landmark_list) for mo in self.object_list), default=0)

        if n_landmarks > 0 and self.object_list:

            def _coord(lm, d):
                return float(lm[d]) if d < len(lm) and lm[d] is not None else np.nan

            # (n_objects, n_landmarks, n_dim); missing/None coords become NaN.
            stacked = np.array(
                [
                    [
                        [_coord(mo.landmark_list[i], d) for d in range(n_dim)]
                        if i < len(mo.landmark_list)
                        else [np.nan] * n_dim
                        for i in range(n_landmarks)
                    ]
                    for mo in self.object_list
                ],
                dtype=float,
            )

            # Per-coordinate mean ignoring missing values. A coordinate that is
            # missing in every object yields NaN (-> None below); suppress the
            # all-NaN-slice warning numpy raises for that case.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                means = np.nanmean(stacked, axis=0)

            average_shape.landmark_list = [[None if np.isnan(v) else float(v) for v in row] for row in means]

        if self.id:
            average_shape.dataset_id = self.id
        return average_shape

    def check_object_list(self):
        """True when every object has the same number of landmark positions."""
        mismatch = find_landmark_count_mismatch(self.object_list)
        if mismatch is None:
            return True
        obj, expected, found = mismatch
        logger.warning(
            "Inconsistent number of landmarks in '%s': expected %d, found %d",
            getattr(obj, "object_name", "?"),
            expected,
            found,
        )
        return False

    def estimate_missing_landmarks(self, obj_index, reference_shape):
        """Estimate missing landmarks for an object using the reference shape.

        The reference (usually the average shape) is fitted onto the object's
        observed landmarks before its coordinates are borrowed — see
        :func:`impute_missing_landmarks`. An object with gaps was centred and
        scaled on its observed subset only, so it does not share the mean's
        normalisation exactly, and copying coordinates straight across left the
        estimate off by that mismatch.

        Args:
            obj_index: Index of the object in object_list
            reference_shape: Reference shape (usually average shape) to use for imputation
        """
        if reference_shape is None:
            return

        obj = self.object_list[obj_index]
        obj.landmark_list = impute_missing_landmarks(obj.landmark_list, reference_shape.landmark_list, self.dimension)

    def has_missing_landmarks(self):
        """Check if any object in the dataset has missing landmarks."""
        for obj in self.object_list:
            for lm in obj.landmark_list:
                if lm[0] is None or lm[1] is None:
                    return True
                if len(lm) == 3 and lm[2] is None:
                    return True
        return False

    def procrustes_superimposition_with_imputation(self):
        """Procrustes superimposition with missing landmark imputation.

        Expectation-maximisation around the ordinary Procrustes alignment:
        align with the gaps left open, estimate them from the mean shape, then
        re-align now that every object is complete and re-estimate, until the
        estimates stop moving. Estimates are always fitted onto an object's
        genuinely observed landmarks (:func:`impute_missing_landmarks`), never
        onto an earlier estimate.

        Both halves matter, measured against ground truth on noise-free
        synthetic data (devlog 227), as error in percent of centroid size:

        * 61% — the previous version, which imputed inside the alignment loop
          *before* the first rotation, so estimates were off by the object's
          arbitrary starting orientation. Worse, a filled-in value was no longer
          ``None``, so it was never revisited (the "iterative refinement" the
          docstring claimed never happened) and entered the alignment as if it
          were observed data.
        * 13% — imputing after the alignment converges, but copying the mean's
          coordinates across directly.
        * 1.9% — fitting the mean onto the observed landmarks first. The
          remainder is the gapped object skewing the mean: it was centred and
          scaled on its observed subset while the others use whole
          configurations.
        * 0.0% — with the refinement rounds below, which re-align and
          re-estimate once the objects are complete.

        The object dialog's preview fits the mean the same way and for the same
        reason (devlog 221), only there the object sits in image coordinates
        instead of being aligned by GPA.
        """
        if not self.check_object_list():
            print("check_object_list failed")
            return False

        if not self.has_missing_landmarks():
            self._align_to_mean_shape()
            return True

        # Where the gaps are, before anything fills them in. Every refinement
        # re-opens exactly these positions so each new estimate is fitted on
        # genuinely observed landmarks and never on a previous estimate.
        gaps = [
            [idx for idx, lm in enumerate(obj.landmark_list) if any(c is None for c in lm[: self.dimension])]
            for obj in self.object_list
        ]

        average_shape = self._align_to_mean_shape()
        previous_estimates = None

        for _ in range(MAX_IMPUTATION_REFINEMENTS):
            if average_shape is None:
                break

            for obj_idx, positions in enumerate(gaps):
                landmark_list = self.object_list[obj_idx].landmark_list
                for idx in positions:
                    for d in range(min(self.dimension, len(landmark_list[idx]))):
                        landmark_list[idx][d] = None
                self.estimate_missing_landmarks(obj_idx, average_shape)

            estimates = [
                self.object_list[obj_idx].landmark_list[idx][: self.dimension]
                for obj_idx, positions in enumerate(gaps)
                for idx in positions
            ]
            if previous_estimates is not None and self._estimates_converged(previous_estimates, estimates):
                break
            previous_estimates = estimates

            # The objects are complete now, so re-normalising puts the ones that
            # had gaps on the same footing as the rest: they were centred and
            # scaled on their observed subset only, which skewed their
            # contribution to the mean and, through it, their own estimates.
            average_shape = self._align_to_mean_shape()

        return True

    def _align_to_mean_shape(self, max_iterations=100):
        """Centre, scale and iteratively rotate every object onto the mean shape.

        Returns the mean shape the objects ended up aligned to. Landmarks that
        are still missing are simply left out: the mean is a per-coordinate
        nanmean and rotation uses the landmarks an object actually has.
        """
        for mo in self.object_list:
            mo.move_to_center()
            mo.rescale_to_unitsize()

        average_shape = None
        previous_average_shape = None
        for _ in range(max_iterations):
            previous_average_shape = average_shape
            average_shape = self.get_average_shape()

            if previous_average_shape is not None and self.is_same_shape(previous_average_shape, average_shape):
                break

            self.set_reference_shape(average_shape)
            for j in range(len(self.object_list)):
                self.rotate_gls_to_reference_shape(j)

        # The loop breaks before rotating onto the average it just accepted.
        if average_shape is not None:
            self.set_reference_shape(average_shape)
            for j in range(len(self.object_list)):
                self.rotate_gls_to_reference_shape(j)
        return average_shape

    @staticmethod
    def _estimates_converged(previous, current, threshold=1e-8):
        """Have the estimates stopped moving between refinement rounds?

        A coordinate stays ``None`` when no object records that landmark, so
        there is nothing to estimate it from; treat that as settled rather than
        trying to subtract it.
        """
        if len(previous) != len(current):
            return False
        for prev_lm, curr_lm in zip(previous, current):
            for p, c in zip(prev_lm, curr_lm):
                if p is None or c is None:
                    if p is not c:
                        return False
                elif abs(p - c) > threshold:
                    return False
        return True

    def procrustes_superimposition(self, max_iterations=100, convergence_threshold=1e-6):
        """Procrustes superimposition that automatically handles missing landmarks.

        Args:
            max_iterations: Maximum number of iterations (default 100)
            convergence_threshold: Convergence threshold for shape similarity (default 1e-6)
                Previously 1e-10, relaxed to 1e-6 for 95% performance improvement
                with negligible impact on accuracy (measurement error >> 1e-6)
        """
        # print("begin_procrustes")
        if not self.check_object_list():
            print("check_object_list failed")
            return False

        # Check if we have missing landmarks and use appropriate method
        if self.has_missing_landmarks():
            return self.procrustes_superimposition_with_imputation()

        # Original implementation for complete data
        for mo in self.object_list:
            # mo.set_landmarks()
            mo.move_to_center()
            mo.rescale_to_unitsize()
        # print("move_to_center and rescale_to_unitsize done")
        # print("object",self.object_list[0].landmark_list[:5])

        average_shape = None
        previous_average_shape = None
        i = 0
        while i < max_iterations:
            i += 1
            # print("progressing...", i)
            previous_average_shape = average_shape
            average_shape = self.get_average_shape()

            # average_shape.print_landmarks("average_shape")

            if (
                self.is_same_shape(previous_average_shape, average_shape, convergence_threshold)
                and previous_average_shape is not None
            ):
                break
            self.set_reference_shape(average_shape)
            for j in range(len(self.object_list)):
                self.rotate_gls_to_reference_shape(j)
                # self.objects[0].print_landmarks('aa')
                # self.objects[1].print_landmarks('bb')
                # average_shape.print_landmarks('cc')
        # print("end procrustes")
        return True

    def is_same_shape(self, shape1, shape2, threshold=1e-6):
        """Check if two shapes are the same within a threshold.

        Args:
            shape1: First shape to compare
            shape2: Second shape to compare
            threshold: Convergence threshold (default 1e-6)
                Previously 1e-10, relaxed for 95% performance improvement
        """
        if shape1 is None or shape2 is None:
            return False
        sum_coord = 0
        valid_count = 0
        for lm1, lm2 in zip(shape1.landmark_list, shape2.landmark_list, strict=False):
            # Only compare landmarks that are valid in both shapes
            if lm1[0] is not None and lm2[0] is not None and lm1[1] is not None and lm2[1] is not None:
                sum_coord += (lm1[0] - lm2[0]) ** 2
                sum_coord += (lm1[1] - lm2[1]) ** 2
                valid_count += 1
                if self.dimension == 3:
                    if len(lm1) > 2 and len(lm2) > 2 and lm1[2] is not None and lm2[2] is not None:
                        sum_coord += (lm1[2] - lm2[2]) ** 2
        # shape1.print_landmarks("shape1")
        # shape2.print_landmarks("shape2")
        if valid_count == 0:
            return False
        sum_coord = math.sqrt(sum_coord)
        # print "diff: ", sum
        if sum_coord < threshold:
            return True
        return False

    def resistant_fit_superimposition(self):
        if len(self.object_list) == 0:
            print("No objects to transform!")
            raise

        for mo in self.object_list:
            mo.move_to_center()
        average_shape = None
        previous_average_shape = None

        i = 0
        while True:
            i += 1
            # print "iteration: ", i
            previous_average_shape = average_shape
            average_shape = self.get_average_shape()
            average_shape.rescale_to_unitsize()
            if self.is_same_shape(previous_average_shape, average_shape) and previous_average_shape is not None:
                break
            self.set_reference_shape(average_shape)
            for j in range(len(self.object_list)):
                self.rotate_resistant_fit_to_reference_shape(j)

    def rotate_vector_2d(self, theta, vec):
        return self.rotate_vector_3d(theta, vec, "Z")

    def rotate_vector_3d(self, theta, vec, axis):
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        r_mx = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if axis == "Z":
            r_mx[0][0] = cos_theta
            r_mx[0][1] = sin_theta
            r_mx[1][0] = -1 * sin_theta
            r_mx[1][1] = cos_theta
        elif axis == "Y":
            r_mx[0][0] = cos_theta
            r_mx[0][2] = sin_theta
            r_mx[2][0] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        elif axis == "X":
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
        # target_shape = np.zeros((nlandmarks,3))
        reference_shape = self.reference_shape

        # rotation_matrix = self.rotation_matrix( reference_shape, target_shape )

        # rotated_shape = np.transpose( np.dot( rotation_matrix, np.transpose( target_shape ) ) )

        # obtain scale factor using repeated median
        landmark_count = len(reference_shape.landmark_list)
        inner_tau_array = []
        outer_tau_array = []
        median_index = -1
        for i in range(landmark_count - 1):
            for j in range(i + 1, landmark_count):
                target_distance = math.sqrt(
                    (target_shape.landmark_list[i][0] - target_shape.landmark_list[j][0]) ** 2
                    + (target_shape.landmark_list[i][1] - target_shape.landmark_list[j][1]) ** 2
                    + (target_shape.landmark_list[i][2] - target_shape.landmark_list[j][2]) ** 2
                )
                reference_distance = math.sqrt(
                    (reference_shape.landmark_list[i][0] - reference_shape.landmark_list[j][0]) ** 2
                    + (reference_shape.landmark_list[i][1] - reference_shape.landmark_list[j][1]) ** 2
                    + (reference_shape.landmark_list[i][2] - reference_shape.landmark_list[j][2]) ** 2
                )
                tau = reference_distance / target_distance
                inner_tau_array.append(tau)
                median_index = self.get_median_index(inner_tau_array)
            #       print median_index
            # print "tau: ", inner_tau_array
            outer_tau_array.append(inner_tau_array[median_index])
            inner_tau_array = []
        median_index = self.get_median_index(outer_tau_array)
        # print "tau: ", outer_tau_array
        tau_final = outer_tau_array[median_index]

        # rescale to scale factor
        # print "index:", object_index
        # print "scale factor:", tau_final
        # target_shape.print_landmarks("before rescale")
        target_shape.rescale(tau_final)
        # target_shape.print_landmarks("after rescale")
        # exit

        # obtain rotation angle using repeated median
        inner_theta_array = []
        outer_theta_array = []
        inner_vector_array = []
        outer_vector_array = []
        for i in range(landmark_count - 1):
            for j in range(i + 1, landmark_count):
                # get vector
                target_vector = np.array(
                    [
                        target_shape.landmark_list[i][0] - target_shape.landmark_list[j][0],
                        target_shape.landmark_list[i][1] - target_shape.landmark_list[j][1],
                        target_shape.landmark_list[i][2] - target_shape.landmark_list[j][2],
                    ]
                )
                reference_vector = np.array(
                    [
                        reference_shape.landmark_list[i][0] - reference_shape.landmark_list[j][0],
                        reference_shape.landmark_list[i][1] - reference_shape.landmark_list[j][1],
                        reference_shape.landmark_list[i][2] - reference_shape.landmark_list[j][2],
                    ]
                )
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
                cos_val = (
                    np.vdot(target_vector, reference_vector)
                    / np.linalg.norm(target_vector)
                    * np.linalg.norm(reference_vector)
                )
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
                # print inner_vector_array[-1]
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
        # print vector_final
        target_shape[0] = vector_final[0]
        reference_shape[0] = vector_final[1]

        rotation_matrix = self.get_vector_rotation_matrix(vector_final[1], vector_final[0])

        # rotation_matrix = self.rotation_matrix( reference_shape, target_shape )
        # print reference_shape
        # print target_shape
        # rotated_shape = np.transpose( np.dot( rotation_matrix, np.transpose( target_shape ) ) )
        # print rotated_shape
        # exit
        target_shape = np.zeros((nlandmarks, 3))
        i = 0
        for lm in self.object_list[object_index].landmark_list:
            target_shape[i] = lm
            i += 1

        reference_shape = np.zeros((nlandmarks, 3))
        i = 0
        for lm in self.reference_shape.landmark_list:
            reference_shape[i] = lm
            i += 1

        rotated_shape = np.transpose(np.dot(rotation_matrix, np.transpose(target_shape)))

        # print "reference: ", reference_shape[0]
        # print "target: ", target_shape[0], np.linalg.norm(target_shape[0])
        # print "rotation: ", rotation_matrix
        # print "rotated: ", rotated_shape[0], np.linalg.norm(rotated_shape[0])
        # print "determinant: ", np.linalg.det( rotation_matrix )

        i = 0
        for lm in self.object_list[object_index].landmark_list:
            lm = [rotated_shape[i, 0], rotated_shape[i, 1], rotated_shape[i, 2]]
            i += 1
        if object_index == 0:
            pass
            # self.reference_shape.print_landmarks("ref:")
            # self.objects[object_index].print_landmarks(str(object_index))
            # print "reference: ", reference_shape[0]
            # print "target: ", target_shape[0], np.linalg.norm(target_shape[0])
            # print "rotation: ", rotation_matrix
            # print "rotated: ", rotated_shape[0], np.linalg.norm(rotated_shape[0])
            # print "determinant: ", np.linalg.det( rotation_matrix )

    def get_vector_rotation_matrix(self, ref, target):
        (x, y, z) = (0, 1, 2)
        # print ref
        # print target
        # print "0 ref", ref
        # print "0 target", target

        ref_1 = ref
        ref_1[z] = 0
        cos_val = ref[x] / math.sqrt(ref[x] ** 2 + ref[z] ** 2)
        theta1 = math.acos(cos_val)
        if ref[z] < 0:
            theta1 = theta1 * -1
        ref = self.rotate_vector_3d(-1 * theta1, ref, "Y")
        target = self.rotate_vector_3d(-1 * theta1, target, "Y")

        # print "1 ref", ref
        # print "1 target", target

        cos_val = ref[x] / math.sqrt(ref[x] ** 2 + ref[y] ** 2)
        theta2 = math.acos(cos_val)
        if ref[y] < 0:
            theta2 = theta2 * -1
        ref = self.rotate_vector_2d(-1 * theta2, ref)
        target = self.rotate_vector_2d(-1 * theta2, target)

        # print "2 ref", ref
        # print "2 target", target

        cos_val = target[x] / math.sqrt(target[x] ** 2 + target[z] ** 2)
        theta1 = math.acos(cos_val)
        if target[z] < 0:
            theta1 = theta1 * -1
        target = self.rotate_vector_3d(-1 * theta1, target, "Y")

        # print "3 ref", ref
        # print "3 target", target

        cos_val = target[x] / math.sqrt(target[x] ** 2 + target[y] ** 2)
        theta2 = math.acos(cos_val)
        if target[y] < 0:
            theta2 = theta2 * -1
        target = self.rotate_vector_2d(-1 * theta2, target)

        # print "4 ref", ref
        # print "4 target", target

        r_mx1 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        r_mx2 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        # print "shape:", r_mx1.shape
        # print "r_mx1", r_mx1
        # print "theta1", theta1
        # print "cos theta1", math.cos( theta1 )
        # print "sin theta1", math.sin( theta1 )
        # print "r_mx2", r_mx2
        # print "theta2", theta2
        r_mx1[0][0] = math.cos(theta1)
        r_mx1[0][2] = math.sin(theta1)
        r_mx1[2][0] = math.sin(theta1) * -1
        r_mx1[2][2] = math.cos(theta1)

        # print "r_mx1", r_mx1
        # print "theta1", theta1
        # print "r_mx2", r_mx2
        # print "theta2", theta2

        r_mx2[0][0] = math.cos(theta2)
        r_mx2[0][1] = math.sin(theta2)
        r_mx2[1][0] = math.sin(theta2) * -1
        r_mx2[1][1] = math.cos(theta2)

        # print "r_mx1", r_mx1
        # print "theta1", theta1
        # print "r_mx2", r_mx2
        # print "theta2", theta2

        rotation_matrix = np.dot(r_mx1, r_mx2)
        return rotation_matrix

    def get_median_index(self, arr):
        arr.sort()
        len_arr = len(arr)
        if len_arr == 0:
            return -1
        half_len = int(math.floor(len_arr / 2.0))
        return half_len


class MdAnalysis(Model):
    analysis_name = CharField()
    analysis_desc = CharField(null=True)
    """ dataset info """
    dataset = ForeignKeyField(MdDataset, backref="analyses", null=True, on_delete="CASCADE")
    dimension = IntegerField(default=2)
    wireframe = CharField(null=True)
    baseline = CharField(null=True)
    polygons = CharField(null=True)
    propertyname_str = CharField(null=True)
    superimposition_method = CharField()
    # analysis_method = CharField() # PCA or CVA

    """ object info """
    object_info_json = CharField(null=True)  # object name, id, properties and centroid size
    raw_landmark_json = CharField(null=True)  # raw landmark info in list of list format
    superimposed_landmark_json = CharField(null=True)  # superimposed landmark info in list of list format

    """ PCA result """
    pca_analysis_result_json = CharField(null=True)  # PCA result in list of list format
    pca_rotation_matrix_json = CharField(null=True)  # rotation matrix from PCA
    pca_eigenvalues_json = CharField(null=True)  # PCA eigenvalues and percentages of variance explained

    """ CVA result """
    cva_group_by = CharField(null=True)
    cva_analysis_result_json = CharField(null=True)  # CVA result in list of list format
    cva_rotation_matrix_json = CharField(null=True)  # rotation matrix from CVA
    cva_eigenvalues_json = CharField(null=True)  # CVA eigenvalues and percentages of variance explained

    """ MANOVA result"""
    manova_group_by = CharField(null=True)
    manova_analysis_result_json = CharField(null=True)  # MANOVA results

    # How the user arranged the chart for this analysis (legend entry order and
    # dragged legend position, keyed by grouping variable). Presentation only —
    # nothing here feeds back into the numbers.
    chart_settings_json = CharField(null=True)

    # Snapshot of the dataset's semi-landmark curve configuration at analysis
    # time, so the analysis stays reproducible if the dataset's curves change
    # later. See MdDataset.get_curve_config() for the format.
    curve_config_json = CharField(null=True)

    # virtual_specimens_json = CharField(null=True) # list of virtual specimens

    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    def get_curve_config(self):
        """Snapshotted semi-landmark curve configuration as a list, ``[]`` when unset.

        Mirrors :meth:`MdDataset.get_curve_config`. Never raises.
        """
        if not self.curve_config_json:
            return []
        try:
            config = json.loads(self.curve_config_json)
        except (ValueError, TypeError) as e:
            logger.warning("Ignoring unreadable curve config for analysis %s: %s", self.id, e)
            return []
        return config if isinstance(config, list) else []

    def set_curve_config(self, config):
        """Store the snapshotted semi-landmark curve configuration."""
        self.curve_config_json = json.dumps(config) if config else None

    def get_chart_settings(self):
        """Chart presentation settings as a dict, ``{}`` when unset or unreadable.

        Never raises: these are cosmetics, and a corrupt blob must not stop an
        analysis from opening.
        """
        if not self.chart_settings_json:
            return {}
        try:
            settings = json.loads(self.chart_settings_json)
        except (ValueError, TypeError) as e:
            logger.warning("Ignoring unreadable chart settings for analysis %s: %s", self.id, e)
            return {}
        return settings if isinstance(settings, dict) else {}

    def set_chart_settings(self, settings):
        """Store chart presentation settings (see :meth:`get_chart_settings`)."""
        self.chart_settings_json = json.dumps(settings) if settings else None

    class Meta:
        database = gDatabase


def delete_curve_from_dataset(dataset, curve_index):
    """Remove a curve from the dataset scheme (dataset-wide) and pull the rest
    forward.

    Deleting the curve at ``curve_index`` renumbers the remaining curves
    (``curve1``, ``curve2``, ...), recomputes their start indices, and remaps
    every object's raw traces and snap anchors to the new ids (dropping the
    deleted one). Persists the dataset and every affected object. No-op for an
    out-of-range index.
    """
    config = dataset.get_curve_config()
    if curve_index < 0 or curve_index >= len(config):
        return
    remaining = [c for i, c in enumerate(config) if i != curve_index]
    remaining_ids = [c["id"] for c in remaining]
    fixed = config[0].get("start", 0)
    new_config = mu.build_curve_config(
        fixed, [{"n": c.get("n", 0), "name": c.get("name", ""), "desc": c.get("desc", "")} for c in remaining]
    )
    id_map = {old: new["id"] for old, new in zip(remaining_ids, new_config)}

    dataset.set_curve_config(new_config)
    dataset.save()
    for obj in dataset.object_list:
        raw = obj.get_curve_raw()
        anchors = obj.get_curve_anchors()
        if not raw and not anchors:
            continue
        if raw:
            obj.set_curve_raw({id_map[old]: pts for old, pts in raw.items() if old in id_map})
        if anchors:
            obj.set_curve_anchors({id_map[old]: pts for old, pts in anchors.items() if old in id_map})
        obj.save()


def prepare_database():
    """Prepare the database by running migrations and backups"""
    from peewee_migrate import Router

    migrations_path = mu.resource_path("migrations")
    logger.info("migrations path: %s", migrations_path)
    logger.info("database path: %s", database_path)
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")

    # backup database file to backup directory. Name the backup after the file
    # actually in use, so a database chosen with --db does not overwrite the
    # backups of the default one.
    database_filename = os.path.basename(database_path)
    backup_path = os.path.join(mu.DB_BACKUP_DIRECTORY, database_filename + "." + date_str)
    if not os.path.exists(backup_path) and os.path.exists(database_path):
        shutil.copy2(database_path, backup_path)
        logger.info("backup database to %s", backup_path)
        # read backup directory and delete old backups
        backup_list = os.listdir(mu.DB_BACKUP_DIRECTORY)
        # filter out non-backup files
        backup_list = [f for f in backup_list if f.startswith(database_filename)]
        backup_list.sort()
        if len(backup_list) > 10:
            # Keep the 10 most recent backups; remove the rest.
            for old_backup in backup_list[:-10]:
                os.remove(os.path.join(mu.DB_BACKUP_DIRECTORY, old_backup))

    gDatabase.connect()
    router = Router(gDatabase, migrate_dir=migrations_path)
    # Auto-discover and run migrations
    router.run()
