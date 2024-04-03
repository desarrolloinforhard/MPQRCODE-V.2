const { ConexionSybase } = require('./database');
const fs = require('fs');
const ruta_archivo = 'configuracion.json';

async function obtenerDSN() {
  return new Promise((resolve, reject) => {
    fs.readFile(ruta_archivo, 'utf8', (err, data) => {
      if (err) {
        reject(err);
        return;
      }
      try {
        const configuracion = JSON.parse(data);
        const dsn_servidor = configuracion.dsn_servidor;
        resolve(dsn_servidor);
      } catch (error) {
        reject(error);
      }
    });
  });
}

async function configurarConexion() {
  const nameDSN = await obtenerDSN();
    const configuracion_sybase = {
        dsn: nameDSN,
        user: 'dba',
        password: 'gestion',
    };

    const conexion_sybase = new ConexionSybase(configuracion_sybase);

    try {
        await conexion_sybase.conectar();
        return conexion_sybase;
    } catch (error) {
        console.error('Error al conectar:', error);
        throw error;
    }
}

class ManejadorConexion {
  constructor() {
    // Configuración de conexión
    this.conexionSybasePromise = configurarConexion(); // Llamamos a la función directamente
    this.conexionSybase = null; // Inicializamos la conexión como null
    this.inicializarConexion();
  }

  async inicializarConexion() {
    try {
      this.conexionSybase = await this.conexionSybasePromise;
    } catch (error) {
      console.error('Error al configurar la conexión:', error);
    }
  }

  async guardaractualizacion() {
    try {
        const fechaActual = new Date();
        const año = fechaActual.getFullYear();
        const mes = (fechaActual.getMonth() + 1).toString().padStart(2, '0'); // Añadir cero delante si es necesario
        const dia = fechaActual.getDate().toString().padStart(2, '0'); // Añadir cero delante si es necesario
        const hora = fechaActual.getHours().toString().padStart(2, '0'); // Añadir cero delante si es necesario
        const minutos = fechaActual.getMinutes().toString().padStart(2, '0'); // Añadir cero delante si es necesario
        const segundos = fechaActual.getSeconds().toString().padStart(2, '0'); // Añadir cero delante si es necesario


        const fecha_hs_completa = `${dia}-${mes}-${año} ${hora}:${minutos}:${segundos}`;
        await this.inicializarConexion(); // Iniciar la conexion
        if (!this.conexionSybase) {
            throw new Error('La conexión no está establecida');
        }
        await this.conexionSybase.conectar();
        const datos_actualizacion = {
            'status': true,
            'ultima_actualizacion': fecha_hs_completa
        };
        await this.conexionSybase.actualizarDatosCondicion('MPQRCODE_CONEXIONSERVIDORAPI', datos_actualizacion, 'id', 1);
    } catch (error) {
        console.error('Error al obtener el ID del usuario:', error);
        throw error;
    }
}


  async obtenerIdUsuario() {
    try {
      await this.inicializarConexion(); // Iniciar la conexion
      if (!this.conexionSybase) {
        throw new Error('La conexión no está establecida');
      }
      await this.conexionSybase.conectar();
      const idUsuario = await this.conexionSybase.specify_search('MPQRCODE_CLIENTE', 'idUSER', 1);
      return idUsuario;
    } catch (error) {
      console.error('Error al obtener el ID del usuario:', error);
      throw error;
    }
  }

  async obtenerToken() {
      try {
        await this.inicializarConexion(); 
          if (!this.conexionSybase) {
            throw new Error('La conexión no está establecida');
          }
          await this.conexionSybase.conectar();
          const token = await this.conexionSybase.specify_search('MPQRCODE_CLIENTE', 'AUTH_TOKEN', 1);
          return token;
      } catch (error) {
          console.error('Error al obtener el token:', error);
          throw error;
      }
  }

