import requests

def obtener_ubicacion_actual(latitud, longitud):
    url = "https://nominatim.openstreetmap.org/reverse"
    parametros = {
        "lat": latitud,
        "lon": longitud,
        "format": "json"
    }
    respuesta = requests.get(url, params=parametros)
    if respuesta.status_code == 200:
        datos = respuesta.json()['address']
        listclave = ['house_number', 'road', 'town', 'city', 'state']
        listdatos = []
        for clave in listclave:                
            if clave in datos:
                listdatos.append(datos[clave])
        if not 'house_number' in datos:
            listdatos.insert(0, "S/N")
        return listdatos
    else:
        print("Error al obtener la ubicación:", respuesta.status_code)
        return None