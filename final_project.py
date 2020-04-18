#Erin Murray
#erinvm

import secrets
import json
import requests

TREFLE_BASEURL = 'https://trefle.io/api/plants/'
TREFLE_KEY = secrets.TREFLE_API_KEY
CACHE_FILENAME = 'trefle_cache.json'
CACHE_DICT = {}
TEMP_PARAMS = {'duration': 'Perennial', 'palatable_browse_animal': 'Low', 'complete_data': 'true', 'growth_habit': 'Tree','temperature_minimum_deg_f': '-12'}



shade_tolerance = ['Tolerant', 'Intermediate', 'Intolerant']
bloom_period = [
                'Spring', 'Early Spring', 'Mid Spring','Late Spring', 
                'Summer', 'Early Summer', 'Mid Summer', 'Late Summer',
                'Fall', 'Winter', 'Late Winter', 'Indeterminate'
                ]
temperature_minimum_deg_f = 'float'
growth_habit = [
                'Forb/herb', 'Graminoid', 'Lichenous',
                'Nonvascular', 'Shrub', 'Subshrub', 'Tree', 'Vine'
                ]
mature_height = 'float'
palatable_browse_animal = ['Low', 'Moderate', 'High']
has_image = True
native_status = ''

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def make_request(baseurl):
    '''Make a request to the Web API using the baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the data returned from making the request in the form of 
        a dictionary
    '''
    endpoint = baseurl + 'token=' + TREFLE_KEY
    response = requests.get(endpoint)
    return response.json()

def make_request_with_cache(baseurl, params):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    '''
    params = {'q': hashtag, 'count': count}
    request_key = construct_unique_key(baseurl, params)
    '''
    request_key = construct_unique_key(baseurl, params)
    if request_key in CACHE_DICT.keys():
        print("cache hit!")
        return CACHE_DICT[request_key]
    else:
        print("cache miss!")
        CACHE_DICT[request_key] = make_request(request_key)
        save_cache(CACHE_DICT)
        return CACHE_DICT[request_key]
    print(CACHE_DICT)

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    try :
        if params.isdigit():
            unique_key = baseurl + params +'?'
    except:
        param_strings = []
        connector = '&'
        for key in params.keys():
            param_strings.append(f'{key}={params[key]}')
            unique_key = baseurl + '?' + connector.join(param_strings) + '&'
    return unique_key



def sort_trefle_json(trefle_results):
    plant_list = []
    for result in trefle_results:
        plant_dict = {}
        new_endpoint = result['link'].split('/')[-1]

        plant_link = make_request_with_cache(TREFLE_BASEURL, new_endpoint)
        try:
            image = plant_link['images'][0]['url'].split('_')
            if 'map' in image:
                try:
                    image = plant_link['images'][1]['url']
                except:
                    image = None
        except:
            image = None
        name = plant_link['common_name']
        duration = plant_link['duration']
        shade = plant_link['main_species']['growth']['shade_tolerance']
        bloom_period = plant_link['main_species']['seed']['bloom_period']
        zone_temp = plant_link['main_species']['growth']['temperature_minimum']['deg_f']
        shape = plant_link['main_species']['specifications']['growth_habit']
        height = plant_link['main_species']['specifications']['mature_height']['ft']
        native = plant_link['main_species']['native_status']
        deer = plant_link['main_species']['products']['palatable_browse_animal']

        plant_dict[name] = [name, zone_temp, duration, shape, bloom_period, shade, native, deer, height, image]
        try:
            name.title()
            plant_list.append(plant_dict)
        except:
            pass
    return plant_list

#potential search terms and keys

CACHE_DICT = open_cache()

params = TEMP_PARAMS
results = make_request_with_cache(TREFLE_BASEURL, TEMP_PARAMS)
plant_list = sort_trefle_json(results)
result_count = len(plant_list)
for plant in plant_list:
    for key in plant.keys():
        for item in plant[key]:
            print(item)

print(f'You have {result_count} plants to choose from!')

