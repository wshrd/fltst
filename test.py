from flask import Flask, render_template, request, redirect, url_for, flash
import ldap3

app = Flask(__name__)
app.secret_key = 'mysecretkey'

# Connect to Active Directory
server = ldap3.Server('s-dc1.domain.org', get_info=ldap3.ALL)
conn = ldap3.Connection(server, user='admin@domain.org', password='password', auto_bind=True)
conn.search('OU=Accounts,DC=domain,DC=org', '(objectClass=organizationalUnit)', attributes=['distinguishedName'])
ous = [ou['distinguishedName'] for ou in conn.entries]

@app.route('/')
def index():
    return render_template('index.html', ous=ous)

@app.route('/select_user', methods=['POST'])
def select_user():
    ou = request.form.get('ou')
    conn.search(ou, '(objectClass=user)', attributes=['sAMAccountName', 'name', 'mail'])
    users = [{"samaccountname": user['sAMAccountName'], "name": user['name'], "mail": user['mail']} for user in conn.entries]
    return render_template('select_user.html', users=users)

@app.route('/set_forwarding', methods=['POST'])
def set_forwarding():
    user = request.form.get('user')
    action = request.form.get('action')
    forward_to = request.form.get('forward_to')

    # Connect to Exchange Server
    ex_server = ldap3.Server('s-dc1.domain.org', get_info=ldap3.ALL)
    ex_conn = ldap3.Connection(ex_server, user='admin@domain.org', password='password', auto_bind=True)
    ex_conn.search('DC=domain,DC=org', '(objectClass=user)', attributes=['distinguishedName', 'msExchMailboxGuid', 'sAMAccountName'])
    mailboxes = {str(mb['sAMAccountName']): mb for mb in ex_conn.entries}
    # Get user mailbox
    user_guid = [mailboxes[mb]['msExchMailboxGuid'] for mb in mailboxes if mb == user]

    if user_guid:
        user_dn = f'msExchMailboxGuid={str(user_guid[0])},DC=domain,DC=org'
    else:
        flash(f"User {user} not found.")
        return redirect(url_for('index'))



    # Set forwarding address
    if action == 'enable':
        forwarding_smtp_address = {'forwardingSmtpAddress': [(ldap3.MODIFY_REPLACE, [forward_to])]}
        deliver_to_mailbox_and_forward = {'deliverToMailboxAndForward': [(ldap3.MODIFY_REPLACE, [True])]}
        msg = f"Mail forwarding enabled for {user}. Mail will be forwarded to {forward_to}."
    elif action == 'disable':
        forwarding_smtp_address = {'forwardingSmtpAddress': [(ldap3.MODIFY_DELETE, [])]}
        deliver_to_mailbox_and_forward = {'deliverToMailboxAndForward': [(ldap3.MODIFY_REPLACE, [False])]}
        msg = f"Mail forwarding disabled for {user}."
    else:
        msg = "Invalid action."

    # Save changes
    ex_conn.modify(user_dn, {'msExchRecipientDisplayType': [(ldap3.MODIFY_REPLACE, ['UserMailbox'])], 'distinguishedName': [(ldap3.MODIFY_REPLACE, [user_dn])], 'msExchRecipientTypeDetails': [(ldap3.MODIFY_REPLACE, [1])]})
    ex_conn.modify(user_dn, forwarding_smtp_address)
    ex_conn.modify(user_dn, deliver_to_mailbox_and_forward)

    flash(msg)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
