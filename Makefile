
REPORTS_DIR = reports
TEST_REPORT = $(REPORTS_DIR)/unittests.xml
PYLINT_REPORT = $(REPORTS_DIR)/pylint.txt


build: clean requ check test
	mkdir dist
	pex -o dist/logtail.pex . -e logtail:tail --validate-entry-point

deploy: build
	cp logtail.pex /target/destination.pex

check: logtail.py reports
	pylint --rcfile=resrc/pylintrc $(PYLINT_EXTRA) logtail.py test_logtail.py | tee $(PYLINT_REPORT)

test: logtail.py reports
	pytest --doctest-modules --junit-xml=$(TEST_REPORT) $(TEST_EXTRA) test_logtail.py

.PHONY: reports
reports:
	mkdir -p reports

.PHONY: requ
requ:
	pip install -r requirements.txt

.PHONY: venv
venv:
	/usr/local/Cellar/python3/3.7.1/bin/python3.7 -m venv venv

.PHONY: clean
clean:
	rm -rf *.egg-info build dist
	rm -f $${PEX_ROOT}/build/logtail-*.whl
	rm -f target.txt
	rm -rf reports
	rm -rf __pycache__
