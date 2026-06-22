SHELL=/bin/bash

.PHONY: up up.d down logs test run dev.up dev.up.d dev.down dev.logs dev.migrate dev.createsuperuser

up:
	docker compose up --build

up.d:
	docker compose up --build -d

down:
	docker compose down --remove-orphans

logs:
	docker compose logs -f mock_api django db

# Aliases from the old Django compose workflow
dev.up: up

dev.up.d: up.d

dev.down: down

dev.logs: logs

dev.migrate:
	docker compose exec django python manage.py migrate

dev.createsuperuser:
	docker compose exec -it django python manage.py createsuperuser

run:
	python3 -m mock_backend

test:
	python3 -m pytest mock_backend/tests django_backend/tests -q
