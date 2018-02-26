
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

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Geracao de usuario OpenLDAP'

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'geracao-usuario-openldap.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Armazenando credenciais ' + credential_path)
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
    print 'Ocorreu um erro: %s' % error

def main():

   documento = 'usuarios.csv'

   #LDAP server configs
   server = "ldap://localhost:389"
   username = 'cn=Manager,dc=example,dc=com'
   password = 'secret'
   dn_base = "dc=example,dc=com"

   #Gmail configs
   sender = 'pedro.goncalves@mercadobackoffice.com'
   subject = 'Novo usuario'
   user_id = 'me'

   #Parametros de conexao
   connection_string = {
      'user': 'root',
      'password': '',
      'host': '127.0.0.1',
      'database': 'testeInternalSistem',
      'port': '3306'
   }

   print('Abrindo arquivo')
   if sum(1 for line in open(documento)) == 0:
      print('Nenhuma linha encontrada no arquivo')
   else:
      with open(documento, 'rb') as ficheiro:
         reader = csv.reader(ficheiro, delimiter=';')
         
         print('Lendo linhas')
         cnx = mysql.connector.connect(**connection_string)
         cursor = cnx.cursor()

         for linha in reader:
            print(linha)
            try:
               usuario = linha[0] + "." + linha[1]
               senha = novaSenha()
               dn = "cn=" + usuario + "," + dn_base

               attrs = {}
               attrs['objectclass'] = ['top','person']
               attrs['cn'] = usuario
               attrs['description'] = 'usuario1'
               attrs['sn'] = linha[1]
               attrs['userPassword'] = hashlib.md5(senha).hexdigest()

               print('Criando registro LDAP')
               l = ldap.initialize(server)
               l.protocol_version = ldap.VERSION3
               l.bind_s(username, password)
               ldif = modlist.addModlist(attrs)

               l.add_s(dn, ldif)

               l.unbind()
               print('Registro LDAP criado. Usuario: ' + usuario)

               print('Preparando envio de email')
               credentials = get_credentials()
               http = credentials.authorize(httplib2.Http())
               service = discovery.build('gmail', 'v1', http=http)

               msg_txt = "Seu usuario e '" + usuario + "' e sua senha '" + senha + "'"
               msg = create_message(sender, linha[2], subject, msg_txt)
               send_message(service, user_id, msg)
               print('Email enviado')

               print('Salvando usuario no banco de dados')
               insert_clause = "INSERT INTO usuario (nome, sobrenome, usuario, senha, estado) values (%s, %s, %s, %s, %s)"
               values = (linha[0], linha[1], usuario,attrs['userPassword'], True)
               cursor.execute(insert_clause, values)
               print('Usuario salvo')
            except ldap.LDAPError, e:
               print e

         cnx.commit()
         cursor.close()
         cnx.close()

if __name__ == '__main__':
    main()
    