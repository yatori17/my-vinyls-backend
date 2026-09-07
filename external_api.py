import requests
from flask import request, jsonify

DISCOGS_TOKEN = "YOUR_DISCOGS_TOKEN_HERE"

def init_external_routes(app, vinyl_tag, ErrorSchema, ListExternalVinylSchema):


    @app.get('/external-vinyl', tags=[vinyl_tag], responses={"200": ListExternalVinylSchema, "400": ErrorSchema, "500": ErrorSchema})
    def search_external_vinyl():
        """Busca discos na API externa do Discogs pelo nome do álbum ou artista."""
        query = request.args.get('query', '')
        if not query:
            return {"mesg": "Query parameter is required"}, 400

        url = f"https://api.discogs.com/database/search?q={query}&type=release"
        
        headers = {
            "User-Agent": "VirtualDiggingApp/1.0",
            "Authorization": f"Discogs token={DISCOGS_TOKEN}"
        }

        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                return {"mesg": f"Error fetching data from Discogs: status {response.status_code}"}, 500

            data = response.json()
            
            results = []
            for item in data.get('results', [])[:5]:
                results.append({
                    "title": item.get('title'),
                    "year": item.get('year'),
                    "genre": item.get('genre', []),
                    "cover_image": item.get('cover_image')
                })

            # Retorna como um dicionário contendo a chave "results" que mapeia para o schema
            return {"results": results}, 200

        except Exception as e:
            return {"mesg": f"Internal server error: {str(e)}"}, 500