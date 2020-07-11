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
    parser.add_argument("-p", "--package", type=str, default="com.example.app", help="The package name of for the Java files")
    parser.add_argument("-f", "--dbfile", type=str, default="database.db", help="The database file name")
    parser.add_argument("-c", "--dbclass", type=str, default="AppDatabase", help="The database class name, without the java extension")
    
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
        
        if "primary key" in field_qualifier:
            # add the primary key constraint
            field_declarations += "\n{}".format("@PrimaryKey(autoGenerate = true)")
        elif "not null" in field_qualifier:
            # add the non null constraint
            field_declarations += "\n{}".format("@NonNull")

        # add the generic field data
        if "primary key" in field_qualifier:
            if "integer" in data_type.lower():
                field_declarations += "\n{} {};".format("private int", camel_cased_name)
            elif "real" in data_type.lower():
                field_declarations += "\n{} {};".format("private double", camel_cased_name)
            else:
                field_declarations += "\n{} {};".format("private String", camel_cased_name)
        else:
            if "integer" in data_type.lower():
                field_declarations += "\n@ColumnInfo(name = \"{}\")\n{} {};".format(field_name, "private int", camel_cased_name)
            elif "real" in data_type.lower():
                field_declarations += "\n@ColumnInfo(name = \"{}\")\n{} {};".format(field_name, "private double", camel_cased_name)
            else:
                field_declarations += "\n@ColumnInfo(name = \"{}\")\n{} {};".format(field_name, "private String", camel_cased_name)

    #print(field_declarations)
    return field_declarations


def get_constructor(class_name, values):
    class_name = clean(class_name)
    # create the constructor name and opening parentheses
    constructor_string = "public "+class_name+"("
    # append the constructor parameters
    completed_fields = list()
    for field_name, data_type, field_qualifier in values:
        if field_name in completed_fields or field_name.lower() in ["foreign", "primary"]:# eliminate the foreign keys and primary key additional data
            continue
        else:
            completed_fields.append(field_name)
        # make a camel case variable name
        camel_cased_name = field_name.replace("_", " ").title().replace(" ", "")
        camel_cased_name = camel_cased_name[0].lower() + camel_cased_name[1:]
        # exclude the priamry key
        if "primary key" not in field_qualifier:
            if "not null" in field_qualifier:
                constructor_string += "@NonNull "
            
            # append the field name to the constructor
            if "integer" in data_type.lower():
               constructor_string += "int "+camel_cased_name +", "
            elif "real" in data_type.lower():
                constructor_string += "double "+camel_cased_name +", "
            else:
                constructor_string += "String "+camel_cased_name +", "

    # remove trailing comma and space and append closing parentheses
    constructor_string = constructor_string.strip(", ") + ") {"
    # append the field initialiastions
    completed_fields = list()
    for field_name, data_type, field_qualifier in values:
        if field_name in completed_fields or field_name.lower() in ["foreign", "primary"]:# eliminate the foreign keys and primary key additional data
            continue
        else:
            completed_fields.append(field_name)
        # make a camel case variable name
        camel_cased_name = field_name.replace("_", " ").title().replace(" ", "")
        camel_cased_name = camel_cased_name[0].lower() + camel_cased_name[1:]
        # exclude the priamry key
        if "primary key" not in field_qualifier:
            constructor_string += "\nthis.{} = {};".format(camel_cased_name, camel_cased_name)

    # add closing braces
    constructor_string += "}\n"

    #return the constructor string
    #print(constructor_string)
    return constructor_string

def get_n_set(values):
    # append the getters and setters
    getters_n_setters = ""
    completed_fields = list()
    for field_name, data_type, field_qualifier in values:
        if field_name in completed_fields or field_name.lower() in ["foreign", "primary"]:# eliminate the foreign keys and primary key additional data
            continue
        else:
            completed_fields.append(field_name)
        getters_n_setters += "\n"
        # make a camel case variable name
        camel_cased_name = clean(field_name.replace("_", " ").title().replace(" ", ""))
        getter_setter_name = camel_cased_name
        camel_cased_name = camel_cased_name[0].lower() + camel_cased_name[1:]
        
        # get the data type
        d_type = "String"
        if "integer" in data_type.lower():
            d_type = "int"
        elif "real" in data_type.lower():
            d_type = "double"
        
        if "not null" in field_qualifier:
            getters_n_setters += f"public void set{getter_setter_name}(@NonNull {d_type} {camel_cased_name}) {{ \nthis.{camel_cased_name} = {camel_cased_name};\n}}\n\n"
            getters_n_setters += f"@NonNull\npublic {d_type} get{getter_setter_name}() {{ \nreturn this.{camel_cased_name};\n}}\n"
        else:
            getters_n_setters += f"public void set{getter_setter_name}({d_type} {camel_cased_name}) {{ \nthis.{camel_cased_name} = {camel_cased_name};\n}}\n\n"
            getters_n_setters += f"public {d_type} get{getter_setter_name}() {{ \nreturn this.{camel_cased_name};\n}}\n"

    # return our getters and setters
    #print(getters_n_setters)
    return getters_n_setters.replace("@NonNull\npublic int", "public int").replace("@NonNull int", "int").replace("@NonNull\npublic double", "public double").replace("@NonNull double", "double")

