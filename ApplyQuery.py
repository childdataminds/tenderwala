import mysql.connector
def Where_Query(value,exp):

    where_final = ""
    for i in range(len(value)):
        if i != 0:
            if exp == "del":
               where_final += " AND "
            else:
                where_final += ","
        where_final += str(value[i]) + "=%s"
    return where_final
def Set_Columns(col):
    cols = ""
    unknowns = ""
    for i in range(len(col)):
        if i != 0:
            unknowns += ","
            cols += ","
        unknowns += "%s"
        cols += col[i]
    return cols,unknowns

def Query(parent,col=None, value=None, query=None,where=None):
    connection_pool = parent['database']
    conn = connection_pool.get_connection()
    table = parent['table']
    # conn = sqlite3.connect(database)
    cursor = conn.cursor()
    if col != None:
        cols,unknowns = Set_Columns(col)
    else:
        cols = unknowns = ""

    if query == "INSERT":
        statement= "INSERT INTO %s(%s)VALUES(%s)" % (table,cols,unknowns)
    elif query == "CREATE":
        statement = "CREATE TABLE IF NOT EXISTS %s(%s)" % (table,cols)
    elif query == "SELECT":
        if where != None:
           where_final = Where_Query(where,"del")
           statement = "SELECT %s FROM %s WHERE %s" % (cols,table,where_final)
        else:
            statement = "SELECT %s FROM %s" % (cols,table)
    elif query == "UPDATE":
        cols_final = Where_Query(col,"=%s")
        where_final = Where_Query(where,"del")
        statement = "UPDATE %s SET %s WHERE %s" % (table,cols_final,where_final)
    elif query == "DELETE":
        if where != None:
            where_final = Where_Query(where,"del")
            statement = "DELETE FROM %s WHERE %s" % (table,where_final)
        else:
            statement = "DELETE FROM %s" % (table,)
    else:
        statement = "NONE"
    # print(statement)
    result = "None"
    if statement != "NONE":
        # try:
        if query == "CREATE" or (query == "SELECT" and where == None) or (query == "DELETE" and where == None):
            try:
               cursor.execute(statement)
            except mysql.connector.Error as err:
                return {"status":False,"message":"Error executing SQL query: %s. For query: %s" % (err,statement)}
        else:
            try:
               cursor.execute(statement, value)
            except mysql.connector.Error as err:
                return {"status":False,"message":"Error executing SQL query: %s. For query: %s" % (err,statement)}
        if query == "SELECT":
            try:
               result = cursor.fetchall()
               result = {"status":True,"data":result}
            except mysql.connector.Error as err:
                return {"status":False,"message":"Error executing SQL query: %s" % err}
        else:
            result = {"status":True,"message":"Done"}
        
        # except sqlite3.Error as err:
        #     return err
    

    conn.commit()
    cursor.close()
    conn.close()
    return result