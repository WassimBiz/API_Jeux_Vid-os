import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from datetime import datetime
from typing import List, Optional
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pymongo import MongoClient, ReturnDocument
from bson import ObjectId

# ==========================
#  CONFIG MONGODB
# ==========================

MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "game_collection_db"
COLLECTION_NAME = "games"

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
games_collection = db[COLLECTION_NAME]

# ==========================
#  APP FASTAPI
# ==========================

app = FastAPI(title="Game Collection API")

# ----------- FRONTEND (fichiers statiques) --------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/", include_in_schema=False)
def root():
    """
    Redirige la racine / vers la page HTML frontend.
    """
    return RedirectResponse(url="/frontend/index.html")

# ==========================
#  SCHEMAS / MODELES
# ==========================

class GameBase(BaseModel):
    titre: str = Field(..., min_length=1)
    genre: List[str] = Field(..., min_length=1)
    plateforme: List[str] = Field(..., min_length=1)
    editeur: Optional[str] = None
    developpeur: Optional[str] = None
    annee_sortie: Optional[int] = Field(
        None, ge=1970, le=datetime.utcnow().year
    )
    metacritic_score: Optional[int] = Field(None, ge=0, le=100)
    temps_jeu_heures: Optional[float] = Field(None, ge=0)
    termine: bool = False


class GameCreate(GameBase):
    """Données attendues pour la création d'un jeu."""
    pass


class GameUpdate(BaseModel):
    """Données pour la mise à jour (tous les champs optionnels)."""
    titre: Optional[str] = Field(None, min_length=1)
    genre: Optional[List[str]] = Field(None, min_length=1)
    plateforme: Optional[List[str]] = Field(None, min_length=1)
    editeur: Optional[str] = None
    developpeur: Optional[str] = None
    annee_sortie: Optional[int] = Field(
        None, ge=1970, le=datetime.utcnow().year
    )
    metacritic_score: Optional[int] = Field(None, ge=0, le=100)
    temps_jeu_heures: Optional[float] = Field(None, ge=0)
    termine: Optional[bool] = None
    favori: Optional[bool] = None


class GameOut(GameBase):
    """Ce qu'on renvoie au client."""
    id: str
    date_ajout: datetime
    date_modification: datetime
    favori: bool = False

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class FavoriteUpdate(BaseModel):
    favori: bool = True


# ==========================
#  UTILITAIRES
# ==========================

def validate_object_id(game_id: str) -> ObjectId:
    """Vérifie que l'id est un ObjectId valide."""
    if not ObjectId.is_valid(game_id):
        raise HTTPException(status_code=400, detail="ID invalide")
    return ObjectId(game_id)


def game_document_to_out(doc: dict) -> GameOut:
    """Convertit un document MongoDB en GameOut."""
    return GameOut(
        id=str(doc["_id"]),
        titre=doc["titre"],
        genre=doc["genre"],
        plateforme=doc["plateforme"],
        editeur=doc.get("editeur"),
        developpeur=doc.get("developpeur"),
        annee_sortie=doc.get("annee_sortie"),
        metacritic_score=doc.get("metacritic_score"),
        temps_jeu_heures=doc.get("temps_jeu_heures"),
        termine=doc.get("termine", False),
        date_ajout=doc["date_ajout"],
        date_modification=doc["date_modification"],
        favori=doc.get("favori", False),
    )


# ==========================
#  ENDPOINTS CRUD DE BASE
# ==========================

@app.post("/api/games", response_model=GameOut, status_code=201)
def create_game(game: GameCreate):
    """
    POST /api/games
    Ajouter un nouveau jeu.
    """
    now = datetime.utcnow()
    doc = game.dict()
    doc["date_ajout"] = now
    doc["date_modification"] = now
    doc["favori"] = False

    result = games_collection.insert_one(doc)
    created = games_collection.find_one({"_id": result.inserted_id})
    return game_document_to_out(created)