# write the dao class, this is rather straight forward
def create_dao(package_name, class_name, table_name):
    class_name = clean(class_name)
    #print(package_name)
    date = datetime.datetime.now()
    
    dao_interface_content = f'''
package {package_name}.data.dao;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import {package_name}.data.entity.{class_name};

import java.util.List;

/**
 * Created on {date}.
 */
@Dao
public interface {class_name}Dao {{
    /**
     * insert a singular item
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    public void insert({class_name} item);

    /**
     * insert multiple items
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    public void insertAll({class_name}... items);

    /**
     * delete all rows
     */
    @Query("DELETE FROM {table_name}")
    public void deleteAll();

    /**
     * @return all rows
     */
    @Query("SELECT * FROM {table_name}")
    List<{class_name}> getAll();
}}
    '''#.format(date, package_name, class_name, table_name)
    # write file
    filename = "data/dao/{}Dao.java".format(class_name)
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, 'w+') as entity_file:
        entity_file.write(dao_interface_content)



# write the entity class
def create_entity(package_name, class_name, table_name, class_field_declarations, class_constructor, class_getters_n_setters):
    class_name = clean(class_name)
    date = datetime.datetime.now()
    
    entity_class_content = f'''
package {package_name}.data.entity;

import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.Ignore;
import androidx.annotation.NonNull;
import androidx.room.PrimaryKey;

import static {package_name}.data.entity.{class_name}.TABLE_NAME;

/**
 * Created on {date}.
 */
@Entity(tableName = TABLE_NAME)
public class {class_name} {{
    /**
     * The table name
     */
    @Ignore
    public static final String TABLE_NAME = "{table_name}";

    {class_field_declarations}

    {class_constructor}

    {class_getters_n_setters}
}}
    '''
    # write file
    filename = "data/entity/{}.java".format(class_name)
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, 'w+') as entity_file:
        entity_file.write(entity_class_content)


# create the db class
def create_db_class(package_name, entities_list, version, database_class_name, database_name, dao_declarations):
    date = datetime.datetime.now()

    db_class_content = f'''
package {package_name}.data;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.sqlite.db.SupportSQLiteDatabase;

import {package_name}.BuildConfig;
import {package_name}.data.dao.*;
import {package_name}.data.entity.*;

/**
 * Created on {date}.
 */
@Database(entities = {{{entities_list}}}, version = {version})
public abstract class {database_class_name} extends RoomDatabase {{
    /**
     * The database file name
     */
    public static final String DATABASE_NAME = "{database_name}";

    {dao_declarations}

    // make the database a singleton
    private static volatile {database_class_name} INSTANCE;

    public static {database_class_name} getDatabase(final Context context) {{
        if (INSTANCE == null) {{
            synchronized ({database_class_name}.class) {{
                if (INSTANCE == null) {{
                    // Create database here
                    // In debug build, do not use Write Ahead Logging, so that we can view the sqlite file directly
                    if (!BuildConfig.DEBUG)
                        INSTANCE = Room.databaseBuilder(context.getApplicationContext(),
                                {database_class_name}.class, DATABASE_NAME)
                                .addCallback(sRoomDatabaseCallback)
                                .build();
                    else INSTANCE = Room.databaseBuilder(context.getApplicationContext(),
                            {database_class_name}.class, DATABASE_NAME)
                            .addCallback(sRoomDatabaseCallback).setJournalMode(JournalMode.TRUNCATE).build();
                }}
            }}
        }}
        return INSTANCE;
    }}

    private static RoomDatabase.Callback sRoomDatabaseCallback =
            new RoomDatabase.Callback() {{

                @Override
                public void onOpen(@NonNull SupportSQLiteDatabase db) {{
                    super.onOpen(db);
                }}
            }};
}}
    '''
    # write file
    filename = "data/{}.java".format(database_class_name)
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, 'w+') as entity_file:
        entity_file.write(db_class_content)


