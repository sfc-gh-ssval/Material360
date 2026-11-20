-- =============================================================================
-- 05_seed_bom.sql — Sample BOM master rows for the 7 synthetic drawings
-- (synthetic_drawings/*.pdf). Replace with your own ERP/PLM BOM extract.
-- Safe to re-run: only inserts part numbers not already present.
-- =============================================================================
USE DATABASE SNOWFLAKE_INTELLIGENCE;
USE SCHEMA ENGINEERING_DRAWINGS;

INSERT INTO BOM_PARTS (part_number, part_name, material, finish, quantity, unit_cost, supplier, source_document)
SELECT s.* FROM (
    SELECT column1 AS part_number, column2 AS part_name, column3 AS material, column4 AS finish,
           column5 AS quantity, column6 AS unit_cost, column7 AS supplier, column8 AS source_document
    FROM VALUES
        ('BRK-20240101', 'Mounting bracket assembly',           'AL6061-T6',  'ANODIZE BLACK',          2,  45.50, 'Pacific Precision',   'BOM_PACIFIC_Q1.xlsx'),
        ('GS-FR-44210',  'Gousset de renfort',                  'S235JR',     'GALVANISATION A CHAUD',  8,  12.30, 'Acier Plus SAS',      'BOM_ACIERPLUS.xlsx'),
        ('KRP-30050200', 'Kabelrinnenplatte',                   'S355J2',     'FEUERVERZINKT',          4,  28.75, 'Stahlwerk GmbH',      'BOM_STAHLWERK_2023.xlsx'),
        ('PC-ES-55100',  'Placa de cubierta',                   'AL5052-H32', 'ANODIZADO NATURAL',      6,  15.80, 'Metales Garcia S.L.', 'BOM_GARCIA_2024.xlsx'),
        ('SA-EN-78500',  'Shaft adapter sleeve',                'SS316L',     'PASSIVATE PER QQ-P-35',  1,  92.00, 'MetalWorks Inc.',     'BOM_METALWORKS_Q2.xlsx'),
        ('SM-EN-66300',  'Sensor mounting plate',               'SS304',      'ELECTROPOLISH',          3,  38.50, 'CleanTech Fab',       'BOM_CLEANTECH.xlsx'),
        ('TLS-IT-90200', 'Telaio saldato per quadro elettrico', 'S235JR',     'VERNICIATURA RAL 7035',  1, 520.00, 'Rossi Costruzioni',   'BOM_ROSSI_2024.xlsx')
) s
WHERE NOT EXISTS (SELECT 1 FROM BOM_PARTS b WHERE b.part_number = s.part_number);