  async obtenerTokenPoint() {
      try {
        await this.inicializarConexion();
          if (!this.conexionSybase) {
            throw new Error('La conexión no está establecida');
          }
          await this.conexionSybase.conectar();
          const tokenPOINT = await this.conexionSybase.specify_search('MPQRCODE_CLIENTE', 'AUTH_TOKENPOINT', 1);
          return tokenPOINT;
      } catch (error) {
          console.error('Error al obtener el token POINT:', error);
          throw error;
      }
  }

async obtenerPago(idPago, existe, nroFactura, respuestaObtenerPago) {
  await this.inicializarConexion(); // Iniciar la conexion

  const jsonResponse = respuestaObtenerPago;

  //console.log(respuestaObtenerPago);

  const datos = {
      data: idPago
  };

  for (const claveJson in jsonResponse) {
      const valorJson = jsonResponse[claveJson];
      if (claveJson === 'order' && typeof valorJson === 'object') {
          for (const recorreDict in valorJson) {
              const valorDict = valorJson[recorreDict];
              if (recorreDict === 'id') {
                  datos['order_id'] = valorDict;
              } else {
                  datos['order_type'] = valorDict;
              }
          }
      } else if (claveJson === 'payer' && typeof valorJson === 'object') {
          for (const recorreDict in valorJson) {
              const valorDict = valorJson[recorreDict];
              if (recorreDict === 'id') {
                  datos['payer_id'] = valorDict;
              } else {
                  //console.log("Se encontró una respuesta no esperada.");
                  //console.log(valorJson);
              }
          }
      } else if (claveJson === 'payment_method' && typeof valorJson === 'object') {
          for (const recorreDict in valorJson) {
              const valorDict = valorJson[recorreDict];
              if (recorreDict === 'id') {
                  datos['payment_metodo_id'] = valorDict;
              } else if (recorreDict === 'issuer_id') {
                  datos['payment_metodo_issuer_id'] = valorDict;
              } else {
                  datos['payment_metodo_type'] = valorDict;
              }
          }
      } else if (claveJson === 'transaction_details' && typeof valorJson === 'object') {
          for (const recorreDict in valorJson) {
              const valorDict = valorJson[recorreDict];
              if (recorreDict === 'total_paid_amount') {
                  datos['transaction_details_total_paid_amount'] = valorDict;
              } else {
                  // No hacer nada
              }
          }
      } else {
          const columnas = await this.conexionSybase.obtenerNombresColumnas("MPQRCODE_OBTENERPAGOServer");
          for (const columnName of columnas) {
              if (claveJson === columnName) {
                  datos[claveJson] = valorJson;
              } else {
                  // No hacer nada
              }
          }
      }
  }
  //console.log(`DATOS = ${JSON.stringify(datos)}`);

  if (existe) {
    const tablaQR = "MPQRCODE_OBTENERPAGOServer";
    //console.log("\nPASO EXISTE\n");
    const pos_id = await this.conexionSybase.specify_search_condicionID(tablaQR, 'pos_id', 'external_reference', nroFactura, 'pos_id', datos.pos_id, false);
    if (datos.pos_id === pos_id.pos_id) {
      //console.log("\nENTRO TRUE EXISTE\n");
      await this.conexionSybase.actualizarDatosCondicionID(tablaQR, datos, 'external_reference', nroFactura, 'pos_id', datos.pos_id);
    } else {
      //console.log("\nENTRO FALSE EXISTE\n");
      await this.conexionSybase.insertarDatosSinObtenerId(tablaQR, datos);
      //console.log('DATOS INSERTADOS');
    }
  } else {
    const tablaQR = "MPQRCODE_OBTENERPAGOServer";
    //console.log("\nFalse\n");
    await this.conexionSybase.insertarDatosSinObtenerId(tablaQR, datos);
  }
}
async posObtenerPago(respuestaObtenerPago, valorId, data) {
  await this.inicializarConexion(); // Iniciar la conexion
  const existe = await this.conexionSybase.checkExistence("MPQRCODE_OBTENERPAGOServer", 'external_reference', respuestaObtenerPago.external_reference);
  //console.log(existe);
  if (existe) { // Existe en QRCODE
    await this.obtenerPago(valorId, existe, respuestaObtenerPago.external_reference, respuestaObtenerPago);
    let dict_valor = {};
    for (const [clave_json, valor_json] of Object.entries(data)) {
        if (clave_json === 'data') {
            dict_valor[clave_json] = valor_json['id'];
        } else {
            dict_valor[clave_json] = valor_json;
        }
    }
    //console.log(`\nVALOR DEL DICCIONARIO \n ${JSON.stringify(dict_valor)} \n`);
    await this.obtenerPago(valorId, false, null, respuestaObtenerPago);
    valorId = Number(valorId);
    const idindbapost = await this.conexionSybase.checkExistence("MPQRCODE_RESPUESTAPOST", "data", valorId);
    if (idindbapost) {
        delete dict_valor['data'];
        await this.conexionSybase.actualizarDatosCondicion("MPQRCODE_RESPUESTAPOST", dict_valor, 'data', valorId);
    } else {
        await this.conexionSybase.insertarDatosSinObtenerId("MPQRCODE_RESPUESTAPOST", dict_valor);
    }
  } else {  // No existe en MPQRCODE
      const dictValor = {};
      for (const claveJson in data) {
          const valorJson = data[claveJson];
          if (claveJson === 'data') {
              dictValor[claveJson] = valorJson['id'];
          } else {
              dictValor[claveJson] = valorJson;
          }
      }
      await this.obtenerPago(valorId, false, null, respuestaObtenerPago);
      valorId = Number(valorId);
      const idindbapost = await this.conexionSybase.checkExistence("MPQRCODE_RESPUESTAPOST", "data", valorId);
      if (idindbapost) {
          delete dictValor['data'];
          await this.conexionSybase.actualizarDatosCondicion("MPQRCODE_RESPUESTAPOST", dictValor, 'data', valorId);
      } else {
          await this.conexionSybase.insertarDatosSinObtenerId("MPQRCODE_RESPUESTAPOST", dictValor);
      }
  }
  console.log("AGREGADOS EN LA BASE DE DATOS");
}

async obtenerPagoPOINT(idPago, existe, nroFactura, respuestaObtenerPago) {
  await this.inicializarConexion(); // Iniciar la conexion

  const jsonResponse = respuestaObtenerPago;

  //console.log(respuestaObtenerPago);

  const datos = {
      data: idPago
  };

  for (const claveJson in jsonResponse) {
      const valorJson = jsonResponse[claveJson];
      if (claveJson === 'order' && typeof valorJson === 'object') {
          for (const recorreDict in valorJson) {
              const valorDict = valorJson[recorreDict];
              if (recorreDict === 'id') {
                  datos['order_id'] = valorDict;
              } else {
                  datos['order_type'] = valorDict;
              }
          }
      } else if (claveJson === 'payer' && typeof valorJson === 'object') {
          for (const recorreDict in valorJson) {
              const valorDict = valorJson[recorreDict];
              if (recorreDict === 'id') {
                  datos['payer_id'] = valorDict;
              } else {
                  //console.log("Se encontró una respuesta no esperada.");
                  //console.log(valorJson);
              }
          }
      } else if (claveJson === 'payment_method' && typeof valorJson === 'object') {
          for (const recorreDict in valorJson) {
              const valorDict = valorJson[recorreDict];
              if (recorreDict === 'id') {
                  datos['payment_metodo_id'] = valorDict;
              } else if (recorreDict === 'issuer_id') {
                  datos['payment_metodo_issuer_id'] = valorDict;
              } else {
                  datos['payment_metodo_type'] = valorDict;
              }
          }
      } else if (claveJson === 'transaction_details' && typeof valorJson === 'object') {
          for (const recorreDict in valorJson) {
              const valorDict = valorJson[recorreDict];
              if (recorreDict === 'total_paid_amount') {
                  datos['transaction_details_total_paid_amount'] = valorDict;
              } else {
                  // No hacer nada
              }
          }
      } else {
          const columnas = await this.conexionSybase.obtenerNombresColumnas("MPQRCODE_OBTENERPAGOPOINTServer");
          for (const columnName of columnas) {
              if (claveJson === columnName) {
                  datos[claveJson] = valorJson;
              } else {
                  // No hacer nada
              }
          }
      }
  }
  //console.log(`DATOS = ${JSON.stringify(datos)}`);

  if (existe) {
    const tablaPOINT = "MPQRCODE_OBTENERPAGOPOINTServer";
    //console.log("\nPASO EXISTE\n");
    const pos_id = false //await this.conexionSybase.specify_search_condicionID(tablaPOINT, 'pos_id', 'external_reference', nroFactura, 'pos_id', datos.pos_id, false);
    if (pos_id == true) {// VER LINEA 172 datos.pos_id === pos_id.pos_id
      //console.log("\nENTRO TRUE EXISTE\n");
      await this.conexionSybase.actualizarDatosCondicionID(tablaPOINT, datos, 'external_reference', nroFactura, 'pos_id', datos.pos_id);
    } else {
      //console.log("\nENTRO FALSE EXISTE\n");
      await this.conexionSybase.insertarDatosSinObtenerId(tablaPOINT, datos);
      //console.log('DATOS INSERTADOS');
    }
  } else {
    const tablaPOINT = "MPQRCODE_OBTENERPAGOPOINTServer";
    //console.log("\nFalse\n");
    await this.conexionSybase.insertarDatosSinObtenerId(tablaPOINT, datos);
  }
}
async posObtenerPagoPOINT(respuestaObtenerPago, valorId, data) {
  await this.inicializarConexion(); // Iniciar la conexion
  const existe = await this.conexionSybase.checkExistence("MPQRCODE_OBTENERPAGOPOINTServer", 'external_reference', respuestaObtenerPago.external_reference);
  //console.log(existe);
  if (existe) { // Existe en QRCODE
    await this.obtenerPagoPOINT(valorId, existe, respuestaObtenerPago.external_reference, respuestaObtenerPago);
    let dict_valor = {};
    for (const [clave_json, valor_json] of Object.entries(data)) {
        if (clave_json === 'data') {
            dict_valor[clave_json] = valor_json['id'];
        } else {
            dict_valor[clave_json] = valor_json;
        }
    }
    //console.log(`\nVALOR DEL DICCIONARIO \n ${JSON.stringify(dict_valor)} \n`);
    await this.obtenerPagoPOINT(valorId, false, null, respuestaObtenerPago);
    valorId = Number(valorId);
    const idindbapost = await this.conexionSybase.checkExistence("MPQRCODE_RESPUESTAPOSTPOINT", "data", valorId);
    if (idindbapost) {
        delete dict_valor['data'];
        await this.conexionSybase.actualizarDatosCondicion("MPQRCODE_RESPUESTAPOSTPOINT", dict_valor, 'data', valorId);
    } else {
        await this.conexionSybase.insertarDatosSinObtenerId("MPQRCODE_RESPUESTAPOSTPOINT", dict_valor);
    }
  } else {  // No existe en MPQRCODE
      const dictValor = {};
      for (const claveJson in data) {
          const valorJson = data[claveJson];
          if (claveJson === 'data') {
              dictValor[claveJson] = valorJson['id'];
          } else {
              dictValor[claveJson] = valorJson;
          }
      }
      await this.obtenerPagoPOINT(valorId, false, null, respuestaObtenerPago);
      valorId = Number(valorId);
      const idindbapost = await this.conexionSybase.checkExistence("MPQRCODE_RESPUESTAPOSTPOINT", "data", valorId);
      if (idindbapost) {
          delete dictValor['data'];
          await this.conexionSybase.actualizarDatosCondicion("MPQRCODE_RESPUESTAPOSTPOINT", dictValor, 'data', valorId);
      } else {
          await this.conexionSybase.insertarDatosSinObtenerId("MPQRCODE_RESPUESTAPOSTPOINT", dictValor);
      }
  }
  console.log("AGREGADOS EN LA BASE DE DATOS");
}

}

module.exports = { ManejadorConexion };