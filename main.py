_version_ = "4.3.6"
"""
Esta interfaz es desarrollado por el equipo de desarrollo de INFORHARD S.R.L.
El objetivo es poder conectar los pagos hechos atravez de MercadoPago, sea por QR o por POINT, al sistema de ventas de INFORHARD S.R.L
El sistema, tiene un menu de configuración para agregar un cliente, agregar sucursales, y cajas.
Una vez que se configura el sistema, se puede iniciar el sistema y realizar los pagos.
"""
import os
path_script = os.path.dirname(os.path.abspath(__file__))
path_GUI = os.path.join(path_script, 'inicio', 'GUI')
import sys
sys.path.append(path_GUI)
from GUIConfigInicialV2 import ConfigInicialMPQRCODE
    
if __name__ == "__main__":
    config = ConfigInicialMPQRCODE(_version_)