VENV=. venv/bin/activate

# Python venv environment
venv/bin/activate: requirements.txt
	test -d venv || python3 -m venv venv
	$(VENV); pip install -Ur requirements.txt
	touch venv/bin/activate

# Run web
run: $(VENV)
	./run_web.sh