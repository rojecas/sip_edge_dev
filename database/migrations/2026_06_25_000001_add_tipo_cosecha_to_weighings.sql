ALTER TABLE weighings
ADD COLUMN tipo_cosecha ENUM(
    'Manual - Incendio',
    'Manual - Quemado',
    'Manual - Verde',
    'Mecanico - Incendio',
    'Mecanico - Verde',
    'No convencional - Verde'
) NOT NULL DEFAULT 'Mecanico - Verde';
