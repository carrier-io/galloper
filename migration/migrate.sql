# from pre 2.0 to 2.0

ALTER TABLE security_report ALTER COLUMN description TYPE TEXT;

ALTER TABLE ui_report ADD COLUMN uid VARCHAR(128) NOT NULL;
ALTER TABLE ui_result DROP COLUMN report_id;
ALTER TABLE ui_result ADD COLUMN report_uid VARCHAR(128);
ALTER TABLE api_report ADD COLUMN status VARCHAR(128);
ALTER TABLE performance_tests ADD COLUMN git JSON;
ALTER TABLE ui_report ADD COLUMN browser_version VARCHAR(128);

#

ALTER TABLE api_report ADD COLUMN test_uid VARCHAR(128);
ALTER TABLE ui_thresholds ADD COLUMN name VARCHAR(256);
ALTER TABLE project_quota ADD COLUMN last_update_time DATETIME DEFAULT (TIMEZONE('utc', CURRENT_TIMESTAMP))
