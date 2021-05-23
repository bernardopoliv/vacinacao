build-and-push:
	docker-compose build
	docker tag vacinacao-img:latest 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.3.2
	docker push 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.3.2

deploy:
	sam deploy --no-confirm-changeset

webapp:
	python src/vacinacao/entrypoints.py
