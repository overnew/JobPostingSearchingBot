import boto3
import os


class SubscribeDataSaver:

    def __init__(self):
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name='ap-northeast-2',
        )

        table_name = '001_TATTOO_Subscribe_Data'  # 테이블 이름
        self.table = dynamodb.Table(table_name)

    def save_subscribe_data(self, user_id, keyword, channel_id):
        self.table.put_item(
            Item=self.__make_json_data(user_id, keyword, channel_id)
        )

    def __make_json_data(self, user_id, keyword, channel_id):
        return {
            'user_id': user_id,
            'channel_id': channel_id,
            'keyword': keyword
        }

    def delete_subscribe_data(self, user_id, channel_id):
        self.table.delete_item(
            Key={'user_id': user_id, 'channel_id': channel_id}
        )