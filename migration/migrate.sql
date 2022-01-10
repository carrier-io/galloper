# from pre 2.0 to 2.0

ALTER TABLE security_report ALTER COLUMN description TYPE TEXT;

ALTER TABLE ui_report ADD COLUMN uid VARCHAR(128) NOT NULL;
ALTER TABLE ui_result DROP COLUMN report_id;
ALTER TABLE ui_result ADD COLUMN report_uid VARCHAR(128);
ALTER TABLE api_report ADD COLUMN status VARCHAR(128);
ALTER TABLE performance_tests ADD COLUMN git JSON;
ALTER TABLE ui_report ADD COLUMN browser_version VARCHAR(128);
ALTER TABLE api_report ADD COLUMN test_uid VARCHAR(128);
ALTER TABLE ui_thresholds ADD COLUMN name VARCHAR(256);
ALTER TABLE project_quota ADD COLUMN last_update_time DATETIME DEFAULT (TIMEZONE('utc', CURRENT_TIMESTAMP))
ALTER TABLE ui_result ADD COLUMN name VARCHAR(256);
ALTER TABLE ui_result ADD COLUMN session_id VARCHAR(256);
ALTER TABLE project_quota ADD COLUMN last_update_time TIMESTAMP DEFAULT (TIMEZONE('utc', CURRENT_TIMESTAMP));
ALTER TABLE ui_performance_tests ADD COLUMN git JSON;
ALTER TABLE ui_performance_tests ADD COLUMN emails TEXT;
# Done 2.0


# from 2.0 to 2.5

ALTER TABLE ui_report ADD COLUMN status VARCHAR(128);

ALTER TABLE task DROP CONSTRAINT task_zippath_key;
ALTER TABLE performance_tests ADD COLUMN region VARCHAR(128);
ALTER TABLE ui_performance_tests ADD COLUMN region VARCHAR(128);
ALTER TABLE security_tests_dast ADD COLUMN region VARCHAR(128);
ALTER TABLE security_tests_sast ADD COLUMN region VARCHAR(128);

ALTER TABLE api_report ADD COLUMN pct50 FLOAT;
ALTER TABLE api_report ADD COLUMN pct75 FLOAT;
ALTER TABLE api_report ADD COLUMN pct90 FLOAT;
ALTER TABLE api_report ADD COLUMN pct99 FLOAT;
ALTER TABLE api_report ADD COLUMN _max FLOAT;
ALTER TABLE api_report ADD COLUMN _min FLOAT;
ALTER TABLE api_report ADD COLUMN mean FLOAT;

--ALTER TABLE ui_result ADD COLUMN source_package VARCHAR(128);
--ALTER TABLE ui_result ADD COLUMN browsertime_package VARCHAR(128);


============================
ALTER TABLE ui_result ADD COLUMN browser_time JSON DEFAULT {}
ALTER TABLE ui_result ADD COLUMN fcp INTEGER DEFAULT 0
ALTER TABLE ui_result ADD COLUMN lcp INTEGER DEFAULT 0
ALTER TABLE ui_result ADD COLUMN cls FLOAT DEFAULT 0.0
ALTER TABLE ui_result ADD COLUMN tbt INTEGER DEFAULT 0
ALTER TABLE ui_result ADD COLUMN fvc INTEGER DEFAULT 0
ALTER TABLE ui_result ADD COLUMN lvc INTEGER DEFAULT 0
