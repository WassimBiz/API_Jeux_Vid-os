# API de Gestion de Collection de Jeux Vidéo

Petit projet de gestion de collection de jeux vidéo avec :

- **Backend** : FastAPI (Python) + MongoDB
- **Base de données** : MongoDB (`game_collection_db`, collection `games`)
- **Frontend léger** : page HTML/JS statique pour tester l'API

---

## 1. Prérequis

- Python 3.10+ installé (testé avec Python 3.12)
- MongoDB en local, accessible sur : `mongodb://localhost:27017`

Python :  
```bash
python --version




2. Installation

Depuis le dossier du projet :

pip install fastapi uvicorn pymongo

3. Structure du projet
TP NoSQL/
│  main.py              # Backend FastAPI + connexion MongoDB
│  README.md
│
└─frontend/
      index.html        # Petite interface HTML/JS pour tester l'API

4. Lancement du serveur

Depuis la racine du projet :

uvicorn main:app --reload


Par défaut :

API : http://127.0.0.1:8000

Interface Swagger (docs auto) : http://127.0.0.1:8000/docs

Frontend HTML :

via redirection : http://127.0.0.1:8000/

ou directement : http://127.0.0.1:8000/frontend/index.html

5. Configuration MongoDB

Dans main.py :

MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "game_collection_db"
COLLECTION_NAME = "games"


La collection utilisée est games.
Les documents ont la structure suivante :

{
  "_id": ObjectId,
  "titre": "string",
  "genre": ["string"],
  "plateforme": ["string"],
  "editeur": "string",
  "developpeur": "string",
  "annee_sortie": 2020,
  "metacritic_score": 90,
  "temps_jeu_heures": 25.5,
  "termine": true,
  "date_ajout": "datetime",
  "date_modification": "datetime",
  "favori": false
}

6. Endpoints principaux
6.1 CRUD Jeux

POST /api/games
Créer un jeu.

Exemple de body JSON :

{
  "titre": "Hades",
  "genre": ["Rogue-lite", "Action"],
  "plateforme": ["PC", "Nintendo Switch"],
  "editeur": "Supergiant Games",
  "developpeur": "Supergiant Games",
  "annee_sortie": 2020,
  "metacritic_score": 93,
  "temps_jeu_heures": 40,
  "termine": true
}


GET /api/games
Lister tous les jeux, avec filtres possibles :

?genre=RPG

?plateforme=PC

?termine=true

?favori=true

?search=Zelda

?annee_min=2015&annee_max=2024

GET /api/games/{id}
Récupérer un jeu par son id.

PUT /api/games/{id}
Mettre à jour un jeu (tous les champs sont optionnels dans le body).

DELETE /api/games/{id}
Supprimer un jeu.

6.2 Favoris

POST /api/games/{id}/favorite

Body :

{ "favori": true }


ou

{ "favori": false }

6.3 Statistiques & Export

GET /api/stats
Renvoie plusieurs statistiques :

total_games : nombre total de jeux

total_playtime : somme des temps_jeu_heures

avg_metacritic : moyenne de metacritic_score

finished_games : nombre de jeux termine = true

GET /api/games/export
Renvoie tous les jeux (format JSON), pratique pour un export.

7. Utilisation via Swagger

Aller sur : http://127.0.0.1:8000/docs

Cliquer sur un endpoint (POST /api/games, etc.).

Cliquer sur “Try it out”.

Remplir le JSON ou les paramètres.

Cliquer sur “Execute” pour envoyer la requête.

Les réponses HTTP et le JSON retourné apparaissent en dessous.

8. Utilisation via la page HTML

Aller sur :

http://127.0.0.1:8000/

ou

http://127.0.0.1:8000/frontend/index.html

Depuis la page :

Remplir le formulaire “Ajouter un jeu” puis cliquer sur Ajouter.

Cliquer sur Rafraîchir pour recharger la liste.

Utiliser les boutons Supprimer / Mettre en favori pour tester les autres routes.

La page HTML utilise fetch pour appeler directement l’API FastAPI.


---

## 2. Scénario de démo courte (pour ton enregistrement)

Idée : une vidéo de **2–3 minutes** où tu montres :

1. **Le projet et le lancement**
2. **Swagger**
3. **Un jeu ajouté**
4. **Le front HTML**
5. **Les stats**

### Jeu à ajouter (exemple prêt à l’emploi)

Dans Swagger (`POST /api/games`), tu peux utiliser ce jeu :

```json
{
  "titre": "Elden Ring",
  "genre": ["Action-RPG", "Open World"],
  "plateforme": ["PC", "PlayStation 5"],
  "editeur": "Bandai Namco",
  "developpeur": "FromSoftware",
  "annee_sortie": 2022,
  "metacritic_score": 96,
  "temps_jeu_heures": 75,
  "termine": false
}