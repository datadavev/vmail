import argparse
import logging

import sqlalchemy
import sqlalchemy.orm
import vmail.config
import vmail.vmail_router.db
import vmail.vmail_router.repo

def initialize_database(settings):
    L = logging.getLogger(__name__)
    L.info("Initializing database at %s", settings.db_connection_string)
    engine = sqlalchemy.create_engine(
        settings.db_connection_string, pool_pre_ping=True
    )
    vmail.vmail_router.db.SQL_BASE.metadata.create_all(engine)
    L.info("Done")


def clear_database(settings):
    L = logging.getLogger(__name__)
    L.info("Clearing database at %s", settings.db_connection_string)
    engine = sqlalchemy.create_engine(
        settings.db_connection_string, pool_pre_ping=True
    )
    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    repository = vmail.vmail_router.repo.VmailRepo(session)
    try:
        n_deleted = repository.clear()
        L.info("Deleted %s records", n_deleted)
    finally:
        session.close()
    L.info("Done")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', help="Command to run", nargs="?", choices=["initialize", "clear" ])
    parser.add_argument('-c', '--config', default=None, help="Enviroment file for settings", required=False)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    settings = vmail.config.get_settings(env_file=args.config)

    if args.command == "initialize":
        return initialize_database(settings)

    if args.command == "clear":
        return clear_database(settings)


if __name__ == "__main__":
    main()
