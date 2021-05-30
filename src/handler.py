from vacinacao.entrypoints import app
from vacinacao.service_layer.indexer import download_and_reindex


def handler(event, context):
    return app(event, context)


def reindex_handler(event, context):
    download_and_reindex()
    return {"statusCode": 200}
