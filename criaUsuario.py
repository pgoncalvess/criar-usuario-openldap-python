import csv
import ldap
import ldap.modlist as modlist
import hashlib
import httplib2
import os
import base64
import mysql.connector

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from email.mime.text import MIMEText
from apiclient import errors

from random import choice

try:
   import argparse
   flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
   flags = None

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python CriaUsuario'

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'gmail-cria-usuario1.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def novaSenha():
   caracters = '0123456789abcdefghijlmnopqrstuwvxz'
   senha = ''
   for x in range(6):
      senha += choice(caracters)

   return senha

def create_message(sender, to, subject, message_text):
   message = MIMEText(message_text)
   message['to'] = to
   message['from'] = sender
   message['subject'] = subject
   return {'raw': base64.urlsafe_b64encode(message.as_string())}

def send_message(service, user_id, message):
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

def main():

   documento = 'usuario_2.csv'
   #LDAP server configs
   server = "ldap://localhost:389"
   username = 'cn=Manager,dc=example,dc=com'
   password = 'secret'
   base_dn = "dc=example,dc=com"

   #Gmail configs
   sender = 'pedro.goncalves@mercadobackoffice.com'
   subject = 'Novo usuario'
   user_id = 'me'

   with open(documento, 'rb') as ficheiro:
      reader = csv.reader(ficheiro, delimiter=';')

      credentials = get_credentials()
      http = credentials.authorize(httplib2.Http())
      service = discovery.build('gmail', 'v1', http=http)

      cnx = mysql.connector.connect(user='root', password='',host='127.0.0.1',database='testeInternalSistem')
      cursor = cnx.cursor()

      for linha in reader:
         print linha
         try:
            usuario = linha[0] + "." + linha[1]
            senha = novaSenha()
            dn = "cn=" + usuario + "," + base_dn

            attrs = {}
            #attrs['objectclass'] = ['top','person','organizationalPerson', 'user']
            attrs['objectclass'] = ['top','person']
            attrs['cn'] = usuario
            attrs['description'] = 'usuario1'
            attrs['sn'] = linha[1]
            attrs['userPassword'] = hashlib.md5(senha).hexdigest()

            l = ldap.initialize(server)
            l.protocol_version = ldap.VERSION3
            l.bind_s(username, password)
            ldif = modlist.addModlist(attrs)

            l.add_s(dn, ldif)

            l.unbind()

            msg_txt = "Seu usuario e '" + usuario + "' e sua senha: '" + senha + "'"
            msg = create_message(sender, linha[2], subject, msg_txt)
            send_message(service, user_id, msg)

            cursor.execute("INSERT INTO usuario (nome, sobrenome, usuario, senha, estado) values (%s, %s, %s, %s, %s)", (linha[0], linha[1], usuario,attrs['userPassword'], True))

            print 'Usuario incluido: ' + usuario + ' e email enviado'

         except ldap.LDAPError, e:
            print e

      cnx.commit()
      cursor.close()
      cnx.close()

if __name__ == '__main__':
    main()
    