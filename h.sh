#!/bin/sh
docker-compose run app sh -c "python manage.py test core"

