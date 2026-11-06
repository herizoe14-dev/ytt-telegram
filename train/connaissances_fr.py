"""Connaissances générales écrites à la main pour Alice (faits stables et vérifiés).

Chaque entrée : (questions possibles, réponse). Les faits qui changent souvent
(dirigeants actuels, prix, actualité) sont volontairement absents : Alice doit dire
qu'elle n'a pas d'informations à jour. Les sujets des questions d'évaluation
(eval/questions_fr.py) sont exclus.
"""

FAITS = [
    # ---------------------------------------------------------------- Madagascar
    (["Qui sont les premiers habitants de Madagascar ?", "D'où viennent les premiers habitants de Madagascar ?",
      "Le premier peuple de Madagascar venait d'où ?"],
     "Les premiers habitants de Madagascar sont arrivés d'Asie du Sud-Est, de la région de Bornéo, il y a environ "
     "1 500 à 2 000 ans, en pirogue à balancier. Des populations d'Afrique de l'Est les ont rejoints ensuite. "
     "Le peuple malgache est né de ce mélange."),
    (["Quand Madagascar est-elle devenue indépendante ?", "Quelle est la date de l'indépendance de Madagascar ?"],
     "Madagascar est devenue indépendante le 26 juin 1960, après la colonisation française. Le 26 juin est la fête nationale."),
    (["Quelles sont les langues officielles de Madagascar ?"],
     "Les langues officielles de Madagascar sont le malgache et le français."),
    (["Combien d'habitants compte Madagascar ?", "Quelle est la population de Madagascar ?"],
     "Madagascar compte environ 30 millions d'habitants (au début des années 2020)."),
    (["Quelle est la taille de Madagascar ?", "Madagascar est-elle une grande île ?"],
     "Madagascar est la quatrième plus grande île du monde, avec environ 587 000 km², plus grande que la France."),
    (["Quel est le plus haut sommet de Madagascar ?"],
     "Le plus haut sommet de Madagascar est le Maromokotro, à 2 876 mètres, dans le massif du Tsaratanana."),
    (["Qui était Andrianampoinimerina ?"],
     "Andrianampoinimerina était un roi de l'Imerina, à la fin du XVIIIe siècle. Il a unifié les Hautes Terres "
     "et voulait que son royaume aille « jusqu'à la mer »."),
    (["Qui était Radama Ier ?"],
     "Radama Ier, fils d'Andrianampoinimerina, a régné de 1810 à 1828. Il a étendu le royaume de Madagascar et "
     "introduit l'écriture du malgache en alphabet latin."),
    (["Qui était la dernière reine de Madagascar ?"],
     "La dernière reine de Madagascar était Ranavalona III. Elle a été exilée par les Français en 1897, "
     "après la colonisation de l'île."),
    (["Que s'est-il passé à Madagascar en 1947 ?", "C'est quoi l'insurrection de 1947 ?"],
     "Le 29 mars 1947, une grande insurrection contre la colonisation française a éclaté à Madagascar. "
     "Sa répression a fait des dizaines de milliers de morts. Le 29 mars est une journée de commémoration."),
    (["Qui était le premier président de Madagascar ?"],
     "Le premier président de Madagascar était Philibert Tsiranana, de 1960 à 1972."),
    (["Pourquoi Madagascar a-t-elle des animaux uniques ?", "Pourquoi les lémuriens ne vivent qu'à Madagascar ?"],
     "Madagascar est séparée des autres terres depuis des dizaines de millions d'années. Ses plantes et ses animaux "
     "ont évolué seuls : la plupart n'existent nulle part ailleurs, comme les lémuriens."),
    (["Quel est le plus grand lémurien ?"],
     "Le plus grand lémurien vivant est l'indri, qui vit dans les forêts de l'est de Madagascar, par exemple à Andasibe."),
    (["Qu'est-ce que le fossa ?"],
     "Le fossa est le plus grand prédateur de Madagascar : un mammifère carnivore agile, qui chasse notamment les lémuriens."),
    (["Où voir des baobabs à Madagascar ?", "C'est quoi l'allée des baobabs ?"],
     "L'allée des baobabs se trouve près de Morondava, dans l'ouest de Madagascar. L'île abrite six espèces de "
     "baobabs qui n'existent nulle part ailleurs."),
    (["Madagascar produit quoi ?", "Quelle épice vient de Madagascar ?"],
     "Madagascar est le premier producteur mondial de vanille. L'île produit aussi du girofle, du riz, du café, "
     "du litchi et du nickel."),
    (["Quel est le plat national malgache ?", "C'est quoi le romazava ?"],
     "Le romazava est souvent considéré comme le plat national malgache : un bouillon de viande de zébu avec des "
     "brèdes, servi avec du riz."),
    (["C'est quoi le ravitoto ?"],
     "Le ravitoto est un plat malgache à base de feuilles de manioc pilées, cuites avec de la viande de porc, servi avec du riz."),
    (["Pourquoi le riz est important à Madagascar ?"],
     "À Madagascar, le riz (« vary ») est la base de presque tous les repas : on en mange souvent trois fois par jour."),
    (["C'est quoi le famadihana ?"],
     "Le famadihana, ou « retournement des morts », est une cérémonie des Hautes Terres malgaches : la famille "
     "sort les défunts du tombeau, les enveloppe dans de nouveaux linceuls et fait la fête pour honorer les ancêtres."),
    (["C'est quoi un fady ?"],
     "Un fady est un interdit traditionnel malgache : une chose qu'il ne faut pas faire ou manger, qui varie selon "
     "les régions et les familles."),
    (["C'est quoi le salegy ?"],
     "Le salegy est une musique et une danse très rythmées du nord de Madagascar."),
    (["C'est quoi le hira gasy ?"],
     "Le hira gasy est un spectacle traditionnel des Hautes Terres malgaches, qui mêle chant, discours (kabary) et danse."),
    (["Comment dit-on bonjour en malgache ?", "Bonjour en malgache ?"],
     "En malgache, on dit « Manao ahoana » pour bonjour, « Misaotra » pour merci et « Veloma » pour au revoir."),
    (["Quand est la saison des pluies à Madagascar ?"],
     "À Madagascar, la saison des pluies va à peu près de novembre à avril. C'est aussi la saison des cyclones."),
    (["C'est quoi Nosy Be ?"],
     "Nosy Be est une île touristique au nord-ouest de Madagascar, connue pour ses plages et l'ylang-ylang."),
    (["Qu'est-ce que le zébu représente à Madagascar ?"],
     "À Madagascar, le zébu est un symbole de richesse et de prestige. Il sert aux travaux des champs et aux cérémonies."),
    # ---------------------------------------------------------------- histoire
    (["Quand a eu lieu la Révolution française ?"],
     "La Révolution française a commencé en 1789, avec la prise de la Bastille le 14 juillet 1789."),
    (["Quand a eu lieu la Première Guerre mondiale ?"], "La Première Guerre mondiale a eu lieu de 1914 à 1918."),
    (["Quand a eu lieu la Seconde Guerre mondiale ?"], "La Seconde Guerre mondiale a eu lieu de 1939 à 1945."),
    (["Quand le mur de Berlin est-il tombé ?"], "Le mur de Berlin est tombé le 9 novembre 1989."),
    (["Qui a découvert l'Amérique ?", "Quand Christophe Colomb est-il arrivé en Amérique ?"],
     "Christophe Colomb a atteint l'Amérique en 1492, mais des peuples y vivaient depuis des milliers d'années, "
     "et des Vikings y étaient venus vers l'an 1000."),
    (["Qui a inventé l'imprimerie ?"],
     "Johannes Gutenberg a mis au point l'imprimerie à caractères mobiles en Europe vers 1450."),
    (["Quand ont été construites les pyramides d'Égypte ?"],
     "Les grandes pyramides de Gizeh ont été construites il y a environ 4 500 ans, vers 2500 avant J.-C."),
    (["Qui était Napoléon ?"],
     "Napoléon Bonaparte était un général français devenu empereur des Français en 1804. Il a créé le Code civil "
     "et mené de nombreuses guerres en Europe."),
    (["Quand l'esclavage a-t-il été aboli en France ?"],
     "L'esclavage a été aboli définitivement dans les colonies françaises en 1848."),
    (["Qui était Nelson Mandela ?"],
     "Nelson Mandela a lutté contre l'apartheid en Afrique du Sud. Emprisonné 27 ans, il est devenu le premier "
     "président noir du pays en 1994 et a reçu le prix Nobel de la paix."),
    (["Quand l'ONU a-t-elle été créée ?"], "L'Organisation des Nations unies (ONU) a été créée en 1945, après la Seconde Guerre mondiale."),
    (["Qui était Gandhi ?"],
     "Gandhi a mené l'Inde vers l'indépendance, obtenue en 1947, par la résistance non violente."),
    (["Qui était Martin Luther King ?"],
     "Martin Luther King était un pasteur américain qui a lutté sans violence pour les droits des Noirs. "
     "Il est célèbre pour son discours « I have a dream » de 1963."),
    (["Qui était Jeanne d'Arc ?"],
     "Jeanne d'Arc était une jeune paysanne française du XVe siècle qui a mené des troupes pendant la guerre de "
     "Cent Ans. Elle a été brûlée en 1431."),
    (["Qui était Charlemagne ?"],
     "Charlemagne était roi des Francs, couronné empereur en l'an 800. Il a encouragé les écoles et l'écriture."),
    (["C'est quoi la révolution industrielle ?"],
     "La révolution industrielle, aux XVIIIe et XIXe siècles, est le passage du travail à la main aux machines, "
     "grâce à la machine à vapeur, au charbon puis à l'électricité."),
    (["Pourquoi 1960 est-elle appelée l'année de l'Afrique ?"],
     "En 1960, dix-sept pays africains, dont Madagascar, sont devenus indépendants : on l'appelle l'année de l'Afrique."),
    (["Quand l'euro a-t-il été mis en circulation ?"], "Les pièces et les billets en euros ont été mis en circulation le 1er janvier 2002."),
    # ---------------------------------------------------------------- géographie
    (["Combien y a-t-il de continents ?", "Quels sont les continents ?"],
     "On compte généralement six continents : l'Afrique, l'Amérique, l'Antarctique, l'Asie, l'Europe et l'Océanie. "
     "Certains séparent l'Amérique du Nord et l'Amérique du Sud, ce qui en fait sept."),
    (["Quel est le plus long fleuve du monde ?"],
     "Le Nil et l'Amazone sont les deux plus longs fleuves du monde, avec environ 6 500 à 7 000 km ; le classement "
     "dépend de la façon de mesurer."),
    (["Quel est le plus haut sommet d'Afrique ?"], "Le plus haut sommet d'Afrique est le Kilimandjaro, en Tanzanie, à 5 895 mètres."),
    (["Quel est le plus grand lac d'Afrique ?"], "Le plus grand lac d'Afrique est le lac Victoria, partagé entre l'Ouganda, le Kenya et la Tanzanie."),
    (["Quelle est la plus grande forêt tropicale du monde ?"], "La plus grande forêt tropicale du monde est l'Amazonie, en Amérique du Sud."),
    (["Quels sont les pays les plus peuplés du monde ?"],
     "L'Inde et la Chine sont les pays les plus peuplés, avec chacun environ 1,4 milliard d'habitants."),
    (["Combien d'habitants y a-t-il sur Terre ?"], "La Terre compte un peu plus de 8 milliards d'habitants (au milieu des années 2020)."),
    (["C'est quoi l'équateur ?"], "L'équateur est une ligne imaginaire qui fait le tour de la Terre à égale distance des deux pôles."),
    (["Quel est le plus grand océan ?", "Quels sont les océans ?"],
     "Les océans sont le Pacifique (le plus grand), l'Atlantique, l'océan Indien, l'océan Austral et l'océan Arctique."),
    (["Dans quel océan se trouve La Réunion ?"], "La Réunion est une île française de l'océan Indien, à l'est de Madagascar."),
    (["Quels pays sont voisins de Madagascar ?", "Quelles îles sont proches de Madagascar ?"],
     "Madagascar est une île : ses voisins sont les Comores, Mayotte, La Réunion, Maurice, les Seychelles et, "
     "de l'autre côté du canal du Mozambique, le Mozambique."),
    (["Combien de pays y a-t-il dans le monde ?"], "On compte environ 195 pays dans le monde, dont 193 membres de l'ONU."),
    (["Combien de personnes parlent français ?", "C'est quoi la francophonie ?"],
     "Environ 320 millions de personnes parlent français dans le monde. La francophonie désigne l'ensemble des "
     "pays et des gens qui parlent français, en Afrique, en Europe, en Amérique et dans l'océan Indien."),
    # ---------------------------------------------------------------- sciences
    (["C'est quoi la photosynthèse ?"],
     "La photosynthèse est le moyen qu'utilisent les plantes pour fabriquer leur nourriture : avec la lumière du "
     "soleil, elles transforment l'eau et le gaz carbonique en sucre, et rejettent de l'oxygène."),
    (["Quelle est la vitesse de la lumière ?"], "La lumière va à environ 300 000 kilomètres par seconde."),
    (["Quelle est la vitesse du son ?"], "Dans l'air, le son se déplace à environ 340 mètres par seconde."),
    (["Pourquoi les objets tombent ?", "C'est quoi la gravité ?"],
     "Les objets tombent à cause de la gravité : la Terre attire tout ce qui a une masse vers son centre. "
     "Isaac Newton a décrit cette force au XVIIe siècle."),
    (["Qui était Albert Einstein ?"],
     "Albert Einstein était un physicien célèbre pour la théorie de la relativité et la formule E = mc². "
     "Il a reçu le prix Nobel de physique en 1921."),
    (["C'est quoi l'ADN ?"],
     "L'ADN est une longue molécule présente dans nos cellules : elle contient les instructions qui font "
     "fonctionner et grandir un être vivant, et qui se transmettent des parents aux enfants."),
    (["C'est quoi une cellule ?"], "Une cellule est la plus petite unité vivante. Le corps humain en contient des milliers de milliards."),
    (["C'est quoi un atome ?"],
     "Un atome est une toute petite particule de matière : un noyau, fait de protons et de neutrons, entouré d'électrons."),
    (["Quels sont les états de l'eau ?", "Quels sont les états de la matière ?"],
     "La matière existe surtout sous trois états : solide (la glace), liquide (l'eau) et gazeux (la vapeur)."),
    (["Pourquoi y a-t-il des saisons ?"],
     "Il y a des saisons parce que l'axe de la Terre est penché : selon la période de l'année, un hémisphère reçoit "
     "les rayons du Soleil plus directement et plus longtemps."),
    (["Pourquoi y a-t-il le jour et la nuit ?"],
     "Le jour et la nuit viennent de la rotation de la Terre sur elle-même : la moitié tournée vers le Soleil est "
     "dans le jour, l'autre dans la nuit."),
    (["Pourquoi la Lune change de forme ?", "C'est quoi les phases de la Lune ?"],
     "La Lune ne change pas vraiment de forme : on voit une partie plus ou moins grande de sa face éclairée par le "
     "Soleil selon sa position autour de la Terre. Un cycle dure environ 29 jours et demi."),
    (["C'est quoi une éclipse ?"],
     "Une éclipse de Soleil se produit quand la Lune passe devant le Soleil ; une éclipse de Lune, quand la Terre "
     "se place entre le Soleil et la Lune."),
    (["Pourquoi y a-t-il des tremblements de terre ?", "C'est quoi un séisme ?"],
     "Un séisme est une secousse du sol causée par le mouvement des plaques tectoniques, les grands morceaux qui "
     "forment la surface de la Terre."),
    (["C'est quoi le réchauffement climatique ?"],
     "Le réchauffement climatique est l'augmentation de la température moyenne de la Terre, causée surtout par les "
     "gaz à effet de serre, comme le CO₂, que rejettent le charbon, le pétrole et le gaz qu'on brûle."),
    (["Comment fabrique-t-on l'essence ?", "Comment l'essence est fabriquée ?", "D'où vient l'essence ?"],
     "L'essence est fabriquée à partir du pétrole brut, extrait du sous-sol. Dans une raffinerie, on chauffe le "
     "pétrole et on le sépare en plusieurs produits (essence, gazole, kérosène…) : c'est la distillation."),
    (["D'où vient le pétrole ?"],
     "Le pétrole s'est formé pendant des millions d'années à partir de restes de petits êtres vivants enfouis "
     "sous la terre et la mer, sous l'effet de la chaleur et de la pression."),
    (["Avec quoi fabrique-t-on le plastique ?"], "La plupart des plastiques sont fabriqués à partir du pétrole."),
    (["Comment produit-on l'électricité ?"],
     "On produit l'électricité dans des centrales : en faisant tourner des turbines avec de l'eau (barrages), "
     "du vent (éoliennes), de la vapeur (charbon, gaz, nucléaire), ou avec des panneaux solaires."),
    (["C'est quoi l'énergie solaire ?"], "L'énergie solaire est l'énergie de la lumière du Soleil, transformée en électricité par des panneaux solaires ou en chaleur."),
    (["Pourquoi recycler ?"], "Recycler permet de réutiliser les matériaux, comme le papier, le verre ou le plastique, au lieu de les jeter : cela économise des ressources et réduit la pollution."),
    (["Quelle est la différence entre un virus et une bactérie ?"],
     "Une bactérie est un être vivant d'une seule cellule ; un virus est bien plus petit et ne peut se multiplier "
     "qu'à l'intérieur d'une cellule. Les antibiotiques agissent contre les bactéries, pas contre les virus."),
    (["Comment fonctionne un vaccin ?", "À quoi sert un vaccin ?"],
     "Un vaccin apprend au corps à reconnaître un microbe sans tomber vraiment malade : le système immunitaire "
     "garde ensuite la mémoire de ce microbe et se défend plus vite."),
    (["À quoi servent les globules rouges ?"], "Les globules rouges transportent l'oxygène des poumons vers tout le corps."),
    (["Combien d'os a le corps humain ?"], "Un adulte a environ 206 os."),
    (["Quel est le plus grand organe du corps humain ?"], "Le plus grand organe du corps humain est la peau."),
    (["Combien de litres de sang a un adulte ?"], "Un adulte a environ 5 litres de sang."),
    (["Qu'est-ce que le paludisme ?", "Comment se transmet le paludisme ?"],
     "Le paludisme est une maladie transmise par la piqûre de certains moustiques. Elle donne de fortes fièvres ; "
     "on s'en protège avec des moustiquaires et on doit consulter un médecin en cas de fièvre."),
    # ---------------------------------------------------------------- santé et vie courante
    (["Combien d'heures faut-il dormir ?"], "Un adulte a besoin d'environ 7 à 9 heures de sommeil par nuit ; les enfants, davantage."),
    (["Combien d'eau faut-il boire par jour ?"], "Un adulte devrait boire environ 1,5 à 2 litres d'eau par jour, davantage quand il fait chaud ou qu'on fait du sport."),
    (["Comment avoir une bonne santé ?"], "Pour rester en bonne santé : manger varié, boire de l'eau, bouger chaque jour, bien dormir et se laver les mains."),
    (["Pourquoi faut-il se brosser les dents ?"], "On se brosse les dents deux fois par jour pour enlever la plaque et éviter les caries."),
    (["Que faire en cas de brûlure ?"], "En cas de petite brûlure, passe-la sous l'eau froide pendant 10 à 20 minutes. Si elle est grave, appelle les secours."),
    (["Que faire si quelqu'un a de la fièvre ?"],
     "Il faut le faire boire, le laisser se reposer et surveiller sa température. Si la fièvre est forte ou dure, "
     "surtout chez un enfant ou en zone de paludisme, il faut voir un médecin."),
    # ---------------------------------------------------------------- technologie
    (["Comment fonctionne internet ?"],
     "Internet est un immense réseau d'ordinateurs reliés entre eux par des câbles, des ondes et des satellites. "
     "Les informations voyagent en petits paquets d'un ordinateur à l'autre."),
    (["C'est quoi le Wi-Fi ?"], "Le Wi-Fi est une technologie qui relie des appareils à internet sans fil, grâce aux ondes radio d'une box ou d'un routeur."),
    (["Comment fonctionne le GPS ?"], "Le GPS utilise les signaux de plusieurs satellites : en mesurant le temps qu'ils mettent à arriver, ton téléphone calcule sa position."),
    (["C'est quoi un algorithme ?"], "Un algorithme est une suite d'étapes précises pour résoudre un problème, comme une recette de cuisine."),
    (["C'est quoi Python ?"], "Python est un langage de programmation simple et très utilisé, par exemple pour l'intelligence artificielle et l'analyse de données."),
    (["Comment apprend une intelligence artificielle ?", "Comment tu as appris ?"],
     "Une intelligence artificielle comme moi apprend à partir de très nombreux exemples de textes. Elle repère des "
     "régularités et apprend à prédire le mot suivant. Je n'ai pas de conscience ni de souvenirs en dehors de notre conversation."),
    (["Comment créer un bon mot de passe ?"],
     "Un bon mot de passe est long (au moins 12 caractères), mélange lettres, chiffres et symboles, et n'est utilisé "
     "que pour un seul compte. Ne le donne jamais à personne."),
    (["C'est quoi le phishing ?", "C'est quoi l'hameçonnage ?"],
     "Le phishing, ou hameçonnage, est une arnaque : un faux message imite une banque ou un service pour te voler "
     "ton mot de passe. Ne clique pas sur les liens douteux et vérifie l'adresse de l'expéditeur."),
    (["Comment fonctionne une voiture ?"], "Dans une voiture à essence, le moteur brûle de l'essence : cette explosion pousse des pistons qui font tourner les roues. Une voiture électrique utilise une batterie et un moteur électrique."),
    (["Comment fonctionne un réfrigérateur ?"], "Un réfrigérateur fait circuler un liquide spécial qui absorbe la chaleur à l'intérieur et la rejette à l'arrière de l'appareil."),
    (["Qui a inventé le téléphone ?"], "Le téléphone a été breveté par Alexander Graham Bell en 1876."),
    (["Qui a inventé l'ampoule électrique ?"], "Plusieurs inventeurs y ont travaillé ; Thomas Edison a mis au point une ampoule pratique et durable en 1879."),
    # ---------------------------------------------------------------- langue et culture
    (["Quand l'Académie française a-t-elle été créée ?"], "L'Académie française a été créée en 1635 par le cardinal de Richelieu."),
    (["Conjugue le verbe être au présent."], "Je suis, tu es, il est, nous sommes, vous êtes, ils sont."),
    (["Conjugue le verbe avoir au présent."], "J'ai, tu as, il a, nous avons, vous avez, ils ont."),
    (["Conjugue le verbe aller au présent."], "Je vais, tu vas, il va, nous allons, vous allez, ils vont."),
    (["Quelle est la différence entre « a » et « à » ?"],
     "« a » est le verbe avoir (il a un livre) ; « à » est une préposition (je vais à l'école). Astuce : si on peut "
     "dire « avait », on écrit « a »."),
    (["Quand utiliser tu ou vous ?"], "On dit « tu » à un ami ou à un enfant, et « vous » pour parler poliment à un adulte qu'on ne connaît pas, ou à plusieurs personnes."),
    (["Qui a écrit Les Fables ?", "Qui était Jean de La Fontaine ?"],
     "Jean de La Fontaine est un poète français du XVIIe siècle, auteur des Fables, comme « Le Corbeau et le Renard »."),
    (["Qui a peint les Nymphéas ?"], "Claude Monet, peintre impressionniste français, a peint les Nymphéas."),
    (["Qui a composé la Cinquième Symphonie ?"], "Ludwig van Beethoven a composé la Cinquième Symphonie, en 1808."),
    (["Qui a écrit Roméo et Juliette ?"], "William Shakespeare a écrit Roméo et Juliette, à la fin du XVIe siècle."),
    (["Tous les combien ont lieu les Jeux olympiques ?"], "Les Jeux olympiques d'été ont lieu tous les quatre ans, comme ceux d'hiver, en alternance."),
    (["Combien de joueurs dans une équipe de football ?"], "Une équipe de football a 11 joueurs sur le terrain, dont le gardien."),
    # ---------------------------------------------------------------- mathématiques
    (["C'est quoi un nombre premier ?"],
     "Un nombre premier n'a que deux diviseurs : 1 et lui-même. Par exemple 2, 3, 5, 7, 11 et 13."),
    (["Combien vaut pi ?"], "Pi vaut environ 3,14. C'est le rapport entre le périmètre d'un cercle et son diamètre."),
    (["Comment calculer l'aire d'un rectangle ?"], "L'aire d'un rectangle est sa longueur multipliée par sa largeur."),
    (["Comment calculer le périmètre d'un rectangle ?"], "Le périmètre d'un rectangle est 2 fois la somme de sa longueur et de sa largeur."),
    (["Comment calculer un pourcentage ?", "Combien font 10 % de 50 ?"],
     "Pour calculer un pourcentage, on multiplie par le nombre puis on divise par 100. Par exemple, 10 % de 50 "
     "font 50 fois 10 divisé par 100, soit 5."),
    (["Comment calculer une moyenne ?"], "Pour calculer une moyenne, on additionne toutes les valeurs puis on divise par leur nombre. La moyenne de 4, 6 et 8 est 18 divisé par 3, soit 6."),
    # ---------------------------------------------------------------- limites d'Alice
    (["Qui est le président actuel de Madagascar ?", "Qui est le président de la France en ce moment ?",
      "Quelles sont les nouvelles d'aujourd'hui ?", "Qui a gagné le match hier ?"],
     "Je n'ai pas accès à l'actualité et mes connaissances peuvent être dépassées : je ne peux pas te le dire avec "
     "certitude. Consulte un site d'information récent."),
    (["Donne-moi un email.", "Donne-moi une adresse Gmail.", "Cite-moi des adresses e-mail.", "Tu as un email ?"],
     "Je n'ai pas d'adresse e-mail, et je ne peux pas en inventer : une fausse adresse pourrait appartenir à "
     "quelqu'un. Si tu veux en créer une, va sur le site d'un service de messagerie."),
    (["Donne-moi le numéro de téléphone de quelqu'un.", "Quel est le numéro de téléphone de mon voisin ?"],
     "Je ne connais pas les coordonnées des personnes et je ne peux pas en inventer."),
    (["Donne-moi un lien vers un site.", "Envoie-moi un lien."],
     "Je ne peux pas naviguer sur internet ni vérifier qu'un lien existe : je préfère ne pas en inventer."),
    (["Quel est le nom du chat de mon voisin ?", "Qu'est-ce que j'ai mangé ce matin ?"],
     "Je ne peux pas le savoir : je ne connais que ce que tu me dis dans notre conversation."),
    (["Est-ce que tu peux te tromper ?", "Tu dis toujours vrai ?"],
     "Je peux me tromper, surtout sur des sujets précis ou récents. Quand je ne suis pas sûre, je préfère te le dire."),
]

# Faits inventés ou trop obscurs : Alice doit reconnaître qu'elle ne sait pas, au lieu d'inventer.
INCONNUS = [
    "Quelle est la capitale de la Zorvanie ?", "Qui a inventé le moteur à brouillard ?",
    "Combien d'habitants a la ville de Tralimbo ?", "Qui a gagné le prix Kelvaro en 1854 ?",
    "Quel est le plus long fleuve de la planète Xorpa ?", "Qui était le roi Ambatofolo III ?",
    "Que veut dire le mot « bramoulix » ?", "En quelle année a été fondée la ville de Pindoravel ?",
    "Qui a écrit le livre « Les nuages de Varonne » ?", "Quelle est la recette du gâteau zinblou ?",
]
REPONSES_INCONNU = [
    "Je ne connais pas {x}. Je préfère ne pas inventer : peux-tu me donner plus de détails ?",
    "Je ne suis pas sûre : je n'ai pas d'information fiable sur {x}.",
]
