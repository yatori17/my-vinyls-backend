# Vinyl API

API REST desenvolvida em Flask para gerenciamento de uma coleção pessoal de vinis, incluindo integração com a API externa do Discogs para busca de álbuns.

## Funcionalidades

- CRUD completo de discos de vinil (criar, listar, atualizar, remover)
- Busca de álbuns na base de dados do Discogs (API externa)
- Persistência em banco de dados relacional via SQLAlchemy

## Tecnologias

- Python 3.x
- Flask
- SQLAlchemy
- Discogs API

## Pré-requisitos

- Python 3.10+ instalado
- Docker (opcional, para execução via container)

## Instalação

1. Clone o repositório:
```bash
   git clone <url-do-repositorio>
   cd my-vinyls-backend
```

2. Crie e ative um ambiente virtual:
```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
   pip install -r requirements.txt
```

4. Configure a variável de ambiente do Discogs (substitua pelo seu token pessoal obtido em discogs.com/settings/developers):

# No Windows (PowerShell)
$env:DISCOGS_TOKEN="seu_token_do_discogs_aqui"

# No Linux/Mac
export DISCOGS_TOKEN="seu_token_do_discogs_aqui"

5. Execute a aplicação:
```bash
   python app.py
```

A API estará disponível em `http://localhost:5000`. A documentação interativa (Swagger) estará disponível em `http://localhost:5000/openapi`.

## Executando com Docker

```bash
docker build -t vinyl-backend .
docker run -d -p 5000:5000 -e DISCOGS_TOKEN="seu_token_do_discogs_aqui" --name vinyl-backend-container vinyl-backend
```

## Rotas disponíveis

| Método | Rota              | Descrição                          |
|--------|-------------------|-------------------------------------|
| GET    | `/vinyls`          | Lista todos os discos               |
| POST   | `/vinyl`           | Adiciona um novo disco              |
| PUT    | `/vinyl/<id>`      | Atualiza um disco existente         |
| DELETE | `/vinyl/<id>`      | Remove um disco                     |
| GET    | `/external-vinyl`  | Busca álbuns na API do Discogs      |

## API Externa

Este projeto consome a [Discogs API](https://www.discogs.com/developers) para busca de álbuns.

- **Autenticação**: requer um token pessoal (gratuito), obtido em [discogs.com/settings/developers](https://www.discogs.com/settings/developers)
- **Licença de uso**: gratuita para uso pessoal/não comercial, conforme os [termos da Discogs API](https://www.discogs.com/developers)
- **Rota utilizada**: `GET /database/search` (busca de releases por nome/artista)