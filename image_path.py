import os
path_script = os.path.dirname(os.path.abspath(__file__))
def Icono_MercadoPago_Blue():
    return os.path.join(path_script, 'assets', 'Icono-MercadoPago-Blue.ico')

def LOGO_INFORHARD_horizontal():
    return os.path.join(path_script, 'assets', 'LOGO_INFORHARD-horizontal.png')

def LOGO_INFORHARD():
    return os.path.join(path_script, 'assets', 'LOGO_INFORHARD.png')

def LOGO_MP():
    logo = os.path.join(path_script, 'assets', 'LOGO_MP.png')
    return logo

def TACHO_BASURA():
    return os.path.join(path_script, 'assets', 'tacho_basura.png')


def REEMPLAZAR():
    return os.path.join(path_script, 'assets', 'reemplazar.png')

def AGREGAR():
    return os.path.join(path_script, 'assets', 'agregar.png')
