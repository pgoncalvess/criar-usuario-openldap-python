import csv

def main():
   with open('usuario.csv', 'rb') as ficheiro:
      reader = csv.reader(ficheiro, delimiter=';')
      for linha in reader:
         print linha

if __name__ == '__main__':
    main()
    