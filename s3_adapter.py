import boto3
import os

class s3Adapter:
    """connection to Object Storage"""

    def __init__(self):
        self.s3_client = self._init_s3_client_()
        self._bucket_ = os.environ['BUCKET_NAME']

    def _init_s3_client_(self):
        return boto3.client(
            service_name='s3',
            endpoint_url='https://storage.yandexcloud.net',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
        )

    def put_object(self, filename, body, mime_type):
        try:
            self.s3_client.put_object(
                Bucket=self._bucket_,
                Key=filename,
                Body=body,
                ContentType=mime_type
            )
            return 0

        except Exception as e:
            return None

    def get_object(self, filename, decode: bool = True) -> bytes | str | None:
        try:
            response = self.s3_client.get_object(Bucket= self._bucket_, Key=filename)

            if decode:
                return response['Body'].read().decode('utf-8')
            return response['Body'].read()

        except self.s3_client.exceptions.NoSuchKey:
            print(f"File {key} not found in bucket {self._bucket_}")
        except Exception as e:
            print(f"Error accessing S3: {str(e)}")
        return None