# Passos para execução local do projeto

## Criar e habilitar um ambiente virtual Python

Referência: https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/

Criação:

```
python3 -m venv venv
```

Habilitação (Linux - para outros SOs, ver a referência)

```
source env/bin/activate
```

## Instalação das dependências

Referência: https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/

```
pip install -r requirements.txt
```

## Rodar a aplicação

```
streamlit run Dashboard-NFe.py
```