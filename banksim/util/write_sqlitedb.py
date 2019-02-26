def insert_simulation_table(cursor, task):
    """
    Insert a row into Simulation table
    :param conn:
    :param task:
    :return:
    """

    sql = '''INSERT INTO Simulation(simid,title,simdate) VALUES(?,?,?)'''
    cursor.execute(sql, task)
    return cursor.lastrowid
