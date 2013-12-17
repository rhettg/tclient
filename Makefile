.PHONY: all flake8 clean dev

GITIGNORES=$(shell cat .gitignore |tr "\\n" ",")

all: flake8

flake8: .gitignore env
	@bin/virtual-env-exec flake8 . --exclude=$(GITIGNORES)

dev: env env/.pip

env:
	@virtualenv --distribute env

env/.pip: env cfg/requirements.txt
	@bin/virtual-env-exec pip install -r cfg/requirements.txt
	@bin/virtual-env-exec pip install -e .
	@touch env/.pip

test: env/.pip
	@bin/virtual-env-exec testify tests

shell:
	@bin/virtual-env-exec ipython

devclean:
	@rm -rf env

clean:
	@rm -rf build dist env
