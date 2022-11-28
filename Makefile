.DEFAULT_GOAL := all
black = black --target-version py39 refact
isort = isort --profile black refact

.PHONY: depends
depends:
	@echo "Installing OS dependencies..."
	@bash ./bin/depends.sh
	@echo "Done"

.PHONY: init
init: depends
	@echo "Setting up virtual environment in venv/"
	@python3 -m venv venv
	@echo "Virtual environment complete."

.PHONY: format
format:
	. venv/bin/activate && ( \
	$(isort)  && \
	$(black) \
	)

.PHONY: lint
lint:
	. venv/bin/activate && ( \
	mypy --show-error-codes refact ; \
	flake8 --ignore=E203,F841,E501,E722,W503 refact ; \
	$(isort) --check-only --df ; \
	$(black) --check --diff  \
	)

.PHONY: install
install: depends init
	. venv/bin/activate && ( \
	pip install -r requirements.txt ; \
	python setup.py install ; \
	python setup.py clean \
	)

.PHONY: update
update: format lint
	. venv/bin/activate && ( \
	pip freeze | grep -v refact > requirements.txt ; \
	git add README.md .gitignore setup.py docs bin refact requirements.txt Makefile ; \
	git commit --allow-empty -m "Updates" ; \
	git push origin main ; \
	python setup.py install ; \
	git status \
	)

.PHONY: docs
docs:
	cd docs
	make -C docs html

.PHONY: clean
clean:
	. venv/bin/activate && ( \
	python setup.py clean ; \
	git status \
	)

.PHONY: test
test: format lint
	. venv/bin/activate && ( \
	python3 setup.py install ; \
	pytest \
	)
	
.PHONY: all
all: format lint update docs install test clean
	git status