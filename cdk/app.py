#!/usr/bin/env python3

import aws_cdk as cdk
from cdk_stack import DynamoCdcLatencyStack

app = cdk.App()
DynamoCdcLatencyStack(app, "DynamoCdcLatencyStack")

app.synth()
