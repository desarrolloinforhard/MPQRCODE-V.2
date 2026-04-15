import tkinter as tk
import ttkbootstrap as ttk  # <- porque tu MessageBox usa ttkbootstrap.Toplevel
from tkinter import ttk as ttk_std  # opcional si querés usar ttk normal también

from tecladohasarV4 import TecladoHasar
from MessageBox import CustomMessageBox  # <- TU messagebox real
from DBFManager import DBFManager
from databaseV2 import ConexionSybase




class MsgBoxLab(tk.Toplevel):
    """
    MessageBox de laboratorio:
    - modal real: transient + grab_set
    - botón default con foco real
    - Enter => default
    - Esc => cancelar
    - Integra TecladoHasar por context stack:
        86 => Enter
        6a => Escape
        4a => acción especial (solo ejemplo)
    """

    def __init__(self, parent, teclado: TecladoHasar, title="Aviso", message=""):
        super().__init__(parent)
        self.parent = parent
        self.teclado = teclado
        self.result = None
        self._ctx_token = None

        self.title(title)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        frm = ttk.Frame(self, padding=14)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=message, wraplength=420, justify="left").pack(fill="x", pady=(0, 10))

        row = ttk.Frame(frm)
        row.pack(fill="x")

        self.btn_ok = ttk.Button(row, text="Aceptar", command=self._ok)
        self.btn_ok.pack(side="right", padx=6)

        self.btn_cancel = ttk.Button(row, text="Cancelar", command=self._cancel)
        self.btn_cancel.pack(side="right", padx=6)

        # binds teclado normal (por si no hay Hasar)
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())

        # modal real
        self.transient(parent)
        self.grab_set()
        self.update_idletasks()
        self._center()
        self.btn_ok.focus_set()
        self.focus_force()

        # instalar contexto Hasar + normal
        if self.teclado:
            self._install_context()

    def _install_context(self):
        hasar_map = {
            "86": lambda: self.after(0, self._ok),       # 86 => Enter
            "6a": lambda: self.after(0, self._cancel),   # 6a => Esc
            "4a": lambda: self.after(0, self._special),  # 4a => special (demo)
        }
        normal_map = {
            "Return": lambda: self.after(0, self._ok),
            "KP_Enter": lambda: self.after(0, self._ok),
            "Escape": lambda: self.after(0, self._cancel),
        }
        self._ctx_token = self.teclado.push_context(
            name="MSGBOX_LAB",
            hasar_map=hasar_map,
            normal_map=normal_map
        )

    def _special(self):
        print("[LAB] SPECIAL 4a capturado (demo)")
        # Consumido, no cierra por defecto

    def _ok(self):
        self.result = "ok"
        self._close()

    def _cancel(self):
        self.result = "cancel"
        self._close()

    def _on_close(self):
        self.result = "cancel"
        self._close()

    def _close(self):
        try:
            if self.teclado and self._ctx_token:
                self.teclado.pop_context(self._ctx_token)
                self._ctx_token = None
        except Exception:
            pass
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def show(self):
        self.wait_window(self)
        return self.result


    def _center(self):
        try:
            self.update_idletasks()
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            self.geometry(f"+{max(x,10)}+{max(y,10)}")
        except Exception:
            pass

def traer_config_teclas_KM84(conexion):
    """
    Devuelve dict {int: str} desde DBA.KM_84_LETER
    conexion.ejecutar_consulta(query) debe devolver list[dict]
    """
    query = 'SELECT nnumtecla, funcion FROM "DBA"."KM_84_LETER"'
    filas = conexion.ejecutar_consulta(query) or []

    cfg = {}
    for r in filas:
        if not isinstance(r, dict):
            continue
        n = r.get("nnumtecla")
        f = r.get("funcion")
        if n is None:
            continue
        ns = str(n).strip()
        if not ns.isdigit():
            continue
        cfg[int(ns)] = "" if f is None else str(f)
    return cfg

def traer_config_funciones_KM84(conexion):
    """
    Devuelve dict {"73":"DOWN", "89":"DOWN", "30":"UP", ...} desde DBA.KM_84
    """
    query = 'SELECT nnumtecla, funcion FROM "DBA"."KM_84"'
    filas = conexion.ejecutar_consulta(query) or []

    cfg = {}
    for r in filas:
        if not isinstance(r, dict):
            continue
        n = r.get("nnumtecla")
        f = r.get("funcion")
        if n is None:
            continue
        ns = str(n).strip()
        if not ns.isdigit():
            continue
        combo = str(int(ns)).zfill(2)  # "73" en vez de "7"
        func = "" if f is None else str(f).strip().upper()
        cfg[combo] = func
    return cfg



def conectar_sybase_desde_tu_app():
    """
    Lee SYBASE.dbf y arma el dict correcto para ConexionSybase:
    requiere claves 'DSN','UID','PWD' (MAYÚSCULAS).
    """
    ruta_dbf_local = r"F:\Sp\FacturaP\Dbf\SYBASE.dbf"

    # 1) leer DBF
    regs = DBFManager(ruta_dbf_local).extraer_parametros_dns()
    if not regs:
        raise RuntimeError(f"No pude leer DNSSISTEMA desde {ruta_dbf_local}")

    datos = regs[0]  # normalmente el 1er registro sirve

    # 2) normalizar claves por si vinieran en minúsculas (seguro)
    datos_norm = {str(k).upper(): v for k, v in datos.items()}

    # 3) validar claves mínimas
    faltan = [k for k in ("DSN", "UID", "PWD") if k not in datos_norm or not str(datos_norm[k]).strip()]
    if faltan:
        raise RuntimeError(f"Faltan parámetros en SYBASE.dbf: {faltan}. Encontré: {list(datos_norm.keys())}")

    # 4) conectar
    cx = ConexionSybase(**datos_norm)
    if not cx.conectar():
        raise RuntimeError("No conectó a Sybase (revisá DSN/Driver/credenciales).")

    return cx

