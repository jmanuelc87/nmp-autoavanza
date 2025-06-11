import aws_cdk.aws_s3 as s3

from constructs import Construct


class Storage(Construct):

    def __init__(self, scope, id):
        super().__init__(scope, id)

        self.bucket = s3.Bucket(self, f"{id}_documents", versioned=True)
