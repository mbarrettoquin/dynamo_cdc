from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    Duration,
)
from aws_cdk.aws_lambda_event_sources import DynamoEventSource

class DynamoCdcLatencyStack(Stack):
    
    # Configuration - Update this to match your DynamoDB table name
    DYNAMODB_TABLE_NAME = "FOS_DocStore_Compare_POC-dev-dynamodb"
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Import existing DynamoDB table by name
        table = dynamodb.Table.from_table_name(
            self, "ExistingDynamoTable",
            table_name=self.DYNAMODB_TABLE_NAME
        )
        
        # Create IAM role for Writer Lambda
        writer_role = iam.Role(
            self, "WriterLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "DynamoWritePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem"
                            ],
                            resources=[table.table_arn]
                        )
                    ]
                )
            }
        )
        
        # Create IAM role for Reader Lambda
        reader_role = iam.Role(
            self, "ReaderLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "DynamoStreamPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:DescribeStream",
                                "dynamodb:GetRecords",
                                "dynamodb:GetShardIterator",
                                "dynamodb:ListStreams"
                            ],
                            resources=[f"{table.table_arn}/*"]
                        )
                    ]
                )
            }
        )
        
        # Create Writer Lambda Function
        writer_lambda = _lambda.Function(
            self, "DynamoCdcLatencyWriter",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="writer.lambda_handler",
            code=_lambda.Code.from_asset("../lambda"),
            role=writer_role,
            timeout=Duration.minutes(1),
            environment={
                "DYNAMODB_TABLE_NAME": self.DYNAMODB_TABLE_NAME
            },
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Create Reader Lambda Function
        reader_lambda = _lambda.Function(
            self, "DynamoCdcLatencyReader",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="reader.lambda_handler",
            code=_lambda.Code.from_asset("../lambda"),
            role=reader_role,
            timeout=Duration.minutes(1),
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Create EventBridge rule to trigger Writer Lambda every 1 minute
        schedule_rule = events.Rule(
            self, "WriterScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(1)),
            description="Triggers DynamoDB CDC latency test writer every 1 minute"
        )
        
        # Add Writer Lambda as target for the scheduled rule
        schedule_rule.add_target(targets.LambdaFunction(writer_lambda))
        
        # Create DynamoDB Stream Event Source for Reader Lambda
        reader_lambda.add_event_source(
            DynamoEventSource(
                table=table,
                starting_position=_lambda.StartingPosition.LATEST,
                batch_size=10,
                max_batching_window=Duration.minutes(1),
                retry_attempts=3
            )
        )
        
        # Output important information
        cdk.CfnOutput(
            self, "WriterLambdaName",
            value=writer_lambda.function_name,
            description="Name of the Writer Lambda function"
        )
        
        cdk.CfnOutput(
            self, "ReaderLambdaName", 
            value=reader_lambda.function_name,
            description="Name of the Reader Lambda function"
        )
        
        cdk.CfnOutput(
            self, "DynamoTableName",
            value=self.DYNAMODB_TABLE_NAME,
            description="DynamoDB table being monitored"
        )
        
        cdk.CfnOutput(
            self, "ReaderLogGroup",
            value=f"/aws/lambda/{reader_lambda.function_name}",
            description="CloudWatch Log Group for latency metrics"
        )