def main():
    root = tk.Tk()
    root.title("Sandbox POS - Hasar + MessageBox")
    root.geometry("560x320")

    # 1) Intentar traer config KM84 desde DBA (LETRAS + FUNCIONES)
    dict_letras = {}
    dict_funciones = {}

    try:
        cx = conectar_sybase_desde_tu_app()

        # A) Letras (KM_84_LETTER / KM_84_LETER)
        dict_letras = traer_config_teclas_KM84(cx)
        print("[DEMO] KM84 LETRAS cargadas:", len(dict_letras))

        # B) Funciones (KM_84)
        dict_funciones = traer_config_funciones_KM84(cx)
        print("[DEMO] KM84 FUNCIONES cargadas:", len(dict_funciones))
        print("[DEMO] Ej funciones:", list(dict_funciones.items())[:10])

    except Exception as e:
        print("[DEMO] No se pudo cargar KM84 desde DBA -> demo sigue con config vacía:", e)

    # 2) Crear TecladoHasar con letras y Hasar ON
    teclado = TecladoHasar(dict_letras, True)

    # 3) Inyectar funciones (UP/DOWN/ENTER/CLEAR) al teclado
    teclado.map_funciones = dict_funciones  # <- esto lo usa el CustomMessageBox


    frm = ttk.Frame(root, padding=14)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Probá tipear en el Entry. Luego abrí el modal.\n"
                        "Hasar (demo): 86=Enter, 6a=Esc, 4a=Special").pack(anchor="w")

    ent = ttk.Entry(frm, width=40)
    ent.pack(anchor="w", pady=10)
    ent.focus_set()

    # Importante: asignar entry al teclado Hasar
    teclado.asignar_entry(ent)

    out = tk.StringVar(value="Resultado: -")
    ttk.Label(frm, textvariable=out).pack(anchor="w", pady=(10, 0))

    def abrir_confirmar():
        mb = CustomMessageBox(
            parent=root,
            title="Confirmación",
            message="¿Deseás continuar?\n\n(Enter / Esc / Hasar 86 / 6a)",
            msg_type="continuar_cancelar",
            teclado_hasar=teclado
        )
        r = mb.show()
        out.set(f"Resultado confirmar: {r}")
        print("CONFIRMAR =", r)


    def abrir_warning():
        mb = CustomMessageBox(
            parent=root,
            title="Advertencia",
            message="El monto ingresado es mayor al permitido.",
            msg_type="warning_ok",
            teclado_hasar=teclado
        )
        r = mb.show()
        out.set(f"Resultado warning: {r}")
        print("WARNING =", r)


    def abrir_error():
        mb = CustomMessageBox(
            parent=root,
            title="Error",
            message="No se pudo conectar con el servidor.\nIntente nuevamente.",
            msg_type="error_ok",
            teclado_hasar=teclado
        )
        r = mb.show()
        out.set(f"Resultado error: {r}")
        print("ERROR =", r)


    def abrir_error_reintentar():
        mb = CustomMessageBox(
            parent=root,
            title="Error de red",
            message="Sin conexión a Internet.\n¿Desea reintentar?",
            msg_type="error_reintentar",
            teclado_hasar=teclado
        )
        r = mb.show()
        out.set(f"Resultado reintentar: {r}")
        print("REINTENTAR =", r)


    def abrir_confirmar_fuerte():
        mb = CustomMessageBox(
            parent=root,
            title="Confirmación crítica",
            message="Esta acción NO se puede deshacer.\n\n¿Confirmar?",
            msg_type="confirmar_fuerte",
            teclado_hasar=teclado
        )
        r = mb.show()
        out.set(f"Resultado crítico: {r}")
        print("CONFIRMAR FUERTE =", r)


    def abrir_anular():
        mb = CustomMessageBox(
            parent=root,
            title="Anular operación",
            message="¿Seguro que desea anular el comprobante?",
            msg_type="anular_confirmar",
            teclado_hasar=teclado
        )
        r = mb.show()
        out.set(f"Resultado anular: {r}")
        print("ANULAR =", r)



    ttk.Button(root, text="Confirmar", command=abrir_confirmar).pack(pady=4)
    ttk.Button(root, text="Warning", command=abrir_warning).pack(pady=4)
    ttk.Button(root, text="Error", command=abrir_error).pack(pady=4)
    ttk.Button(root, text="Error + Reintentar", command=abrir_error_reintentar).pack(pady=4)
    ttk.Button(root, text="Confirmación fuerte", command=abrir_confirmar_fuerte).pack(pady=4)
    ttk.Button(root, text="Anular", command=abrir_anular).pack(pady=4)

    def toggle():
        teclado.set_modo_teclado_hasar(not teclado.teclado_hasar_activo)
        print("[LAB] hasar_mode =", teclado.teclado_hasar_activo)

    ttk.Button(frm, text="Toggle Hasar Mode", command=toggle).pack(anchor="w")

    root.mainloop()


if __name__ == "__main__":
    main()
