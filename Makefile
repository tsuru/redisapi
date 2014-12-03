clean:
	@find . -name "*.pyc" -delete
deps:
	@pip install -r requirements.txt

test-deps:
	@pip install -r test_requirements.txt

test: test-deps
	@python -m unittest discover
	@flake8 .
