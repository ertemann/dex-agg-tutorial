Welcome to this small tutorial on building a crypto dex aggregator in Python

# pre-requisites/Setup

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

Before continuing we will also quickly setup a CI in github to format, lint and typecheck our files using our current Poetry environment. 

`mkdir .github/workflows` and create a file called ci.yml (`echo ci.yml`). You can copy the content from the ci.yml file in this repository or set up your own system. You can also configure what exactly black and ruff will touch in the pyproject.toml. A good example for a configuration can be found [here](https://github.com/astral-sh/ruff).


## making a plan

Requirements:
- Build a basic dex-aggregator API
- Query prices of token pairs from 2 DEX
- Handle correct input validation
- Add readme to run the API locally

We can query the prices from the chain using libraries like Viem/Wagmi or straight up Python Request. For the Web API we can use the popular Django REST framework so we are future proofing if we need to add complex cache, user UIs/swagger or backends to the equation. We can handle the validation of input with some common pattern-matching and potentially a whitelisted set of token-pairs. For the Readme its likely best to build a simple docker container so running the system locally won't be an issue.

add django REST `poetry add django djangorestframework`

If you want to learn more about django it is best to take a look at the [following tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial01/) as we will be skipping over some of the basics of building an API with django.

To get started with django we can run: ` poetry run django-admin startproject config dex_agg_tutorial` to create the files we need to manage the API and associated models. Most importantly this creates the settings.py and urls.py files in our new config directory so we can configure the API urls that will load upon launching the app.

You can now test the Django setup using: `poetry run python dex_agg_tutorial manage.py runserver`

# Core Logic/Guide


# Error handling/Tests


# Conclusion