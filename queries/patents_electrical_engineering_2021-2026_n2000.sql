-- Electrical engineering: up to 2000 publications per WIPO field (1-8).
-- Maximum output: 16000 rows. WIPO concordance: March 2026.
-- Publication dates: 2021-01-01 through 2026-09-30 inclusive.
-- Query logic and sampling seed retained from the verified Instruments extraction.
-- No patent-family deduplication or cross-field deduplication.
-- Run in BigQuery using GoogleSQL. Check the estimated bytes first.
WITH fields AS (
  SELECT * FROM UNNEST([
    STRUCT(1 AS field_number, 'Electrical machinery, apparatus, energy' AS field_name,
      [
          'F21H%', 'F21K%', 'F21L%', 'F21S%', 'F21V%',
          'F21W%', 'F21Y%', 'H01B%', 'H01C%', 'H01F%',
          'H01G%', 'H01H%', 'H01J%', 'H01K%', 'H01M%',
          'H01R%', 'H01T%', 'H02B%', 'H02G%', 'H02H%',
          'H02J%', 'H02K%', 'H02M%', 'H02N%', 'H02P%',
          'H02S%', 'H05B%', 'H05C%', 'H05F%', 'H99Z%'
      ] AS ipc_rules),
    STRUCT(2 AS field_number, 'Audio-visual technology' AS field_name,
      [
          'G09F%', 'G09G%', 'G11B%', 'H04N3/%', 'H04N5/%',
          'H04N7/%', 'H04N9/%', 'H04N11/%', 'H04N13/%', 'H04N15/%',
          'H04N17/%', 'H04N19/%', 'H04N23/%', 'H04N25/%', 'H04N101/%',
          'H04R%', 'H04S%', 'H05K%'
      ] AS ipc_rules),
    STRUCT(3 AS field_number, 'Telecommunications' AS field_name,
      [
          'G08C%', 'H01P%', 'H01Q%', 'H04B%', 'H04H%',
          'H04J%', 'H04K%', 'H04M%', 'H04N1/%', 'H04Q%'
      ] AS ipc_rules),
    STRUCT(4 AS field_number, 'Digital communication' AS field_name,
      [
          'H04L%', 'H04N21/%', 'H04W%'
      ] AS ipc_rules),
    STRUCT(5 AS field_number, 'Basic communication processes' AS field_name,
      [
          'H03B%', 'H03C%', 'H03D%', 'H03F%', 'H03G%',
          'H03H%', 'H03J%', 'H03K%', 'H03L%', 'H03M%'
      ] AS ipc_rules),
    STRUCT(6 AS field_number, 'Computer technology' AS field_name,
      [
          'G06C%', 'G06D%', 'G06E%', 'G06F%', 'G06G%',
          'G06J%', 'G06K%', 'G06M%', 'G06N%', 'G06T%',
          'G06V%', 'G10L%', 'G11C%', 'G16B%', 'G16C%',
          'G16Y%', 'G16Z%'
      ] AS ipc_rules),
    STRUCT(7 AS field_number, 'IT methods for management' AS field_name,
      [
          'G06Q%'
      ] AS ipc_rules),
    STRUCT(8 AS field_number, 'Semiconductors' AS field_name,
      [
          'H01L%', 'H10%'
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
  'Electrical engineering' AS wipo_sector,
  publication_number,
  publication_date,
  title_en,
  abstract_en,
  ARRAY_TO_STRING(ipc_codes, ';') AS ipc_codes
FROM sampled
ORDER BY wipo_field_number, publication_number;
