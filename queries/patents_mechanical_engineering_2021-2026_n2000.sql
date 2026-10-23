-- Mechanical engineering: up to 2000 publications per WIPO field (25-32).
-- Maximum output: 16000 rows. WIPO concordance: March 2026.
-- Publication dates: 2021-01-01 through 2026-09-30 inclusive.
-- Query logic and sampling seed retained from the verified Instruments extraction.
-- No patent-family deduplication or cross-field deduplication.
-- Run in BigQuery using GoogleSQL. Check the estimated bytes first.
WITH fields AS (
  SELECT * FROM UNNEST([
    STRUCT(25 AS field_number, 'Handling' AS field_name,
      [
          'B25J%', 'B65B%', 'B65C%', 'B65D%', 'B65G%',
          'B65H%', 'B66B%', 'B66C%', 'B66D%', 'B66F%',
          'B67B%', 'B67C%', 'B67D%'
      ] AS ipc_rules),
    STRUCT(26 AS field_number, 'Machine tools' AS field_name,
      [
          'A62D%', 'B21B%', 'B21C%', 'B21D%', 'B21F%',
          'B21G%', 'B21H%', 'B21J%', 'B21K%', 'B21L%',
          'B23B%', 'B23C%', 'B23D%', 'B23F%', 'B23G%',
          'B23H%', 'B23K%', 'B23P%', 'B23Q%', 'B24B%',
          'B24C%', 'B24D%', 'B25B%', 'B25C%', 'B25D%',
          'B25F%', 'B25G%', 'B25H%', 'B26B%', 'B26D%',
          'B26F%', 'B27B%', 'B27C%', 'B27D%', 'B27F%',
          'B27G%', 'B27H%', 'B27J%', 'B27K%', 'B27L%',
          'B27M%', 'B27N%', 'B30B%'
      ] AS ipc_rules),
    STRUCT(27 AS field_number, 'Engines, pumps, turbines' AS field_name,
      [
          'F01B%', 'F01C%', 'F01D%', 'F01K%', 'F01L%',
          'F01M%', 'F01P%', 'F02B%', 'F02C%', 'F02D%',
          'F02F%', 'F02G%', 'F02K%', 'F02M%', 'F02N%',
          'F02P%', 'F03B%', 'F03C%', 'F03D%', 'F03G%',
          'F03H%', 'F04B%', 'F04C%', 'F04D%', 'F04F%',
          'F23R%', 'F99Z%', 'G21B%', 'G21C%', 'G21D%',
          'G21F%', 'G21G%', 'G21H%', 'G21J%', 'G21K%'
      ] AS ipc_rules),
    STRUCT(28 AS field_number, 'Textile and paper machines' AS field_name,
      [
          'A41H%', 'A43D%', 'A46D%', 'B31B%', 'B31C%',
          'B31D%', 'B31F%', 'B41B%', 'B41C%', 'B41D%',
          'B41F%', 'B41G%', 'B41J%', 'B41K%', 'B41L%',
          'B41M%', 'B41N%', 'C14B%', 'D01B%', 'D01C%',
          'D01D%', 'D01F%', 'D01G%', 'D01H%', 'D02G%',
          'D02H%', 'D02J%', 'D03C%', 'D03D%', 'D03J%',
          'D04B%', 'D04C%', 'D04G%', 'D04H%', 'D05B%',
          'D05C%', 'D06G%', 'D06H%', 'D06J%', 'D06M%',
          'D06P%', 'D06Q%', 'D21B%', 'D21C%', 'D21D%',
          'D21F%', 'D21G%', 'D21H%', 'D21J%', 'D99Z%'
      ] AS ipc_rules),
    STRUCT(29 AS field_number, 'Other special machines' AS field_name,
      [
          'A01B%', 'A01C%', 'A01D%', 'A01F%', 'A01G%',
          'A01J%', 'A01K%', 'A01L%', 'A01M%', 'A21B%',
          'A21C%', 'A22B%', 'A22C%', 'A23N%', 'A23P%',
          'B02B%', 'B28B%', 'B28C%', 'B28D%', 'B29B%',
          'B29C%', 'B29D%', 'B29K%', 'B29L%', 'B33Y%',
          'B99Z%', 'C03B%', 'C08J%', 'C12L%', 'C13B5/%',
          'C13B15/%', 'C13B25/%', 'C13B45/%', 'C13C%', 'C13G%',
          'C13H%', 'F41A%', 'F41B%', 'F41C%', 'F41F%',
          'F41G%', 'F41H%', 'F41J%', 'F42B%', 'F42C%',
          'F42D%'
      ] AS ipc_rules),
    STRUCT(30 AS field_number, 'Thermal processes and apparatus' AS field_name,
      [
          'F22B%', 'F22D%', 'F22G%', 'F23B%', 'F23C%',
          'F23D%', 'F23H%', 'F23K%', 'F23L%', 'F23M%',
          'F23N%', 'F23Q%', 'F24B%', 'F24C%', 'F24D%',
          'F24F%', 'F24H%', 'F24J%', 'F24S%', 'F24T%',
          'F24V%', 'F25B%', 'F25C%', 'F27B%', 'F27D%',
          'F28B%', 'F28C%', 'F28D%', 'F28F%', 'F28G%'
      ] AS ipc_rules),
    STRUCT(31 AS field_number, 'Mechanical elements' AS field_name,
      [
          'F15B%', 'F15C%', 'F15D%', 'F16B%', 'F16C%',
          'F16D%', 'F16F%', 'F16G%', 'F16H%', 'F16J%',
          'F16K%', 'F16L%', 'F16M%', 'F16N%', 'F16P%',
          'F16S%', 'F16T%', 'F17B%', 'F17C%', 'F17D%',
          'G05G%'
      ] AS ipc_rules),
    STRUCT(32 AS field_number, 'Transport' AS field_name,
      [
          'B60B%', 'B60C%', 'B60D%', 'B60F%', 'B60G%',
          'B60H%', 'B60J%', 'B60K%', 'B60L%', 'B60M%',
          'B60N%', 'B60P%', 'B60Q%', 'B60R%', 'B60S%',
          'B60T%', 'B60V%', 'B60W%', 'B61B%', 'B61C%',
          'B61D%', 'B61F%', 'B61G%', 'B61H%', 'B61J%',
          'B61K%', 'B61L%', 'B62B%', 'B62C%', 'B62D%',
          'B62H%', 'B62J%', 'B62K%', 'B62L%', 'B62M%',
          'B63B%', 'B63C%', 'B63G%', 'B63H%', 'B63J%',
          'B64B%', 'B64C%', 'B64D%', 'B64F%', 'B64G%',
          'B64U%'
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
  'Mechanical engineering' AS wipo_sector,
  publication_number,
  publication_date,
  title_en,
  abstract_en,
  ARRAY_TO_STRING(ipc_codes, ';') AS ipc_codes
FROM sampled
ORDER BY wipo_field_number, publication_number;
