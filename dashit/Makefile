build-optimize-guides:
	go build -o optimize_guides

install: build-optimize-guides
	cd dashit-seq && $(MAKE) install-develop
	cd dashit-reads && $(MAKE) install-develop
