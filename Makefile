build-and-push:
	docker-compose build
	docker tag vacinacao-img:latest 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.3.1
	docker push 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.3.1

deploy:
	sam deploy

run-app:
	python src/vacinacao/entrypoints.py
