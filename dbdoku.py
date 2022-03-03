import sys
import os
import pyodbc
import codecs
import shutil
import datetime
from git import Repo
import re

#-------Settings--------------------------------------------------

uid = 'dbdoku' #username for SQL-Server.
pwd = 'secret' #password for SQL-Server.


#server=input #enable this to allow server input.
server = 'servername' #enable this to specify the server for automation.


#dsninput=input('Enter Database (A for ALL):') #enable this to allow database input.
dsninput = 'A' #enable this to specify database for automation.

archivedNamespace = 'old' #change to define your archive schema. Ignore if you dont have one.

logFileName = 'dbdoku.log' #change to specify the name of you log file. Ignore if you dont use one.


path = '/var/www/dbdoku/' #where to put the html files, linux style.
#path = 'C:\\Users\\username\\Desktop\\dbdoku\\' #where to put the html files, windows style.

PATH_OF_GIT_REPO = path+r".git"  #where is the git folder? usually inside path.
COMMIT_MESSAGE = "Changes from " + str(datetime.datetime.now()) #git commit message.

#-------End of Settings-------------------------------------------

#-------Functions-------------------------------------------------

def git_pull():
    try:
        repo = Repo(PATH_OF_GIT_REPO)
        repo.remotes.origin.pull()
        print("INFO ",datetime.datetime.now()," Pulling worked.")
    except:
        print("ERRO ",datetime.datetime.now()," Pulling failed!")

def git_push():
    print("INFO ",datetime.datetime.now()," Pushing started, this is definitely the last thing you should see in Git if you output this log to a file.")
    try:
        repo = Repo(PATH_OF_GIT_REPO)
        repo.git.add(all=True)
        repo.index.commit(COMMIT_MESSAGE)
        origin = repo.remote(name='origin')
        origin.push()
        print("INFO ",datetime.datetime.now()," Pushing worked.")
    except:
        print("ERRO ",datetime.datetime.now()," Pushing failed!")
        
        
def xstr(s):
    if s is None:
        return ''
    return str(s)

def depon(fi,constr,schema,table):
    fi.write("""
                        <h1>Dependencies</h1>
                        <div>
                            <h2>Dependent on this object</h2>
                            <table border='1'>
                                    <tr>
                                        <th>Schema</th>
                                        <th>Name</th>
                                        <th>Type</th>
                                    </tr>""")
    try:
        cnxndepon = pyodbc.connect(constr)
        cursordepon = cnxndepon.cursor()
        cursordepon.execute(""" SELECT referencing_schema_name,referencing_entity_name,referencing_class_desc
                                        FROM sys.dm_sql_referencing_entities ('"""+xstr(schema)+"""."""+xstr(table)+"""', 'OBJECT'); """)
        try:
            rowdepon = cursordepon.fetchone()
            while rowdepon:
                fi.write("""
                        <tr>
                            <td>"""+xstr(rowdepon[0])+"""</td>
                            <td>"""+xstr(rowdepon[1])+"""</td>
                            <td>"""+xstr(rowdepon[2])+"""</td>
                        </tr>""")
                try:
                    rowdepon = cursordepon.fetchone()
                except:
                     print("WARN ",datetime.datetime.now()," Here the server cant resolve a dependency, lets ignore that.")
        except:
            if (xstr(schema)!=archivedNamespace):
                print("ERRO ",datetime.datetime.now()," The first dependency was not resolvable, thats bad. We ignore this for now, this should be checked on the server!")
            else:
                print("WARN ",datetime.datetime.now()," The first dependency was not resolvable, thats not optimal. We ignore this, because the object is in the archived schema.")
        
        cursordepon.close()
        del cursordepon
        cnxndepon.close()
    except pyodbc.Error as e:
        if (xstr(schema)!=archivedNamespace):
            print("ERRO ",datetime.datetime.now()," SQL-Server threw an error, you should check on the server: ", e)
        else:
            print("WARN ",datetime.datetime.now()," SQL-Server threw an error, the object is in the archived schema, though: ", e)
    fi.write("""
                </table>
            </div>""")

