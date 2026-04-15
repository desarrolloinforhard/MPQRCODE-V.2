import json
import pypyodbc
import traceback
import re
import os
from DBFManager import DBFManager
import sys

def cargar_dict_tablas_desde_json(nombre_archivo="TABLAS_DBA.json"):
    if getattr(sys, 'frozen', False):
        # Ejecutado como .exe compilado con PyInstaller
        base_path = os.path.dirname(sys.executable)
    else:
        # Ejecutado como script .py
        base_path = os.path.dirname(__file__)

    ruta_absoluta = os.path.join(base_path, nombre_archivo)
    print(f"[🔍] Leyendo JSON desde: {ruta_absoluta}")

    try:
        with open(ruta_absoluta, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: [tuple(c) for c in v] for k, v in data.items()}
    except Exception as e:
        print(f"❌ Error al cargar el archivo JSON de tablas: {e}")
        return {}

    
def normalizar_tipo(tipo: str) -> str:
    tipo = tipo.lower().replace(" ", "")

    # Eliminar decoradores como PRIMARY KEY, NOT NULL, IDENTITY
    for palabra in ["primarykey", "notnull", "identity"]:
        tipo = tipo.replace(palabra, "")

    # Normalizar los tipos base
    if tipo in ["int", "integer"]:
        return "int"
    if tipo.startswith("varchar"):
        return "varchar"  # Ignora longitud para comparación lógica
    if tipo.startswith("float"):
        return "float"
    if tipo.startswith("bit"):
        return "bit"
    if tipo == "text":
        return "text"
    if tipo == "money":
        return "money"
    if tipo == "datetime":
        return "datetime"

    return tipo.strip()


