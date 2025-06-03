from aws_cdk import Stack

from .databases import Tables
from .lambdas import Lambdas


class ApplicationStack(Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        # tbls = Tables(self, "tbl_wa")

        Fn = Lambdas(self, "Fn")