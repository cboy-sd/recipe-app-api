#!/bin/sh
docker-compose run --rm app  sh -c "python manage.py test core"

