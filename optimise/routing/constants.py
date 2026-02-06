messages_fr = {
    "WAS_SCHEDULED_BUT_DROPPED": "Était programmé mais abandonné. Ne correspondait pas au planning.",
    "OUTSIDE_OPTIMISATION_PERIOD": "Était en dehors de la période d'optimisation. N'a jamais été programmé.",
    "NO_SKILL_MATCH": "N'a pas été programmé car aucune {0} correspondance de compétence.",
    "TIME_CONSTRAINT_INCORRECT": " Contrainte temporelle incorrecte, l'heure de début est après l'heure de fin.",
    "LARGE_WORK_DURATION": "La durée du travail est supérieure à la plage horaire disponible.",
    "SPARE_PART_AVAILABILITY": "La pièce de rechange n'est disponible qu'après la date de début obligatoire.",
    "time_unit_missing": "Clé 'time_unit' manquante.",
    "unsupported_time_unit": "Unité de time_unit non prise en charge: {0}",
    "unsupported_day_min_unit": "Unité 'day_min_unit' non prise en charge, valeurs prises en charge: [{0}], obtenu: {1}",
    "missing_required_keys": "Clés requises manquantes dans JSON.",
    "orders_should_be_list": "'orders' devrait être une liste.",
    "teams_should_be_dict": "'teams' devrait être un dictionnaire.",
    "optimization_horizon_greater": "'optimization_horizon' devrait être supérieur à 0.",
    "optimization_target": "optimization_target devrait être un de: {0}",
    "failed_to_create_optimization_instances": "Échec de la création des instances d'optimisation, {0}",
    "failed_to_add_order_to_instance": "Impossible d'ajouter la commande à l'instance, avec l'identifiant de commande: {0}, {1}",
    "missing_required_field": "Champ requis manquant: {}",
    "failed_to_add_worker_to_instance": "Impossible d'ajouter le travailleur à l'instance, avec l'identifiant du travailleur: {0} {1}",
    "failed_to_create_instance": "Impossible de créer l'instance, {0}",
    "missing_key_in_worker_dict": "Clé manquante dans le dictionnaire du travailleur {0}",
    "worker_has_no_skills": "Le travailleur n'a pas de compétences définis",
    "worker_has_no_depot": "Le travailleur n'a pas de dépôt définis",
    "order_priority_between": "La priorité de la commande doit être comprise entre 1 et 5. Valeurs obtenues pour (id,priority) : ({0},{1})",
    "missing_order_field": "Le champ 'order' est manquant: {0}",
    "error_processing_order": "Erreur de traitement de la commande: {0}, {1}",
    "must_start_datetime_conflict": "'must_start_datetime' ne peut pas être postérieur à 'latest_end_datetime'",
    "invalid_status_for_delete_routing_solution": "Suppression invalide due au paramètre 'status': {0}. Vous pouvez supprimer les solutions de routage avec le 'status' 'FINISHED' ou 'FAILED'.",
    "successfully_deleted_routing_solutions": "Solutions de routage supprimées avec succès: {0}",
    "invalid_status_for_download_routing_solution": "Vous ne pouvez télécharger que les solutions avec le 'status' 'FINISHED', 'status' actuel: {0}.",
    "neither_time_matrix_nor_distance_matrix_defined": "Ni 'time_matrix' ni 'distance_matrix' ne sont définis.",
    "failed_to_create_instance_from_dict": "Impossible de créer une instance à partir du dictionnaire, {0}",
    "error_in_time_interval": "Erreur dans l'intervalle de temps: le début ne peut pas être supérieur à la fin. Obtenu début={0}, fin={1}",
    "date_value_should_be_datetime_or_string": "La valeur de la date doit être un objet datetime ou string.",
    "no_destinations_provided":"Aucune destination fournie et aucune donnée enregistrée disponible.",
    "unsupported_distance_matrix_method": "Méthode 'distance matrix' non prise en charge: {0}. Méthodes disponibles: {1}",
    "solution_routing_not_found": "'Routing solution' non trouvée pour l'identifiant: {0}",
    "delete_solution_routing_not_allowed": "la suppression de la solution de routage avec l'identifiant : {0} n'est pas autorisée lorsque l'optimisation est en cours",
    "optimization_has_started": "l'optimisation a commencé",
    "optimization_has_finished": "l'optimisation a fini",
    "optimizing_for_skill": "optimisation pour la compétence {0}",
    "invalid_time_unit": "Unité de temps invalide. 'from_unit': {0}, 'to_unit': {1}",
    "preprocessing_request": "Requête de prétraitement",
}

