#!/usr/bin/env python3
import os

import aws_cdk as cdk

from application import ApplicationStack


app = cdk.App()
ApplicationStack(app, "ApplicationStack")
app.synth()
