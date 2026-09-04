.PHONY: build install clean deb

build:
	dpkg-buildpackage -b -us -uc

install: build
	sudo dpkg -i ../vibevi_*.deb
	sudo apt install -f

clean:
	rm -rf build/ debian/vibevi/ debian/.debhelper/ debian/files
	rm -f ../vibevi_*.deb ../vibevi_*.changes ../vibevi_*.buildinfo

deb: build
