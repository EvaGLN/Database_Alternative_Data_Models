# POC Neo4j : une famille sur trois générations

Petit projet qui montre le **modèle graphe** avec Neo4j, pour le PLD
« Database Alternative Data Models » (parcours Graphe).

Un script Python (`poc_graph.py`) se connecte à Neo4j et déroule, sur un
graphe de famille (7 personnes, 7 relations `PARENT_DE`) :

| Étape | Ce que le script montre |
|---|---|
| 5. CREATE | création des nœuds (`GrandParent`, `Parent`, `Enfant`) et des relations |
| 6. READ | les enfants directs d'Anna (`MATCH` + `WHERE`) |
| 7. READ | les ancêtres d'Eva, avec un chemin de longueur variable (`*1..3`) |
| 8. UPDATE | l'âge de Sammy modifié avec `SET`, affiché avant et après |
| 10. Fonction distinctive | le plus court chemin entre Eva et Jack (`shortestPath`) |
| 9. DELETE | une relation supprimée, un nœud relié dont la suppression est refusée, puis `DETACH DELETE` |

Une seule relation est stockée (`PARENT_DE`, du parent vers l'enfant). Les
liens « grand-parent de », « enfant de »… ne sont pas stockés : ils se
déduisent par parcours du graphe.

## Prérequis

- Docker (démarré)
- Python 3.10 ou plus (`python3 --version`)
- le pilote officiel Neo4j : `pip install neo4j`

## 1. Lancer Neo4j

    docker run --name neo4j -p 7474:7474 -p 7687:7687 \
      -e NEO4J_AUTH=neo4j/password -d neo4j:latest

Attendre une trentaine de secondes. `docker logs neo4j` doit afficher
« Started ». L'interface web (Neo4j Browser) est sur
http://localhost:7474 (identifiants `neo4j` / `password`).

Si le conteneur existe déjà : `docker start neo4j`.

## 2. Lancer le POC

    pip install neo4j
    python3 poc_graph.py

Le script vide la base au début (`MATCH (n) DETACH DELETE n`) : on peut le
rejouer autant de fois que nécessaire.

## 3. Voir le graphe

Dans le Neo4j Browser (http://localhost:7474), après l'exécution :

    MATCH (n) RETURN n

## Résultat attendu

Le chemin entre Eva et Jack peut passer par Theo ou par Gertrude, et le numéro
du nœud dans le message de refus varie ; le texte exact des messages d'erreur
dépend aussi de la version de Neo4j.

```
Enfants d'Anna :
  Jack
  Sammy
Ancêtres d'Eva :
  Mathieu - à 1 génération(s)
  Gertrude - à 2 génération(s)
  Theo - à 2 génération(s)
Âge de Sammy : 15 -> 16
Chemin Eva -> Jack : Eva -> Mathieu -> Theo -> Anna -> Jack
Avant les suppressions : 7 nœuds, 7 relations
Relation Anna -> Sammy supprimée : 7 nœuds, 6 relations
Suppression refusée : Cannot delete node<2>, because it still has relationships. To delete this node, you must first delete its relationships.
Rien n'a changé : 7 nœuds, 6 relations
Mathieu supprimé avec DETACH DELETE : 6 nœuds, 3 relations
```

## En cas de problème

| Message | Cause probable |
|---|---|
| `ModuleNotFoundError: No module named 'neo4j'` | le pilote n'est pas installé pour cette version de Python : refaire `pip install neo4j` |
| `ServiceUnavailable` / connexion refusée | Neo4j n'a pas fini de démarrer (attendre, voir `docker logs neo4j`) ou le conteneur est arrêté (`docker start neo4j`) |
| `AuthError` | le mot de passe ne correspond pas à `NEO4J_AUTH` : modifier `AUTH` en haut de `poc_graph.py` |
| `pip` ne trouve pas `neo4j` | Python trop ancien : essayer `pip install "neo4j<6"` |
| erreur d'import étrange sur `neo4j` | un fichier nommé `neo4j.py` existe dans le dossier : le renommer |

## Nettoyer

    docker rm -f neo4j

## Sources

- Documentation Neo4j : https://neo4j.com/docs/
- Neo4j GraphAcademy : https://graphacademy.neo4j.com/
- GeeksforGeeks, types de bases de données NoSQL