const express = require('express'); // Modulo Express
const {Conexion_Api} = require('../Conexion_APIs_MP');
const rutaMPQRCODE = express.Router();
const {ManejadorConexion} = require('../crear_conexion_database');
const moment = require('moment');
// Obtener la fecha actual
const fechaActual = moment().format('DD-MM-YYYY');

// Obtener la hora actual
const horaActual = moment().format('HH:mm:ss');
let conexion_sybase = new ManejadorConexion();

async function obtenerDatosUsuario() {
  try {
    const idUsuario = await conexion_sybase.obtenerIdUsuario();
    const tokenQR = await conexion_sybase.obtenerToken();
    console.log(idUsuario, tokenQR)
    return { idUsuario, tokenQR };
  } catch (error) {
    console.error('Error al obtener los datos del usuario:', error);
    throw error;
  }
}
let respuestaAPIsMP; // Declaración de la variable global

obtenerDatosUsuario()
    .then(datos => {
        // Aquí se asigna el valor a respuestaAPIsMP cuando la promesa se resuelve
        respuestaAPIsMP = new Conexion_Api(datos.idUsuario, datos.tokenQR);
        // Puedes usar respuestaAPIsMP aquí dentro del bloque then
    })
    .catch(error => {
        console.error('Error al obtener los datos del usuario:', error);
    });
// -/-/-/-/-/-/-/-/-/-/-/-/-/-/ FUNCIONES -/-/-/-/-/-/-/-/-/-/-/-/-/-/
// Ruta MPQRCODE
rutaMPQRCODE.get('/', (req, res) => {
  res.end('Routing /api/MPQRCODE para metodos POST: HABILITADO ');
});

rutaMPQRCODE.post('/', async (req, res) => {
  try {
      const data = req.body;
      if ('action' in data) {
        console.log(data);
          if (data.action === 'payment.updated') {
            setTimeout(async () => {
              try {
                  const resultado = await respuestaAPIsMP.obtener_pago(data.data.id);
                  const infoPOS = await respuestaAPIsMP.obtener_pos(resultado.pos_id);
                  if (resultado.status == 'refunded' && resultado.status_detail == 'refunded') {
                    console.log(`\n
                    *************************************
                    Aviso de reembolso con Código QR: RECIBIDO
                    *************************************
                    Factura: ${resultado.external_reference}
                    Monto: $${resultado.transaction_amount}
                    Sucursal: ${resultado.description}
                    Caja: ${infoPOS.name}
                    ID Pago: ${data.data.id}
                    Fecha de Recepción: ${fechaActual}
                    Hora de Recepción: ${horaActual}
                    --------------------------------------\n`);
                    conexion_sybase.posObtenerPago(resultado, data.data.id, data);
                } else {
                    console.log(`\n
                    *************************************
                    Aviso de pago con Código QR: ERROR
                    *************************************
                    Factura: ${resultado.external_reference}
                    Monto: $${resultado.transaction_amount}
                    Sucursal: ${resultado.description}
                    Caja: ${infoPOS.name}
                    ERROR: ${resultado.status_detail}
                    ID Pago: ${data.data.id}
                    Fecha de Recepción: ${fechaActual}
                    Hora de Recepción: ${horaActual}
                    --------------------------------------\n`);
                }                 
                  
              } catch (error) {
                  console.error('Error al obtener el pago:', error);
              }
          }, 1000);
          } else if (data.action == 'payment.created') {
              setTimeout(async () => {
                try {
                    const resultado = await respuestaAPIsMP.obtener_pago(data.data.id);
                    const infoPOS = await respuestaAPIsMP.obtener_pos(resultado.pos_id);
                    if (resultado.status == 'approved' && resultado.status_detail == 'accredited') {
                      console.log(`\n
                      *************************************
                      Aviso de pago con Código QR: RECIBIDO
                      *************************************
                      Factura: ${resultado.external_reference}
                      Monto: $${resultado.transaction_amount}
                      Sucursal: ${resultado.description}
                      Caja: ${infoPOS.name}
                      ID Pago: ${data.data.id}
                      Fecha de Recepción: ${fechaActual}
                      Hora de Recepción: ${horaActual}
                      --------------------------------------\n`);
                      conexion_sybase.posObtenerPago(resultado, data.data.id, data);
                  } else {
                      console.log(`\n
                      *************************************
                      Aviso de pago con Código QR: ERROR
                      *************************************
                      Factura: ${resultado.external_reference}
                      Monto: $${resultado.transaction_amount}
                      Sucursal: ${resultado.description}
                      Caja: ${infoPOS.name}
                      ERROR: ${resultado.status_detail}
                      ID Pago: ${data.data.id}
                      Fecha de Recepción: ${fechaActual}
                      Hora de Recepción: ${horaActual}
                      --------------------------------------\n`);
                  }                 
                    
                } catch (error) {
                    console.error('Error al obtener el pago:', error);
                }
            }, 1000);
          }
      } else if ('message' in data){
          console.log('Received JSON de /api/MPQRCODE:', data.message);
      } /*else {
        console.log('ENTRADA POST NO CONFIGURADO EN EL SERVIDOR', data);
      }*/
      res.status(200).send('OK');
  } catch (error) {
      console.error('Error al procesar la solicitud:', error);
      res.status(500).send('Error');
  }
});

module.exports = rutaMPQRCODE