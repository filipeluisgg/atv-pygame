Para gerar um executável, rode o comando abaixo em um venv 
que tenha as dependencias do 'requirements.txt' instalado:

pyinstaller.exe --onefile --windowed --add-data "assets;assets" main.py

