all:

install:
	mkdir -p $(DESTDIR)/usr/share/iscsi-ansible/

	cp -a ansible.cfg $(DESTDIR)/usr/share/iscsi-ansible/
	cp -a *.yml $(DESTDIR)/usr/share/iscsi-ansible/
	cp -a group_vars $(DESTDIR)/usr/share/iscsi-ansible/
	cp -a plugins $(DESTDIR)/usr/share/iscsi-ansible/
	cp -a roles $(DESTDIR)/usr/share/iscsi-ansible/
	cp -a hosts $(DESTDIR)/usr/share/iscsi-ansible/

uninstall:
	rm -rf $(DESTDIR)/usr/share/iscsi-ansible