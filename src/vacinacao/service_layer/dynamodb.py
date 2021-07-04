import datetime
import logging

import boto3

from vacinacao.settings import DYNAMODB_TABLE_NAME

logger = logging.getLogger(__name__)


def _get_subscription_table():
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    return dynamodb.Table(DYNAMODB_TABLE_NAME)


def get_subscription(name: str) -> dict:
    table = _get_subscription_table()
    subscription = table.get_item(Key={"Name": name})
    subscription = subscription.get("Item", {})
    logger.info("Retrieved subscription", extra={"name": name})
    return subscription


def get_all_subscriptions():
    logger.info("Fetching for all items...")
    table = _get_subscription_table()
    response = table.scan()
    subscriptions = response["Items"]
    logger.info("Retrieved all items", extra={"count": len(subscriptions)})
    return subscriptions


def add_subscription(name: str, email: str):
    table = _get_subscription_table()
    table.put_item(
        Item={
            "name": name.lower(),
            "email": email.lower(),
            "notified": [],
            "subscription_dt": datetime.datetime.now().isoformat(),
        }
    )
    logger.info(
        "Email added to notification list", extra={"name": name, "email": email}
    )
