FROM public.ecr.aws/lambda/python:3.8

# Requirements first for easier layer caching
COPY src/vacinacao/requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY src /var/task
RUN pip install -e /var/task
COPY tests/ /tests/

CMD ["handler.handler"]
