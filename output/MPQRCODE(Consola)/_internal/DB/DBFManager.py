from dbfread import DBF
import re

class DBFManager:
    def __init__(self, ruta_archivo):
        self.ruta = ruta_archivo
        self.tabla = None

    def abrir_archivo(self):
        try:
            self.tabla = DBF(self.ruta, load=True, encoding='latin1')
            print(f"✅ Archivo {self.ruta} cargado correctamente.")
        except Exception as e:
            print(f"❌ Error al abrir el archivo DBF: {e}")

    def obtener_columnas(self):
        if self.tabla:
            return self.tabla.field_names
        else:
            print("⚠ No se ha cargado ningún archivo DBF.")
            return []

    def obtener_registros(self, cantidad=None):
        if self.tabla:
            if cantidad:
                return [registro for i, registro in enumerate(self.tabla) if i < cantidad]
            else:
                return list(self.tabla)
        else:
            print("⚠ No se ha cargado ningún archivo DBF.")
            return []

    def filtrar_por_columna(self, columna, valor):
        if self.tabla:
            return [registro for registro in self.tabla if str(registro.get(columna, "")).strip() == str(valor)]
        else:
            print("⚠ No se ha cargado ningún archivo DBF.")
            return []

    def buscar_valor(self, columna, contiene):
        if self.tabla:
            return [registro for registro in self.tabla if contiene.lower() in str(registro.get(columna, "")).lower()]
        else:
            print("⚠ No se ha cargado ningún archivo DBF.")
            return []
        
    def extraer_parametros_dns(self):
        resultados = []
        try:
            tabla = DBF(self.ruta, encoding='latin1', load=True)
            for registro in tabla:
                cadena = registro.get("DNSSISTEMA", "")
                # Buscar patrones como UID=..., PWD=..., DSN=...
                pares = re.findall(r'([A-Z]+)=([^;]*)', cadena)
                datos = {clave: valor for clave, valor in pares}
                resultados.append(datos)
        except Exception as e:
            print(f"❌ Error al procesar el archivo: {e}")
            return None
        return resultados

    def cantidad_registros(self):
        return len(self.tabla) if self.tabla else 0
