from flask import Flask, render_template, request, redirect, url_for, flash
import ldap3
    
ex_server = ldap3.Server('ldap://s-exch2.gusev.int:389', get_info=ldap3.ALL)
ex_conn = ldap3.Connection(ex_server, user='v.titov@GUSEV.INT', password='cegthgfhjkm2014', auto_bind=True)
ex_conn.search('DC=GUSEV,DC=INT', '(objectClass=msExchMailbox)', attributes=['distinguishedName'])
mailboxes = {mb['entry_dn']: mb for mb in ex_conn.entries}

