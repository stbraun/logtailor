build: requ clean logtail.py
	mkdir dist
	pex -o dist/logtail.pex . -e logtail:tail --validate-entry-point

deploy: build
	cp logtail.pex /target/destination.pex

requ: requirements.txt
	pip install -r requirements.txt

.PHONY: venv
venv:
	/usr/local/Cellar/python3/3.7.1/bin/python3.7 -m venv venv

.PHONY: clean
clean:
	rm -rf *.egg-info build dist $${PEX_ROOT}/build/logtail-*.whl
	rm -rf dist/
	rm -f target.txt
