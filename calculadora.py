"""def calcular_porcentaje(cantidad, porcentaje):
    
    Calcula el porcentaje de una cantidad dada.
    
    :param cantidad: La cantidad a la que se le va a aplicar el porcentaje.
    :param porcentaje: El porcentaje que se quiere calcular.
    :return: El valor del porcentaje calculado.
    
    valor_porcentaje = (porcentaje / 100) * cantidad
    return valor_porcentaje

def sumar_iva(cantidad, porcentaje_iva):
    
    Suma el porcentaje de IVA a una cantidad dada.
    
    :param cantidad: La cantidad original.
    :param porcentaje_iva: El porcentaje de IVA a sumar.
    :return: La cantidad con IVA incluido.
    
    iva = calcular_porcentaje(cantidad, porcentaje_iva)
    cantidad_con_iva = cantidad + iva
    return cantidad_con_iva

# Ejemplo de uso
total = 7919.99
porcentaje_base = 6.29
porcentaje_iva = 21

# Calcular el 6.29% del total
resultado_base = calcular_porcentaje(total, porcentaje_base)

# Sumar el 21% de IVA al resultado base
resultado_con_iva = sumar_iva(resultado_base, porcentaje_iva)

print(f"El {porcentaje_base}% de {total} es: {resultado_base}")
print(f"El {porcentaje_iva}% de {resultado_base} es: {calcular_porcentaje(resultado_base, porcentaje_iva)}")
print(f"El resultado con IVA incluido es: {resultado_con_iva}")
"""

def calcular_porcentaje(cantidad, total):
    """
    Calcula el porcentaje que una cantidad representa de un total.
    
    :param cantidad: La cantidad que se quiere calcular como porcentaje.
    :param total: El total del cual se quiere saber el porcentaje.
    :return: El porcentaje que la cantidad representa del total.
    """
    if total == 0:
        return 0  # Evita la división por cero
    porcentaje = (cantidad / total) * 100
    return porcentaje

def calcular_iva(cantidad_sin_iva):
    """
    Calcula el IVA a partir de la cantidad sin IVA y la cantidad con IVA.
    
    :param cantidad_sin_iva: La cantidad sin IVA.
    :param cantidad_con_iva: La cantidad con IVA.
    :return: El valor del IVA.
    """
    cantidad_sin_iva = cantidad_sin_iva / (1 + 21 / 100)
    return cantidad_sin_iva

# Ejemplo de uso
total = 7919.99
cantidad_sin_iva = 602.71

# Calcular el IVA
iva = calcular_iva(cantidad_sin_iva)

# Calcular el porcentaje de la cantidad base sin IVA sobre el total
porcentaje_base = calcular_porcentaje(iva, total)

print(f"El IVA calculado es: {iva}")
print(f"El porcentaje base es: {porcentaje_base}%")
