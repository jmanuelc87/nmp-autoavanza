from aws_cdk import Stack, aws_lambda, aws_lambda_event_sources

from .databases import Tables
from .lambdas import Lambdas
from .apis import WebhookApi


class ApplicationStack(Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        Tbls = Tables(self, "tbls")

        Fns = Lambdas(self, "Fns")

        Api = WebhookApi(self, "Api", lambdas=Fns)

        Tbls.messages_metadata.grant_full_access(Fns.whatsapp_in)

        Fns.whatsapp_in.add_environment(
            key="MESSAGES_METADATA", value=Tbls.messages_metadata.table_name
        )

        Fns.process_stream.add_environment(
            key="ENV_LANG_CHAIN_AGENT", value=Fns.lang_chain_agent.function_name
        )

        Fns.process_stream.add_event_source(
            aws_lambda_event_sources.DynamoEventSource(
                table=Tbls.messages_metadata,
                starting_position=aws_lambda.StartingPosition.TRIM_HORIZON,
            )
        )
        
        Tbls.messages_metadata.grant_full_access(Fns.process_stream)
