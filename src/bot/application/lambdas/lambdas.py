import sys

from .layers import Layers
from aws_cdk import Duration, aws_lambda
from constructs import Construct


LAMBDA_TIMEOUT = 900


BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(LAMBDA_TIMEOUT),
    memory_size=256,
    tracing=aws_lambda.Tracing.ACTIVE,
)

COMMON_LAMBDA_CONF = dict(runtime=aws_lambda.Runtime.PYTHON_3_11, **BASE_LAMBDA_CONFIG)


class Lambdas(Construct):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        layers = Layers(self, "layers")

        self.whatsapp_in = aws_lambda.Function(
            self,
            "whatsapp_in",
            handler="lambda_function.lambda_handler",
            description="process incoming whatsapp messages",
            code=aws_lambda.Code.from_asset("./application/lambdas/code/whatsapp_in"),
            layers=[],
            **COMMON_LAMBDA_CONF,
        )

        self.process_stream = aws_lambda.Function(
            self,
            "process_stream",
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset(
                "./application/lambdas/code/process_stream"
            ),
            layers=[layers.bs4_requests, layers.pymupdf],
            **COMMON_LAMBDA_CONF,
        )

        self.lang_chain_agent = aws_lambda.Function(
            self,
            "lang_chain_agent",
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset(
                "./application/lambdas/code/lang_chain_agent"
            ),
            layers=[layers.bs4_requests, layers.langchain],
            **COMMON_LAMBDA_CONF,
        )
