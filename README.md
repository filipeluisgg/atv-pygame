### Requisitos
Python 3.12.x instalado em seu sitema operacional.
___

### Para gerar um executável jogável

Atenção: Siga as orientações abaixo com o CMD do windows com privilégios de administrador, e não pelo powerShell.

1- Ao clonar o repositório para sua máquina, na raiz do projeto execute: `python -m venv venv` para criar um ambiente virtual.

2- Para ativar o ambiente virtual, com o terminal apontando para pasta raiz do projeto, execute: `.\venv\Scripts\activate`

3- Instale as dependencias do projeto com o comando: `pip install -r requirements.txt`

4- Com isso, para gerar o executável do jogo, execute `pyinstaller.exe --onefile --windowed --add-data "assets;assets" main.py`

Após este último comando, na pasta raiz será criada uma pasta chamada `dist`, dentro dela estará o arquivo `.exe`, basta executá-lo.

