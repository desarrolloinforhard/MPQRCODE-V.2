import os
path_script = os.path.dirname(os.path.abspath(__file__))
def Icono_MercadoPago_Blue():
    return os.path.join(path_script, 'Icono-MercadoPago-Blue.ico')

def LOGO_INFORHARD_horizontal():
    return os.path.join(path_script, 'LOGO_INFORHARD-horizontal.png')

def LOGO_INFORHARD():
    return os.path.join(path_script, 'LOGO_INFORHARD.png')

def LOGO_MP():
    logo = os.path.join(path_script, 'LOGO_MP.png')
    print(logo)
    return logo
