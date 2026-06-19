install:
	@python3 -m pip install --upgrade pip
	@pip install pygame flake8 mypy matplotlib

run:
	@python3 fly_in.py config.txt

debug:
	@python3 -m pdb fly_in.py config.txt

clean:
	@rm -rf __pycache__ */__pycache__
	@rm -rf .mypy_cache

lint:
	@flake8 .
	@mypy . --warn-return-any \
	--warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs \
	--check-untyped-defs

.PHONY: install clean lint debug run
