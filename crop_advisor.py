import json
import os
import math

# Constantes
SAISONS = ["spring", "summer", "fall", "winter"]
SAISONS_FR = ["printemps", "été", "automne", "hiver"]
JOURS_PAR_SAISON = 28

def charger_donnees():
    """Chargement des données de cultures depuis le fichier JSON"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(script_dir, 'stardew_crops.json'), 'r', encoding='utf-8') as fichier:
            donnees = json.load(fichier)
            return donnees['crops']
    except FileNotFoundError:
        print("Erreur: Le fichier stardew_crops.json n'a pas été trouvé.")
        exit(1)
    except json.JSONDecodeError:
        print("Erreur: Le fichier stardew_crops.json n'est pas un fichier JSON valide.")
        exit(1)

def calculer_rentabilite(culture, jour_actuel):
    """Calcule le profit par jour pour une culture spécifique, en tenant compte du jour actuel"""
    # Traitement spécial pour les cultures de forage (growthDays = 0)
    if culture['growthDays'] == 0:
        return 0  # On ne peut pas planter les cultures de forage
    
    # Le jour où on plante compte comme jour 1, donc pas besoin de +1
    jours_restants = JOURS_PAR_SAISON - jour_actuel
    
    # Vérifier d'abord si la culture aura le temps d'atteindre la maturité
    if culture['growthDays'] > jours_restants:
        return 0  # Pas le temps d'atteindre la maturité avant la fin de la saison
    
    # Si la récolte est multiple
    if culture['multipleHarvest']:
        # Première récolte
        premiere_recolte = culture['growthDays']
        
        # Si on a au moins le temps pour une récolte
        if premiere_recolte <= jours_restants:
            # Profit pour la première récolte (inclut le coût des graines)
            profit_premiere_recolte = culture['sellPrice'] - culture['seedPrice']
            
            # Nombre de récoltes supplémentaires possibles
            if culture['regrowthDays'] > 0:
                recoltes_supplementaires = max(0, math.floor((jours_restants - premiere_recolte) / culture['regrowthDays']))
                
                # Profit pour les récoltes supplémentaires (pas de coût de graines)
                profit_recoltes_suppl = culture['sellPrice'] * recoltes_supplementaires
                
                # Profit total sur la saison
                profit_total = profit_premiere_recolte + profit_recoltes_suppl
            else:
                profit_total = profit_premiere_recolte
            
            # Profit par jour sur toute la durée de vie
            return profit_total / premiere_recolte  # Utiliser le temps jusqu'à la première récolte pour le calcul
        else:
            # Pas le temps de récolter avant la fin de la saison
            return 0
    else:
        # Pour les cultures à récolte unique
        profit_brut = culture['sellPrice'] - culture['seedPrice']
        return profit_brut / culture['growthDays']

def obtenir_cultures_par_saison(cultures, saison):
    """Filtre les cultures disponibles pour une saison donnée"""
    return [c for c in cultures if saison in c['seasons']]

def recommander_cultures(cultures, saison, jour):
    """Recommande les meilleures cultures à planter en fonction de la saison et du jour"""
    # Filtrer les cultures de la saison
    cultures_disponibles = obtenir_cultures_par_saison(cultures, saison)
    
    # Calculer la rentabilité pour chaque culture
    cultures_rentabilite = []
    for culture in cultures_disponibles:
        rentabilite = calculer_rentabilite(culture, jour)
        if rentabilite > 0:  # Ne recommande que les cultures qui peuvent être récoltées
            jours_restants = JOURS_PAR_SAISON - jour
            
            # Calcul du profit total
            nb_recoltes = 1
            if culture['multipleHarvest']:
                premiere_recolte = culture['growthDays']
                
                # Vérification précise des dates de récolte
                if premiere_recolte <= jours_restants:
                    # Date de la première récolte
                    jour_recolte = jour + premiere_recolte
                    
                    # Compter le nombre de récoltes possibles
                    recoltes_supplementaires = 0
                    while True:
                        # Calcul de la date de la prochaine récolte
                        jour_recolte += culture['regrowthDays']
                        
                        # Vérifier si cette récolte est possible avant la fin de saison
                        if jour_recolte <= JOURS_PAR_SAISON:
                            recoltes_supplementaires += 1
                        else:
                            break
                            
                    nb_recoltes = 1 + recoltes_supplementaires
                    profit_total = (culture['sellPrice'] - culture['seedPrice']) + (culture['sellPrice'] * recoltes_supplementaires)
                else:
                    profit_total = culture['sellPrice'] - culture['seedPrice']
            else:
                profit_total = culture['sellPrice'] - culture['seedPrice']
                
            cultures_rentabilite.append({
                'nom': culture['name'],
                'rentabilite': rentabilite,
                'profit_total': profit_total,
                'jours_croissance': culture['growthDays'],
                'multiple': culture['multipleHarvest'],
                'frequency': culture['frequency'],
                'type': culture['type'],
                'nb_recoltes': nb_recoltes
            })
    
    # Trier par rentabilité décroissante
    cultures_rentabilite.sort(key=lambda x: x['rentabilite'], reverse=True)
    
    return cultures_rentabilite

def traduire_frequence(frequence):
    """Traduit la fréquence en français"""
    if frequence == "common":
        return "commune"
    elif frequence == "rare":
        return "rare"
    elif frequence == "forage":
        return "forage (cueillie)"
    return frequence

def afficher_recommandations(recommandations, top_n=5):
    """Affiche les recommandations de cultures"""
    if not recommandations:
        print("\nAucune culture ne peut être plantée et récoltée avant la fin de la saison.")
        return
    
    print("\nVoici les cultures les plus rentables à planter maintenant :")
    print("\n{:<20} {:<15} {:<15} {:<15} {:<15} {:<15}".format(
        "Culture", "Type", "Rentabilité/j", "Jours croiss.", "Multi-récolte", "Fréquence"))
    print("-" * 95)
    
    for i, r in enumerate(recommandations[:top_n]):
        if i < len(recommandations):  # Vérifier que l'index est valide
            multi = "Oui" if r['multiple'] else "Non"
            print("{:<20} {:<15} {:<15.2f} {:<15} {:<15} {:<15}".format(
                r['nom'], 
                r['type'],
                r['rentabilite'], 
                r['jours_croissance'], 
                multi, 
                traduire_frequence(r['frequency'])))
            # Afficher une info supplémentaire pour les cultures à récoltes multiples
            if r['multiple']:
                print("   └─ Profit estimé sur la saison : {:.0f}g ({} récoltes)".format(r['profit_total'], r['nb_recoltes']))

def main():
    """Fonction principale du programme"""
    print("=" * 60)
    print("CONSEILLER DE CULTURE STARDEW VALLEY")
    print("=" * 60)
    
    # Charger les données
    try:
        cultures = charger_donnees()
        
        # Demander la saison
        print("\nChoisissez une saison :")
        for i, saison in enumerate(SAISONS_FR):
            print(f"{i+1}. {saison.capitalize()}")
        
        choix_saison = 0
        while choix_saison < 1 or choix_saison > 4:
            try:
                choix_saison = int(input("\nVotre choix (1-4) : "))
                if choix_saison < 1 or choix_saison > 4:
                    print("Veuillez entrer un nombre entre 1 et 4.")
            except ValueError:
                print("Veuillez entrer un nombre entre 1 et 4.")
        
        saison = SAISONS[choix_saison - 1]
        
        # Demander le jour
        jour = 0
        while jour < 1 or jour > 28:
            try:
                jour = int(input("\nJour de la saison (1-28) : "))
                if jour < 1 or jour > 28:
                    print("Veuillez entrer un jour entre 1 et 28.")
            except ValueError:
                print("Veuillez entrer un nombre entre 1 et 28.")
        
        # Obtenir et afficher les recommandations
        recommandations = recommander_cultures(cultures, saison, jour)
        
        jours_restants = JOURS_PAR_SAISON - jour
        if jours_restants < 4:
            print(f"\nATTENTION: Il ne reste que {jours_restants} jours dans cette saison!")
            print("Il est peut-être préférable d'attendre la saison suivante pour planter.")
            
        afficher_recommandations(recommandations)
        
        print("\nNotes importantes :")
        print("- La rentabilité est calculée en or par jour jusqu'à la maturité de la culture.")
        print("- Les cultures qui n'atteindront pas la maturité avant la fin de la saison ne sont pas recommandées.")
        print("- Les cultures à récoltes multiples tiennent compte des récoltes supplémentaires possibles.")
        print("- Pour les cultures multi-récoltes, seule la première récolte inclut le coût des graines.")
        print("- Certaines cultures rares nécessitent des conditions spéciales pour obtenir leurs graines.")
        print("- Ce calcul ne tient pas compte des bonus de qualité ou des transformations.")
    except Exception as e:
        print(f"\nErreur lors de l'exécution du programme : {e}")
        print("Veuillez vérifier que le fichier stardew_crops.json est correctement configuré.")

if __name__ == "__main__":
    main()