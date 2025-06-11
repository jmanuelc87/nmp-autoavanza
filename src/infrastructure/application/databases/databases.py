from aws_cdk import RemovalPolicy, aws_dynamodb as ddb
from constructs import Construct


REMOVAL_POLICY = RemovalPolicy.DESTROY

TABLE_CONFIG = dict(
    removal_policy=REMOVAL_POLICY, billing_mode=ddb.BillingMode.PAY_PER_REQUEST
)


class Tables(Construct):

    def __init__(self, scope, id):
        super().__init__(scope, id)

        self.messages_metadata = ddb.Table(
            self,
            f"{id}_messages_metadata",
            partition_key=ddb.Attribute(
                name="messages_id", type=ddb.AttributeType.STRING
            ),
            stream=ddb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        self.sessions = ddb.Table(
            self,
            f"{id}_sessions",
            partition_key=ddb.Attribute(
                name="session_id", type=ddb.AttributeType.STRING
            ),
            **TABLE_CONFIG,
        )

        self.user_metadata = ddb.Table(
            self,
            f"{id}_user_metadata",
            partition_key=ddb.Attribute(
                name="phone_number", type=ddb.AttributeType.STRING
            ),
            **TABLE_CONFIG,
        )
