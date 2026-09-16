# Maps OSM landuse/natural/leisure tags to SCS Curve Number categories.
# CN values assume average (HSG C-ish) soil conditions typical for Hyderabad.

CN_CATEGORIES = {
    "water": 98,
    "paved_urban": 92,
    "residential": 82,
    "vegetation": 65,
    "forest": 70,
    "farmland": 75,
    "bare_ground": 85,
}

# Maps each raw "key=value" OSM tag to one of the categories above.
TAG_TO_CATEGORY = {
    # Water
    "natural=water": "water",
    "natural=wetland": "water",
    "leisure=swimming_pool": "water",
    "leisure=marina": "water",
    "leisure=boating": "water",

    # Paved / built-up / impervious
    "landuse=commercial": "paved_urban",
    "landuse=retail": "paved_urban",
    "landuse=industrial": "paved_urban",
    "landuse=railway": "paved_urban",
    "landuse=construction": "paved_urban",
    "landuse=garages": "paved_urban",
    "landuse=governmental": "paved_urban",
    "landuse=military": "paved_urban",
    "landuse=landfill": "paved_urban",
    "landuse=brownfield": "paved_urban",
    "landuse=quarry": "paved_urban",
    "landuse=club": "paved_urban",
    "leisure=stadium": "paved_urban",
    "leisure=sports_centre": "paved_urban",
    "leisure=fitness_centre": "paved_urban",
    "leisure=indoor_play": "paved_urban",

    # Residential / institutional
    "landuse=residential": "residential",
    "landuse=religious": "residential",
    "landuse=school": "residential",
    "landuse=education": "residential",
    "landuse=hospital Grounds": "residential",
    "landuse=Hospital Grounds": "residential",
    "landuse=yes": "residential",

    # Vegetation / open green space
    "leisure=park": "vegetation",
    "leisure=pitch": "vegetation",
    "leisure=playground": "vegetation",
    "leisure=garden": "vegetation",
    "leisure=track": "vegetation",
    "leisure=golf_course": "vegetation",
    "leisure=recreation_ground": "vegetation",
    "leisure=nature_reserve": "vegetation",
    "leisure=dog_park": "vegetation",
    "leisure=sport": "vegetation",
    "landuse=grass": "vegetation",
    "landuse=recreation_ground": "vegetation",
    "landuse=meadow": "vegetation",
    "landuse=village_green": "vegetation",
    "landuse=allotments": "vegetation",
    "natural=grassland": "vegetation",
    "natural=scrub": "vegetation",
    "natural=heath": "vegetation",
    "natural=tree_row": "vegetation",

    # Forest
    "natural=wood": "forest",
    "landuse=forest": "forest",

    # Farmland
    "landuse=farmland": "farmland",
    "landuse=orchard": "farmland",
    "landuse=plant_nursery": "farmland",

    # Bare ground
    "natural=sand": "bare_ground",
    "natural=bare_rock": "bare_ground",
    "natural=rock": "bare_ground",
    "natural=stone": "bare_ground",
    "natural=hill": "bare_ground",
}

DEFAULT_CATEGORY = "residential"  # fallback for any tag we haven't seen


def get_cn(tags: dict) -> int:
    """Given an OSM tags dict, return the Curve Number for this feature."""
    for key in ["landuse", "natural", "leisure"]:
        if key in tags:
            tag_str = f"{key}={tags[key]}"
            category = TAG_TO_CATEGORY.get(tag_str, DEFAULT_CATEGORY)
            return CN_CATEGORIES[category]
    return CN_CATEGORIES[DEFAULT_CATEGORY]