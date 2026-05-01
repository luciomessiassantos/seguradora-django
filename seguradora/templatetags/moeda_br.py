from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='br_money')
def br_money(value):

    if value is None:
        return '-'
    
    
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except:
            return value

    
    quantize = Decimal('0.01')
    value = value.quantize(quantize)  
    integer_part = int(value)
    decimal_part = abs(value - integer_part) * 100
    decimal_part = int(round(decimal_part))
    
   
    int_str = f"{integer_part:,}".replace(",", ".")
    
    # Monta o resultado
    return f"{int_str},{decimal_part:02d}"