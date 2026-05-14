# Make!Mana

Projeto organizado em duas areas principais:

- `Frontend/`: templates HTML, CSS, JavaScript e imagens.
- `Backend/`: aplicacao Flask, modelos, dados, testes, dependencias e configuracao de deploy.

## Como executar localmente

Na raiz do projeto:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app Backend.app run
```

Depois acesse:

- Site: `http://127.0.0.1:5000/`
- Carrinho/pedido: `http://127.0.0.1:5000/pedido`
- Perfil: `http://127.0.0.1:5000/perfil`
- Admin: `http://127.0.0.1:5000/admin`

Credenciais padrao de desenvolvimento:

- Usuario: `admin`
- Senha: `admin123`

## Testes

```powershell
python -m pip install -r Backend\requirements-dev.txt
python -m pytest
```
