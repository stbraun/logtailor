build: clean
	pex -o logtail.pex . -e logtail:tail --validate-entry-point

deploy: build
	cp logtail.pex /target/destination.pex

.PHONY: clean
clean:
	rm -rf *.egg-info build dist $${PEX_ROOT}/build/logtail-*.whl