messages_en = {
    "WAS_SCHEDULED_BUT_DROPPED": 'Was Scheduled but Dropped. Did not fit in planing.',
    "OUTSIDE_OPTIMISATION_PERIOD": 'Was outside optimisation period. Was never scheduled.',
    "NO_SKILL_MATCH": 'Was not scheduled because no {0} skill match.',
    "TIME_CONSTRAINT_INCORRECT": 'Incorrect Time constraint, start time is after end time',
    "LARGE_WORK_DURATION": 'Work duration is larger than available time span.',
    "SPARE_PART_AVAILABILITY": 'Spare part availability is after the must start date',
    "time_unit_missing": "Missing 'time_unit' key.",
    "unsupported_time_unit": "Unsupported time unit: {0}",
    "unsupported_day_min_unit": "Unsupported day_min_unit, supported values: [{0}], got: {1}",
    "missing_required_keys": "Missing required keys in JSON.",
    "orders_should_be_list": "'orders' should be a list.",
    "teams_should_be_dict": "'teams' should be a dict.",
    "optimization_horizon_greater": "'optimization_horizon' should be greater than 0.",
    "optimization_target": "optimization_target should be one of: {0}",
    "failed_to_create_optimization_instances": "Failed to create optimization instances, {0}",
    "failed_to_add_order_to_instance": "Failed to add order to instance, with order id: {0}, {1}",
    "missing_required_field": "Missing required field: {0}",
    "failed_to_add_worker_to_instance": "Failed to add worker to instance, with worker id: {0} {1}",
    "failed_to_create_instance": "Failed to create instance, {0}",
    "missing_key_in_worker_dict": "Missing key in worker dictionary, {0}",
    "worker_has_no_skills": "Worker has no skills defined",
    "worker_has_no_depot": "Worker has no depot defined",
    "order_priority_between": "Order priority must be between 1 and 5. Got values for (id,priority): ({0},{1})",
    "missing_order_field": "Missing order field: {0}",
    "error_processing_order": "Error processing order: {0}, {1}",
    "must_start_datetime_conflict": "must_start_datetime cannot be later than latest_end_datetime",
    "invalid_status_for_delete_routing_solution": "Invalid remove by 'status' parameter: {0}. You can remove routing solutions with status 'FINISHED' or 'FAILED'.",
    "successfully_deleted_routing_solutions": "Successfully deleted {0} routing solutions.",
    "invalid_status_for_download_routing_solution": "You can only download the solutions with status 'FINISHED', current status: {0}.",
    "neither_time_matrix_nor_distance_matrix_defined": "Neither time_matrix nor distance_matrix defined.",
    "failed_to_create_instance_from_dict": "Failed to create instance from dict, {0}",
    "error_in_time_interval": "Error in time interval: start cannot be greater than end. Got start={0}, end={1}",
    "date_value_should_be_datetime_or_string": "Date value should be a datetime object or a string.",
    "no_destinations_provided":"No destinations provided and no saved data available.",
    "unsupported_distance_matrix_method": "Unsupported distance matrix method: {0}. Available methods: {1}",
    "solution_routing_not_found": "Routing solution not found for id: {0}",
    "delete_solution_routing_not_allowed": "deleting routing solution with id : {0} is not allowed when optimization is in progress",
    "optimization_has_started": "optimization has started",
    "optimization_has_finished": "optimization has finished",
    "optimizing_for_skill": "optimizing for skill {0}",
    "invalid_time_unit": "Invalid time unit. 'from_unit': {0}, 'to_unit': {1}",
    "preprocessing_request": "Preprocessing request",



}


def translate(message, language):
    if not language:
        language = 'en'
    if language == 'fr':
        return messages_fr.get(message, message)
    elif language == 'en':
        return messages_en.get(message, message)
    else:
        raise ValueError(f"Language {language} not supported.")

