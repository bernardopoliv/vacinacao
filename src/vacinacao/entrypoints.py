import json

from flask import request
from flask_lambda import FlaskLambda

from vacinacao.main import read
from vacinacao import settings

app = FlaskLambda(__name__)


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        searched_name = request.form["name"]
        found = read(searched_name)
        return (
            json.dumps({"found": found}),
            200,
            {'Content-Type': 'application/json'}
        )

    html_template = open(f"{settings.ROOT_DIR}/templates/search.html").read()
    html_content = html_template.replace(r"{{ BASE_URL }}", settings.BASE_URL)
    return (html_content, 200)


if __name__ == '__main__':
    app.run(debug=True)
