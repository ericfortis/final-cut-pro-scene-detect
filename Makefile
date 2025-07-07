SRC = fcpscene.app
OUT = .fcpscene.app

INSTALL_TO ?= ~/Desktop/fcpscene.app
# Installing to Desktop because it can't be directly to /Application or
# ~/Applications due to permissions. Actually, it partially works, because
# `open -a fcpscene.app` is fine but double-clicking it in Finder is not.

all: $(OUT)

$(OUT):
	osacompile -o $(OUT) $(SRC)/main.applescript
	cp $(SRC)/Info.plist $(OUT)/Contents/Info.plist
	cp $(SRC)/applet.icns $(OUT)/Contents/Resources/applet.icns

install: $(OUT)
	cp -R $(OUT) $(INSTALL_TO)

uninstall:
	rm -rf $(INSTALL_TO)

clean:
	rm -rf $(OUT)


test:
	python3 -m unittest discover -s tests -v


.PHONY: *
