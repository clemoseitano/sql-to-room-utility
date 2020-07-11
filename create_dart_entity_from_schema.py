import re
import os
import errno
import datetime
import argparse
# A program for converting an sql(ite) file into a model class for use with RoomDB for android

def get_input_args():
    """
    Retrieves and parses the 4 command line arguments provided by the user when
    they run the program from a terminal window.
    This function returns these arguments as an ArgumentParser object.
    Parameters:
     None - simply using argparse module to create & store command line arguments
    Returns:
     parse_args() -data structure that stores the command line arguments object  
    """
    # Create Parse using ArgumentParser
    parser = argparse.ArgumentParser()
    # Create 4 command line arguments
    parser.add_argument("-d", "--dir", type=str, help="The directory of the sql schema")
    
    return parser.parse_args()


def read_sql_file(sql_file):
    tables_dict = dict()
    print(sql_file)
    with open(sql_file, 'r') as file:
        #read the file as a single line
        data = file.read().replace('\n', '')
        data = data.replace('"', '`')
        # split the line into segments
        sql_data_segments = list(data.split(";"))
        for segment in sql_data_segments:
            # if not a create table statement, ignore it
            if "create table" not in segment.lower():
                continue
            else:
                # get the table name from the segment, 
                # the table name is the last word before the opening parentheses
                #print(segment)
                entity = clean(segment.split("(")[0].strip().split(" ")[-1])
                # print the entity name
                #print(entity)
                # get the text within the parentheses
                columns_data = re.search(r'\(.*\)', segment)
                #print(columns_data.group(0)[1:-1].strip())
                # split the text within the parentheses
                dirty_columns_data = columns_data.group(0)[1:-1].strip().split(",")
                                # add a primary key field if not was defined for any column
                if "primary key" not in ", ".join(dirty_columns_data).lower():
                    dirty_columns_data.append("\t`auto_incremented_id_field`\tINTEGER PRIMARY KEY AUTOINCREMENT")
                # remove unneccesary white space from the egdes of each word
                clean_columns_data = [x.strip().replace("\t", " ") for x in dirty_columns_data]
                #print(clean_columns_data)
                # get column names and other data
                column_names = [clean(x.split(" ")[0].strip()) for x in clean_columns_data]
                #print(column_names)
                # get the data types for each column
                column_data_types = [clean(x.split(" ")[1].strip()) for x in clean_columns_data]
                #print(column_data_types)
                # get other column data for each column
                other_column_data = list()
                for column in clean_columns_data:
                    if "primary key" in column.lower():
                        other_column_data.append("primary key")
                    elif "not null" in column.lower():
                        other_column_data.append("not null")
                    else:
                        other_column_data.append("")
                #print(other_column_data)
                # set the columns data for the entity in the dictionary
                tables_dict[entity] = list(zip(column_names, column_data_types, other_column_data))
                #print(list(tables_dict[entity]))
    #print(tables_dict)
    # return our tables data as a dictionary
    return tables_dict;

def clean(txt):
    return txt.strip("`").strip("'").strip('"')

def get_field_declarations(values):
    field_declarations = ""
    completed_fields = list()
    for field_name, data_type, field_qualifier in values:
        if field_name in completed_fields or field_name.lower() in ["foreign", "primary"]:# eliminate the foreign keys and primary key additional data
            continue
        else:
            completed_fields.append(field_name)
        field_declarations += "\n"
        # create a field declaration for our class
        # make a camel case variable name
        camel_cased_name = field_name.replace("_", " ").title().replace(" ", "")
        camel_cased_name = camel_cased_name[0].lower() + camel_cased_name[1:]
        
        # add the generic field data
        if "primary key" in field_qualifier:
            if "integer" in data_type.lower() or "timestamp" in data_type.lower():
                field_declarations += "\n{} {};".format("int get ", camel_cased_name)
            elif "real" in data_type.lower():
                field_declarations += "\n{} {};".format("double get ", camel_cased_name)
            else:
                field_declarations += "\n{} {};".format("String get ", camel_cased_name)
        else:
            if "integer" in data_type.lower() or "timestamp" in data_type.lower():
                field_declarations += "\n@BuiltValueField(wireName: \"{}\")\n{} {};".format(field_name, "int get ", camel_cased_name)
            elif "real" in data_type.lower():
                field_declarations += "\n@BuiltValueField(wireName: \"{}\")\n{} {};".format(field_name, "double get ", camel_cased_name)
            else:
                field_declarations += "\n@BuiltValueField(wireName: \"{}\")\n{} {};".format(field_name, "String get ", camel_cased_name)

    #print(field_declarations)
    return field_declarations

def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def lowerFirstLetter(name):
    return name[0].lower() + name[1:]

# write the entity class
def create_entity(class_name, class_field_declarations):
    class_name = clean(class_name)
    date = datetime.datetime.now()
    
    entity_class_content = f'''
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part '{camel_to_snake(class_name)}.g.dart';

//
// Created on {date}.
//
abstract class {class_name} implements Built<{class_name}, {class_name}Builder> {{
    {class_field_declarations}

    {class_name}._();
    static Serializer<{class_name}> get serializer => _${lowerFirstLetter(class_name)}Serializer;
    factory {class_name}([updates({class_name}Builder b)]) = _${class_name};
}}
    '''
    # write file
    filename = "data/{}.dart".format(camel_to_snake(class_name))
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, 'w+') as entity_file:
        entity_file.write(entity_class_content)

if __name__ == '__main__':
    in_arg = get_input_args()
    if in_arg is None:
        print("\n\nNo arguments provided\n\n")
        exit()
    elif in_arg.dir is None:
        print("\n\nNo sqlite database or schema provided\n\n")
        exit()

    # get arguments
    my_sql_schema = read_sql_file(in_arg.dir)
    
    #print(my_sql_schema)
    for key, value in my_sql_schema.items():
        # print(key.replace("_", " ").title().replace(" ", ""))
        # get class name
        class_name  = key.replace("_", " ").title().replace(" ", "")

        # get the fields for the entity
        class_field_declarations = get_field_declarations(value)
        
        create_entity(class_name, class_field_declarations)
