FROM yml-api as web
WORKDIR /opt/app
EXPOSE 8000
ADD . .
ENTRYPOINT ["python", "manage.py", "startserver", "lcfmv"]

FROM yml-api-test as test
WORKDIR /opt/app
ADD . .
ENTRYPOINT ["sh", "-c", "cp -r /opt/git .git && git pull origin $BRANCH && python manage.py test"]

