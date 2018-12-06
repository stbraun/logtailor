build: clean requ
	mkdir dist
	pex -o dist/logtail.pex . -e logtail:tail --validate-entry-point

deploy: build
	cp logtail.pex /target/destination.pex

check: logtail.py reports
	pylint --rcfile=resrc/pylintrc $(PYLINT_EXTRA) logtail.py | tee reports/pylint.txt

reports:
	mkdir reports

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
