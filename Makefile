VENV=. venv/bin/activate

# Python venv environment
venv/bin/activate: requirements.txt
	test -d venv || python3 -m venv venv
	$(VENV); pip install -Ur requirements.txt
	touch venv/bin/activate

setup: $(VENV) 
	mkdir instance

# Run web
run: $(VENV)
	./run_web.sh