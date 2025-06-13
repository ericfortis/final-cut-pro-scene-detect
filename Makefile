PYTHON=python3
SRC_DIR=src
TEST_DIR=tests

test:
	PYTHONPATH=$(SRC_DIR) $(PYTHON) -m unittest discover -s $(TEST_DIR) -v

.PHONY: *
