from django.db import connections

class mes_database:
    def select_sql(self, sql):
        with connections['default'].cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def select_sql_dict(self, sql):
        with connections['default'].cursor() as cur:
            cur.execute(sql)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    def select_sql_dict_param(self, sql, param):
        with connections['default'].cursor() as cur:
            cur.execute(sql, param)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    def execute_sql(self, sql):
        with connections['default'].cursor() as cur:
            cur.execute(sql)

class vnedc_database:
    def select_sql(self, sql):
        with connections['VNEDC'].cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def select_sql_dict(self, sql):
        with connections['VNEDC'].cursor() as cur:
            cur.execute(sql)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    def select_sql_dict_param(self, sql, param):
        with connections['VNEDC'].cursor() as cur:
            cur.execute(sql, param)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    def execute_sql(self, sql):
        with connections['VNEDC'].cursor() as cur:
            cur.execute(sql)