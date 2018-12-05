build: requ
	mkdir dist
	pex -o dist/logtail.pex . -e logtail:tail --validate-entry-point

deploy: build
	cp logtail.pex /target/destination.pex

venv: clean
	/usr/local/Cellar/python3/3.7.1/bin/python3.7 -m venv venv

activate: venv
	source venv/bin/activate

requ: activate, requirements.txt
	pip install -r requirements.txt

.PHONY: clean
clean:
	rm -rf *.egg-info build dist $${PEX_ROOT}/build/logtail-*.whl
	rm -rf dist/
	rm -f target.txt
