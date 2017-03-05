import bloop
import boto3

ENQUEUE_PROFILE_NAME = "pqs-worker-us-west-2"
WEBSITE_PROFILE_NAME = "pqs-website-us-west-2"

WEBSITE_PORT = 8080


def build_engine(profile_name) -> bloop.Engine:
    session = boto3.Session(profile_name=profile_name)
    dynamodb = session.client("dynamodb")
    dynamodbstreams = session.client("dynamodbstreams")
    engine = bloop.Engine(dynamodb=dynamodb, dynamodbstreams=dynamodbstreams)
    return engine
