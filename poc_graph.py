#!/usr/bin/python3
"""POC Neo4j : CRUD et fonctions du modèle graphe sur une famille."""
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")


def run(driver, query, **params):
    """Exécute une requête Cypher et renvoie la liste des résultats."""
    records, _, _ = driver.execute_query(
        query, parameters_=params, database_="neo4j")
    return records


def etat(driver):
    """Renvoie le nombre de nœuds et de relations du graphe."""
    noeuds = run(driver, "MATCH (n) RETURN count(n) AS n")[0]["n"]
    relations = run(driver, "MATCH ()-[r]->() RETURN count(r) AS n")[0]["n"]
    return str(noeuds) + " nœuds, " + str(relations) + " relations"


with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    run(driver, "MATCH (n) DETACH DELETE n")  # repartir d'un graphe vide

    # 5. CREATE : des nœuds et des relations PARENT_DE (parent vers enfant)
    run(driver, """
        CREATE (Theo:GrandParent {nom: 'Theo', age: 72, statut: 'retraite',
                                  sexe: 'homme'}),
        (Gertrude:GrandParent {nom: 'Gertrude', age: 69,
                               statut: 'retraite', sexe: 'femme'}),
        (Mathieu:Parent {nom: 'Mathieu', age: 43, statut: 'travail',
                         sexe: 'homme'}),
        (Anna:Parent {nom: 'Anna', age: 39, statut: 'travail',
                      sexe: 'femme'}),
        (Eva:Enfant {nom: 'Eva', age: 20, statut: 'chomage',
                     sexe: 'femme'}),
        (Jack:Enfant {nom: 'Jack', age: 18, statut: 'etudiant',
                      sexe: 'homme'}),
        (Sammy:Enfant {nom: 'Sammy', age: 15, statut: 'etudiant',
                       sexe: 'homme'}),
        (Theo)-[:PARENT_DE]->(Mathieu), (Theo)-[:PARENT_DE]->(Anna),
        (Gertrude)-[:PARENT_DE]->(Mathieu),
        (Gertrude)-[:PARENT_DE]->(Anna),
        (Mathieu)-[:PARENT_DE]->(Eva),
        (Anna)-[:PARENT_DE]->(Jack), (Anna)-[:PARENT_DE]->(Sammy)
    """)

    # 6. READ : les voisins directs (MATCH + WHERE)
    print("Enfants d'Anna :")
    for rec in run(driver, """
            MATCH (p:Parent)-[:PARENT_DE]->(e)
            WHERE p.nom = $nom
            RETURN e.nom AS enfant""", nom="Anna"):
        print(" ", rec["enfant"])

    # 7. READ : plusieurs sauts, avec un chemin de longueur variable (*1..3)
    print("Ancêtres d'Eva :")
    for rec in run(driver, """
            MATCH p = (a)-[:PARENT_DE*1..3]->(:Enfant {nom: $nom})
            RETURN a.nom AS ancetre, length(p) AS generations
            ORDER BY generations, ancetre""", nom="Eva"):
        print(" ", rec["ancetre"], "- à", rec["generations"], "génération(s)")

    # 8. UPDATE : modifier une propriété avec SET (lecture avant et après)
    lire_age = "MATCH (e:Enfant {nom: $nom}) RETURN e.age AS age"
    avant = run(driver, lire_age, nom="Sammy")[0]["age"]
    run(driver, "MATCH (e:Enfant {nom: $nom}) SET e.age = e.age + 1",
        nom="Sammy")
    apres = run(driver, lire_age, nom="Sammy")[0]["age"]
    print("Âge de Sammy :", avant, "->", apres)

    # 10. FONCTION DISTINCTIVE : le plus court chemin entre deux personnes
    # (avant les suppressions, pour garder le graphe complet)
    for rec in run(driver, """
            MATCH p = shortestPath(
              (:Enfant {nom: $a})-[:PARENT_DE*]-(:Enfant {nom: $b}))
            RETURN [n IN nodes(p) | n.nom] AS chemin""", a="Eva", b="Jack"):
        print("Chemin Eva -> Jack :", " -> ".join(rec["chemin"]))

    # 9. DELETE : une relation d'abord, puis un nœud avec DETACH DELETE
    print("Avant les suppressions :", etat(driver))
    run(driver, """
        MATCH (:Parent {nom: 'Anna'})-[r:PARENT_DE]->(:Enfant {nom: 'Sammy'})
        DELETE r""")
    print("Relation Anna -> Sammy supprimée :", etat(driver))
    try:  # sans DETACH, un nœud encore relié ne peut pas être supprimé
        run(driver, "MATCH (p:Parent {nom: 'Mathieu'}) DELETE p")
    except Neo4jError as erreur:
        print("Suppression refusée :", erreur.message)
        print("Rien n'a changé :", etat(driver))
    run(driver, "MATCH (p:Parent {nom: 'Mathieu'}) DETACH DELETE p")
    print("Mathieu supprimé avec DETACH DELETE :", etat(driver))