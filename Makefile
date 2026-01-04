run:
	sudo resolvectl flush-caches

	sudo \
	/home/${USER}/Development/dns/.venv/bin/python3.10 \
	/home/${USER}/Development/dns/app.py