# create the data repository classes for handling data access in the background
def create_repository(package_name, database_class_name, entity_name):
    entity_name = clean(entity_name)
    date = datetime.datetime.now()

    # create a prepender for Dao instances
    mod_class_name = entity_name[0].lower() + entity_name[1:]

    repository_class_content = f'''
package {package_name}.data.repository;

import android.content.Context;
import android.os.AsyncTask;

import {package_name}.data.DataAccessListener;
import {package_name}.data.{database_class_name};
import {package_name}.data.dao.{entity_name}Dao;
import {package_name}.data.entity.{entity_name};

import java.util.ArrayList;
import java.util.List;

/**
 * Created on {date}.
 */
public class {entity_name}Repository extends BaseRepository {{
    private {database_class_name} db;
    private static {entity_name}Repository thisInstance;
    
    /**
     * A method to initialise the class and load the relevant data from the data streams provided
     *
     * @param context a {{@link Context}} instance to interact with the data
     */
    private {entity_name}Repository(Context context) {{
        db = {database_class_name}.getDatabase(context);
    }}

    public static synchronized {entity_name}Repository getInstance(Context context) {{
        if (thisInstance == null)
            thisInstance = new {entity_name}Repository(context);
        return thisInstance;
    }}

    /**
     * Asynchronously insert a  entity into our local database
     *
     * @param entity the entity to insert
     */
    public void insert({entity_name} entity) {{
        new Save{entity_name}sAsync(db).execute(entity);
    }}

    /**
     * Asynchronously insert a list of entities into our local database
     *
     * @param entity the entity to insert
     */
    public void insert({entity_name}[] entity) {{
        new Save{entity_name}sAsync(db).execute(entity);
    }}

    public void save{entity_name}s(List<{entity_name}> entities) {{
        if (entities != null) {{
            {entity_name}[] items = new {entity_name}[entities.size()];
            items = entities.toArray(items);
            new Save{entity_name}sAsync(db).execute(items);
        }}
    }}

    /**
     * A method to get the list of {{@link {entity_name}}}s in our database and notify listeners when the data is available.
     */
    public void load{entity_name}s() {{
        {entity_name}Repository.Get{entity_name}sAsync task = new {entity_name}Repository.Get{entity_name}sAsync(db, mDataAccessListener);
        task.execute();
    }}

    /**
     * An {{@link AsyncTask}} class for saving entity data
     */
    private static class Save{entity_name}sAsync extends AsyncTask<{entity_name}, Integer, Integer> {{
        private final {entity_name}Dao m{entity_name}Dao;

        Save{entity_name}sAsync({database_class_name} db) {{
            m{entity_name}Dao = db.{mod_class_name}Dao();
        }}

        @Override
        protected Integer doInBackground(final {entity_name}... params) {{
            m{entity_name}Dao.insertAll(params);
            return 0;
        }}

        @Override
        protected void onProgressUpdate(Integer... values) {{
            super.onProgressUpdate(values);
        }}

        @Override
        protected void onPostExecute(Integer integer) {{
            super.onPostExecute(integer);
        }}
    }}

    /**
     * A class to get entities asynchronously
     */
    private static class Get{entity_name}sAsync extends AsyncTask<Void, Integer, ArrayList<{entity_name}>> {{
        private final {entity_name}Dao m{entity_name}Dao;
        private DataAccessListener mDataAccessListener;
        private int requestCode = 0;

        Get{entity_name}sAsync({database_class_name} db, DataAccessListener listener) {{
            m{entity_name}Dao = db.{mod_class_name}Dao();
            mDataAccessListener = listener;
        }}

        @Override
        protected ArrayList<{entity_name}> doInBackground(final Void... params) {{
            return new ArrayList<>(m{entity_name}Dao.getAll());
        }}

        @Override
        protected void onProgressUpdate(Integer... values) {{
            super.onProgressUpdate(values);
        }}

        @Override
        protected void onPostExecute(ArrayList<{entity_name}> entities) {{
            super.onPostExecute(entities);
            if (entities != null)
                if (mDataAccessListener != null) {{
                    {entity_name}[] entitiesArray = new {entity_name}[entities.size()];
                    entitiesArray = entities.toArray(entitiesArray);
                    if (requestCode == 0)
                        mDataAccessListener.onDataLoaded(entitiesArray);
                    else mDataAccessListener.onDataRequestCompleted(requestCode, entitiesArray);
                }}
        }}
    }}
}}
    '''
    # write file
    filename = f"data/repository/{entity_name}Repository.java"
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, 'w+') as entity_file:
        entity_file.write(repository_class_content)

