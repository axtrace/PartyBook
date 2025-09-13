import os
import ydb
import ydb.iam


class YdbAdapter:
    """connection to YDB"""

    def __init__(self):
        self.driver = None
        self.pool = None

    def _ensure_connected(self):
        if self.driver:
            return
        
        try:
            # Отладочная информация
            endpoint = os.getenv('YDB_ENDPOINT', '').rstrip('/')
            database = os.getenv('YDB_DATABASE', '')
            print(f"Connecting to YDB: endpoint={endpoint}, database={database}")
            
            # Используем метаданные сервисного аккаунта для аутентификации
            credentials = ydb.iam.MetadataUrlCredentials()
            
            self.driver = ydb.Driver(
                endpoint=endpoint,
                database=database,
                credentials=credentials,
                root_certificates=ydb.load_ydb_root_certificate()
            )
            
            # Wait for the driver to become active for requests.
            print("Waiting for YDB driver to become active...")
            self.driver.wait(fail_fast=True, timeout=10)
            print("YDB driver is ready!")

            # Create the session pool instance to manage YDB sessions.
            self.pool = ydb.SessionPool(self.driver)
            print("YDB session pool created successfully!")
            
        except Exception as e:
            print(f"Error connecting to YDB: {str(e)}")
            raise

    def _run_transaction(self, session, query):
        # Create the transaction and execute query.
        return session.transaction().execute(
            query,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        )

    def execute_query(self, query):
        self._ensure_connected()
        result = self.pool.retry_operation_sync(
            lambda session: self._run_transaction(session, query))
        return result