"""Conversations de test (jamais vues à l'entraînement) : la mémoire d'Alice.

Chaque conversation est une suite de messages de l'utilisateur ; seule la dernière
réponse est contrôlée (elle doit contenir l'une des réponses attendues). Les prénoms,
villes et nombres ne figurent pas dans les gabarits d'entraînement.
"""
CONVERSATIONS = [
    (["Bonjour, je m'appelle Mahery.", "Quelle est la capitale du Japon ?", "Comment je m'appelle ?"],
     ["mahery"], "prénom"),
    (["Salut ! Moi c'est Solène.", "Combien font 6 plus 7 ?", "C'est quoi un briquet ?", "Tu te souviens de mon prénom ?"],
     ["solene"], "prénom"),
    (["J'ai 27 ans.", "Combien font 9 fois 3 ?", "Quel âge j'ai ?"], ["27"], "fait personnel"),
    (["J'habite à Toamasina.", "Quelle est la couleur d'une banane ?", "Dans quelle ville j'habite ?"],
     ["toamasina"], "fait personnel"),
    (["Mon animal préféré est le hibou.", "Bonjour Alice, ça va ?", "Quel est mon animal préféré ?"],
     ["hibou"], "fait personnel"),
    (["Retiens ce nombre : 58.", "Quelle est la capitale du Canada ?", "Quel nombre je t'ai demandé de retenir ?"],
     ["58"], "retenir"),
    (["Combien font 7 fois 8 ?", "Et si j'ajoute 4 ?"], ["60"], "calcul enchaîné"),
    (["Combien font 25 plus 15 ?", "Et la moitié de ce résultat ?"], ["20"], "calcul enchaîné"),
    (["Rova a 9 mangues. Elle en mange 3. Combien lui en reste-t-il ?", "Et si elle en achète encore 5 ?"],
     ["11"], "problème enchaîné"),
    (["Quelle est la capitale du Portugal ?", "Et celle de la Grèce ?"], ["athenes"], "question elliptique"),
    (["C'est quoi un zébu ?", "Et un caméléon ?"], ["lezard", "couleur"], "question elliptique"),
    (["Je m'appelle Bastien et j'ai 31 ans.", "Quel âge aurai-je dans 4 ans ?"], ["35"], "mémoire + calcul"),
    (["Bonjour !", "Je m'appelle Nirina.", "Combien font 12 moins 5 ?", "Quelle est la capitale de l'Italie ?",
      "Merci. Au fait, comment je m'appelle ?"], ["nirina"], "longue conversation"),
    (["J'aime beaucoup le basket.", "C'est quoi un volcan ?", "Combien font 4 fois 4 ?",
      "Quelle est la capitale de l'Espagne ?", "Quel sport est-ce que j'aime ?"], ["basket"], "longue conversation"),
    (["Je suis Lalaina.", "Je vis à Fianarantsoa.", "Quel est mon prénom et où j'habite ?"],
     ["lalaina"], "deux faits"),
    (["Qui es-tu ?", "Et qui t'a créée ?", "Tu es Qwen, non ?"], ["alice"], "identité"),
]
