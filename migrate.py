import datetime
from peewee_migrate import Router
from peewee import SqliteDatabase
from MdModel import MdDataset, MdObject, MdImage, MdThreeDModel, MdAnalysis
import MdUtils as mu
import os
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

database_path = os.path.join(mu.DEFAULT_DB_DIRECTORY, 'Modan2.db')
gDatabase = SqliteDatabase(database_path,pragmas={'foreign_keys': 1})

def get_timestamp():
    import datetime
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d")
migrations_path = mu.resource_path('migrations')
#migrations_path = "migrations"
logger = logging.getLogger(__name__)
logger.info(f"migrations_path: {migrations_path}")
logger.info(f"database path: {database_path}")
gDatabase.connect()
tables = gDatabase.get_tables()

logger.info(f"tables: {tables}")
router = Router(gDatabase, migrate_dir=migrations_path)
logger.debug(f"router: {router}")
# set migration_name to YYYYMMDD_HHMMSS
migration_name = get_timestamp()
logger.info(f"migration_name: {migration_name}")
ret = router.create(auto=[MdDataset,MdObject,MdImage,MdThreeDModel,MdAnalysis], name=migration_name)
logger.info(f"migration result: {ret}")


