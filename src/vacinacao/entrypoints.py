import json

from flask import request, Response
from flask_lambda import FlaskLambda

from vacinacao.service_layer.searcher import search_name
from vacinacao import settings
from flask_cors import CORS

app = FlaskLambda(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def home():
    html_template = open(f"{settings.ROOT_DIR}/templates/search.html").read()
    html_content = html_template.replace(r"{{ BASE_URL }}", settings.BASE_URL)
    return html_content, 200


@app.route("/search", methods=["POST"])
def search():
    found = search_name(json.loads(request.data)["name"])

    return Response(json.dumps(found), headers={"Content-Type": "application/json"})


if __name__ == "__main__":
    app.run(debug=True)
