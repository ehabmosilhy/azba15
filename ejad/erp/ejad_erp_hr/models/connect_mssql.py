# -*- coding: utf-8 -*-


from odoo import api, fields, models
from datetime import datetime


class ConnectMssql(models.Model):
    _name = "connect.mssql"
    _description = 'Connect to MS SQL Server'

    server_name = fields.Char('Server', required=True, help="The server name, could be an IP or a URL")
    database_name = fields.Char('Database name', required=True)
    user_name = fields.Char('User name', required=True)
    password = fields.Char('Password', required=True)
    query = fields.Text('SQL Query/Instruction',
                        help="A Select statement or an insert/update/delete instruction")
    result = fields.Text('Result')

    #
    # def execute_query1(self):
    #     try:
    #         import pymssql
    #         conf = self.env['connect.mssql'].search([])
    #         if conf:
    #             # Connection Parameters
    #             conf = conf[0]
    #             my_server = conf.server_name
    #             my_user = conf.user_name
    #             my_database = conf.database_name
    #             my_password = conf.password
    #             conn = pymssql.connect(server=my_server, user=my_user, password=my_password, database=my_database)
    #             cursor = conn.cursor()
    #             my_query = 'select user_id,row,su_date_start,su_actual_in,su_actual_out from inoutrep where row in (1,2,3,4,5,6,7,8)'
    #             cursor.execute(
    #                 'select user_id,row,su_date_start,su_actual_in,su_actual_out from inoutrep where row in (1,2,3,4,5,6,7,8)')
    #         # Make the connection and execute the query
    #
    #
    #             cursor.execute(my_query)
    #
    #             # Check whether the query is a select statement or an insert/update/delete instruction
    #             if my_query.strip().split(" ")[0].lower() == "select":
    #                 rows = cursor.fetchall()
    #                 my_result = ""
    #                 for i in rows:
    #                     for x in i:
    #                         my_result += "\t" + str(x)
    #                     my_result += "\n"
    #
    #                 # Show the result
    #                 self.result = my_result
    #             else:
    #                 conn.commit()
    #                 self.result = "Statement executed successfully, please check your database or make a select statement."
    #             conn.close()
    #
    #     except:
    #         self.result = "An Error Occurred, please check your parameters!\n" \
    #                       "And make sure (pymssql) is installed (pip3 install pymssql)."
