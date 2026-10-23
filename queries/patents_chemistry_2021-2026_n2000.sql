-- Chemistry: up to 2000 publications per WIPO field (14-24).
-- Maximum output: 22000 rows. WIPO concordance: March 2026.
-- Publication dates: 2021-01-01 through 2026-09-30 inclusive.
-- Query logic and sampling seed retained from the verified Instruments extraction.
-- No patent-family deduplication or cross-field deduplication.
-- Run in BigQuery using GoogleSQL. Check the estimated bytes first.
WITH fields AS (
  SELECT * FROM UNNEST([
    STRUCT(14 AS field_number, 'Organic fine chemistry' AS field_name,
      [
          'A61K8/%', 'A61Q%', 'C07B%', 'C07C%', 'C07D%',
          'C07F%', 'C07H%', 'C07J%', 'C40B%'
      ] AS ipc_rules),
    STRUCT(15 AS field_number, 'Biotechnology' AS field_name,
      [
          'C07G%', 'C07K%', 'C12M%', 'C12N%', 'C12P%',
          'C12Q%', 'C12R%', 'C12S%'
      ] AS ipc_rules),
    STRUCT(16 AS field_number, 'Pharmaceuticals' AS field_name,
      [
          'A61K6/%', 'A61K9/%', 'A61K31/%', 'A61K33/%', 'A61K35/%',
          'A61K36/%', 'A61K38/%', 'A61K39/%', 'A61K41/%', 'A61K45/%',
          'A61K47/%', 'A61K48/%', 'A61K49/%', 'A61K50/%', 'A61K51/%',
          'A61K101/%', 'A61K103/%', 'A61K125/%', 'A61K127/%', 'A61K129/%',
          'A61K131/%', 'A61K133/%', 'A61K135/%', 'A61P%'
      ] AS ipc_rules),
    STRUCT(17 AS field_number, 'Macromolecular chemistry, polymers' AS field_name,
      [
          'C08B%', 'C08C%', 'C08F%', 'C08G%', 'C08H%',
          'C08K%', 'C08L%'
      ] AS ipc_rules),
    STRUCT(18 AS field_number, 'Food chemistry' AS field_name,
      [
          'A01H%', 'A21D%', 'A23B%', 'A23C%', 'A23D%',
          'A23F%', 'A23G%', 'A23J%', 'A23K%', 'A23L%',
          'C12C%', 'C12F%', 'C12G%', 'C12H%', 'C12J%',
          'C13B10/%', 'C13B20/%', 'C13B30/%', 'C13B35/%', 'C13B40/%',
          'C13B50/%', 'C13B99/%', 'C13D%', 'C13F%', 'C13J%',
          'C13K%'
      ] AS ipc_rules),
    STRUCT(19 AS field_number, 'Basic materials chemistry' AS field_name,
      [
          'A01N%', 'A01P%', 'C05B%', 'C05C%', 'C05D%',
          'C05F%', 'C05G%', 'C06B%', 'C06C%', 'C06D%',
          'C06F%', 'C09B%', 'C09C%', 'C09D%', 'C09F%',
          'C09G%', 'C09H%', 'C09J%', 'C09K%', 'C10B%',
          'C10C%', 'C10F%', 'C10G%', 'C10H%', 'C10J%',
          'C10K%', 'C10L%', 'C10M%', 'C10N%', 'C11B%',
          'C11C%', 'C11D%', 'C99Z%'
      ] AS ipc_rules),
    STRUCT(20 AS field_number, 'Materials, metallurgy' AS field_name,
      [
          'B22C%', 'B22D%', 'B22F%', 'C01B%', 'C01C%',
          'C01D%', 'C01F%', 'C01G%', 'C03C%', 'C04B%',
          'C21B%', 'C21C%', 'C21D%', 'C22B%', 'C22C%',
          'C22F%'
      ] AS ipc_rules),
    STRUCT(21 AS field_number, 'Surface technology, coating' AS field_name,
      [
          'B05C%', 'B05D%', 'B32B%', 'C23C%', 'C23D%',
          'C23F%', 'C23G%', 'C25B%', 'C25C%', 'C25D%',
          'C25F%', 'C30B%'
      ] AS ipc_rules),
    STRUCT(22 AS field_number, 'Micro-structural and nano-technology' AS field_name,
      [
          'B81B%', 'B81C%', 'B82B%', 'B82Y%'
      ] AS ipc_rules),
    STRUCT(23 AS field_number, 'Chemical engineering' AS field_name,
      [
          'B01B%', 'B01D1/%', 'B01D3/%', 'B01D5/%', 'B01D7/%',
          'B01D8/%', 'B01D9/%', 'B01D11/%', 'B01D12/%', 'B01D15/%',
          'B01D17/%', 'B01D19/%', 'B01D21/%', 'B01D24/%', 'B01D25/%',
          'B01D27/%', 'B01D29/%', 'B01D33/%', 'B01D35/%', 'B01D36/%',
          'B01D37/%', 'B01D39/%', 'B01D41/%', 'B01D43/%', 'B01D57/%',
          'B01D59/%', 'B01D61/%', 'B01D63/%', 'B01D65/%', 'B01D67/%',
          'B01D69/%', 'B01D71/%', 'B01F%', 'B01J%', 'B01L%',
          'B02C%', 'B03B%', 'B03C%', 'B03D%', 'B04B%',
          'B04C%', 'B05B%', 'B06B%', 'B07B%', 'B07C%',
          'B08B%', 'C14C%', 'D06B%', 'D06C%', 'D06L%',
          'F25J%', 'F26B%', 'H05H%'
      ] AS ipc_rules),
    STRUCT(24 AS field_number, 'Environmental technology' AS field_name,
      [
          'A62C%', 'B01D45/%', 'B01D46/%', 'B01D47/%', 'B01D49/%',
          'B01D50/%', 'B01D51/%', 'B01D52/%', 'B01D53/%', 'B09B%',
          'B09C%', 'B65F%', 'C02F%', 'E01F8/%', 'F01N%',
          'F23G%', 'F23J%', 'G01T%'
      ] AS ipc_rules)
  ])
), publications AS (
  SELECT
    p.publication_number,
    p.publication_date,
    (SELECT t.text FROM UNNEST(p.title_localized) AS t
     WHERE t.language = 'en' AND LENGTH(TRIM(t.text)) > 0
     ORDER BY t.text LIMIT 1) AS title_en,
    (SELECT a.text FROM UNNEST(p.abstract_localized) AS a
     WHERE a.language = 'en' AND LENGTH(TRIM(a.text)) > 0
     ORDER BY a.text LIMIT 1) AS abstract_en,
    ARRAY(
      SELECT DISTINCT i.code FROM UNNEST(p.ipc) AS i
      WHERE i.code IS NOT NULL AND LENGTH(TRIM(i.code)) > 0
      ORDER BY i.code
    ) AS ipc_codes
  FROM `patents-public-data.patents.publications` AS p
  WHERE p.publication_date >= 20210101
    AND p.publication_date < 20261001
), matched AS (
  SELECT p.*, f.field_number, f.field_name
  FROM publications AS p
  CROSS JOIN fields AS f
  WHERE p.title_en IS NOT NULL
    AND p.abstract_en IS NOT NULL
    AND EXISTS (
      SELECT 1
      FROM UNNEST(p.ipc_codes) AS code
      CROSS JOIN UNNEST(f.ipc_rules) AS rule
      WHERE REGEXP_REPLACE(UPPER(code), r'\s+', '') LIKE rule
    )
), sampled AS (
  SELECT *
  FROM matched
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY field_number
    ORDER BY FARM_FINGERPRINT(CONCAT(
      'wipo-pilot-v1|', CAST(field_number AS STRING), '|', publication_number
    )), publication_number
  ) <= 2000
)
SELECT
  field_number AS wipo_field_number,
  field_name AS wipo_field_name,
  'Chemistry' AS wipo_sector,
  publication_number,
  publication_date,
  title_en,
  abstract_en,
  ARRAY_TO_STRING(ipc_codes, ';') AS ipc_codes
FROM sampled
ORDER BY wipo_field_number, publication_number;
