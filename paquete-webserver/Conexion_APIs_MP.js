const axios = require('axios');

class Conexion_Api {
    constructor(id_user, access_token) {
        this.id_user = id_user;
        this.access_token = access_token;
    }

    obtener_pos = async (pos_id) => {
      const url = `https://api.mercadopago.com/pos/${pos_id}`;
      
      const headers = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.access_token}`
      };
      
      try {
          const response = await axios.get(url, { headers });
          return response.data; // Solo se retorna la propiedad 'data'
      } catch (error) {
          console.error('Error al obtener el POS:', error);
          throw error;
      }
    };

    
    obtener_pago = async (nro_operacion) => {
        const url = `https://api.mercadopago.com/v1/payments/${nro_operacion}`;
        
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.access_token}`
        };
        
        try {
            const response = await axios.get(url, { headers });
            return response.data; // Solo se retorna la propiedad 'data'
        } catch (error) {
            console.error('Error al obtener el pago:', error.data);
            throw error;
        }
    }
    
    buscar_intencion_pago_POINT = async (paymentintentid) => {
        const url = `https://api.mercadopago.com/point/integration-api/payment-intents/${paymentintentid}`;
        
        const headers = {
            'Content-Type': 'application/json',
            'x-test-scope': 'sandbox',
            'Authorization': `Bearer ${this.access_token}`
        };
        
        try {
            const response = await axios.get(url, { headers });
            return response;
        } catch (error) {
            console.error('Error al buscar intención de pago POINT:', error);
            throw error;
        }
    }
    
    obtener_dispositivo_POINTALL = async () => {
        const url = `https://api.mercadopago.com/point/integration-api/devices?&limit=50`;
        
        const headers = {
            'Content-Type': 'application/json',
            //'x-test-scope': 'sandbox',
            'Authorization': `Bearer ${this.access_token}`
        };
        
        try {
            const response = await axios.get(url, { headers });
            return response;
        } catch (error) {
            console.error('Error al obtener dispositivos POINTALL:', error);
            throw error;
        }
    }
}

module.exports.Conexion_Api = Conexion_Api;