class ConexionSybase:
    def __init__(self, **kwargs):
        self.dsn_name = kwargs["DSN"]
        self.usuario = kwargs["UID"]
        self.contrasena = kwargs["PWD"]
        self.conexion = None
        self.cursor = None

    def conectar(self):
        try:
            self.conexion = pypyodbc.connect(
                DSN=self.dsn_name,
                user=self.usuario,
                password=self.contrasena,
                Driver="{Adaptive Server Anywhere 9.0}"
            )
            self.cursor = self.conexion.cursor()
        except pypyodbc.Error as err:
            print(f"Error al conectar a Sybase: {err}")

    def desconectar(self):
        if self.conexion:
            self.conexion.close()

    def obtener_columnas_tabla(self, nombre_tabla):
        try:
            self.conectar()
            query = f"""
                SELECT c.column_name
                FROM syscolumn c
                JOIN systable t ON c.table_id = t.table_id
                WHERE t.table_name = '{nombre_tabla.upper()}'
            """
            self.cursor.execute(query)
            columnas = [fila[0] for fila in self.cursor.fetchall()]
            return columnas
        except Exception as e:
            print(f"Error al obtener columnas de la tabla {nombre_tabla}: {e}")
            return []

    
    
    def crear_tabla_generica(self, nombre_tabla, columnas):
        """Crea una tabla según el diccionario.

        - El JSON actual marca PRIMARY KEY en cada columna de la PK compuesta.
        - ASA requiere UNA sola PK de nivel tabla: PRIMARY KEY (col1, col2, ...)
        """
        try:
            self.conectar()

            pk_cols = []
            cols_sql_parts = []

            for nombre, tipo in columnas:
                tipo_str = str(tipo)

                if 'PRIMARY KEY' in tipo_str.upper():
                    pk_cols.append(nombre)
                    # quitar PRIMARY KEY del tipo de columna (se vuelve constraint de tabla)
                    tipo_str = re.sub(r'\bPRIMARY\s+KEY\b', '', tipo_str, flags=re.I)
                    tipo_str = ' '.join(tipo_str.split())

                cols_sql_parts.append(f"{nombre} {tipo_str}")

            columnas_sql = ',\n    '.join(cols_sql_parts)

            if pk_cols:
                columnas_sql += ',\n    PRIMARY KEY (' + ', '.join(pk_cols) + ')'

            query = f"CREATE TABLE {nombre_tabla} (\n    {columnas_sql}\n)"
            self.cursor.execute(query)
            self.conexion.commit()
            print(f"✅ Tabla {nombre_tabla} creada con éxito.")
        except Exception as e:
            print(f"❌ Error al crear la tabla {nombre_tabla}: {e}")

    def actualizar_tabla_desde_dict(self, nombre_tabla, columnas):
        columnas_actuales = self.obtener_columnas_tabla(nombre_tabla)
        columnas_deseadas = [col[0] for col in columnas]

        if not self.tabla_existe(nombre_tabla):
            print(f"🆕 Tabla {nombre_tabla} no existe. Creando...")
            self.crear_tabla_generica(nombre_tabla, columnas)
            return
        elif not columnas_actuales:
            print(f"⚠️ La tabla {nombre_tabla} existe pero no se pudieron obtener sus columnas.")
            return


        if set(columnas_actuales) != set(columnas_deseadas):
            # Obtener las columnas reales como (nombre, tipo)
            query_info = f"""
                SELECT c.column_name, d.domain_name
                FROM syscolumn c
                JOIN systable t ON c.table_id = t.table_id
                JOIN sysdomain d ON c.domain_id = d.domain_id
                WHERE t.table_name = '{nombre_tabla.upper()}'
            """
            self.cursor.execute(query_info)
            columnas_actuales_info = [(row[0], row[1]) for row in self.cursor.fetchall()]

            diferencias = []

            nombres_actuales = [nombre for nombre, _ in columnas_actuales_info]
            nombres_deseadas = [nombre for nombre, _ in columnas]
            faltan = [c for c in nombres_deseadas if c not in nombres_actuales]
            sobran = [c for c in nombres_actuales if c not in nombres_deseadas]

            # ✅ Si solo faltan columnas (no sobran): ALTER TABLE ADD y evitar recreación
            # Esto evita errores cuando la tabla está referenciada por FKs con acciones (CASCADE/SET NULL/etc.).
            if faltan and not sobran:
                print(f"🔁 Tabla {nombre_tabla} desactualizada (solo faltan columnas). Aplicando ALTER TABLE ADD...")
                for nombre_deseado in faltan:
                    tipo = next((t for n, t in columnas if n == nombre_deseado), None)
                    if not tipo:
                        continue
                    tipo_str = str(tipo)
                    # No tiene sentido agregar PRIMARY KEY en un ALTER ADD de columna
                    tipo_str = re.sub(r"\bPRIMARY\s+KEY\b", "", tipo_str, flags=re.I)
                    tipo_str = " ".join(tipo_str.split())
                    try:
                        self.cursor.execute(f"ALTER TABLE {nombre_tabla} ADD {nombre_deseado} {tipo_str}")
                        self.conexion.commit()
                        print(f"✅ Columna agregada: {nombre_tabla}.{nombre_deseado}")
                    except Exception as e:
                        print(f"❌ Error al agregar columna {nombre_deseado} en {nombre_tabla}: {e}")
                return

            # Detectar columnas que faltan (por nombre)
            for nombre_deseado in nombres_deseadas:
                if nombre_deseado not in nombres_actuales:
                    tipo = next((tipo for nombre, tipo in columnas if nombre == nombre_deseado), "UNKNOWN")
                    diferencias.append(f"➕ Falta columna: {nombre_deseado} ({tipo})")

            # Detectar columnas extra (por nombre)
            for nombre_actual in nombres_actuales:
                if nombre_actual not in nombres_deseadas:
                    tipo = next((tipo for nombre, tipo in columnas_actuales_info if nombre == nombre_actual), "UNKNOWN")
                    diferencias.append(f"➖ Columna extra: {nombre_actual} ({tipo})")

            if diferencias:
                print(f"🔍 Diferencias detectadas en la tabla {nombre_tabla}:")
                for diff in diferencias:
                    print(f"   {diff}")
                print(f"🔁 Tabla {nombre_tabla} desactualizada. Recreando...")
            try:
                self.cursor.execute(f"ALTER TABLE {nombre_tabla} RENAME {nombre_tabla}_old")
                self.conexion.commit()

                self.crear_tabla_generica(nombre_tabla, columnas)

                # 🔄 Extraer los nombres de columnas
                nombres_deseadas = [c[0] for c in columnas]
                nombres_comunes = [nombre for nombre in nombres_deseadas if nombre in columnas_actuales]

                if nombres_comunes:
                    columnas_str = ", ".join(nombres_comunes)
                    self.cursor.execute(f"""
                        INSERT INTO {nombre_tabla} ({columnas_str})
                        SELECT {columnas_str} FROM {nombre_tabla}_old
                    """)
                    self.conexion.commit()
                    print(f"📥 Datos migrados a {nombre_tabla}")
                else:
                    print("⚠️ No hay columnas comunes para migrar datos.")


                self.cursor.execute(f"DROP TABLE {nombre_tabla}_old")
                self.conexion.commit()
            except Exception as e:
                print(f"❌ Error al recrear la tabla {nombre_tabla}: {e}")
        else:
            print(f"✔️ La tabla {nombre_tabla} ya está actualizada.")

    def actualizar_todas_las_tablas(self, tablas_definidas):
        for nombre_tabla, columnas in tablas_definidas.items():
            self.actualizar_tabla_desde_dict(nombre_tabla, columnas)
            
            
    def tabla_existe(self, nombre_tabla):
        try:
            self.conectar()
            query = f"SELECT COUNT(*) FROM systable WHERE table_name = '{nombre_tabla.upper()}'"
            self.cursor.execute(query)
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"Error al verificar existencia de la tabla {nombre_tabla}: {e}")
            return False




if __name__ == "__main__":
    datos_dbf_local = DBFManager(r"F:\Sp\FacturaP\Dbf\SYBASE.dbf").extraer_parametros_dns()[0]
    conexion = ConexionSybase(**datos_dbf_local)
    dict_tablas = cargar_dict_tablas_desde_json()

    if dict_tablas:
        conexion.actualizar_todas_las_tablas(dict_tablas)
    else:
        print("⚠️ No se pudieron cargar las definiciones de tablas.")
