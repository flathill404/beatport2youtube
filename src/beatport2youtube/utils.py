def get_search_query(beatport_result):
    """Construct a search string for YouTube based on Beatport results."""
    search_string = f"{beatport_result['name']} {beatport_result['mix_name']} {beatport_result['isrc']}"

    return search_string
