import json

from flask import request, render_template
from flask_lambda import FlaskLambda

from vacinacao.main import read
from vacinacao import settings

app = FlaskLambda(__name__)


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        searched_name = request.form["name"]
        found = read(searched_name)
        return render_template('results.html', found=found)

    html_template = open(f"{settings.ROOT_DIR}/templates/search.html").read()
    html_content = html_template.replace(r"{{ BASE_URL }}", settings.BASE_URL)
    return (html_content, 200)


if __name__ == '__main__':
    app.run(debug=True)
