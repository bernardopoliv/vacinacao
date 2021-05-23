FROM public.ecr.aws/lambda/python:3.8

COPY src/vacinacao/requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY src /var/task
RUN pip install -e /var/task


CMD ["handler.handler"]