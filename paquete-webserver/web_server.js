const express = require('express');
const bodyParser = require('body-parser');
const { ManejadorConexion } = require('./crear_conexion_database.js');

const app = express();

app.use(bodyParser.json());
// Definir rutas
const rutaMPQRCODE = require('./routers/MPQRCODE');
app.use('/api/MPQRCODE', rutaMPQRCODE);
const rutaMPPOINT = require('./routers/MPPOINT');
app.use('/api/MPPOINT', rutaMPPOINT);

app.get('/', (req, res) => {
    res.end('Servidor API de Inforhard para conexión entre MercadoPago y SISTEMAPAGO de Inforhard S.R.L');
});

// Crear una instancia de ManejadorConexion
const manejadorConexion = new ManejadorConexion();

// Imprimir la fecha y hora actual cada segundo y llamar a guardaractualizacion
setInterval(async () => {
    await manejadorConexion.guardaractualizacion();
}, 5000); // 1000 milisegundos = 1 segundo

// Preguntar por el número de puerto
const PORT = process.env.PORT || 5000;

// Iniciar el servidor
app.listen(PORT, () => {
    console.log(`Servidor escuchando en el puerto ${PORT}`);
});
