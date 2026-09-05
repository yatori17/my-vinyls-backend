from flask import Flask, jsonify, request
from flask_openapi3 import OpenAPI, Info, Tag
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError

from model import Session, Vinyl
from schemas import *

info = Info(title="Virtual Digging API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

# Defining tags for Swagger documentation
home_tag = Tag(name="Documentation", description="API Documentation")
vinyl_tag = Tag(name="Vinyl", description="Management of the vinyl record collection")

@app.get('/', tags=[home_tag])
def home():
    """Redirects to OpenAPI/Swagger documentation."""
    return jsonify({"message": "Welcome to the Virtual Digging API! Access /openapi/swagger to view the documentation."}), 200


@app.get('/vinyls', tags=[vinyl_tag], responses={"200": ListVinylsSchema, "400": ErrorSchema})
def get_vinyls():
    """Lists all vinyl records registered in the collection."""
    try:
        session = Session()
        vinyls = session.query(Vinyl).all()
        session.close()

        if not vinyls:
            return {"vinyls": []}, 200

        return present_vinyls(vinyls), 200
    except Exception as e:
        return {"mesg": f"Could not retrieve vinyls: {str(e)}"}, 400


@app.post('/vinyl', tags=[vinyl_tag], responses={"201": VinylViewSchema, "400": ErrorSchema})
def add_vinyl(body: VinylSchema):
    """Adds a new vinyl record to the collection."""
    vinyl = Vinyl(
        name=body.name,
        genre=body.genre,
        year=body.year,
        artist=body.artist,
        conservation_state=body.conservation_state
    )
    try:
        session = Session()
        session.add(vinyl)
        session.commit()
        
        result = present_vinyl(vinyl)
        session.close()
        return result, 201
    except IntegrityError as e:
        session.rollback()
        session.close()
        return {"mesg": "Database integrity error."}, 400
    except Exception as e:
        session.rollback()
        session.close()
        return {"mesg": f"Could not save the new vinyl: {str(e)}"}, 400


@app.get('/vinyl', tags=[vinyl_tag], responses={"200": VinylViewSchema, "404": ErrorSchema})
def get_vinyl(query: VinylSearchSchema):
    """Searches for a specific vinyl by album name or artist."""
    vinyl_name = query.name
    try:
        session = Session()
        vinyl = session.query(Vinyl).filter(Vinyl.name.like(f"%{vinyl_name}%")).first()
        
        if not vinyl:
            session.close()
            return {"mesg": "Vinyl not found in the collection."}, 404
        
        result = present_vinyl(vinyl)
        session.close()
        return result, 200
    except Exception as e:
        return {"mesg": f"Error searching for vinyl: {str(e)}"}, 400


@app.put('/vinyl/<int:id>', tags=[vinyl_tag], responses={"200": VinylViewSchema, "404": ErrorSchema, "400": ErrorSchema})
def update_vinyl(path: VinylPath, body: VinylUpdateSchema):
    """Updates an existing vinyl's information by ID."""
    try:
        session = Session()
        # Usa o ID que veio na URL através do path.vinyl_id
        vinyl = session.query(Vinyl).filter(Vinyl.id == path.id).first()
        
        if not vinyl:
            session.close()
            return {"mesg": "Vinyl not found for update."}, 404
            
        vinyl.name = body.name
        vinyl.genre = body.genre
        vinyl.year = body.year
        vinyl.artist = body.artist
        vinyl.conservation_state = body.conservation_state
        
        session.commit()
        result = present_vinyl(vinyl)
        session.close()
        return result, 200
    except Exception as e:
        session.rollback()
        session.close()
        return {"mesg": f"Could not update vinyl: {str(e)}"}, 400
    
    
    
@app.delete('/vinyl/<int:id>', tags=[vinyl_tag], responses={"200": VinylViewSchema, "404": ErrorSchema})
def delete_vinyl(path: VinylPath):
    """Removes a vinyl from the collection using its ID."""
    vinyl_id = path.id
    try:
        session = Session()
        vinyl = session.query(Vinyl).filter(Vinyl.id == vinyl_id).first()
        
        if not vinyl:
            session.close()
            return {"mesg": "Vinyl not found for removal."}, 404
            
        session.delete(vinyl)
        session.commit()
        session.close()
        
        return {"mesg": "Vinyl successfully removed", "id": vinyl_id}, 200
    except Exception as e:
        session.rollback()
        session.close()
        return {"mesg": f"Could not remove vinyl: {str(e)}"}, 400


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)