def depof(fi,constr,schema,table):
    fi.write("""
            <div>
                <h2>Dependent on other objects</h2>
                <table border='1'>
                        <tr>
                            <th>Database</th>
                            <th>Schema</th>
                            <th>Name</th>
                            <th>Column</th>
                            <th>Type</th>
                        </tr>""")
    try:
        cnxndepof = pyodbc.connect(constr)
        cursordepof = cnxndepof.cursor()

        
        cursordepof.execute(""" SELECT
                                        referenced_database_name,referenced_schema_name,referenced_entity_name,referenced_minor_name,referenced_class_desc
                                    FROM
                                        sys.dm_sql_referenced_entities (
                                            '"""+xstr(schema)+"""."""+xstr(table)+"""',
                                            'OBJECT'); """)
        
        try:
            rowdepof = cursordepof.fetchone()
            while rowdepof:
                fi.write("""
                        <tr>
                            <td>"""+xstr(rowdepof[0])+"""</td>
                            <td>"""+xstr(rowdepof[1])+"""</td>
                            <td>"""+xstr(rowdepof[2])+"""</td>
                            <td>"""+xstr(rowdepof[3])+"""</td>
                            <td>"""+xstr(rowdepof[4])+"""</td>
                        </tr>""")
                try:
                    rowdepof = cursordepof.fetchone()
                except:
                    print("WARN ",datetime.datetime.now()," Here the server cant resolve a dependency, lets ignore that.")
        except:
            if (xstr(schema)!=archivedNamespace):
                print("ERRO ",datetime.datetime.now()," The first dependency was not resolvable, thats bad. We ignore this for now, this should be checked on the server!")
            else:
                print("WARN ",datetime.datetime.now()," The first dependency was not resolvable, thats not optimal. We ignore this, because the object is in the archived schema.")
        
        cursordepof.close()
        del cursordepof
        cnxndepof.close()
    except pyodbc.Error as e:
        if (xstr(schema)!=archivedNamespace):
            print("ERRO ",datetime.datetime.now()," SQL-Server threw an error, you should check on the server: ", e)
        else:
            print("WARN ",datetime.datetime.now()," SQL-Server threw an error, the object is in the archived schema, though: ", e)
    fi.write("""
            </table>
        </div>""")
    
def trigger(fi,constr,schema,table):
    fi.write("""
                        <h1>Trigger</h1>
                        <div>
                        <table border='1'>
                        <th>Name</th>
                        <th>IsUpdate</th>
                        <th>IsDelete</th>
                        <th>IsInsert</th>
                        <th>IsAfter</th>
                        <th>IsInsteadof</th>
                        <th>Disabled</th>
                        <th>Definition</th>
                            """)
    try:
        cnxntrigger = pyodbc.connect(constr)
        cursortrigger = cnxntrigger.cursor()
        cursortrigger.execute(""" SELECT 
        s.name AS table_schema 
        ,OBJECT_NAME(id) AS table_name 
        ,OBJECTPROPERTY( id, 'ExecIsUpdateTrigger') AS isupdate 
        ,OBJECTPROPERTY( id, 'ExecIsDeleteTrigger') AS isdelete 
        ,OBJECTPROPERTY( id, 'ExecIsInsertTrigger') AS isinsert 
        ,OBJECTPROPERTY( id, 'ExecIsAfterTrigger') AS isafter 
        ,OBJECTPROPERTY( id, 'ExecIsInsteadOfTrigger') AS isinsteadof 
        ,OBJECTPROPERTY(id, 'ExecIsTriggerDisabled') AS [disabled] 
        ,OBJECT_DEFINITION (OBJECT_ID(concat(s.name,'.',sysobjects.name))) AS trigger_definition

        FROM sysobjects 

        INNER JOIN sysusers 
            ON sysobjects.uid = sysusers.uid 

        INNER JOIN sys.tables t 
            ON sysobjects.parent_obj = t.object_id 

        INNER JOIN sys.schemas s 
            ON t.schema_id = s.schema_id 

        WHERE sysobjects.type = 'TR' 
        and t.name = '"""+xstr(table)+"""'
        and s.name = '"""+xstr(schema)+"""'; """)
        try:
            rowtrigger = cursortrigger.fetchone()
            while rowtrigger:
                fi.write("""
                        <tr>
                            <td>"""+xstr(rowtrigger[1])+"""</td>
                            <td>"""+xstr(rowtrigger[2])+"""</td>
                            <td>"""+xstr(rowtrigger[3])+"""</td>
                            <td>"""+xstr(rowtrigger[4])+"""</td>
                            <td>"""+xstr(rowtrigger[5])+"""</td>
                            <td>"""+xstr(rowtrigger[6])+"""</td>
                            <td>"""+xstr(rowtrigger[7])+"""</td>
                            <td><pre>"""+xstr(rowtrigger[8])+"""</pre></td>
                        </tr>""")
                rowtrigger = cursortrigger.fetchone()
        except:
            if (xstr(schema)!=archivedNamespace):
                print("ERRO ",datetime.datetime.now()," No Trigger found, even though one was determined beforehand.")
            else:
                print("WARN ",datetime.datetime.now()," No Trigger found, even though one was determined beforehand.  We ignore this, because the object is in the archived schema.")
        
        cursortrigger.close()
        del cursortrigger
        cnxntrigger.close()
    except pyodbc.Error as e:
        if (xstr(schema)!=archivedNamespace):
            print("ERRO ",datetime.datetime.now()," SQL-Server threw an error, you should check on the server: ", e)
        else:
            print("WARN ",datetime.datetime.now()," SQL-Server threw an error, the object is in the archived schema, though: ", e)
    fi.write("""
                </table>
            </div>""")