@app.get("/api/games", response_model=List[GameOut])
def list_games(
    genre: Optional[str] = Query(None),
    plateforme: Optional[str] = Query(None),
    termine: Optional[bool] = Query(None),
    favori: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Recherche dans le titre"),
    annee_min: Optional[int] = Query(None),
    annee_max: Optional[int] = Query(None),
):
    """
    GET /api/games
    Lister tous les jeux, avec filtrage possible :
    - /api/games?genre=RPG&plateforme=PC
    - /api/games?termine=true
    - /api/games?search=Zelda
    """
    query: dict = {}

    if genre:
        query["genre"] = genre          # champ tableau → match si le genre est présent
    if plateforme:
        query["plateforme"] = plateforme
    if termine is not None:
        query["termine"] = termine
    if favori is not None:
        query["favori"] = favori
    if search:
        query["titre"] = {"$regex": search, "$options": "i"}
    if annee_min is not None or annee_max is not None:
        query["annee_sortie"] = {}
        if annee_min is not None:
            query["annee_sortie"]["$gte"] = annee_min
        if annee_max is not None:
            query["annee_sortie"]["$lte"] = annee_max

    docs = games_collection.find(query).sort("date_ajout", -1)
    return [game_document_to_out(doc) for doc in docs]


@app.get("/api/games/{game_id}", response_model=GameOut)
def get_game(game_id: str):
    """
    GET /api/games/{id}
    Obtenir un jeu spécifique.
    """
    oid = validate_object_id(game_id)
    doc = games_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    return game_document_to_out(doc)


@app.put("/api/games/{game_id}", response_model=GameOut)
def update_game(game_id: str, game_update: GameUpdate):
    """
    PUT /api/games/{id}
    Modifier un jeu (mise à jour partielle).
    """
    oid = validate_object_id(game_id)
    update_data = {
        k: v
        for k, v in game_update.dict(exclude_unset=True).items()
    }
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    update_data["date_modification"] = datetime.utcnow()

    result = games_collection.find_one_and_update(
        {"_id": oid},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")

    return game_document_to_out(result)


@app.delete("/api/games/{game_id}", status_code=204)
def delete_game(game_id: str):
    """
    DELETE /api/games/{id}
    Supprimer un jeu.
    """
    oid = validate_object_id(game_id)
    result = games_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    return JSONResponse(status_code=204, content=None)


# ==========================
#  FAVORIS
# ==========================

@app.post("/api/games/{game_id}/favorite", response_model=GameOut)
def set_favorite(game_id: str, fav: FavoriteUpdate):
    """
    POST /api/games/{id}/favorite
    Permet de marquer / dé-marquer un jeu en favori.
    Body JSON :
    { "favori": true }  ou  { "favori": false }
    """
    oid = validate_object_id(game_id)
    result = games_collection.find_one_and_update(
        {"_id": oid},
        {
            "$set": {
                "favori": fav.favori,
                "date_modification": datetime.utcnow(),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    return game_document_to_out(result)


# ==========================
#  STATISTIQUES
# ==========================

@app.get("/api/stats")
def get_stats():
    """
    GET /api/stats
    Retourne des stats globales :
    - nombre total de jeux
    - temps de jeu total
    - moyenne Metacritic
    - nombre de jeux terminés
    """
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_games": {"$sum": 1},
                "total_playtime": {
                    "$sum": {"$ifNull": ["$temps_jeu_heures", 0]}
                },
                "avg_metacritic": {"$avg": "$metacritic_score"},
                "finished_games": {
                    "$sum": {
                        "$cond": [{"$eq": ["$termine", True]}, 1, 0]
                    }
                },
            }
        }
    ]

    agg = list(games_collection.aggregate(pipeline))
    if not agg:
        return {
            "total_games": 0,
            "total_playtime": 0,
            "avg_metacritic": None,
            "finished_games": 0,
        }

    data = agg[0]
    return {
        "total_games": data.get("total_games", 0),
        "total_playtime": data.get("total_playtime", 0),
        "avg_metacritic": data.get("avg_metacritic"),
        "finished_games": data.get("finished_games", 0),
    }


# ==========================
#  EXPORT DES DONNÉES
# ==========================

@app.get("/api/games/export", response_model=List[GameOut])
def export_games():
    """
    GET /api/games/export
    Exporte tous les jeux (format JSON).
    """
    docs = games_collection.find({})
    return [game_document_to_out(doc) for doc in docs]
