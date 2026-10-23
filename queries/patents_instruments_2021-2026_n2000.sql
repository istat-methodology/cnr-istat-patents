-- Instruments full extraction: up to 2000 publications per WIPO field (9-13).
-- Maximum output: 10000 rows. Sampling seed unchanged from the verified pilot.
-- Source: WIPO IPC-Technology Concordance, March 2026.
-- Publication dates: 2021-01-01 through 2026-09-30 inclusive.
-- No patent-family deduplication or cross-field deduplication.
-- Run in BigQuery using GoogleSQL. Check the estimated bytes first.
WITH fields AS (
  SELECT * FROM UNNEST([
    STRUCT(9 AS field_number, 'Optics' AS field_name,
      [
          'G02B%', 'G02C%', 'G02F%', 'G03B%', 'G03C%',
          'G03D%', 'G03F%', 'G03G%', 'G03H%', 'H01S%'
      ] AS ipc_rules),
    STRUCT(10 AS field_number, 'Measurement' AS field_name,
      [
          'G01B%', 'G01C%', 'G01D%', 'G01F%', 'G01G%',
          'G01H%', 'G01J%', 'G01K%', 'G01L%', 'G01M%',
          'G01N1/%', 'G01N3/%', 'G01N5/%', 'G01N7/%', 'G01N9/%',
          'G01N11/%', 'G01N13/%', 'G01N15/%', 'G01N17/%', 'G01N19/%',
          'G01N21/%', 'G01N22/%', 'G01N23/%', 'G01N24/%', 'G01N25/%',
          'G01N27/%', 'G01N29/%', 'G01N30/%', 'G01N31/%', 'G01N35/%',
          'G01N37/%', 'G01P%', 'G01Q%', 'G01R%', 'G01S%',
          'G01V%', 'G01W%', 'G04B%', 'G04C%', 'G04D%',
          'G04F%', 'G04G%', 'G04R%', 'G12B%', 'G99Z%'
      ] AS ipc_rules),
    STRUCT(11 AS field_number, 'Analysis of biological materials' AS field_name,
      [
          'G01N33/%'
      ] AS ipc_rules),
    STRUCT(12 AS field_number, 'Control' AS field_name,
      [
          'G05B%', 'G05D%', 'G05F%', 'G07B%', 'G07C%',
          'G07D%', 'G07F%', 'G07G%', 'G08B%', 'G08G%',
          'G09B%', 'G09C%', 'G09D%'
      ] AS ipc_rules),
    STRUCT(13 AS field_number, 'Medical technology' AS field_name,
      [
          'A61B%', 'A61C%', 'A61D%', 'A61F%', 'A61G%',
          'A61H%', 'A61J%', 'A61K40/%', 'A61L%', 'A61M%',
          'A61N%', 'G16H%', 'H05G%'
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
  'Instruments' AS wipo_sector,
  publication_number,
  publication_date,
  title_en,
  abstract_en,
  ARRAY_TO_STRING(ipc_codes, ';') AS ipc_codes
FROM sampled
ORDER BY wipo_field_number, publication_number;
