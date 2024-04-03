const odbc = require('odbc');

class ConexionSybase {
    constructor({ user, password, dsn }) {
        this.config = {
            connectionString: `DSN=${dsn};UID=${user};PWD=${password}`,
        };
        this.connection = null;
        this.connected = false;
    }

    async conectar() {
        try {
            this.connection = await odbc.connect(this.config.connectionString);
            this.connected = true;
            return true;
        } catch (error) {
            console.error(`Error al conectar a Sybase: ${error}`);
            return false;
        }
    }

    async insertarDatosSinObtenerId(tabla, datos) {
        try {
            await this.conectar();
            const columnas = Object.keys(datos).map(col => `"${col}"`).join(", ");
            const valores = Object.values(datos).map(val => typeof val !== 'object' ? `'${val}'` : `'${JSON.stringify(val)}'`).join(", ");
            const consultaInsert = `INSERT INTO ${tabla} (${columnas}) VALUES (${valores})`;
            await this.executeQuery(consultaInsert);
        } catch (error) {
            console.error(`Error al insertar datos: ${error}`);
        } finally {
            await this.desconectar();
        }
    }

    async actualizarDatosCondicion(tabla, datos, condicion, valorCondicion) {
        try {
            await this.conectar();
            const asignaciones = Object.entries(datos).map(([col, v]) => {
                if (typeof v === 'object') {
                    v = JSON.stringify(v);
                }
                return `"${col}" = '${v}'`;
            }).join(', ');
    
            const consultaUpdate = `UPDATE ${tabla} SET ${asignaciones} WHERE ${condicion} = '${valorCondicion}'`;
            await this.executeQuery(consultaUpdate);
        } catch (error) {
            console.error('Error al actualizar datos:', error);
        } finally {
            this.desconectar();
        }
    }
    

    async actualizarDatosCondicionID(tabla, datos, condicion1, valorCondicion1, condicion2, valorCondicion2) {
        try {
            //console.log(`\nTabla = ${tabla}, \nDatos = ${datos}, \ncondicion1 = ${condicion1}, \ncondicion2 = ${condicion2}, \nvalorCondicion2 = ${valorCondicion2}`);
            await this.conectar();
            const asignaciones = Object.entries(datos).map(([col, v]) => {
                if (typeof v !== 'object') {
                    return `"${col}" = '${v}'`;
                } else {
                    return `"${col}" = '${JSON.stringify(v)}'`;
                }
            }).join(', ');
    
            const consultaUpdate = `UPDATE ${tabla} SET ${asignaciones} WHERE ${condicion1} = '${valorCondicion1}' AND ${condicion2} = '${valorCondicion2}'`;
    
            await this.executeQuery(consultaUpdate);
        } catch (err) {
            console.error(`Error al actualizar datos: ${err}`);
        } finally {
            await this.desconectar();
        }
    }
    
    

    async obtenerNombresColumnas(tabla) {
        try {
            await this.conectar();
            const columnInfo = await this.connection.query(`SELECT * FROM ${tabla} WHERE 1=0`);
            
            if (columnInfo && columnInfo.columns && typeof columnInfo.columns[Symbol.iterator] === 'function') {
                // Si columnInfo.columns existe y es un iterable
                const nombresColumnas = columnInfo.columns.map(column => column.name);
                return nombresColumnas;
            } else {
                // Si no hay columnas o no es un iterable
                console.error('No se pudieron obtener los nombres de las columnas o la respuesta no es iterable.');
                return null;
            }
        } catch (error) {
            console.error('Error al obtener nombres de columnas:', error);
            return null;
        }
    }
    
    

    async executeQuery(sql) {
        try {
            const result = await this.connection.query(sql);
            return result;
        } catch (error) {
            console.error('Error al ejecutar consulta:', error);
            throw error;
        }
    }

    cursor(row_type_callable = null) {
        if (!this.connected) {
            throw new Error('Attempt to use a closed connection.');
        }
        return new Cursor(this, row_type_callable); // Asumiendo que Cursor está definido
    }

    async specify_search(nombre_tabla, nombre_columna, condicion) {
        try {
            await this.conectar();
    
            const query = `SELECT ${nombre_columna} FROM ${nombre_tabla} WHERE idINCREMENT = ${condicion}`;
            const resultado = await this.executeQuery(query); // Usando executeQuery en lugar de this.connection.query
    
            if (resultado && resultado.length > 0) {
                const id_valor = resultado[0][nombre_columna];
                return id_valor;
            } else {
                return null;
            }
        } catch (error) {
            console.error(`Error al obtener el valor de '${nombre_columna}': ${error.message}`);
            return null;
        }
    }

    async checkExistence(nombreTabla, condicion, valorCondicion) {
        try {
            await this.conectar();
            const query = `SELECT 1 FROM ${nombreTabla} WHERE ${condicion} = '${valorCondicion}'`;
            const resultado = await this.executeQuery(query);
            
            if (resultado && resultado.length > 0) {
                return true; // Existe al menos una fila que cumple con la condición
            } else {
                return false; // No hay filas que cumplan con la condición
            }
        } catch (error) {
            console.error('Error al verificar la existencia de filas:', error);
            return false;
        }
    }

    async specify_search_condicionID(nombre_tabla, nombre_columna, condicion1, valor_condicion1, condicion2, valor_condicion2, valor_unico) {
        try {
            await this.conectar();
            const query = `SELECT ${nombre_columna} FROM ${nombre_tabla} WHERE ${condicion1} = '${valor_condicion1}' AND ${condicion2} = '${valor_condicion2}'`;
            const resultado = await this.executeQuery(query);
    
            if (resultado !== null && !valor_unico) {
                const id_valor = resultado;
                return id_valor[0];
            } else if (resultado !== null && valor_unico) {
                const id_valor = resultado;
                return id_valor;
            } else {
                //console.log('\nENTRO EN NULL\n');
                return null;
            }
        } catch (err) {
            console.error(`Error al obtener el valor de 'id': ${err}`);
            return null;
        }
    }    
    

    async desconectar() {
        try {
            if (this.connection) {
                await this.connection.close();
            } else {
                console.log('No hay conexión para cerrar.');
            }
        } catch (error) {
            console.error(`Error al cerrar conexión: ${error}`);
            throw error;
        }
    }
}
/*
const configuracion_sybase = {
    dsn: 'GestionIH01',
    user: 'dba',
    password: 'gestion',
};

conexion_sybase = new ConexionSybase(configuracion_sybase);

console.log(conexion_sybase)
console.log(conexion_sybase.conectar())
*/
module.exports = { ConexionSybase };
