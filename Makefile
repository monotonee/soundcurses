PWD=$(shell pwd)
TEST_DIR=$(PWD)/tests

.PHONY: all test

test: $(TEST_DIR)
	python -m unittest -v $</*.py