# create the base repository class
def create_base_repository(package_name):
    date = datetime.datetime.now()

    base_repository_content = f'''
package {package_name}.repository;

import androidx.annotation.Nullable;

import {package_name}.data.DataAccessListener;

/**
 * Created on {date}
 */
public class BaseRepository {{
    /**
     * A parameter for checking whether there is an observer waiting for the result for a data request or not
     */
    boolean hasPendingDataRequest = false;
    /**
     * A listener for reporting changes during data access
     */
    DataAccessListener mDataAccessListener = null;

    /**
     * A method to get the current data access listener for the class
     *
     * @return the {{@link DataAccessListener}} for the class
     */
    @Nullable
    public DataAccessListener getDataAccessListener() {{
        return mDataAccessListener;
    }}

    /**
     * A method to set the data access listener for the class
     *
     * @param listener the data access listener
     */
    public void setDataAccessListener(@Nullable DataAccessListener listener) {{
        this.mDataAccessListener = listener;
    }}
}}

    '''
    # write file
    filename = "data/repository/BaseRepository.java"
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, 'w+') as entity_file:
        entity_file.write(base_repository_content)


# create the base repository class
def create_data_listener(package_name):
    date = datetime.datetime.now()

    base_repository_content = f'''
package {package_name}.data;

/**
 * Created on {date}
 */
public interface DataAccessListener {{
    /**
     * A method to return results after a data query transaction is completed
     *
     * @param results the results returned
     */
    public void onDataLoaded(Object[] results);

    /**
     * A method to notify observers when data save has completed
     */
    public void onDataSaved();

    /**
     * A method to notify observers when data save has completed
     *
     * @param requestCode the request that initiated this action
     */
    default void onDataSaved(int requestCode) {{
    }}

    /**
     * A method to return results after a data query transaction is completed
     *
     * @param requestCode the code to use to differentiate results
     * @param results     the results returned
     */
    public void onDataRequestCompleted(int requestCode, Object[] results);
}}

    '''
    # write file
    filename = "data/DataAccessListener.java"
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, 'w+') as entity_file:
        entity_file.write(base_repository_content)


if __name__ == '__main__':
    in_arg = get_input_args()
    if in_arg is None:
        print("\n\nNo arguments provided\n\n")
        exit()
    elif in_arg.dir is None:
        print("\n\nNo sqlite database or schema provided\n\n")
        exit()

    # get arguments
    version = 1
    database_name = in_arg.dbfile
    package_name = in_arg.package
    database_class_name = in_arg.dbclass
    my_sql_schema = read_sql_file(in_arg.dir)
    
    entities_list = list()
    dao_declarations = list()
    
    #print(my_sql_schema)
    for key, value in my_sql_schema.items():
        # print(key.replace("_", " ").title().replace(" ", ""))
        # get class name
        class_name  = key.replace("_", " ").title().replace(" ", "")

        # get the fields for the entity
        class_field_declarations = get_field_declarations(value)
        
        # get the constructor for the entity
        class_constructor = get_constructor(class_name, value)
        
        # get the getters and setters for the entity
        class_getters_n_setters = get_n_set(value)

        # format the table name
        table_name = key.lower() + "s"
        if(key.lower()[-1]=="s"):
            table_name = key + "es"
        
        create_entity(package_name, class_name, table_name, class_field_declarations, class_constructor, class_getters_n_setters)

        create_dao(package_name, class_name, table_name)

        create_repository(package_name, database_class_name, class_name)

        # add the entity to the entities list
        entities_list.append(f"{class_name}.class")

        # add the dao to the dao list
        mod_class_name = class_name[0].lower() + class_name[1:]
        dao_declarations.append(f"public abstract {class_name}Dao {mod_class_name}Dao();")



    create_db_class(package_name, ", ".join(entities_list), version, database_class_name, database_name, "\n\n".join(dao_declarations))
    create_base_repository(package_name)
    create_data_listener(package_name)



