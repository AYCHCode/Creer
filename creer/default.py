def default_type(obj, type_key='type', parent_name='"no parent name"', nullable=True):
    if not type_key in obj:
        raise Exception("no type to default for " + parent_name)

    if isinstance(obj[type_key], str): # transform it to a dict
        obj[type_key] = { 'name': obj[type_key] }

    this_type = obj[type_key]

    if 'name' not in this_type:
        raise Exception("no name for type in " + parent_name)

    this_type['nullable'] = None
    this_type['const'] = bool(this_type['const']) if 'const' in this_type else False

    CONST_KEYWORD = 'const '
    if this_type['name'].startswith(CONST_KEYWORD):
        this_type['const'] = True
        # remove the const from the start of the string
        this_type['name'] = this_type['name'][len(CONST_KEYWORD):]

    if this_type['name'].endswith('!') or this_type['name'].endswith('?'):
        this_type['nullable'] = this_type['name'].endswith('?')
        this_type['name'] = this_type['name'][:-1] # cut off ! or ? mark

    # if this is a shorthand list, e.g. GameObject[], format it
    if this_type['name'].endswith('[]'):
        this_type['valueType'] = this_type['name'][0:-2]  # cut off the '[]'
        this_type['name'] = 'list'

    this_type['is_game_object'] = this_type['name'][0].isupper() # primitives are always lower case, GameObjects are upper

    if this_type['is_game_object']:
        # game objects can be nullable
        this_type['nullable'] = bool(this_type['nullable']) if 'nullable' in this_type else nullable

    if this_type['name'] == "list" or this_type['name'] == "dictionary":
        if not 'valueType' in this_type:
            raise Exception("no 'valueType' for nested type " + parent_name)
        else:
            default_type(this_type, 'valueType', parent_name, nullable=False)
    else:
        this_type['valueType'] = None

    if this_type['name'] == "dictionary":
        if not 'keyType' in this_type:
            raise Exception("no keyType for " + parent_name)
        else:
            default_type(this_type, 'keyType', parent_name, nullable=False)
    else:
        this_type['keyType'] = None

def game_obj(obj, key):
    if not 'description' in obj:
        raise Exception("no 'description' in obj '{0}'".format(key))

    if not 'parentClasses' in obj:
        obj['parentClasses'] = [] # parentClasses are classes defined in the data

    if not 'serverParentClasses' in obj:
        obj['serverParentClasses'] = [] # these are defined on the server and not exposed to clients

    if not 'attributes' in obj:
        obj['attributes'] = {}

    if not 'attributes' in obj:
        obj['attributes'] = {}

    for attribute_key, attribute_parms in obj['attributes'].items():
        default_type(attribute_parms, 'type', "'{0}'s attribute '{1}'.".format(key, attribute_key))
        if not 'description' in attribute_parms:
            raise Exception("no 'description' in obj '{0}'s attribute '{1}'.".format(key, attribute_key))
        if not 'default' in attribute_parms:
            attribute_parms['default'] = None

    functions_for(obj, key)

def functions_for(obj, key):
    if not 'functions' in obj:
        obj['functions'] = {}

    for function_key, function_parms in obj["functions"].items():
        if not 'description' in function_parms:
            raise Exception("no 'description' in obj '{0}'s function '{1}'".format(key, function_key))

        if not 'serverPredefined' in function_parms:
            function_parms['serverPredefined'] = False

        if not 'altersState' in function_parms: # assume all functions alter the game state, unless explicity set in the data
            function_parms['altersState'] = True

        if not 'arguments' in function_parms:
            function_parms['arguments'] = []
        argument_names = []
        must_be_optional = False
        for i, arg_parms in enumerate(function_parms['arguments']):
            if not 'name' in arg_parms:
                raise Exception("no 'name' in obj '{0}'s function '{1}'s parameter at index {2}".format(key, function_key, i))
            default_type(arg_parms, 'type', "'{0}'s function '{1}'s parameter '{2}'".format(key, function_key, arg_parms['name']))
            if not 'description' in arg_parms:
                raise Exception("no 'description' in obj '{0}'s function '{1}'s parameter '{2}'".format(key, function_key, arg_parms['name']))
            if not 'default' in arg_parms:
                if must_be_optional:
                    raise Exception("all args must be optional from this point in obj '{0}'s function '{1}'s parameter '{2}'".format(key, function_key, arg_parms['name']))
                arg_parms['default'] = None
                arg_parms['optional'] = False
            else: # they defined a default value, so this argument is optional
                arg_parms['optional'] = True
                if not 'optionals_start_index' in function_parms:
                    function_parms['optionals_start_index'] = i
                    function_parms['optionals'] = 0
                function_parms['optionals'] += 1
                must_be_optional = True
            argument_names.append(arg_parms['name'])
        function_parms['argument_names'] = argument_names

        if 'returns' in function_parms:
            default_type(function_parms['returns'], 'type', "obj '{0}'s function '{1}'s return".format(key, function_key))
            if not 'description' in function_parms['returns']:
                raise Exception("no 'description' in obj '{0}'s function '{1}'s return".format(key, function_key))
            if not 'default' in function_parms['returns']:
                function_parms['returns']['default'] = None
        else:
            function_parms['returns'] = None