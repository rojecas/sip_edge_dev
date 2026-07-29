la forma en la que ellos pesan es la siguiente: 

La balanza tiene una plataforma plana, que no puede contener cosas pequeñas sin que se caigan, entonces tienen varios contenedores uno grande para la caña y dos pequeños, para la materia extraña mineral y para la materia extraña vegetal.

- Taran el contenedor grande (en la balanza),
- lo retiran de la balanza y luego lo colocan en el dispensador que entrega la muestra (caña + materia extrana mineral + materia extraña vegetal - otros vegetales y raices distintos a caña -)
- Mueven el contenedor grande desde el dispensador hasta la balanza y obtienen el peso total.
- Retiran la muestra de la balanza y la ponen sobre la mesa de trabajo.
- Luego taran un contenedor pequeño en la balanza
- Lo retiran y lo llevan a la mesa de trabajo, donde escogen manualmente toda la materia extraña mineral
- Al terminar de escoger el material mineral llevan la muestra de materia extraña y la pesan.
- Repiten los ultimos tres pasos para la materia extraña vegetal 
1. Teniendo en cuenta lo anterior creo que seria irrelevante, dado que descuentan el peso de los contenedores.
2. La comunicacion puede iniciarse en cualquiera de los dos extremos, la balanza tambien tiene un boton de impresion, que envia los datos de peso actuales. Creo que la estrategia pasa por darle foco a los campos de texto donde se capturan los valores, un boton de tara y un boton de lectura, junto a cada textbox. Si se seleccion un campo de texto y se envia el peso desde la balanza deberia ser capturado. Comentarios?
3. El tema del timeout debe ser flexible, porque esta balanza como muchas otras no imprimen el valor medido si la medida no es estable. entonces un valor de 500 ms es muy pequeño, yo lo dejaria configurable de 1 a 10 segundos, con un indicador de espera a que la medida sea estable.
4. Debe establecerse un flujo de trabajo, que asegure las medidas parciales: Tara total (opcional -porque se puede realizar en la balanza, ademas la medida no importa) -> Peso de la muestra -> tara recipiente pequeño (de nuevo opcional) -> peso material 1 (mineral o vegetal) -> Tara (opcional) -> peso del material faltante. Seria bueno tener un boton de reset de la medida, para el caso en que comentan un error, pero que este protegido por un mensaje de confirmacion en pantalla. Despues de la captura de todos los pesos un boton para confirmar el dato, construir la trama de datos y enviar al pc.