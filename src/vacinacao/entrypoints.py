import json

from flask_lambda import FlaskLambda

from vacinacao.main import read

app = FlaskLambda(__name__)


@app.route("/search", methods=["GET"])
def search():
    found = read()
    return (
        json.dumps({"found": found}),
        200,
        {'Content-Type': 'application/json'}
    )


if __name__ == '__main__':
    app.run(debug=True)
