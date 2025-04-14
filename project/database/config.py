from sqlmodel import SQLModel, create_engine

from project.core.settings import settings

postgres_url = settings.DB_CONNECTION
connect_args = {
    "check_same_thread": False
}  # check_same_thread is for SQLite, not PostgreSQL

engine = create_engine(
    postgres_url, echo=True
)  # To display the logs of the SQLModel queries


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    print("Attempting to create database and tables via direct execution...")
    create_db_and_tables()
    print("Database and tables should be created if they didn't exist.")
