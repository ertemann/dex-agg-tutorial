Welcome to this small tutorial on building a crypto dex aggregator in Python

# pre-requisites/Setup

## python setup

Install Poetry `pipx install poetry`

Create poetry project `poetry new PROJECT_NAME`

add Ruff, blackl mypy `poetry add black ruff mypy`

You can use ruff and black using: `poetry run black dex_agg_tutorial` and `poetry run ruff check` and `poetry run mypy`

setup as git 

1. `git init`
2. `git checkout -b master`
3. `git add .`
4. `git commit -a -m "project setup"`
5. Create a new EMPTY repo on your git account
6. `git remote add origin https://github.com/ertemann/dex-agg-tutorial.git`
7. `git push --set-upstream origin master`

You can also use the above tools to setup a CI in github to format, lint and typecheck our files using our current Poetry environment or as we do in this tutorial, setup a pre-push hook that is called when you make git commands in this environment.

You can find the hook in the home directory of this codebase under `pre-push.sh` and copy it to your github folder using `cp pre-push.sh .git/hooks/pre-push`. Just make it executable and you will always have a pretty codebase `.git/hooks/pre-push`.

You can configure what exactly black and ruff will touch in the pyproject.toml. A good example for a configuration can be found [here](https://github.com/astral-sh/ruff).

## Implementation plan and requirements

Requirements:
- Build a basic dex-aggregator API
- Query prices of token pairs from 2 DEXs
- Handle correct input validation
- Add readme to run the API locally

We can query the prices from the chain using libraries like Viem/Wagmi or straight up Python Request. For the Web API we can use the popular Django REST framework so we are future proofing if we need to add complex cache, user UIs/swagger or backends to the equation. We can handle the validation of input with some common pattern-matching and potentially a whitelisted set of token-pairs. For the Readme it is likely best to build a simple docker container so running the system locally won't be an issue.

## Setting up django

add django REST `poetry add django djangorestframework`

If you want to learn more about django it is best to take a look at the [following tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial01/) as we will be skipping over some of the basics of building an API with django. In short you should view it as a complete web-framework that uses python to host server-side functions (aka a backend) to serve, receive and store data.

To get started with django we can run: ` poetry run django-admin startproject config dex_agg_tutorial` to create the files we need to manage the API and associated models. Most importantly this creates the settings.py and urls.py files in our new config directory so we can configure the API urls that will load upon launching the app.

You can now test the Django setup using: `poetry run python dex_agg_tutorial manage.py runserver` and we should add the django restframework implementation into these settings following [this setup instruction](https://www.django-rest-framework.org/#quickstart).

1. add rest_framework to INSTALLED_APPS in settings.py
2. add an initial URL to the urlpatterns list in urls.py
3. add global access settings for the api to settings.py

``` python
# allow anyone to view the api urls/endpoints
REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"]}
```

For this tutorial we will only consider an admin user (which is standard protected under /admin) and a public view, but you can extend the access model of the API to different tiers of paid users without too much problem. You can setup different endpoints by combining "view" classes from django with the proper url setup. For extended documentation on creating and managing views in the django restframework you can navigate [here](https://www.django-rest-framework.org/api-guide/views/).

Lastly in our setup we will make a directory for our core logic to separate it from the django setup `mkdir dex_agg_tutorial/core` (and `touch dex_agg_tutorial/core/__init__.py`) after which our general setup is complete and our directory structure should look like this:

```
  dex-agg-tutorial/
  ├── dex_agg_tutorial/
  │   ├── __init__.py
  │   ├── config/
  │   │   ├── __init__.py
  │   │   ├── asgi.py
  │   │   ├── settings.py
  │   │   ├── urls.py
  │   │   └── wsgi.py
  │   ├── core/
  │   │   ├── __init__.py
  │   └── manage.py
  ├── docs/
  │   ├── ANALYSIS.md
  │   └── TUTORIAL.md
  ├── tests/
  │   └── __init__.py
  ├── poetry.lock
  ├── pyproject.toml
  └── README.md
  ```

# The core application

As discussed before our app consists of the following items: the django api and config, the logic to query the right token price and a validation setup of input and output. To simplify our coding going forward we are therefore splitting up our logic into three files and will create a set of example functions to determine our app logic. For the tutorial we are naming the files `views.py`, `validation.py` and `queries.py` which are hosted under the `/core` directory.

## building the skeleton



# Error handling/Tests


# Conclusion