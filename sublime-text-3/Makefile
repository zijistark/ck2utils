SOURCE_DIR:=$(REPO_ROOT)/ck2utils/sublime-text-3
INSTALL_DIR:="$(shell cygpath $$APPDATA)"/"Sublime Text 3"/Packages/User

all:
	# cd $(SOURCE_DIR) && \
	# for i in \
	# 	CK2_EMF-MiniSWMH.sublime-syntax \
	# 	CK2_EMF-SWMH.sublime-syntax \
	# 	CK2_MiniSWMH.sublime-syntax \
	# 	CK2_EMF-Vanilla.sublime-syntax \
	# 	CK2_SWMH.sublime-syntax ; \
	# do cp CK2.sublime-syntax $$i -vf ; done 
	# $(SOURCE_DIR)/update_syntax_vars.py
	rsync -rthhi \
		--exclude=/*/ \
		--exclude=/.*/ \
		--exclude=/*.sublime-settings \
		--exclude=/Makefile \
		--exclude=/update_syntax_vars.py \
		$(SOURCE_DIR)/ $(INSTALL_DIR)/

reverse:
	rsync -thhi \
		$(INSTALL_DIR)/CK2script.sublime-syntax \
		$(INSTALL_DIR)/CK2script.tmPreferences \
		$(INSTALL_DIR)/Zizzle.tmTheme \
		$(SOURCE_DIR)/
