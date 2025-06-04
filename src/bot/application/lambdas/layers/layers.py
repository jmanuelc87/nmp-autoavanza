import json

from aws_cdk import aws_lambda
from constructs import Construct


class Layers(Construct):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        # layer con beautiful soup y requests
        self.bs4_requests = aws_lambda.LayerVersion(
            self,
            "Bs4Requests",
            code=aws_lambda.Code.from_asset("./application/lambdas/layers/bs4_requests.zip"),
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_8,
                aws_lambda.Runtime.PYTHON_3_9,
                aws_lambda.Runtime.PYTHON_3_10,
                aws_lambda.Runtime.PYTHON_3_11,
            ],
            description="BeautifulSoup y Requests",
        )

        # layer con pymupdf
        self.pymupdf = aws_lambda.LayerVersion(
            self,
            "PyMuPDF",
            code=aws_lambda.Code.from_asset("./application/lambdas/layers/pymupdf_layer.zip"),
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_8,
                aws_lambda.Runtime.PYTHON_3_9,
                aws_lambda.Runtime.PYTHON_3_10,
                aws_lambda.Runtime.PYTHON_3_11,
            ],
            description="pymunpdf"
        )
