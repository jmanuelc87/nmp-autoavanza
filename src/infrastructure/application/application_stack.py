from aws_cdk import Stack

from .databases import Tables
from .storage import Storage


class ApplicationStack(Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        Tbls = Tables(self, "wa")

        Store = Storage(self, "monte")