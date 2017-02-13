PIP_OPTIONS = --user
RELEASE_OPENPGP_FINGERPRINT ?= C505B5C93B0DB3D338A1B6005FE92C12EE88E1F0
RELEASE_OPENPGP_CMD ?= gpg
PYPI_REPO ?= pypi
NOSETESTS ?= $(shell command -v nosetests3 nosetests | head -n 1)
NOSE2 ?= $(shell command -v nose2-3 nose2-3.4 | head -n 1)
SHELL := /bin/bash
PYTHON_VERSION := $(shell python -c "import sys;t='{v[0]}.{v[1]}'.format(v=list(sys.version_info[:2]));sys.stdout.write(t)")

.PHONY: FORCE_MAKE

.PHONY: default
default: list

## list targets (help) {{{
.PHONY: list
# https://stackoverflow.com/a/26339924/2239985
list:
	@echo "This Makefile has the following targets:"
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^(:?[^[:alnum:]]|FORCE_MAKE$$)' -e '^$@$$' | sed 's/^/    /'
## }}}

## Git hooks {{{
.PHONY: install-pre-commit-hook
install-pre-commit-hook: ./dev/hooks/pre-commit
	ln -srf "$<" "$(shell git rev-parse --git-dir)/hooks"

.PHONY: run-pre-commit-hook
run-pre-commit-hook: ./dev/hooks/pre-commit
	"$<"

.PHONY: remove-pre-commit-hook
remove-pre-commit-hook:
	rm -f "$(shell git rev-parse --git-dir)/hooks/pre-commit"
## }}}

## check {{{
.PHONY: check
check: check-unit-tests-with-coverage check-integration-tests check-docs check-lint

# TODO
.PHONY: check-tox
check-tox:
	tox

.PHONY: check-docs
check-docs:
	$(MAKE) "docs" > /dev/null

.PHONY: check-lint
check-lint: check-flake8 check-pylint check-travis.yml

.PHONY: check-flake8
check-flake8:
	flake8 .

.PHONY: check-pylint
check-pylint: yaml4rst/
	if [[ "$(PYTHON_VERSION)" == "3.6" ]]; then \
		echo "Skip test as pylint had issues with this version"; \
	else \
		pylint "$<" --reports=n --rcfile .pylintrc --disable=C,I,R; \
	fi

.PHONY: check-pylint-tests
check-pylint-tests: tests/
	pylint "$<" --reports=n --rcfile .pylintrc --disable=protected-access,missing-docstring,invalid-name,too-many-public-methods,too-many-lines

.PHONY: check-radon
check-radon: yaml4rst/
	radon cc "$<" --total-average

.PHONY: check-travis.yml
check-travis.yml: .travis.yml
	yamllint "$<"

.PHONY: check-nose
check-nose:
	$(NOSETESTS)

.PHONY: check-unit-tests
check-unit-tests: check-nose

.PHONY: check-unit-tests-with-coverage
check-unit-tests-with-coverage:
	$(NOSETESTS) --with-coverage --cover-package yaml4rst --cover-branches --cover-erase --cover-min-percentage=100

.PHONY: check-integration-tests
check-integration-tests: prepare-real-data check-real-data

# Copy over test files:
# find . -type f  -regex '.*defaults/main\.yml$' | while read -r dfile; do name="$(echo "$dfile" | sed --regexp-extended 's#.*/([^/.]+\.[^/]+)/.+#\1#')"; cp "$dfile" "${HOME}/.ansible/yaml4rst/tests/input_files/${name}.yml"; done

.PHONY: prepare-real-data
prepare-real-data: ./tests/raw_input_files
	for raw_input_file in "$<"/*; do \
		echo "Preparing $$raw_input_file"; \
		io_file="./tests/input_files/$$(basename "$$raw_input_file")"; \
		sed --regexp-extended '/^(\s*#\s*(\.{2})?\s*.*?)\s*[[({]{3}[[:digit:]]*$$/d;' "$$raw_input_file" > "$$io_file"; \
	done

.PHONY: check-real-data
check-real-data: ./tests/input_files
	rm -f ./tests/output_files/*
	if git diff --quiet -- tests/output_files/; then exit 3; fi
	for input_file in "$<"/*; do \
		echo "Checking $$input_file"; \
		output_file="./tests/output_files/$$(basename "$$input_file")"; \
		full_role_name="$$(basename "$$input_file")"; \
		yaml4rst -q -n -e "ansible_full_role_name=$${full_role_name%.*}" "$$input_file" -o "$$output_file"; \
		yaml4rst -q -n -e "ansible_full_role_name=$${full_role_name%.*}" "$$output_file" -o "$$output_file.check_idempotency"; \
		if ! diff "$$output_file" "$$output_file.check_idempotency"; then \
			echo "Failed: diff $$output_file $$output_file.check_idempotency"; \
			exit 2; \
		fi; \
		rm "$$output_file.check_idempotency"; \
	done
	git diff --quiet -- tests/output_files/
	git add tests/output_files/

# Does not work on Travis, different versions. Using check-nose for now.
.PHONY: check-nose2
check-nose2:
	$(NOSE2) --start-dir tests

.PHONY: check-fixmes
check-fixmes:
	ag '(:?[F]IXME|[T]ODO|[n]ottest)' --ignore 'yaml4rst/defaults.py' && exit 1 || :

## }}}

## development {{{

.PHONY: clean
clean:
	find . -name '*.py[co]' -delete
	rm -rf *.egg *.egg-info

.PHONY: distclean
distclean: clean
	rm -rf build dist dist_signed .coverage

.PHONY: build
build: setup.py
	"./$<" bdist_wheel sdist

.PHONY: install-dev
install-dev: setup.py
	pip3 install "$(PIP_OPTIONS)" --editable . --no-deps

.PHONY: docs
docs:
	if [[ "$(PYTHON_VERSION)" == "3.3" ]]; then \
		echo "Skip test as sphinx has dropped support for this version"; \
	else \
		$(MAKE) -C "docs" html; \
	fi

.PHONY: release-versionbump
release-versionbump: yaml4rst/_meta.py CHANGES.rst
	editor $?
	sh -c 'git commit --all --message="Release version $$(./setup.py --version)"'

.PHONY: release-sign
release-sign: distclean build
	rm -rf dist_signed
	mv dist dist_signed
	find dist_signed -type f -regextype posix-extended -regex '^.*(:?\.(:?tar\.gz|whl))$$' -print0 \
		| xargs --null --max-args=1 $(RELEASE_OPENPGP_CMD) --default-key "$(RELEASE_OPENPGP_FINGERPRINT)" --detach-sign --armor
	git tag --sign --local-user "$(RELEASE_OPENPGP_FINGERPRINT)" --message "Released version $(shell ./setup.py --version)" "v$(shell ./setup.py --version)"

.PHONY: release-prepare
release-prepare: check release-versionbump release-sign

.PHONY: pypi-register
pypi-register: build
	twine register -r "$(PYPI_REPO)" "$(shell find dist -type f -name '*.whl' | sort | head -n 1)"

.PHONY: pypi-register
pypi-upload: build
	twine upload -r "$(PYPI_REPO)" dist_signed/*

.PHONY: git-push
git-push:
	git push --follow-tags

.PHONY: release-publish
release-publish:  pypi-register pypi-upload git-push

.PHONY: release
release: release-prepare release-publish

## }}}
