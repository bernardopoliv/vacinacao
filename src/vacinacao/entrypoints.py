import json

from flask import request, render_template, Response
from flask_lambda import FlaskLambda

from vacinacao.main import read
from vacinacao import settings

app = FlaskLambda(__name__)


@app.route("/", methods=["GET"])
def home():
    html_template = open(f"{settings.ROOT_DIR}/templates/search.html").read()
    html_content = html_template.replace(r"{{ BASE_URL }}", settings.BASE_URL)
    return (html_content, 200)


@app.route("/search", methods=["POST"])
def search():
    found = read(
        json.loads(request.data)["name"]
    )
    response = Response(
        json.dumps({"found": found}),
        headers={"Content-Type": "application/json"}
    )

    return response


if __name__ == '__main__':
    app.run(debug=True)
