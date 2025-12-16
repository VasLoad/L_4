import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import logging

from config import DB_FILE_PATH
from enums.db_settings_param_name import DBSettingsParamName, DBParamName
from errors import (
    # DatabaseNotFoundError,
    DatabaseIntegrityError,
    DatabaseQueryError,
)

logger = logging.getLogger(__name__)


class SQLiteQuerySender:
    def __init__(self, db_path: str):
        self.__db_path = db_path

    def execute(
        self,
        query: str,
        params: Optional[list[Any]] = None,
        fetchone: bool = False,
        fetchall: bool = False,
        commit: bool = False,
    ):
        if params is None:
            params = []

        self.__prepare_db_file_path()

        conn: Optional[sqlite3.Connection] = None
        cursor: Optional[sqlite3.Cursor] = None

        try:
            conn = sqlite3.connect(self.__db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(query, tuple(params))

            if commit:
                conn.commit()

            if fetchone:
                row = cursor.fetchone()
                if row is None:
                    # raise DatabaseNotFoundError()

                    return {}
                return dict(row)

            if fetchall:
                return [dict(r) for r in cursor.fetchall()]

            return cursor.rowcount

        except sqlite3.IntegrityError as ex:
            logger.exception(ex)

            raise DatabaseIntegrityError(str(ex))

        except sqlite3.Error as ex:
            logger.exception(ex)

            raise DatabaseQueryError(str(ex))

        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    def __prepare_db_file_path(self):
        db_path = Path(self.__db_path)

        db_path.parent.mkdir(parents=True, exist_ok=True)

        if not db_path.exists():
            db_path.touch()


class BaseRepository(ABC):
    def __init__(self, sender: SQLiteQuerySender):
        self._sender = sender

    @abstractmethod
    def create_table(self):
        pass


class UsersRepository(BaseRepository):
    def __init__(self, sender: SQLiteQuerySender):
        super().__init__(sender)

    def create_table(self):
        query = f"""
            CREATE TABLE IF NOT EXISTS users (
                {DBParamName.USER_ID} INTEGER NOT NULL PRIMARY KEY
            );
        """

        self._sender.execute(
            query=query,
            commit=True,
        )

    def check_user(self, user_id: int) -> bool:
        query = f"""
            SELECT 1
            FROM users
            WHERE {DBParamName.USER_ID} = ?
            LIMIT 1
        """

        # try:
        #     self._sender.execute(
        #         query=query,
        #         params=(user_id,),
        #         fetchone=True
        #     )
        # except DatabaseNotFoundError:
        #     return False

        result = self._sender.execute(
            query=query,
            params=[user_id],
            fetchone=True
        )

        return result.get("1") is not None

    def add_user(self, user_id):
        query = f"""
            INSERT OR IGNORE INTO users
            ({DBParamName.USER_ID})
            VALUES (?)
        """

        self._sender.execute(
            query=query,
            params=[user_id],
            commit=True
        )


class UserSettingsRepository(BaseRepository):
    def __init__(self, sender: SQLiteQuerySender):
        super().__init__(sender)

    def create_table(self):
        query = f"""
            CREATE TABLE IF NOT EXISTS user_settings (
                {DBParamName.USER_ID} INTEGER PRIMARY KEY,
                {DBSettingsParamName.SEND_INFORMATION_IMAGE} BOOL NOT NULL DEFAULT TRUE
            );
        """

        self._sender.execute(
            query=query,
            commit=True
        )

    def get_settings(self, user_id: int) -> dict:
        query = f"""
            SELECT {DBSettingsParamName.SEND_INFORMATION_IMAGE}
            FROM user_settings
            WHERE {DBParamName.USER_ID} = ?
        """

        return self._sender.execute(
            query=query,
            params=[user_id],
            fetchone=True
        )

    def get_settings_param_value(self, user_id, param: DBSettingsParamName) -> Optional[Any]:
        query = f"""
            SELECT {param}
            FROM user_settings
            WHERE {DBParamName.USER_ID} = ?
        """

        return self._sender.execute(
            query=query,
            params=[user_id],
            fetchone=True
        ).get(param)

    def set_user_default_settings(
        self,
        user_id: int,
        show_information_image: bool = True,
    ) -> None:
        query = f"""
            INSERT INTO user_settings ({DBParamName.USER_ID}, {DBSettingsParamName.SEND_INFORMATION_IMAGE})
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                {DBSettingsParamName.SEND_INFORMATION_IMAGE} = excluded.{DBSettingsParamName.SEND_INFORMATION_IMAGE}
        """

        self._sender.execute(
            query=query,
            params=[user_id, int(show_information_image)],
            commit=True
        )

    def update_param_value(self, user_id: int, param: DBSettingsParamName, value: Any) -> None:
        query = f"""
            UPDATE user_settings
            SET {param} = ?
            WHERE {DBParamName.USER_ID} = ?
        """

        self._sender.execute(
            query=query,
            params=[value, user_id],
            commit=True
        )

    def delete_user_settings(self, user_id, set_default: bool = False):
        query = f"""
            DELETE FROM user_settings
            WHERE {DBParamName.USER_ID} = ?
        """

        self._sender.execute(
            query=query,
            params=[user_id],
            commit=True
        )

        if set_default:
            self.set_user_default_settings(user_id)

db_sender = SQLiteQuerySender(DB_FILE_PATH)


def register_user(sender: SQLiteQuerySender, user_id: int):
    UsersRepository(sender).add_user(user_id)
    UserSettingsRepository(sender).set_user_default_settings(user_id)
