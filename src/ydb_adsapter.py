import os
import json

import ydb
import ydb.iam

# Create driver in global space.
driver = ydb.Driver(
    endpoint=os.getenv('YDB_ENDPOINT'),
    database=os.getenv('YDB_DATABASE'),
    credentials=ydb.iam.MetadataUrlCredentials(),
)

# Wait for the driver to become active for requests.

driver.wait(fail_fast=True, timeout=5)

# Create the session pool instance to manage YDB sessions.
pool = ydb.SessionPool(driver)

user_id = 934329
query = """
        SELECT isAutoSend FROM users
        WHERE userId = {0}
        ;
""".format(user_id)


def execute_query(session):
    # Create the transaction and execute query.
    return session.transaction().execute(
        query,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )


def handler(event, context):
    # Execute query with the retry_operation helper.
    result = pool.retry_operation_sync(execute_query)
    res = ""
    for row in result[0].rows:
        print(row)
        res += str(row) + "\n"
    print(res)
    data = json.loads(res.strip().replace("'", '"'))
    print(data)
    return data['isAutoSend']

    return {
        'statusCode': 200,
        'body': res,
        'type': result
    }
