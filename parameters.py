# The following dictionary defines, on each line,
# a value name (like the tag name of MuseScore) and the excel column name
# to which it is associated (the one on the second row)
legacy_names = {
    'original_title': "Titre original (sous-Titre d'une partition de la traduction)",
    'work-number': 'Ordre physique',
    'work-title': "Titre original (sous-Titre d'une partition de la traduction)",
    'rights': 'Copyright Internationale',
    'composer': 'Compositeur',
    'lyricist': 'Auteur',
    'arranger': 'Auteur',  # TODO
    # this is unused !
}

def column_infos_from_header(header):
    column_names = {}
    various_names_to_tag = {}
    for name in header.columns:
        if name and 'Unnamed:' not in name:
            verbose_name = header.iloc[2][name]
            column_names[name] = [name, verbose_name]
            various_names_to_tag[verbose_name] = name.split('.')[0]  # if titre.1 => titre
    # for key, value in legacy_names.items():
    #
    #     various_names_to_tag[value] =
    various_names_to_tag['original_title'] = 'titre'
    various_names_to_tag['work-title'] = 'titre'
    various_names_to_tag['rights'] = 'copyright'
    # TODO: add other translations here

    return column_names, various_names_to_tag
