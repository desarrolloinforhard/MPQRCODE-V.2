_version_ = "2.5.4"
import os
path_script = os.path.dirname(os.path.abspath(__file__))
path_GUI = os.path.join(path_script, 'inicio', 'GUI')
import sys
sys.path.append(path_GUI)
from GUIConfigInicialV2 import ConfigInicialMPQRCODE
    
if __name__ == "__main__":
    config = ConfigInicialMPQRCODE()