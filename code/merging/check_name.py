
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Filter the merged_df for the season 2016-2017
filtered_df = merged_df[merged_df['Season'] >= '2016-2017'].copy()

# Clean some dirty characters
filtered_df['Player'] = filtered_df['Player'].str.replace('A\(c\)','e')
filtered_df['Player'] = filtered_df['Player'].str.replace('A\(r\)','i')
filtered_df['Player'] = filtered_df['Player'].str.replace('A 1/4 ','u')
filtered_df['Player'] = filtered_df['Player'].str.replace('A-','i')
filtered_df['Player'] = filtered_df['Player'].str.replace('A\+-','n')
filtered_df['Player'] = filtered_df['Player'].str.replace('A,','o')
filtered_df['Player'] = filtered_df['Player'].str.replace('A!','a')

# All unique player names
names = list(filtered_df['Player'].unique())

# Build a dictionary with all names matched by the algorithm for each name in the list
THRESHOLD = 0.7
matches = dict()
for name in names:
    results = process.extractBests(name, names, scorer=fuzz.token_set_ratio,
                                   score_cutoff=THRESHOLD)
    matches[name] = []
    for result in results:
        if result[0] == name:
            continue
        if result[1] > 80:
            matches[name].append(result)


# Empty dict that will store for each name:
# - The name to which it maps to (e.g. 'Aleix Garcia Serrano' maps to 'Aleix Garcia')
# - The name(s) that maps to it (e.g. 'Aleix Garcia' is mapped by 'Aleix Garcia')
# - The name(s) that are a false match (e.g. 'Alexis Sanchez' is ignored by 'Aleix Garcia')
matches_final = dict()

# For every unique name build an empty dict that will store the data
for name in matches.keys():
    
    # If the algorithm didn't find any possible match is skipped
    if len(matches[name]) == 0:
        continue
    
    # Empty dict for the name
    matches_final[name] = {
        'Mapped_by': set(),  # If exists, a set of name(s) that refer to this name
        'Maps_to': '',       # If exists, a name to which this one should refer t
        'Ignores': set()     # If exists, a set of bad matches that should be ignored
        }

# For every name that had at least a match by the algorithm...
for name in matches_final.keys(): 
    
    # -------------------- MULTI-NAME CHECK SECTION --------------------
    # This part of the code checks wheter all the names that have a possible relationship refer
    # to the same player or not
    
    # Starting from a name (name) gathers all the name that could be related and stores them in the
    # names_checked list
    names_to_check = [name]
    names_checked = []
    while len(names_to_check) > 0:
        for el in matches[names_to_check[0]]:
            if el[0] not in names_checked:
                if el[0] not in names_to_check:
                    names_to_check.append(el[0])
        names_checked.append(names_to_check[0])
        names_to_check.pop(0)
    
    # Asks wheter all those names refer to the same player; if so, it asks to point which name is
    # the correct one and the data will be updated accordingly
    print('\nDo the following names all refer to the same player?')
    for el in names_checked:
        print(f' {names_checked.index(el)+1}. {el}')
    idx = input('If so, enter the number of the proper name, otherwise enter nothing: ')
    
    if idx.isdigit():
        
        idx = int(idx)-1
        
        if idx > (len(names_checked)-1) or idx < 0:
            raise IndexError('The entered number is not one of the choices')
        
        for name_checked in names_checked:
            
            if name_checked == names_checked[idx]:
                continue
                
            else:
                matches_final[name_checked]['Maps_to'] = names_checked[idx]
                matches_final[names_checked[idx]]['Mapped_by'].add(name_checked)
                
                for name_to_ignore in names_checked:
                    if name_to_ignore != names_checked[idx] and name_to_ignore != name_checked:
                        matches_final[name_checked]['Ignores'].add(name_to_ignore)
        
    elif len(idx) == 0:
        
        # If the names were just two and they do not refer to the same player, an ignore
        # relationship is set between the two so they will not be analized in the name-to-name
        # section
        if len(names_checked) == 2:
            matches_final[names_checked[0]]['Ignores'].add(names_checked[1])
            matches_final[names_checked[1]]['Ignores'].add(names_checked[0])
        continue
    
    else:
        raise ValueError('The entered value is invalid')
        
    # -------------------- NAME-TO-NAME MATCH SECTION --------------------
    # For names that still have unresolved matches, check them
            
    for el in matches[name]:
        
        # Skip the matched name if it has already a relationship with the key name ('name' variable)
        if el[0] in matches_final[name]['Mapped_by'] or el[0] == matches_final[name]['Maps_to']\
            or el[0] in matches_final[name]['Ignores']:
                continue
        
        # Asks if the two names matches
        check = input(f'Is {el[0]} a good match for {name} ([y]/n)? ' )
        
        # If so, it asks to choos which of the two should be considered the proper one and update
        # the data accordingly
        if (len(check) == 0) or (check == 'y'):
            check = input(f'-> {el[0]} or {name} should be the proper name (1/2)? ' )
            
            if check == '1':
                matches_final[name]['Maps_to'] = el[0]
                matches_final[el[0]]['Mapped_by'].add(name)
                
            elif check == '2':
                matches_final[el[0]]['Maps_to'] = name
                matches_final[name]['Mapped_by'].add(el[0])
                
            else:
                raise ValueError(f'{check} is an invalid answer')
                
        # If they do not match an ignore relationship is set between the two
        elif check == 'n':
            matches_final[name]['Ignores'].add(el[0])
            matches_final[el[0]]['Ignores'].add(name)
        
        else:
            raise ValueError(f'{check} is an invalid answer')