#-------End of Functions------------------------------------------

#-------Code------------------------------------------------------
dsnarray = []
print("INFO ",datetime.datetime.now(), ' Starting Script')


try:
    if dsninput == 'A':
        git_pull()
        fileList = os.listdir(path)
        for fileName in fileList:
            if fileName != logFileName and fileName != ".git" and fileName != "README.md":
                shutil.rmtree(path+fileName, ignore_errors=True) 
        print("INFO ",datetime.datetime.now(),' Starting with index.html...')
        fo = codecs.open(path+'index.html','w+', "utf-8")
        fo.write("""
        <ul>
        """)
        constr = "DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+";DATABASE=master;UID=" + uid + ";PWD="+ pwd +";"
        cnxn = pyodbc.connect(constr)
        cursor = cnxn.cursor()
        cursor.execute("""select name from sys.databases WHERE name NOT IN ('tempdb') and state_desc = 'ONLINE'; """)

        row = cursor.fetchone()
        while row:
            fo.write("""
                <li><a href ='"""+row[0]+"""/index.html'>"""+row[0]+"""</a></li>
            """)
            dsnarray.append(row[0])
            row = cursor.fetchone()
        fo.write("""
            </ul><br />"""+ str(datetime.datetime.now()))
        fo.close()
        cursor.close()
        del cursor
        cnxn.close()
    else:
        dsnarray.append(dsninput)
        shutil.rmtree(path+dsninput, ignore_errors=True)

    for dsn in dsnarray:
        print("INFO ",datetime.datetime.now(),' Generating for Database ',dsn)
        os.mkdir(path+dsn)
        os.mkdir(path+dsn+'/data')
        f = codecs.open(path+dsn+'/index.html','w+', "utf-8")

        header = ''
        body = ''
        footer = ''
        #----------------------------------
        #Header for HTML file
        #----------------------------------
        print("INFO ",datetime.datetime.now(),' Generating Header')
        header = """
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <title>"""+dsn+""" Doku</title>
            <style>
            * {
              box-sizing: border-box;
            }

            .column {
              float: left;
              width: 25%;
              padding: 10px;
            }

            /* Clear floats after the columns */
            .row:after {
              content: "";
              display: table;
              clear: both;
            }
            </style>
        </head>
          <body>
          <a href ="../index.html">Back</a>
        """
        f.write(header)

        #----------------------------------
        #Footer for HTML file
        #----------------------------------
        print("INFO ",datetime.datetime.now(),' Generating Footer')
        footer = """
            
          </body>
        </html>
        """
       
        #----------------------------------
        #Tables and Views
        #----------------------------------
        f.write("""<div class="row">""")
        types = ['BASE TABLE','VIEW']
        for tabletype in types:
            f.write("""
                    <div class="column">
                            <h1>"""+tabletype+"""</h1>
                        <ul>
                    """)
            constr = "DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+";DATABASE="+dsn+";UID=" + uid + ";PWD="+ pwd +";"
            cnxn = pyodbc.connect(constr)
            cursor = cnxn.cursor()
            if tabletype == 'BASE TABLE':
                cursor.execute("""SELECT
                            table_schema,table_name, (SELECT 
                                count(id)

                            FROM sysobjects 

                            INNER JOIN sysusers 
                                ON sysobjects.uid = sysusers.uid 

                            INNER JOIN sys.tables t 
                                ON sysobjects.parent_obj = t.object_id 

                            INNER JOIN sys.schemas s 
                                ON t.schema_id = s.schema_id 

                            WHERE sysobjects.type = 'TR' 
                            and t.name = table_name
                            and s.name = table_Schema)
                            FROM INFORMATION_SCHEMA.TABLES
                            WHERE TABLE_TYPE = '"""+tabletype+"""'
                            ORDER BY table_schema,TABLE_NAME""")
            else:
                cursor.execute("""SELECT
                            table_schema,table_name,isnull(OBJECT_DEFINITION (OBJECT_ID(concat(table_catalog,'.',table_SCHEMA,'.',table_NAME))),'')
                            FROM INFORMATION_SCHEMA.VIEWS
                            ORDER BY table_schema,TABLE_NAME""")

            row = cursor.fetchone()
            while row:
                print("INFO ",datetime.datetime.now(),' Generating',dsn,tabletype,row[0],row[1])
                f.write("""
                        <li>
                            <a href='data/"""+tabletype+'_'+row[0]+'_'+row[1]+""".html'>"""+row[0]+'.'+row[1]+"""</a>
                        </li>
                        """)
                fi = codecs.open(path+dsn+'/data/'+tabletype+'_'+row[0]+'_'+row[1]+'.html','w+', "utf-8")
                fi.write(header)
                fi.write("""
                        <table border ='1'>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Length</th>
                            </tr>
                            <tr>
                        """)
                cnxnfields = pyodbc.connect(constr)
                cursorfields = cnxnfields.cursor()
                cursorfields.execute("""declare @schema varchar(10) = '"""+xstr(row[0])+"""',@tabname varchar(255) = '"""+xstr(row[1])+"""'
                                                                    SELECT
                                    column_name,DATA_TYPE,isnull(CHARACTER_MAXIMUM_LENGTH,0)
                                                                    
                                    FROM INFORMATION_SCHEMA.COLUMNS
                                    WHERE TABLE_SCHEMA = @schema and table_name = @tabname
                                    ORDER BY ORDINAL_POSITION""")

                rowfields = cursorfields.fetchone()
                while rowfields:
                    fi.write("""
                                <td>"""+xstr(rowfields[0])+"""</td>
                                <td>"""+xstr(rowfields[1])+"""</td>
                                <td>"""+xstr(rowfields[2])+"""</td>
                            </tr>
                        """)           
                    rowfields = cursorfields.fetchone()
                
                fi.write("""
                        </table>
                        """)
                if tabletype == 'VIEW':
                     fi.write("""
                            <h1>SQL Code</h1>
                            <div>
                                <pre>"""+xstr(row[2])+"""</pre>
                            </div>
                            """)
                else:
                    fi.write("""
                            <h1>Foreign Keys</h1>
                            <div>
                                <table border='1'>
                                    <tr>
                                        <th>Name</th>
                                        <th>Table</th>
                                        <th>ColumnFrom</th>
                                        <th>ColumnTo</th>
                                    </tr>""")
                    cnxnfk = pyodbc.connect(constr)
                    cursorfk = cnxnfk.cursor()
                    cursorfk.execute("""declare @tabname varchar(255) = '"""+xstr(row[1])+"""'
                                                                                            SELECT
                                                c.CONSTRAINT_NAME,
                                                cu.TABLE_NAME AS ReferencingTable, 
                                                    cu.COLUMN_NAME AS ReferencingColumn,
                                                ku.TABLE_NAME AS ReferencedTable, 
                                                    ku.COLUMN_NAME AS ReferencedColumn
                                            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS c
                                            INNER JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE cu
                                            ON cu.CONSTRAINT_NAME = c.CONSTRAINT_NAME
                                            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                                            ON ku.CONSTRAINT_NAME = c.UNIQUE_CONSTRAINT_NAME
                                            WHERE cu.TABLE_NAME = @tabname""")

                    rowfk = cursorfk.fetchone()
                    while rowfk:
                        fi.write("""
                                <tr>
                                    <td>"""+xstr(rowfk[0])+"""</td>
                                    <td>"""+xstr(rowfk[3])+"""</td>
                                    <td>"""+xstr(rowfk[2])+"""</td>
                                    <td>"""+xstr(rowfk[4])+"""</td>
                                </tr>""")
                        rowfk = cursorfk.fetchone()


                    fi.write("""
                        </table>
                        </div>""")                    
                    cursorfk.close()
                    del cursorfk
                    cnxnfk.close()
                if tabletype == 'BASE TABLE':
                    if row[2] > 0:
                        trigger(fi,constr,xstr(row[0]),xstr(row[1]))  
                depon(fi,constr,xstr(row[0]),xstr(row[1]))
                if tabletype == 'VIEW':
                    depof(fi,constr,xstr(row[0]),xstr(row[1]))
                fi.write(footer)
                fi.close()
                cursorfields.close()
                del cursorfields
                cnxnfields.close()
                row = cursor.fetchone()
            f.write("""
                </ul>
            </div>
                    """)
            cursor.close()
            del cursor
            cnxn.close()
        #----------------------------------
        #Procedures and Functions
        #----------------------------------


        types = ['PROCEDURE','FUNCTION']
        for tabletype in types:
            f.write("""
                    <div class="column">
                        <h1>"""+tabletype+"""</h1>
                        <ul>""")
            cnxn = pyodbc.connect(constr)
            cursor = cnxn.cursor()
            cursor.execute("""select ROUTINE_SCHEMA,
                            ROUTINE_NAME,
                            isnull(DATA_TYPE,''),
                            isnull(CHARACTER_MAXIMUM_LENGTH,0),
                            isnull(OBJECT_DEFINITION (OBJECT_ID(concat(specific_catalog,'.',ROUTINE_SCHEMA,'.',ROUTINE_NAME))),'')
                                                    
                            from INFORMATION_SCHEMA.ROUTINES where ROUTINE_TYPE = '"""+tabletype+"'")

            row = cursor.fetchone()
            while row:
                print("INFO ",datetime.datetime.now(),' Generating',dsn,tabletype,row[0],row[1])
                f.write("""
                        <li>
                            <a href='data/"""+tabletype+'_'+row[0]+'_'+row[1]+""".html'>"""+row[0]+'.'+row[1]+"""</a>
                        </li>""")
                fi = codecs.open(path+dsn+'/data/'+tabletype+'_'+row[0]+'_'+row[1]+'.html','w+', "utf-8")
                fi.write(header)
                if tabletype == 'FUNCTION':
                    fi.write("""
                        <table border ='1'>
                            <tr>
                                <th>Type</th>
                                <th>Length</th>
                            </tr>
                            <tr>""")
                    fi.write("""
                            <td>"""+xstr(row[2])+"""</td>
                            <td>"""+xstr(row[3])+"""</td>
                        </tr>""")           
                    fi.write("""
                    </table>""")
                fi.write("""
                    <h1>SQL Code</h1>
                    <div>
                        <pre>"""+xstr(row[4])+"""</pre>
                    </div>""")
                depon(fi,constr,xstr(row[0]),xstr(row[1]))
                depof(fi,constr,xstr(row[0]),xstr(row[1]))
                fi.write(footer)
                fi.close()
                row = cursor.fetchone()
            f.write("""
                </ul>
            </div>""")
            cursor.close()
            del cursor
            cnxn.close()

    
                
        #------------------------------------------
        f.write("""
            </div>""")
        f.write(footer)
    print("INFO ",datetime.datetime.now()," Done")
    f.close()
    print("INFO ",datetime.datetime.now()," Now we start pushing to git.")
    git_push()
    print("INFO ",datetime.datetime.now()," And we are DONE!")
    exit
except:
     print("ERRO ",datetime.datetime.now()," Unexpected error:", sys.exc_info()[0])
     exit
#-------End of Code-----------------------------------------------
