"Simple file for doing database operations"
import os
import sqlite3

from sqlite_orm.database import Database
from sqlite_orm.field import IntegerField, TextField, BaseField
from sqlite_orm.table import BaseTable

import settings
from common.logger import logger


def get_realtime_setting(setting, convert=lambda x: x, default=None):
    "Returns the given setting's value at real-time"
    # pylint: disable=bare-except
    try:
        with DB() as database:
            query = database.db.query(Settings).select().execute()
            settings_db = None
            for res in query:
                settings_db = Settings.to_user_class(res)
                # Could be only one record
                break
        if settings_db is not None:
            value = getattr(settings_db, setting)
            if value:
                return convert(value)
    except:
        logger.warning("Could not get the %s from database", setting)

    try:
        return getattr(settings, setting)
    except AttributeError:
        return default


def set_realtime_setting(name, value):
    "Sets the given setting's value at real-time"
    if name not in Settings.fields():
        raise AttributeError(
            "{!r} object has no attribute {!r}"
            "".format(Settings.__name__, name)
        )
    with DB() as database:
        setting = database.select(Settings)[0]
        setattr(setting, name, value)
        database.update(setting)


class _CustomBaseTable(BaseTable):
    def __init__(self, *fields):
        super().__init__()

        table_fields = self.fields()
        if len(table_fields) == len(fields):
            for idx, table_field in enumerate(table_fields):
                setattr(self, table_field, fields[idx])

    @classmethod
    def fields(cls):
        "Returns the table fields"
        fields = []
        for key in cls.__dict__:
            attribute = getattr(cls, key)
            if isinstance(attribute, BaseField):
                fields.append(key)
        return fields

    @classmethod
    def to_user_class(cls, user_tuple):
        "Converts the given object to the class object"
        # Get fields
        user = cls()
        index = 0
        for key in cls.__dict__:
            attribute = getattr(cls, key)
            if isinstance(attribute, BaseField):
                setattr(user, key, user_tuple[index])
                index += 1
        return user

    def __str__(self):
        return self.__dict__.__str__()

    def __repr__(self):
        return f"{str(self)}"


class User(_CustomBaseTable):
    "The User table"
    __table_name__ = 'users'

    id = IntegerField(primary_key=True)
    name = TextField(not_null=True)
    last_update_time = TextField(not_null=True)
    follower_count = IntegerField(not_null=True)
    mean_like_count = IntegerField(not_null=True)
    mean_comment_count = IntegerField(not_null=True)
    category = TextField(default_value="General")


class Settings(_CustomBaseTable):
    "The Settings table"
    __table_name__ = 'settings'

    id = IntegerField(primary_key=True, auto_increment=True)
    WAIT_TIME_S = TextField(default_value=settings.WAIT_TIME_S)
    LOAD_EVERY_X_CYCLE = TextField(default_value=settings.LOAD_EVERY_X_CYCLE)
    LOG_LEVEL = TextField(default_value=settings.LOG_LEVEL)
    WAIT_SECS = TextField(default_value=settings.WAIT_SECS)
    LISTENER_WAIT_TIME = TextField(default_value=settings.LISTENER_WAIT_TIME)


class DB:
    "The main database object"
    tables = (User, Settings,)

    def __init__(self):
        is_db_exists = os.path.isfile(settings.DB_NAME)
        self._db = Database(settings.DB_NAME)
        if not is_db_exists:
            self._create_db_for_first_use()

    @property
    def db(self):
        "Returns the database"
        return self._db

    def _create_db_for_first_use(self, skip_error=False):
        logger.debug("Creating tables")
        # Create the tables
        for table in self.tables:
            try:
                self.db.query(table).create().execute()
            except sqlite3.OperationalError:
                if not skip_error:
                    logger.error(
                        "Could not created table %s",
                        table.__table_name__
                    )
                    raise
                logger.warning(
                    "Could not created table %s",
                    table.__table_name__
                )
        self.insert(Settings())

    def select(self, select_from, *condition_expressions, logical_operator='AND'):
        "Returns the values from database based on conditions"
        query = self._db.query(select_from).select()

        if condition_expressions:
            query = query.filter(
                *condition_expressions,
                logical_operator_inner=logical_operator
            )

        result = query.execute()
        result_list = []
        for res in result:
            result_list.append(select_from(*res))
        return result_list

    def insert(self, obj):
        "Inserts the record"
        self.db.query().insert(obj).execute()

    def delete(self, obj):
        "Deletes record from database based on id"
        self.db.query(obj.__class__).delete().filter(
            obj.__class__.id == obj.id
        ).execute()

    def update(self, obj, *parts):
        "Updates the database"
        if not parts:
            # Update all fields
            parts = tuple(obj.fields())

        kwargs = {}
        for part in parts:
            kwargs[part] = getattr(obj, part)

        self.db.query(obj.__class__).update(
            **kwargs
        ).filter(obj.__class__.id == obj.id).execute()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.db.close()

    def __del__(self):
        # pylint:disable=bare-except
        try:
            self._db.close()
        except:
            pass
