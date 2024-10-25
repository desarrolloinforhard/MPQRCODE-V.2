import json
import requests

def lambda_handler(event, context):
    # Verificar si el evento contiene información HTTP
    if 'requestContext' in event and 'http' in event['requestContext']:
        method = event['requestContext']['http']['method']
        
        # Si el método es GET, retornar 200 OK
        if method == 'GET':
            headers = {
                "Content-Type": 'application/json'
            }
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps('GET request received. OK.')
            }
        
        # Si es POST, procesar la notificación
        elif method == 'POST':
            # Imprimir el evento recibido
            print("Evento recibido:", event)

            # Extraer el cuerpo de la notificación
            try:
                body = json.loads(event['body'])
            except Exception as e:
                print(f"Error al leer el cuerpo de la notificación: {str(e)}")
                return {
                    'statusCode': 400,
                    'body': json.dumps('Error en el formato del cuerpo de la solicitud.')
                }

            # Imprimir el contenido de la notificación
            print("Contenido de la notificación:", body)

            # Cargar las URLs de sucursales desde el archivo JSON
            try:
                with open('urlSucursales.json', 'r') as file:
                    urls_sucursales = json.load(file)
            except Exception as e:
                print(f"Error al cargar el archivo de URLs: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps('Error al cargar las URLs.')
                }

            # Reenviar la notificación a cada URL
            for sucursal, url in urls_sucursales.items():
                try:
                    response = requests.post(url, json=body)
                    print(f"Notificación enviada a {sucursal} ({url}), respuesta: {response.status_code}")
                except Exception as e:
                    print(f"Error al enviar notificación a {sucursal}: {str(e)}")

            return {
                'statusCode': 200,
                'body': json.dumps('Notificación procesada y reenviada.')
            }
    else:
        # Si no se puede detectar el método HTTP, manejar otros tipos de invocaciones
        print("Evento recibido sin información HTTP:", event)
        return {
            'statusCode': 400,
            'body': json.dumps('Método HTTP no soportado o evento inválido.')
        }


"""import json
import requests

def lambda_handler(event, context):
    # Imprimir el evento recibido
    print("Evento recibido:", event)

    # Extraer el cuerpo de la notificación
    body = json.loads(event['body'])

    # Imprimir el contenido de la notificación
    print("Contenido de la notificación:", body)

    # Cargar las URLs de sucursales desde el archivo JSON
    try:
        with open('urlSucursales.json', 'r') as file:
            urls_sucursales = json.load(file)
    except Exception as e:
        print(f"Error al cargar el archivo de URLs: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error al cargar las URLs.')
        }

    # Reenviar la notificación a cada URL
    for sucursal, url in urls_sucursales.items():
        try:
            response = requests.post(url, json=body)
            print(f"Notificación enviada a {sucursal} ({url}), respuesta: {response.status_code}")
        except Exception as e:
            print(f"Error al enviar notificación a {sucursal}: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Notificación procesada y reenviada.')
    }

"""

