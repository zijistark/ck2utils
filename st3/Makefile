SOURCE_DIR:=$(REPO_ROOT)/ck2utils/st3
INSTALL_DIR:="$(shell cygpath $$APPDATA)"/"Sublime Text 3"/Packages/User

all:
	rsync -rthhi \
		--exclude=/*/ \
		--exclude=/.*/ \
		--exclude=/Makefile \
		--exclude=/*.p{l,y} \
		$(SOURCE_DIR)/ $(INSTALL_DIR)/

reverse:
	rsync -thhi \
		$(INSTALL_DIR)/{CK2script,ZCK,HoI4}.sublime-syntax \
		$(INSTALL_DIR)/{CK2script,ZCK,HoI4}.tmPreferences \
		$(INSTALL_DIR)/Zizzle.tmTheme \
		$(SOURCE_DIR)/
