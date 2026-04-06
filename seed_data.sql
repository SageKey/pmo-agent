BEGIN TRANSACTION;
CREATE TABLE app_settings (
    key             TEXT PRIMARY KEY,
    category        TEXT NOT NULL,
    value           TEXT NOT NULL,          -- stored as string, coerced via value_type
    value_type      TEXT NOT NULL,          -- 'float', 'int', 'bool', 'string'
    label           TEXT NOT NULL,          -- display label for admin UI
    description     TEXT,                   -- longer help text
    min_value       REAL,                   -- optional numeric bound
    max_value       REAL,                   -- optional numeric bound
    unit            TEXT,                   -- '%', 'hrs', '$' etc. for display
    sort_order      INTEGER DEFAULT 0,
    updated_at      TEXT DEFAULT (datetime('now')),
    updated_by      TEXT
);
INSERT INTO "app_settings" VALUES('util_under_enabled','utilization','1','bool','Under-utilized state','When enabled, roles below the ''under'' threshold are flagged as under-utilized. Disable to merge this range into ''ideal''.',NULL,NULL,NULL,10,'2026-04-05 18:41:19',NULL);
INSERT INTO "app_settings" VALUES('util_under_max','utilization','0.70','float','Under → Ideal boundary','Utilization at or above this value exits ''under-utilized'' and enters the ideal band. Default 70%.',0.0,1.5,'%',20,'2026-04-05 18:41:19',NULL);
INSERT INTO "app_settings" VALUES('util_ideal_enabled','utilization','1','bool','Ideal state','The target utilization band. Typically always enabled.',NULL,NULL,NULL,30,'2026-04-05 18:41:19',NULL);
INSERT INTO "app_settings" VALUES('util_ideal_max','utilization','0.8','float','Ideal → Stretched boundary','Utilization at or above this value exits the ideal band. Default 80%.',0.0,1.5,'%',40,'2026-04-05 18:47:31',NULL);
INSERT INTO "app_settings" VALUES('util_stretched_enabled','utilization','1','bool','Stretched state','When enabled, roles between ideal and over are flagged as stretched (warning). Disable to merge this range into ''over''.',NULL,NULL,NULL,50,'2026-04-05 18:48:46',NULL);
INSERT INTO "app_settings" VALUES('util_stretched_max','utilization','1.00','float','Stretched → Over boundary','Utilization at or above this value is flagged as over-capacity. Default 100%.',0.0,2.0,'%',60,'2026-04-05 18:41:19',NULL);
INSERT INTO "app_settings" VALUES('util_over_enabled','utilization','1','bool','Over-capacity state','When enabled, roles above the stretched threshold are flagged as over-capacity. Typically always enabled.',NULL,NULL,NULL,70,'2026-04-05 18:41:19',NULL);
CREATE TABLE approved_work (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    jira_key            TEXT,
    title               TEXT NOT NULL,
    work_type           TEXT,                      -- Project, Enhancement, Break/Fix, Bug
    work_classification TEXT,                      -- CapEx or Support
    approved_date       TEXT,
    approver            TEXT,
    notes               TEXT
);
INSERT INTO "approved_work" VALUES(1,NULL,'Work Item 1','Enhancement','Support','2026-02-17','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(2,NULL,'Work Item 2','Project','CapEx','2026-01-16','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(3,NULL,'Work Item 3','Project','CapEx','2026-01-16','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(4,NULL,'Work Item 4','Project','CapEx','2026-01-16','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(5,NULL,'Work Item 5','Enhancement','Support','2026-02-17','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(6,NULL,'Work Item 6','Break/Fix','Support','2026-01-29','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(7,NULL,'Work Item 7','Break/Fix','Support','2026-02-17','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(8,NULL,'Work Item 8','Project','CapEx','2026-01-12','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(9,NULL,'Work Item 9','Project','CapEx','2026-02-09','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(10,NULL,'Work Item 10','Project','CapEx','2026-12-22','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(11,NULL,'Work Item 11','Project','CapEx','2026-12-12','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(12,NULL,'Work Item 12','Enhancement','Support','2026-01-15','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(13,NULL,'Work Item 13','Enhancement','Support','2026-02-13','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(14,NULL,'Work Item 14','Enhancement','Support','2026-01-15','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(15,NULL,'Work Item 15','Bug','Support','2025-10-08','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(16,NULL,'Work Item 16','Enhancement','Support','2026-01-19','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(17,NULL,'Work Item 17','Enhancement','Support','2026-12-10','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(18,NULL,'Work Item 18','Enhancement','Support','2026-01-16','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(19,NULL,'Work Item 19','Enhancement','Support','2026-01-16','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(20,NULL,'Work Item 20','Enhancement','Support','2026-01-16','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(21,NULL,'Work Item 21','Enhancement','Support','2026-02-18','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(22,NULL,'Work Item 22','Project','CapEx','2026-02-04','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(23,NULL,'Work Item 23','Enhancement','Support','2026-01-14','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(24,NULL,'Work Item 24','Bug','Support','2026-02-18','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(25,NULL,'Work Item 25','Enhancement','Support',NULL,NULL,NULL);
INSERT INTO "approved_work" VALUES(26,NULL,'Work Item 26','Bug','Support',NULL,NULL,NULL);
INSERT INTO "approved_work" VALUES(27,NULL,'Work Item 27','Project','CapEx',NULL,NULL,NULL);
INSERT INTO "approved_work" VALUES(28,NULL,'Work Item 28','Enhancement','Support','2026-02-20','Felix Krause',NULL);
INSERT INTO "approved_work" VALUES(29,NULL,'Work Item 29','Enhancement','Support','2026-02-25','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(30,NULL,'Work Item 30','Project','CapEx','2026-02-27','Sage Ivanov',NULL);
INSERT INTO "approved_work" VALUES(31,NULL,'Work Item 31','Project','CapEx','2026-03-03','Sage Ivanov',NULL);
CREATE TABLE initiatives (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, sponsor TEXT,
        status TEXT NOT NULL DEFAULT 'Active', it_involvement INTEGER NOT NULL DEFAULT 0,
        priority TEXT, target_start TEXT, target_end TEXT, sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
    );
INSERT INTO "initiatives" VALUES('INIT-01','Supply Chain Modernization','End-to-end overhaul of supply chain systems and processes','Camille Okafor','Active',1,'Highest','2025-01-15','2026-09-30',1,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-02','Customer Experience Platform','Unified platform for omnichannel customer engagement','Nolan Pierce','Active',1,'High','2025-03-01','2026-12-31',2,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-03','Workforce Optimization','Modernize workforce planning, scheduling, and productivity tools','Beatrice Lin','Active',1,'High','2025-04-01','2026-10-31',3,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-04','Financial Close Transformation','Accelerate month-end close from 10 days to 3 days','Nolan Pierce','Active',1,'Highest','2025-02-01','2026-06-30',4,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-05','Data Analytics Center of Excellence','Establish enterprise analytics capability and self-service BI','Rafael Bauer','Active',1,'High','2025-06-01','2026-12-31',5,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-06','Cybersecurity Posture Enhancement','Strengthen security controls, zero trust architecture, and compliance','Rafael Bauer','Active',1,'Highest','2025-01-01','2026-12-31',6,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-07','ERP System Consolidation','Consolidate three legacy ERPs into a single platform','Nolan Pierce','Active',1,'High','2025-03-15','2026-12-31',7,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-08','Digital Commerce Expansion','Expand e-commerce channels and digital storefront capabilities','Camille Okafor','Active',1,'Medium','2025-07-01','2026-09-30',8,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-09','Fleet Management Overhaul','Replace aging fleet management systems and optimize routing','Camille Okafor','Active',1,'Medium','2025-09-01','2026-11-30',9,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-10','Vendor Risk Management Program','Implement third-party risk assessment and continuous monitoring','Beatrice Lin','Active',1,'High','2025-05-01','2026-08-31',10,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-11','Product Lifecycle Management','Digital PLM system for product design through retirement','Camille Okafor','Active',1,'Medium','2025-08-01','2026-12-31',11,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-12','Cloud Infrastructure Migration','Migrate on-premise workloads to cloud with hybrid strategy','Rafael Bauer','Active',1,'Highest','2025-01-01','2026-12-31',12,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-13','Employee Experience Modernization','Redesign HR tech stack for improved employee lifecycle','Beatrice Lin','Active',1,'Medium','2025-06-15','2026-10-31',13,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-14','Regulatory Compliance Automation','Automate regulatory reporting and compliance workflows','Nolan Pierce','Active',1,'High','2025-04-01','2026-09-30',14,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-15','Manufacturing Execution System','Implement MES for real-time shop floor visibility','Camille Okafor','Active',1,'Medium','2025-10-01','2026-12-31',15,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-16','Sustainability Reporting Platform','ESG metrics collection, analysis, and regulatory reporting','Grace Chandler','Active',1,'Low','2025-09-01','2026-12-31',16,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-17','Customer Loyalty Relaunch','Redesign loyalty program with personalized rewards engine','Nolan Pierce','Active',1,'High','2025-05-01','2026-08-31',17,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-18','Inventory Optimization Program','AI-driven inventory balancing across distribution network','Camille Okafor','On Hold',1,'Medium','2025-07-01','2026-10-31',18,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-19','Legacy System Decommission','Retire 12 end-of-life applications and migrate data','Rafael Bauer','Complete',1,'High','2025-01-01','2025-12-31',19,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-20','Corporate Real Estate Rationalization','Optimize office footprint post-hybrid work model','Beatrice Lin','Active',0,'Medium','2025-06-01','2026-06-30',20,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-21','Leadership Development Academy','Build internal leadership pipeline and succession readiness','Grace Chandler','Active',0,'High','2025-03-01','2026-12-31',21,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-22','Brand Refresh Campaign','Update brand identity, messaging, and market positioning','Camille Okafor','Active',0,'Medium','2025-08-01','2026-06-30',22,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-23','Safety Culture Transformation','Zero-incident safety program across all facilities','Camille Okafor','Active',0,'Highest','2025-01-01','2026-12-31',23,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-24','Community Engagement Program','Corporate social responsibility and community partnerships','Grace Chandler','Active',0,'Low','2025-04-01','2026-12-31',24,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-25','Diversity & Inclusion Strategy','Enterprise D&I goals, programs, and metrics framework','Grace Chandler','Active',0,'High','2025-02-01','2026-12-31',25,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-26','Operational Excellence (Lean/6Sigma)','Enterprise-wide continuous improvement program','Camille Okafor','Active',0,'Highest','2025-01-01','2026-12-31',26,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-27','New Market Entry - Southeast Region','Expand operations into southeast US markets','Nolan Pierce','Active',0,'High','2025-06-01','2026-09-30',27,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-28','Talent Acquisition Redesign','Modernize recruiting process and employer brand','Beatrice Lin','Active',0,'Medium','2025-07-01','2026-06-30',28,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-29','Executive Succession Planning','Formal succession plans for top 50 leadership roles','Grace Chandler','Active',0,'High','2025-03-01','2026-09-30',29,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-30','Environmental Compliance Review','Audit and remediate environmental regulatory gaps','Camille Okafor','Active',0,'Medium','2025-05-01','2026-08-31',30,'2026-04-06 16:40:29','2026-04-06 16:40:29');
INSERT INTO "initiatives" VALUES('INIT-31','Workplace Wellness Initiative','Employee health, mental wellness, and benefits optimization','Beatrice Lin','Active',0,'Low','2025-09-01','2026-12-31',31,'2026-04-06 16:40:29','2026-04-06 16:40:29');
CREATE TABLE project_assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    person_name     TEXT NOT NULL,
    role_key        TEXT NOT NULL,
    allocation_pct  REAL DEFAULT 1.0,
    UNIQUE(project_id, person_name, role_key)
);
INSERT INTO "project_assignments" VALUES(1,'DEMO-034','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(2,'DEMO-034','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(3,'DEMO-034','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(4,'DEMO-034','June Kim','technical',1.0);
INSERT INTO "project_assignments" VALUES(5,'DEMO-034','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(6,'DEMO-016','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(7,'DEMO-016','Ivy Krause','ba',1.0);
INSERT INTO "project_assignments" VALUES(8,'DEMO-016','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(9,'DEMO-016','Liam Garcia','technical',1.0);
INSERT INTO "project_assignments" VALUES(10,'DEMO-016','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(11,'DEMO-026','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(12,'DEMO-026','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(13,'DEMO-026','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(14,'DEMO-026','Jasper Okonkwo','technical',1.0);
INSERT INTO "project_assignments" VALUES(16,'DEMO-014','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(17,'DEMO-014','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(18,'DEMO-014','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(19,'DEMO-014','Jonas Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(20,'DEMO-014','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(21,'DEMO-006','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(22,'DEMO-006','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(23,'DEMO-006','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(24,'DEMO-006','June Kim','technical',1.0);
INSERT INTO "project_assignments" VALUES(25,'DEMO-006','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(26,'DEMO-017','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(27,'DEMO-017','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(28,'DEMO-017','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(29,'DEMO-017','Jonas Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(30,'DEMO-017','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(31,'DEMO-028','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(32,'DEMO-028','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(33,'DEMO-028','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(34,'DEMO-028','June Kim','technical',1.0);
INSERT INTO "project_assignments" VALUES(35,'DEMO-028','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(36,'DEMO-019','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(37,'DEMO-019','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(38,'DEMO-019','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(39,'DEMO-019','June Kim','technical',1.0);
INSERT INTO "project_assignments" VALUES(40,'DEMO-019','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(41,'DEMO-005','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(42,'DEMO-005','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(43,'DEMO-005','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(44,'DEMO-005','James Fontaine','technical',1.0);
INSERT INTO "project_assignments" VALUES(45,'DEMO-005','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(46,'DEMO-012','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(47,'DEMO-012','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(48,'DEMO-012','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(49,'DEMO-012','Jonas Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(50,'DEMO-012','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(51,'DEMO-038','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(52,'DEMO-038','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(53,'DEMO-038','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(54,'DEMO-038','June Kim','technical',1.0);
INSERT INTO "project_assignments" VALUES(55,'DEMO-038','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(56,'DEMO-002','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(57,'DEMO-002','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(58,'DEMO-002','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(59,'DEMO-002','James Fontaine','technical',1.0);
INSERT INTO "project_assignments" VALUES(60,'DEMO-002','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(61,'DEMO-003','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(62,'DEMO-003','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(63,'DEMO-003','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(64,'DEMO-003','Jonas Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(65,'DEMO-003','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(66,'DEMO-009','Priya Romano','pm',1.0);
INSERT INTO "project_assignments" VALUES(67,'DEMO-009','Ivy Krause','ba',1.0);
INSERT INTO "project_assignments" VALUES(68,'DEMO-009','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(69,'DEMO-009','Jonas Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(70,'DEMO-025','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(71,'DEMO-025','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(72,'DEMO-025','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(73,'DEMO-025','Liam Garcia','technical',1.0);
INSERT INTO "project_assignments" VALUES(74,'DEMO-004','Lucas Garcia','pm',1.0);
INSERT INTO "project_assignments" VALUES(75,'DEMO-004','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(76,'DEMO-004','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(77,'DEMO-004','Jonas Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(78,'DEMO-029','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(79,'DEMO-029','Owen Reyes','ba',1.0);
INSERT INTO "project_assignments" VALUES(80,'DEMO-029','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(81,'DEMO-029','Max Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(82,'DEMO-024','Priya Romano','pm',1.0);
INSERT INTO "project_assignments" VALUES(83,'DEMO-024','Ivy Krause','ba',1.0);
INSERT INTO "project_assignments" VALUES(84,'DEMO-024','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(85,'DEMO-024','Chloe Costa','technical',1.0);
INSERT INTO "project_assignments" VALUES(86,'DEMO-027','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(87,'DEMO-027','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(88,'DEMO-027','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(89,'DEMO-027','James Fontaine','technical',1.0);
INSERT INTO "project_assignments" VALUES(90,'DEMO-007','Priya Romano','pm',1.0);
INSERT INTO "project_assignments" VALUES(91,'DEMO-007','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(92,'DEMO-007','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(93,'DEMO-007','June Kim','technical',1.0);
INSERT INTO "project_assignments" VALUES(94,'DEMO-015','Priya Romano','pm',1.0);
INSERT INTO "project_assignments" VALUES(95,'DEMO-015','Rosa Flores','ba',1.0);
INSERT INTO "project_assignments" VALUES(96,'DEMO-015','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(97,'DEMO-015','Liam Garcia','technical',1.0);
INSERT INTO "project_assignments" VALUES(98,'DEMO-013','Lucas Garcia','pm',1.0);
INSERT INTO "project_assignments" VALUES(99,'DEMO-013','Rosa Flores','ba',1.0);
INSERT INTO "project_assignments" VALUES(100,'DEMO-013','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(101,'DEMO-013','Sophia Nakamura','technical',1.0);
INSERT INTO "project_assignments" VALUES(102,'DEMO-031','Sophia Rivera','technical',1.0);
INSERT INTO "project_assignments" VALUES(103,'DEMO-030','Max Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(104,'DEMO-036','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(105,'DEMO-036','Rosa Flores','ba',1.0);
INSERT INTO "project_assignments" VALUES(106,'DEMO-036','Caleb Bauer','functional',1.0);
INSERT INTO "project_assignments" VALUES(107,'DEMO-036','Sophia Nakamura','technical',1.0);
INSERT INTO "project_assignments" VALUES(108,'DEMO-037','Priya Romano','pm',1.0);
INSERT INTO "project_assignments" VALUES(109,'DEMO-037','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(110,'DEMO-037','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(111,'DEMO-037','Liam Garcia','technical',1.0);
INSERT INTO "project_assignments" VALUES(112,'DEMO-032','Priya Romano','pm',1.0);
INSERT INTO "project_assignments" VALUES(113,'DEMO-032','Rosa Flores','ba',1.0);
INSERT INTO "project_assignments" VALUES(114,'DEMO-032','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(115,'DEMO-032','Jonas Dupont','technical',1.0);
INSERT INTO "project_assignments" VALUES(116,'DEMO-001','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(117,'DEMO-001','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(118,'DEMO-001','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(119,'DEMO-001','June Kim','technical',1.0);
INSERT INTO "project_assignments" VALUES(120,'DEMO-001','Jonas Fontaine','developer',1.0);
INSERT INTO "project_assignments" VALUES(121,'DEMO-008','Lucas Garcia','pm',1.0);
INSERT INTO "project_assignments" VALUES(122,'DEMO-008','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(123,'DEMO-008','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(124,'DEMO-008','Sophia Nakamura','technical',1.0);
INSERT INTO "project_assignments" VALUES(125,'DEMO-033','Liam Nguyen','pm',1.0);
INSERT INTO "project_assignments" VALUES(126,'DEMO-033','Silas Ivanov','ba',1.0);
INSERT INTO "project_assignments" VALUES(127,'DEMO-033','Arlo Haruki','functional',1.0);
INSERT INTO "project_assignments" VALUES(128,'DEMO-033','Jonas Fontaine','technical',1.0);
INSERT INTO "project_assignments" VALUES(129,'DEMO-033','Jonas Fontaine','developer',1.0);
CREATE TABLE project_attachments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    file_size       INTEGER DEFAULT 0,
    mime_type       TEXT,
    stored_path     TEXT NOT NULL,
    uploaded_by     TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE TABLE project_audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    action          TEXT NOT NULL,
    actor           TEXT NOT NULL,
    field_changed   TEXT,
    old_value       TEXT,
    new_value       TEXT,
    details         TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
INSERT INTO "project_audit_log" VALUES(1,'DEMO-006','comment_added','Sage Ivanov',NULL,NULL,NULL,'Milestone completed','2026-04-03 23:18:46');
INSERT INTO "project_audit_log" VALUES(2,'DEMO-006','milestones_seeded','Sage Ivanov',NULL,NULL,NULL,'Updated health status','2026-04-04 00:30:20');
INSERT INTO "project_audit_log" VALUES(3,'DEMO-006','task_added','Sage Ivanov',NULL,NULL,NULL,'Comment added','2026-04-04 00:30:29');
INSERT INTO "project_audit_log" VALUES(4,'DEMO-006','task_added','Sage Ivanov',NULL,NULL,NULL,'Milestone completed','2026-04-04 00:30:29');
INSERT INTO "project_audit_log" VALUES(5,'DEMO-006','task_added','Sage Ivanov',NULL,NULL,NULL,'Milestone completed','2026-04-04 00:30:29');
INSERT INTO "project_audit_log" VALUES(6,'DEMO-006','task_added','Sage Ivanov',NULL,NULL,NULL,'Updated health status','2026-04-04 00:30:29');
INSERT INTO "project_audit_log" VALUES(7,'DEMO-006','task_added','Sage Ivanov',NULL,NULL,NULL,'Milestone completed','2026-04-04 00:30:29');
INSERT INTO "project_audit_log" VALUES(8,'DEMO-006','task_added','Sage Ivanov',NULL,NULL,NULL,'Assignment updated','2026-04-04 00:30:29');
INSERT INTO "project_audit_log" VALUES(9,'DEMO-006','task_added','Sage Ivanov',NULL,NULL,NULL,'Assignment updated','2026-04-04 00:30:29');
INSERT INTO "project_audit_log" VALUES(10,'DEMO-006','task_added','Sage Ivanov',NULL,NULL,NULL,'Milestone completed','2026-04-04 00:30:29');
INSERT INTO "project_audit_log" VALUES(11,'DEMO-006','task_completed','Sage Ivanov',NULL,NULL,NULL,'Progress updated','2026-04-04 00:35:32');
INSERT INTO "project_audit_log" VALUES(12,'DEMO-016','milestones_seeded','Sage Ivanov',NULL,NULL,NULL,'Updated health status','2026-04-04 00:45:40');
INSERT INTO "project_audit_log" VALUES(13,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Assignment updated','2026-04-04 00:45:47');
INSERT INTO "project_audit_log" VALUES(14,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Updated health status','2026-04-04 00:45:47');
INSERT INTO "project_audit_log" VALUES(15,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Updated health status','2026-04-04 00:45:47');
INSERT INTO "project_audit_log" VALUES(16,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Comment added','2026-04-04 00:45:47');
INSERT INTO "project_audit_log" VALUES(17,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Assignment updated','2026-04-04 00:45:47');
INSERT INTO "project_audit_log" VALUES(18,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Comment added','2026-04-04 00:45:47');
INSERT INTO "project_audit_log" VALUES(19,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Updated health status','2026-04-04 00:45:47');
INSERT INTO "project_audit_log" VALUES(20,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Comment added','2026-04-04 00:45:47');
INSERT INTO "project_audit_log" VALUES(21,'DEMO-016','task_added','Sage Ivanov',NULL,NULL,NULL,'Updated health status','2026-04-04 00:46:39');
INSERT INTO "project_audit_log" VALUES(22,'DEMO-026','milestones_seeded','Sage Ivanov',NULL,NULL,NULL,'Updated health status','2026-04-04 01:22:35');
INSERT INTO "project_audit_log" VALUES(23,'DEMO-026','comment_added','Layla Flores',NULL,NULL,NULL,'Assignment updated','2026-04-05 13:48:54');
INSERT INTO "project_audit_log" VALUES(24,'DEMO-026','comment_added','Sage Ivanov',NULL,NULL,NULL,'Comment added','2026-04-05 13:53:38');
INSERT INTO "project_audit_log" VALUES(25,'DEMO-026','milestone_added','Hazel Romano',NULL,NULL,NULL,'Comment added','2026-04-05 14:02:39');
INSERT INTO "project_audit_log" VALUES(26,'DEMO-026','milestone_updated','Hazel Romano',NULL,NULL,NULL,'Updated health status','2026-04-05 14:02:39');
INSERT INTO "project_audit_log" VALUES(27,'DEMO-026','milestone_completed','Marcus Fischer',NULL,NULL,NULL,'Milestone completed','2026-04-05 14:02:39');
INSERT INTO "project_audit_log" VALUES(28,'DEMO-026','milestone_deleted','Marcus Fischer',NULL,NULL,NULL,'Assignment updated','2026-04-05 14:02:39');
INSERT INTO "project_audit_log" VALUES(29,'DEMO-006','milestone_added','Hazel Romano',NULL,NULL,NULL,'Assignment updated','2026-04-05 14:08:52');
INSERT INTO "project_audit_log" VALUES(30,'DEMO-006','milestone_completed','Marcus Fischer',NULL,NULL,NULL,'Assignment updated','2026-04-05 14:09:17');
INSERT INTO "project_audit_log" VALUES(31,'DEMO-006','milestone_deleted','Marcus Fischer',NULL,NULL,NULL,'Comment added','2026-04-05 14:09:26');
CREATE TABLE project_comments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    author          TEXT NOT NULL,
    body            TEXT NOT NULL,
    comment_type    TEXT NOT NULL DEFAULT 'comment',  -- 'comment', 'status_update', 'system'
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
INSERT INTO "project_comments" VALUES(1,'DEMO-006','Sage Ivanov','Requirements gathering complete.','comment','2026-04-03 23:18:46','2026-04-03 23:18:46');
CREATE TABLE project_mapping (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sse_key         TEXT NOT NULL UNIQUE,           -- SSE-xxx Jira key
    ete_project_id  TEXT,                           -- ETE-xx portfolio project ID
    sse_title       TEXT,                           -- Human-readable SSE title
    relationship    TEXT DEFAULT 'subtask',         -- subtask, support, related
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
INSERT INTO "project_mapping" VALUES(1,'DEMO-SSE-001','DEMO-006','Related work item 1','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(2,'DEMO-SSE-002','DEMO-006','Related work item 2','support',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(3,'DEMO-SSE-003','DEMO-001','Related work item 3','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(4,'DEMO-SSE-004','DEMO-004','Related work item 4','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(5,'DEMO-SSE-005','DEMO-025','Related work item 5','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(6,'DEMO-SSE-006','DEMO-028','Related work item 6','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(7,'DEMO-SSE-007','DEMO-027','Related work item 7','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(8,'DEMO-SSE-008','DEMO-013','Related work item 8','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(9,'DEMO-SSE-009','DEMO-008','Related work item 9','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(10,'DEMO-SSE-010','DEMO-021','Related work item 10','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(11,'DEMO-SSE-011','DEMO-020','Related work item 11','related',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(12,'DEMO-SSE-012','DEMO-009','Related work item 12','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(13,'DEMO-SSE-013','DEMO-009','Related work item 13','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(14,'DEMO-SSE-014','DEMO-009','Related work item 14','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(15,'DEMO-SSE-015','DEMO-009','Related work item 15','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(16,'DEMO-SSE-016','DEMO-003','Related work item 16','related',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(17,'DEMO-SSE-017','DEMO-003','Related work item 17','related',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(18,'DEMO-SSE-018','DEMO-027','Related work item 18','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(19,'DEMO-SSE-019','DEMO-027','Related work item 19','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(20,'DEMO-SSE-020','DEMO-027','Related work item 20','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(21,'DEMO-SSE-021','DEMO-005','Related work item 21','support',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(22,'DEMO-SSE-022','DEMO-009','Related work item 22','related',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(23,'DEMO-SSE-023','DEMO-028','Related work item 23','subtask',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(24,'DEMO-SSE-024','DEMO-022','Related work item 24','related',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
INSERT INTO "project_mapping" VALUES(25,'DEMO-SSE-025','DEMO-033','Related work item 25','related',NULL,'2026-04-03 22:36:19','2026-04-03 22:36:19');
CREATE TABLE project_milestones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    milestone_type  TEXT NOT NULL DEFAULT 'deliverable',
    due_date        TEXT,
    completed_date  TEXT,
    status          TEXT NOT NULL DEFAULT 'not_started',
    owner           TEXT,
    jira_epic_key   TEXT,
    progress_pct    REAL DEFAULT 0.0,
    sort_order      INTEGER DEFAULT 0,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
INSERT INTO "project_milestones" VALUES(1,'DEMO-006','Vendor Contract Signed','gate','2026-03-01',NULL,'not_started',NULL,NULL,0.0,0,NULL,'2026-04-04 00:30:20','2026-04-04 00:30:20');
INSERT INTO "project_milestones" VALUES(2,'DEMO-006','Vendor Contract Signed','gate','2026-03-08',NULL,'not_started',NULL,NULL,0.0,1,NULL,'2026-04-04 00:30:20','2026-04-04 00:30:20');
INSERT INTO "project_milestones" VALUES(3,'DEMO-006','Build Phase Kickoff','gate','2026-03-14',NULL,'not_started',NULL,NULL,0.0,2,NULL,'2026-04-04 00:30:20','2026-04-04 00:30:20');
INSERT INTO "project_milestones" VALUES(4,'DEMO-006','Requirements Signed Off','gate','2026-03-21',NULL,'not_started',NULL,NULL,0.0,3,NULL,'2026-04-04 00:30:20','2026-04-04 00:30:20');
INSERT INTO "project_milestones" VALUES(5,'DEMO-006','Hypercare Complete','deliverable','2026-03-28',NULL,'not_started',NULL,NULL,0.0,4,NULL,'2026-04-04 00:30:20','2026-04-04 00:30:20');
INSERT INTO "project_milestones" VALUES(6,'DEMO-006','Stakeholder Demo','gate','2026-04-03',NULL,'not_started',NULL,NULL,0.0,5,NULL,'2026-04-04 00:30:20','2026-04-04 00:30:20');
INSERT INTO "project_milestones" VALUES(7,'DEMO-006','UAT Sign-Off','go_live','2026-04-10',NULL,'not_started',NULL,NULL,0.0,6,NULL,'2026-04-04 00:30:20','2026-04-04 00:30:20');
INSERT INTO "project_milestones" VALUES(8,'DEMO-006','UAT Sign-Off','checkpoint','2026-04-17',NULL,'not_started',NULL,NULL,0.0,7,NULL,'2026-04-04 00:30:20','2026-04-04 00:30:20');
INSERT INTO "project_milestones" VALUES(9,'DEMO-016','Discovery Complete','gate','2026-03-03',NULL,'not_started',NULL,NULL,0.0,0,NULL,'2026-04-04 00:45:40','2026-04-04 00:45:40');
INSERT INTO "project_milestones" VALUES(10,'DEMO-016','Technical Design Review','gate','2026-03-20',NULL,'not_started',NULL,NULL,0.0,1,NULL,'2026-04-04 00:45:40','2026-04-04 00:45:40');
INSERT INTO "project_milestones" VALUES(11,'DEMO-016','Technical Design Review','gate','2026-04-06',NULL,'not_started',NULL,NULL,0.0,2,NULL,'2026-04-04 00:45:40','2026-04-04 00:45:40');
INSERT INTO "project_milestones" VALUES(12,'DEMO-016','Requirements Signed Off','gate','2026-04-23',NULL,'not_started',NULL,NULL,0.0,3,NULL,'2026-04-04 00:45:40','2026-04-04 00:45:40');
INSERT INTO "project_milestones" VALUES(13,'DEMO-016','Build Phase Kickoff','deliverable','2026-05-10',NULL,'not_started',NULL,NULL,0.0,4,NULL,'2026-04-04 00:45:40','2026-04-04 00:45:40');
INSERT INTO "project_milestones" VALUES(14,'DEMO-016','Stakeholder Demo','gate','2026-05-27',NULL,'not_started',NULL,NULL,0.0,5,NULL,'2026-04-04 00:45:40','2026-04-04 00:45:40');
INSERT INTO "project_milestones" VALUES(15,'DEMO-016','Production Cutover','go_live','2026-06-13',NULL,'not_started',NULL,NULL,0.0,6,NULL,'2026-04-04 00:45:40','2026-04-04 00:45:40');
INSERT INTO "project_milestones" VALUES(16,'DEMO-016','Technical Design Review','checkpoint','2026-06-30',NULL,'not_started',NULL,NULL,0.0,7,NULL,'2026-04-04 00:45:40','2026-04-04 00:45:40');
INSERT INTO "project_milestones" VALUES(17,'DEMO-026','Technical Design Review','gate','2025-12-06',NULL,'not_started',NULL,NULL,0.0,0,NULL,'2026-04-04 01:22:35','2026-04-04 01:22:35');
INSERT INTO "project_milestones" VALUES(18,'DEMO-026','Build Phase Kickoff','gate','2025-12-26',NULL,'not_started',NULL,NULL,0.0,1,NULL,'2026-04-04 01:22:35','2026-04-04 01:22:35');
INSERT INTO "project_milestones" VALUES(19,'DEMO-026','Integration Testing','gate','2026-01-15',NULL,'not_started',NULL,NULL,0.0,2,NULL,'2026-04-04 01:22:35','2026-04-04 01:22:35');
INSERT INTO "project_milestones" VALUES(20,'DEMO-026','Production Cutover','gate','2026-02-04',NULL,'not_started',NULL,NULL,0.0,3,NULL,'2026-04-04 01:22:35','2026-04-04 01:22:35');
INSERT INTO "project_milestones" VALUES(21,'DEMO-026','Hypercare Complete','deliverable','2026-02-23',NULL,'not_started',NULL,NULL,0.0,4,NULL,'2026-04-04 01:22:35','2026-04-04 01:22:35');
INSERT INTO "project_milestones" VALUES(22,'DEMO-026','UAT Sign-Off','gate','2026-03-15',NULL,'not_started',NULL,NULL,0.0,5,NULL,'2026-04-04 01:22:35','2026-04-04 01:22:35');
INSERT INTO "project_milestones" VALUES(23,'DEMO-026','Requirements Signed Off','go_live','2026-04-04',NULL,'not_started',NULL,NULL,0.0,6,NULL,'2026-04-04 01:22:35','2026-04-04 01:22:35');
INSERT INTO "project_milestones" VALUES(24,'DEMO-026','UAT Sign-Off','checkpoint','2026-04-24',NULL,'not_started',NULL,NULL,0.0,7,NULL,'2026-04-04 01:22:35','2026-04-04 01:22:35');
CREATE TABLE project_role_allocations (
    project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role_key    TEXT NOT NULL,
    allocation  REAL DEFAULT 0.0,
    PRIMARY KEY (project_id, role_key)
);
INSERT INTO "project_role_allocations" VALUES('DEMO-034','pm',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-034','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-034','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-034','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-034','developer',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-034','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-034','dba',0.05);
INSERT INTO "project_role_allocations" VALUES('DEMO-034','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-016','pm',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-016','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-016','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-016','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-016','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-016','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-016','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-016','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-026','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-026','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-026','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-026','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-026','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-026','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-026','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-026','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-014','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-014','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-014','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-014','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-014','developer',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-014','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-014','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-014','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-006','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-006','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-006','functional',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-006','technical',0.65);
INSERT INTO "project_role_allocations" VALUES('DEMO-006','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-006','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-006','dba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-006','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-017','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-017','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-017','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-017','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-017','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-017','infrastructure',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-017','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-017','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-028','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-028','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-028','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-028','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-028','developer',0.6);
INSERT INTO "project_role_allocations" VALUES('DEMO-028','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-028','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-028','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-019','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-019','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-019','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-019','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-019','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-019','infrastructure',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-019','dba',0.05);
INSERT INTO "project_role_allocations" VALUES('DEMO-019','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-005','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-005','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-005','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-005','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-005','developer',0.6);
INSERT INTO "project_role_allocations" VALUES('DEMO-005','infrastructure',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-005','dba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-005','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-012','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-012','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-012','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-012','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-012','developer',0.65);
INSERT INTO "project_role_allocations" VALUES('DEMO-012','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-012','dba',0.05);
INSERT INTO "project_role_allocations" VALUES('DEMO-012','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-038','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-038','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-038','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-038','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-038','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-038','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-038','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-038','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-002','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-002','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-002','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-002','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-002','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-002','infrastructure',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-002','dba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-002','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-003','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-003','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-003','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-003','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-003','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-003','infrastructure',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-003','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-003','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-020','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-020','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-020','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-020','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-020','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-020','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-020','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-020','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-018','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-018','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-018','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-018','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-018','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-018','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-018','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-018','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-021','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-021','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-021','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-021','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-021','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-021','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-021','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-021','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-022','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-022','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-022','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-022','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-022','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-022','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-022','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-022','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-023','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-023','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-023','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-023','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-023','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-023','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-023','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-023','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-035','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-035','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-035','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-035','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-035','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-035','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-035','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-035','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-010','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-010','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-010','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-010','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-010','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-010','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-010','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-010','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-011','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-011','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-011','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-011','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-011','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-011','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-011','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-011','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-009','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-009','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-009','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-009','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-009','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-009','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-009','dba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-009','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-025','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-025','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-025','functional',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-025','technical',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-025','developer',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-025','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-025','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-025','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-004','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-004','ba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-004','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-004','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-004','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-004','infrastructure',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-004','dba',0.05);
INSERT INTO "project_role_allocations" VALUES('DEMO-004','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-029','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-029','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-029','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-029','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-029','developer',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-029','infrastructure',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-029','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-029','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-024','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-024','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-024','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-024','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-024','developer',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-024','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-024','dba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-024','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-027','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-027','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-027','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-027','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-027','developer',0.6);
INSERT INTO "project_role_allocations" VALUES('DEMO-027','infrastructure',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-027','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-027','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-007','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-007','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-007','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-007','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-007','developer',0.6);
INSERT INTO "project_role_allocations" VALUES('DEMO-007','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-007','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-007','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-015','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-015','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-015','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-015','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-015','developer',0.4);
INSERT INTO "project_role_allocations" VALUES('DEMO-015','infrastructure',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-015','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-015','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-013','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-013','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-013','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-013','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-013','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-013','infrastructure',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-013','dba',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-013','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-031','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-031','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-031','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-031','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-031','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-031','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-031','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-031','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-030','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-030','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-030','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-030','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-030','developer',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-030','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-030','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-030','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-036','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-036','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-036','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-036','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-036','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-036','infrastructure',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-036','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-036','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-037','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-037','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-037','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-037','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-037','developer',0.4);
INSERT INTO "project_role_allocations" VALUES('DEMO-037','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-037','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-037','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-032','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-032','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-032','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-032','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-032','developer',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-032','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-032','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-032','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-001','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-001','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-001','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-001','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-001','developer',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-001','infrastructure',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-001','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-001','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-008','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-008','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-008','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-008','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-008','developer',0.75);
INSERT INTO "project_role_allocations" VALUES('DEMO-008','infrastructure',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-008','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-008','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-033','pm',0.1);
INSERT INTO "project_role_allocations" VALUES('DEMO-033','ba',0.15);
INSERT INTO "project_role_allocations" VALUES('DEMO-033','functional',0.2);
INSERT INTO "project_role_allocations" VALUES('DEMO-033','technical',0.25);
INSERT INTO "project_role_allocations" VALUES('DEMO-033','developer',0.6);
INSERT INTO "project_role_allocations" VALUES('DEMO-033','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-033','dba',0.05);
INSERT INTO "project_role_allocations" VALUES('DEMO-033','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-039','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-039','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-039','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-039','technical',0.3);
INSERT INTO "project_role_allocations" VALUES('DEMO-039','developer',0.4);
INSERT INTO "project_role_allocations" VALUES('DEMO-039','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-039','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-039','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-040','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-040','ba',0.3);
INSERT INTO "project_role_allocations" VALUES('DEMO-040','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-040','technical',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-040','developer',0.5);
INSERT INTO "project_role_allocations" VALUES('DEMO-040','infrastructure',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-040','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-040','wms',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-041','pm',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-041','ba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-041','functional',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-041','technical',0.4);
INSERT INTO "project_role_allocations" VALUES('DEMO-041','developer',0.3);
INSERT INTO "project_role_allocations" VALUES('DEMO-041','infrastructure',0.3);
INSERT INTO "project_role_allocations" VALUES('DEMO-041','dba',0.0);
INSERT INTO "project_role_allocations" VALUES('DEMO-041','wms',0.0);
CREATE TABLE project_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    milestone_id    INTEGER REFERENCES project_milestones(id) ON DELETE SET NULL,
    parent_task_id  INTEGER REFERENCES project_tasks(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT,
    assignee        TEXT,
    role_key        TEXT,
    start_date      TEXT,
    end_date        TEXT,
    est_hours       REAL DEFAULT 0.0,
    actual_hours    REAL DEFAULT 0.0,
    status          TEXT NOT NULL DEFAULT 'not_started',
    progress_pct    REAL DEFAULT 0.0,
    priority        TEXT DEFAULT 'Medium',
    jira_key        TEXT,
    sort_order      INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
INSERT INTO "project_tasks" VALUES(1,'DEMO-006',1,NULL,'Task 1',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'complete',100.0,'Medium',NULL,0,'2026-04-04 00:30:29','2026-04-04 00:35:32');
INSERT INTO "project_tasks" VALUES(2,'DEMO-006',2,NULL,'Task 2',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:30:29','2026-04-04 00:30:29');
INSERT INTO "project_tasks" VALUES(3,'DEMO-006',3,NULL,'Task 3',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:30:29','2026-04-04 00:30:29');
INSERT INTO "project_tasks" VALUES(4,'DEMO-006',4,NULL,'Task 4',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:30:29','2026-04-04 00:30:29');
INSERT INTO "project_tasks" VALUES(5,'DEMO-006',5,NULL,'Task 5',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:30:29','2026-04-04 00:30:29');
INSERT INTO "project_tasks" VALUES(6,'DEMO-006',6,NULL,'Task 6',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:30:29','2026-04-04 00:30:29');
INSERT INTO "project_tasks" VALUES(7,'DEMO-006',7,NULL,'Task 7',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:30:29','2026-04-04 00:30:29');
INSERT INTO "project_tasks" VALUES(8,'DEMO-006',8,NULL,'Task 8',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:30:29','2026-04-04 00:30:29');
INSERT INTO "project_tasks" VALUES(9,'DEMO-016',9,NULL,'Task 9',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:45:47','2026-04-04 00:45:47');
INSERT INTO "project_tasks" VALUES(10,'DEMO-016',10,NULL,'Task 10',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:45:47','2026-04-04 00:45:47');
INSERT INTO "project_tasks" VALUES(11,'DEMO-016',11,NULL,'Task 11',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:45:47','2026-04-04 00:45:47');
INSERT INTO "project_tasks" VALUES(12,'DEMO-016',12,NULL,'Task 12',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:45:47','2026-04-04 00:45:47');
INSERT INTO "project_tasks" VALUES(13,'DEMO-016',13,NULL,'Task 13',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:45:47','2026-04-04 00:45:47');
INSERT INTO "project_tasks" VALUES(14,'DEMO-016',14,NULL,'Task 14',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:45:47','2026-04-04 00:45:47');
INSERT INTO "project_tasks" VALUES(15,'DEMO-016',15,NULL,'Task 15',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:45:47','2026-04-04 00:45:47');
INSERT INTO "project_tasks" VALUES(16,'DEMO-016',16,NULL,'Task 16',NULL,NULL,NULL,NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,0,'2026-04-04 00:45:47','2026-04-04 00:45:47');
INSERT INTO "project_tasks" VALUES(17,'DEMO-016',9,NULL,'Task 17',NULL,'Atlas Jensen','pm',NULL,NULL,0.0,0.0,'not_started',0.0,'Medium',NULL,8,'2026-04-04 00:46:39','2026-04-04 00:46:39');
CREATE TABLE projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    type            TEXT,
    portfolio       TEXT,
    sponsor         TEXT,
    health          TEXT,
    pct_complete    REAL DEFAULT 0.0,
    priority        TEXT,
    start_date      TEXT,
    end_date        TEXT,
    actual_end      TEXT,
    team            TEXT,
    pm              TEXT,
    ba              TEXT,
    functional_lead TEXT,
    technical_lead  TEXT,
    developer_lead  TEXT,
    tshirt_size     TEXT,
    est_hours       REAL DEFAULT 0.0,
    notes           TEXT,
    sort_order      INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
, budget REAL DEFAULT 0.0, actual_cost REAL DEFAULT 0.0, forecast_cost REAL DEFAULT 0.0, initiative_id TEXT REFERENCES initiatives(id), planned_it_start TEXT);
INSERT INTO "projects" VALUES('DEMO-034','Billing Cycle Automation','Key Initiative','Corporate Services','Beatrice Lin','🔵 NEEDS TECHNICAL SPEC',0.4,'High','2025-10-14','2026-06-01',NULL,'Systems Applications','Cleo Kim','Theo Ivanov',NULL,NULL,'Caleb Okonkwo','XXL: > 640 Hours',1480.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 15:19:42',0.0,72967.09,154268.34,'INIT-04',NULL);
INSERT INTO "projects" VALUES('DEMO-016','Fleet Tracking Integration','Key Initiative','Finance Systems','Camille Okafor','🟢 ON TRACK',0.1,'High','2026-02-15','2026-06-30',NULL,'Synnergie','Cleo Kim','Felix Krause','Atlas Wright','Sophia Costa','Caleb Okonkwo','L: 160-320 Hours',240.0,NULL,1,'2026-04-02 03:35:22','2026-04-05T12:39:58.509667',0.0,2424.96,22257.23,'INIT-09',NULL);
INSERT INTO "projects" VALUES('DEMO-026','Shipping Label Automation','Key Initiative','Platform Engineering','Rafael Bauer','🟢 ON TRACK',0.5,'High','2025-11-17','2026-04-24',NULL,'Systems Applications','Cleo Kim','Theo Ivanov',NULL,NULL,'Sophia Campbell','XXL: > 640 Hours',640.0,NULL,1,'2026-04-02 03:35:22','2026-04-05T12:41:03.745553',0.0,35235.97,79981.82,'INIT-01',NULL);
INSERT INTO "projects" VALUES('DEMO-014','Capacity Planning Dashboard','Key Initiative','Platform Engineering','Rafael Bauer','🟢 ON TRACK',0.0,'High','2026-02-02','2026-06-30',NULL,'Infrastructure','Cleo Kim','Theo Ivanov','Max Svensson','Atlas Garcia','Caleb Okonkwo',NULL,320.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,0.0,39088.73,'INIT-05',NULL);
INSERT INTO "projects" VALUES('DEMO-006','Analytics Self-Service Platform','Enhancement','Finance Systems','Nolan Pierce','🔵 NEEDS TECHNICAL SPEC',0.1,'High','2026-02-23','2026-04-17',NULL,'Synnergie','Cleo Kim','Theo Ivanov','Atlas Wright','Zara Fontaine','Caleb Okonkwo','M: 80-160 Hours',120.0,NULL,1,'2026-04-02 03:35:22','2026-04-05 15:07:38',0.0,0.0,0.0,'INIT-05',NULL);
INSERT INTO "projects" VALUES('DEMO-017','Cost Center Realignment','Enhancement','Corporate Services','Beatrice Lin','🔵 NEEDS TECHNICAL SPEC',0.0,'Medium','2026-04-01','2026-09-16',NULL,'Systems Applications','Cleo Kim','Theo Ivanov','Atlas Wright','Atlas Garcia','Caleb Okonkwo','L: 160-320 Hours',240.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 19:53:49',0.0,0.0,26539.8,'INIT-07',NULL);
INSERT INTO "projects" VALUES('DEMO-028','Product Catalog Unification','Enhancement','Finance Systems','Nolan Pierce','⚪ NOT STARTED',0.0,'Medium','2026-04-01','2026-05-20',NULL,'Synnergie','Cleo Kim','Theo Ivanov','Atlas Wright','Zara Fontaine','Caleb Okonkwo','XXL: > 640 Hours',640.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,62533.74,'INIT-02',NULL);
INSERT INTO "projects" VALUES('DEMO-019','Legacy Payments Modernization','Enhancement','Operations','Camille Okafor','⚪ NOT STARTED',0.0,'Medium','2026-04-01','2026-04-29',NULL,'Systems Applications','Cleo Kim','Theo Ivanov','Atlas Wright','Zara Fontaine','Caleb Okonkwo','S: < 80 Hours',40.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 19:53:49',0.0,0.0,0.0,'INIT-07',NULL);
INSERT INTO "projects" VALUES('DEMO-005','Financial Close Acceleration','Enhancement','Finance Systems','Nolan Pierce','⚪ NOT STARTED',0.0,'Medium','2026-04-01','2026-06-24',NULL,'Synnergie','Cleo Kim','Theo Ivanov','Max Svensson','Sage Hughes','Caleb Okonkwo','M: 80-160 Hours',120.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,0.0,0.0,'INIT-04',NULL);
INSERT INTO "projects" VALUES('DEMO-012','Loyalty Program Launch','Enhancement','Corporate Services','Beatrice Lin','🔵 NEEDS TECHNICAL SPEC',0.0,'Highest','2026-04-01','2026-06-17',NULL,'Systems Applications','Cleo Kim','Theo Ivanov','Atlas Wright','Atlas Garcia','Caleb Okonkwo','S: < 80 Hours',40.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 19:53:49',0.0,0.0,0.0,'INIT-17',NULL);
INSERT INTO "projects" VALUES('DEMO-038','Procurement Approval Overhaul','Enhancement','Corporate Services','Beatrice Lin','⚪ NOT STARTED',0.0,'Highest','2026-04-01','2026-06-17',NULL,'Systems Applications','Cleo Kim','Theo Ivanov','Atlas Wright','Zara Fontaine','Caleb Okonkwo',NULL,200.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,20241.72,'INIT-26',NULL);
INSERT INTO "projects" VALUES('DEMO-002','Budget Variance Reporting','Enhancement','Corporate Services','Beatrice Lin','🔵 NEEDS FUNCTIONAL SPEC',0.0,'Medium','2026-04-01','2026-05-27',NULL,'Systems Applications','Cleo Kim','Theo Ivanov','Max Svensson','Sage Hughes','Caleb Okonkwo',NULL,200.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 19:53:49',0.0,0.0,22405.98,'INIT-04',NULL);
INSERT INTO "projects" VALUES('DEMO-003','Order Routing Optimization','Enhancement','Finance Systems','Nolan Pierce','🟢 ON TRACK',0.0,'Highest','2026-04-01','2026-05-20',NULL,'Synnergie','Cleo Kim','Theo Ivanov','Atlas Wright','Atlas Garcia','Caleb Okonkwo',NULL,200.0,NULL,1,'2026-04-02 03:35:22','2026-04-05 15:07:38',0.0,0.0,24941.06,'INIT-01',NULL);
INSERT INTO "projects" VALUES('DEMO-020','Employee Directory Migration','Enhancement','Finance Systems','Nolan Pierce','⏸️ POSTPONED',0.0,NULL,'2026-04-01','2026-09-23',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0,'INIT-03',NULL);
INSERT INTO "projects" VALUES('DEMO-018','Mobile Dispatch App','Enhancement','Finance Systems','Nolan Pierce','⏸️ POSTPONED',0.0,NULL,'2026-04-01','2026-08-26',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0,'INIT-09',NULL);
INSERT INTO "projects" VALUES('DEMO-021','Invoice OCR Integration','Enhancement','Finance Systems','Nolan Pierce','⏸️ POSTPONED',0.0,NULL,'2026-04-01','2026-05-13',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0,'INIT-19',NULL);
INSERT INTO "projects" VALUES('DEMO-022','Identity Access Management','Enhancement','Finance Systems','Nolan Pierce','⏸️ POSTPONED',0.0,NULL,'2026-04-01','2026-09-02',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0,'INIT-06',NULL);
INSERT INTO "projects" VALUES('DEMO-023','Inventory Sync Platform','Bug','Finance Systems','Nolan Pierce','⏸️ POSTPONED',0.0,NULL,'2026-04-01','2026-07-29',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0,'INIT-18',NULL);
INSERT INTO "projects" VALUES('DEMO-035','Vendor Portal MVP','Enhancement','Finance Systems','Camille Okafor','⏸️ POSTPONED',0.0,NULL,'2026-04-01','2026-05-06',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0,'INIT-10',NULL);
INSERT INTO "projects" VALUES('DEMO-010','Reorder Point Calculator','Enhancement','Corporate Services','Beatrice Lin','⏸️ POSTPONED',0.0,NULL,'2026-04-01','2026-04-29',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0,'INIT-18',NULL);
INSERT INTO "projects" VALUES('DEMO-011','Supplier Onboarding Workflow','Enhancement','Corporate Services','Beatrice Lin','⏸️ POSTPONED',0.0,NULL,'2026-04-01','2026-05-13',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0,'INIT-08',NULL);
INSERT INTO "projects" VALUES('DEMO-009','Data Lake Foundation','Enhancement','Corporate Services','Beatrice Lin','🔴 NEEDS HELP',0.0,'High','2026-04-01','2026-06-10',NULL,'Systems Applications','Sage Ivanov','Felix Krause','Max Svensson','Atlas Garcia',NULL,'M: 80-160 Hours',120.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 16:04:25',0.0,0.0,0.0,'INIT-05',NULL);
INSERT INTO "projects" VALUES('DEMO-025','Contract Lifecycle Tool','Enhancement','Finance Systems','Nolan Pierce','✅ COMPLETE',1.0,'Highest','2026-02-04','2026-02-27',NULL,'Synnergie','Cleo Kim','Theo Ivanov','Max Svensson','Sophia Costa',NULL,'M: 80-160 Hours',120.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,15072.23,13425.2,'INIT-10',NULL);
INSERT INTO "projects" VALUES('DEMO-004','Shop Floor Digitization','Enhancement','Operations','Camille Okafor','✅ COMPLETE',1.0,'Highest','2026-03-02','2026-03-20',NULL,'Synnergie','Oliver Reyes','Theo Ivanov','Atlas Wright','Atlas Garcia',NULL,'M: 80-160 Hours',120.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,12525.67,12341.64,'INIT-15',NULL);
INSERT INTO "projects" VALUES('DEMO-029','Returns Portal Upgrade','Key Initiative','Platform Engineering','Rafael Bauer','✅ COMPLETE',1.0,'Highest','2025-12-01','2026-03-21',NULL,'Infrastructure','Cleo Kim','Atlas Chen','Atlas Wright','Cleo Brennan',NULL,NULL,120.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,11629.05,10410.57,'INIT-02',NULL);
INSERT INTO "projects" VALUES('DEMO-024','CRM Contact Deduplication','Enhancement','Corporate Services','Beatrice Lin','✅ COMPLETE',1.0,'High','2025-10-27','2026-01-09','2026-02-15','Systems Applications','Sage Ivanov','Felix Krause','Max Svensson','Maya Romano',NULL,'S: < 80 Hours',60.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,8533.8,12815.52,'INIT-08',NULL);
INSERT INTO "projects" VALUES('DEMO-027','Inventory Turn Analytics','Key Initiative','Operations','Camille Okafor','✅ COMPLETE',1.0,'High','2025-11-12','2026-01-23','2026-01-23','Synnergie','Cleo Kim','Theo Ivanov','Atlas Wright','Sage Hughes',NULL,'L: 160-320 Hours',360.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,33924.25,34279.31,'INIT-18',NULL);
INSERT INTO "projects" VALUES('DEMO-007','Expense Report Redesign','Enhancement','Finance Systems','Nolan Pierce','✅ COMPLETE',1.0,'High','2024-12-22','2026-02-06','2026-02-28','Synnergie','Sage Ivanov','Theo Ivanov','Max Svensson','Zara Fontaine',NULL,'L: 160-320 Hours',310.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,30982.37,43057.99,'INIT-04',NULL);
INSERT INTO "projects" VALUES('DEMO-015','Customer Portal Rebuild','Enhancement','Finance Systems','Camille Okafor','✅ COMPLETE',1.0,'High','2025-10-20','2026-02-20','2026-02-20','Synnergie','Sage Ivanov','Iris Ivanov','Max Svensson','Sophia Costa',NULL,'M: 80-160 Hours',160.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,13889.01,18543.91,'INIT-02',NULL);
INSERT INTO "projects" VALUES('DEMO-013','Compliance Documentation System','Key Initiative','Operations','Camille Okafor','✅ COMPLETE',1.0,'High','2026-01-12','2026-02-05','2026-02-28','Synnergie','Oliver Reyes','Iris Ivanov','Max Svensson','Aria Santos',NULL,'M: 80-160 Hours',120.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,7436.44,10216.47,'INIT-14',NULL);
INSERT INTO "projects" VALUES('DEMO-031','Price List Automation','Key Initiative','Platform Engineering','Rafael Bauer','✅ COMPLETE',1.0,'High','2025-12-12','2025-12-31','2026-02-27','Infrastructure',NULL,NULL,NULL,'Cleo Bauer',NULL,NULL,0.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,7965.32,6861.75,'INIT-11',NULL);
INSERT INTO "projects" VALUES('DEMO-030','Help Desk Ticket Triage','Key Initiative','Platform Engineering','Rafael Bauer','✅ COMPLETE',1.0,'High','2025-12-22','2026-02-06','2026-02-15','Infrastructure',NULL,NULL,NULL,'Cleo Brennan',NULL,NULL,0.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,9596.81,8732.95,'INIT-12',NULL);
INSERT INTO "projects" VALUES('DEMO-036','Warehouse Returns Automation','Enhancement','Operations','Camille Okafor','✅ COMPLETE',1.0,'High','2026-04-01','2026-06-17',NULL,'Systems Applications','Cleo Kim','Iris Ivanov','Atlas Wright','Aria Santos',NULL,'S: < 80 Hours',40.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,11503.27,12338.92,'INIT-26',NULL);
INSERT INTO "projects" VALUES('DEMO-037','Distribution Network Optimization','Key Initiative','Finance Systems','Nolan Pierce','✅ COMPLETE',1.0,'High','2025-10-27','2025-12-29','2026-01-09','Synnergie','Sage Ivanov','Theo Ivanov','Max Svensson','Sophia Costa',NULL,NULL,320.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,28461.17,27276.19,'INIT-01',NULL);
INSERT INTO "projects" VALUES('DEMO-032','Single Sign-On Rollout','Enhancement','Corporate Services','Beatrice Lin','✅ COMPLETE',1.0,'Highest','2026-04-01','2026-08-19',NULL,'Systems Applications','Sage Ivanov','Iris Ivanov','Max Svensson','Atlas Garcia',NULL,'S: < 80 Hours',40.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,6504.88,6526.16,'INIT-06',NULL);
INSERT INTO "projects" VALUES('DEMO-001','Quality Audit Module','Enhancement','Operations','Grace Chandler','✅ COMPLETE',1.0,'Highest','2026-04-01','2026-09-09',NULL,'Synnergie','Cleo Kim','Theo Ivanov','Max Svensson','Zara Fontaine','Caleb Okonkwo','S: < 80 Hours',80.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 15:19:42',0.0,7801.19,6484.66,'INIT-14',NULL);
INSERT INTO "projects" VALUES('DEMO-008','Cross-Dock Scheduling Tool','Enhancement','Finance Systems','Nolan Pierce','✅ COMPLETE',1.0,'High','2026-04-01','2026-04-29',NULL,'Synnergie','Oliver Reyes','Theo Ivanov','Max Svensson','Aria Santos',NULL,'L: 160-320 Hours',320.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,39252.83,39114.75,'INIT-01',NULL);
INSERT INTO "projects" VALUES('DEMO-033','Demand Planning Enhancements','Enhancement','Platform Engineering','Rafael Bauer','✅ COMPLETE',1.0,'High','2026-03-03','2026-03-13',NULL,'Systems Applications','Cleo Kim','Theo Ivanov','Max Svensson','Caleb Okonkwo','Caleb Okonkwo','S: < 80 Hours',40.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,0.0,0.0,'INIT-05',NULL);
INSERT INTO "projects" VALUES('DEMO-039','Warehouse Robotics Integration','Key Initiative','Operations','Camille Okafor','📋 PIPELINE',0.0,'Medium',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,200.0,NULL,1,'2026-04-06 16:40:29','2026-04-06 16:40:29',0.0,0.0,0.0,'INIT-01','2026-Q3');
INSERT INTO "projects" VALUES('DEMO-040','AI-Powered Demand Forecasting','Key Initiative','Finance Systems','Nolan Pierce','📋 PIPELINE',0.0,'High',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,400.0,NULL,1,'2026-04-06 16:40:29','2026-04-06 16:40:29',0.0,0.0,0.0,'INIT-05','2026-Q4');
INSERT INTO "projects" VALUES('DEMO-041','Zero Trust Network Architecture','Key Initiative','Platform Engineering','Rafael Bauer','📋 PIPELINE',0.0,'Highest',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,600.0,NULL,1,'2026-04-06 16:40:29','2026-04-06 16:40:29',0.0,0.0,0.0,'INIT-06','2026-Q3');
CREATE TABLE rm_assumptions (
    key     TEXT PRIMARY KEY,
    value   REAL NOT NULL
);
INSERT INTO "rm_assumptions" VALUES('base_hours_per_week',40.0);
INSERT INTO "rm_assumptions" VALUES('admin_pct',0.1);
INSERT INTO "rm_assumptions" VALUES('breakfix_pct',0.1);
INSERT INTO "rm_assumptions" VALUES('project_pct',0.8);
INSERT INTO "rm_assumptions" VALUES('available_project_hrs',32.0);
INSERT INTO "rm_assumptions" VALUES('max_projects_per_person',3.0);
INSERT INTO "rm_assumptions" VALUES('annual_budget',1000000.0);
CREATE TABLE role_phase_efforts (
    role_key    TEXT NOT NULL,
    phase       TEXT NOT NULL,
    effort      REAL NOT NULL,
    PRIMARY KEY (role_key, phase)
);
INSERT INTO "role_phase_efforts" VALUES('pm','discovery',0.1);
INSERT INTO "role_phase_efforts" VALUES('pm','planning',0.25);
INSERT INTO "role_phase_efforts" VALUES('pm','design',0.15);
INSERT INTO "role_phase_efforts" VALUES('pm','build',0.2);
INSERT INTO "role_phase_efforts" VALUES('pm','test',0.2);
INSERT INTO "role_phase_efforts" VALUES('pm','deploy',0.1);
INSERT INTO "role_phase_efforts" VALUES('dba','discovery',0.05);
INSERT INTO "role_phase_efforts" VALUES('dba','planning',0.1);
INSERT INTO "role_phase_efforts" VALUES('dba','design',0.3);
INSERT INTO "role_phase_efforts" VALUES('dba','build',0.25);
INSERT INTO "role_phase_efforts" VALUES('dba','test',0.2);
INSERT INTO "role_phase_efforts" VALUES('dba','deploy',0.1);
INSERT INTO "role_phase_efforts" VALUES('ba','discovery',0.3);
INSERT INTO "role_phase_efforts" VALUES('ba','planning',0.2);
INSERT INTO "role_phase_efforts" VALUES('ba','design',0.2);
INSERT INTO "role_phase_efforts" VALUES('ba','build',0.1);
INSERT INTO "role_phase_efforts" VALUES('ba','test',0.15);
INSERT INTO "role_phase_efforts" VALUES('ba','deploy',0.05);
INSERT INTO "role_phase_efforts" VALUES('functional','discovery',0.2);
INSERT INTO "role_phase_efforts" VALUES('functional','planning',0.1);
INSERT INTO "role_phase_efforts" VALUES('functional','design',0.3);
INSERT INTO "role_phase_efforts" VALUES('functional','build',0.15);
INSERT INTO "role_phase_efforts" VALUES('functional','test',0.15);
INSERT INTO "role_phase_efforts" VALUES('functional','deploy',0.1);
INSERT INTO "role_phase_efforts" VALUES('technical','discovery',0.05);
INSERT INTO "role_phase_efforts" VALUES('technical','planning',0.1);
INSERT INTO "role_phase_efforts" VALUES('technical','design',0.2);
INSERT INTO "role_phase_efforts" VALUES('technical','build',0.4);
INSERT INTO "role_phase_efforts" VALUES('technical','test',0.15);
INSERT INTO "role_phase_efforts" VALUES('technical','deploy',0.1);
INSERT INTO "role_phase_efforts" VALUES('developer','discovery',0.0);
INSERT INTO "role_phase_efforts" VALUES('developer','planning',0.05);
INSERT INTO "role_phase_efforts" VALUES('developer','design',0.1);
INSERT INTO "role_phase_efforts" VALUES('developer','build',0.5);
INSERT INTO "role_phase_efforts" VALUES('developer','test',0.25);
INSERT INTO "role_phase_efforts" VALUES('developer','deploy',0.1);
INSERT INTO "role_phase_efforts" VALUES('infrastructure','discovery',0.05);
INSERT INTO "role_phase_efforts" VALUES('infrastructure','planning',0.1);
INSERT INTO "role_phase_efforts" VALUES('infrastructure','design',0.15);
INSERT INTO "role_phase_efforts" VALUES('infrastructure','build',0.2);
INSERT INTO "role_phase_efforts" VALUES('infrastructure','test',0.15);
INSERT INTO "role_phase_efforts" VALUES('infrastructure','deploy',0.35);
INSERT INTO "role_phase_efforts" VALUES('wms','discovery',0.1);
INSERT INTO "role_phase_efforts" VALUES('wms','planning',0.15);
INSERT INTO "role_phase_efforts" VALUES('wms','design',0.1);
INSERT INTO "role_phase_efforts" VALUES('wms','build',0.1);
INSERT INTO "role_phase_efforts" VALUES('wms','test',0.05);
INSERT INTO "role_phase_efforts" VALUES('wms','deploy',0.5);
CREATE TABLE schema_info (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);
INSERT INTO "schema_info" VALUES('version','1');
CREATE TABLE sdlc_phase_weights (
    phase   TEXT PRIMARY KEY,
    weight  REAL NOT NULL
);
INSERT INTO "sdlc_phase_weights" VALUES('discovery',0.1);
INSERT INTO "sdlc_phase_weights" VALUES('planning',0.1);
INSERT INTO "sdlc_phase_weights" VALUES('design',0.15);
INSERT INTO "sdlc_phase_weights" VALUES('build',0.3);
INSERT INTO "sdlc_phase_weights" VALUES('test',0.2);
INSERT INTO "sdlc_phase_weights" VALUES('deploy',0.15);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('project_assignments',131);
INSERT INTO "sqlite_sequence" VALUES('vendor_consultants',10);
INSERT INTO "sqlite_sequence" VALUES('vendor_timesheets',275);
INSERT INTO "sqlite_sequence" VALUES('approved_work',31);
INSERT INTO "sqlite_sequence" VALUES('vendor_invoices',2);
INSERT INTO "sqlite_sequence" VALUES('project_mapping',25);
INSERT INTO "sqlite_sequence" VALUES('project_comments',3);
INSERT INTO "sqlite_sequence" VALUES('project_audit_log',31);
INSERT INTO "sqlite_sequence" VALUES('project_milestones',26);
INSERT INTO "sqlite_sequence" VALUES('project_tasks',17);
CREATE TABLE task_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    depends_on_id   INTEGER NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL DEFAULT 'finish_to_start'
);
CREATE TABLE team_members (
    name                 TEXT PRIMARY KEY,
    role                 TEXT NOT NULL,
    role_key             TEXT NOT NULL,
    team                 TEXT,
    vendor               TEXT,
    classification       TEXT,
    rate_per_hour        REAL DEFAULT 0.0,
    weekly_hrs_available REAL DEFAULT 0.0,
    support_reserve_pct  REAL DEFAULT 0.0
, include_in_capacity INTEGER DEFAULT 1);
INSERT INTO "team_members" VALUES('Caleb Bauer','Functional','functional','Business Analysis','Blue Harbor Group','MSA',144.0,35.0,0.4,1);
INSERT INTO "team_members" VALUES('James Fontaine','Technical','technical','Business Analysis','Blue Harbor Group','MSA',119.0,35.0,0.4,1);
INSERT INTO "team_members" VALUES('Sophia Nakamura','Technical','technical','Business Analysis','Blue Harbor Group','T&M',94.0,35.0,0.4,1);
INSERT INTO "team_members" VALUES('Arlo Haruki','Functional','functional','Business Analysis','Blue Harbor Group','T&M',130.0,35.0,0.4,1);
INSERT INTO "team_members" VALUES('Liam Garcia','Technical','technical','Business Analysis','Blue Harbor Group','T&M',149.0,35.0,0.0,1);
INSERT INTO "team_members" VALUES('June Kim','Technical','technical','Business Analysis','Blue Harbor Group','T&M',95.0,35.0,0.0,1);
INSERT INTO "team_members" VALUES('Jonas Dupont','Technical','technical','Business Analysis','Blue Harbor Group','MSA',83.0,35.0,0.6,1);
INSERT INTO "team_members" VALUES('Elena Bell','DBA','dba','Business Analysis','Blue Harbor Group','MSA',96.0,35.0,0.8,1);
INSERT INTO "team_members" VALUES('Ivy Krause','Business Analyst','ba','Delivery','Northwind Consulting',NULL,181.0,40.0,0.6,1);
INSERT INTO "team_members" VALUES('Jonas Fontaine','Developer','developer','Delivery','Northwind Consulting',NULL,145.0,25.0,0.0,1);
INSERT INTO "team_members" VALUES('Marcus Garcia','Developer','developer','Delivery','Northwind Consulting',NULL,161.0,25.0,0.4,1);
INSERT INTO "team_members" VALUES('Jasper Okonkwo','Developer','developer','Delivery','Northwind Consulting',NULL,92.0,25.0,0.1,1);
INSERT INTO "team_members" VALUES('Chloe Costa','Developer','developer','Delivery','Northwind Consulting',NULL,99.0,25.0,0.25,1);
INSERT INTO "team_members" VALUES('Silas Ivanov','Business Analyst','ba','Delivery','Northwind Consulting',NULL,141.0,35.0,0.5,1);
INSERT INTO "team_members" VALUES('Rosa Flores','Business Analyst','ba','Delivery','Northwind Consulting',NULL,84.0,35.0,0.2,1);
INSERT INTO "team_members" VALUES('Owen Reyes','Business Analyst','ba','Delivery','Northwind Consulting',NULL,100.0,35.0,0.5,1);
INSERT INTO "team_members" VALUES('Liam Nguyen','Project Manager','pm','Fulfillment Tech','Northwind Consulting',NULL,95.0,35.0,0.5,1);
INSERT INTO "team_members" VALUES('Priya Romano','Project Manager','pm',NULL,NULL,NULL,0.0,45.0,0.15,1);
INSERT INTO "team_members" VALUES('Lucas Garcia','Project Manager','pm','Fulfillment Tech','Northwind Consulting','T&M',77.0,32.0,0.68,1);
INSERT INTO "team_members" VALUES('Ethan Bell','WMS Consultant','wms','Fulfillment Tech','Northwind Consulting','T&M',181.0,35.0,0.6,1);
INSERT INTO "team_members" VALUES('Sophia Rivera','Infrastructure','infrastructure','Fulfillment Tech','Northwind Consulting',NULL,133.0,40.0,0.6,1);
INSERT INTO "team_members" VALUES('Max Dupont','Infrastructure','infrastructure','Fulfillment Tech','Northwind Consulting',NULL,158.0,40.0,0.6,1);
INSERT INTO "team_members" VALUES('Aria Nguyen','Infrastructure','infrastructure','Fulfillment Tech','Northwind Consulting',NULL,86.0,40.0,0.6,1);
INSERT INTO "team_members" VALUES('Stella Svensson','Technical','technical','Business Analysis','Blue Harbor Group','T&M',177.0,35.0,0.0,1);
CREATE TABLE vendor_approvals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    consultant_id       INTEGER NOT NULL REFERENCES vendor_consultants(id),
    month               TEXT NOT NULL,             -- 'YYYY-MM'
    total_hours         REAL NOT NULL DEFAULT 0.0,
    status              TEXT NOT NULL DEFAULT 'draft', -- draft, submitted, approved
    vendor_approved     INTEGER NOT NULL DEFAULT 0,
    vendor_approved_by  TEXT,
    vendor_approved_at  TEXT,
    ete_approved        INTEGER NOT NULL DEFAULT 0,
    ete_approved_by     TEXT,
    ete_approved_at     TEXT,
    UNIQUE(consultant_id, month)
);
CREATE TABLE vendor_consultants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,
    billing_type    TEXT NOT NULL DEFAULT 'MSA',   -- 'MSA' or 'T&M'
    hourly_rate     REAL NOT NULL DEFAULT 0.0,     -- 0 for MSA-covered
    role_key        TEXT,
    active          INTEGER NOT NULL DEFAULT 1
);
INSERT INTO "vendor_consultants" VALUES(1,'Atlas Wright','MSA',93.0,'functional',1);
INSERT INTO "vendor_consultants" VALUES(2,'Zara Fontaine','T&M',141.0,'technical',1);
INSERT INTO "vendor_consultants" VALUES(3,'Max Svensson','T&M',127.0,'functional',1);
INSERT INTO "vendor_consultants" VALUES(4,'Sage Hughes','MSA',163.0,'technical',1);
INSERT INTO "vendor_consultants" VALUES(5,'Sophia Costa','T&M',163.0,'technical',1);
INSERT INTO "vendor_consultants" VALUES(6,'Atlas Garcia','MSA',149.0,'technical',1);
INSERT INTO "vendor_consultants" VALUES(7,'Elena Flores','MSA',106.0,'dba',1);
INSERT INTO "vendor_consultants" VALUES(8,'Aria Santos','T&M',103.0,'technical',1);
INSERT INTO "vendor_consultants" VALUES(9,'Jonas Nguyen','T&M',155.0,'technical',1);
CREATE TABLE vendor_invoices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    month           TEXT NOT NULL,                 -- 'YYYY-MM'
    msa_amount      REAL NOT NULL DEFAULT 0.0,
    tm_amount       REAL NOT NULL DEFAULT 0.0,
    total_amount    REAL NOT NULL DEFAULT 0.0,
    invoice_number  TEXT,
    received_date   TEXT,
    paid            INTEGER NOT NULL DEFAULT 0,
    notes           TEXT
);
INSERT INTO "vendor_invoices" VALUES(1,'2026-03',50932.14,55233.86,106166.0,'INV-0001','2026-04-02',0,NULL);
CREATE TABLE vendor_timesheets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    consultant_id   INTEGER NOT NULL REFERENCES vendor_consultants(id),
    entry_date      TEXT NOT NULL,                 -- ISO date
    project_key     TEXT,                          -- Jira key (SSE-xxx) or NULL for general support
    project_name    TEXT,
    task_description TEXT,
    work_type       TEXT NOT NULL DEFAULT 'Support', -- 'Project' or 'Support'
    hours           REAL NOT NULL DEFAULT 0.0,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
INSERT INTO "vendor_timesheets" VALUES(1,1,'2026-03-02',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(2,1,'2026-03-02',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(3,1,'2026-03-02',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(4,1,'2026-03-03',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(5,1,'2026-03-03',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(6,1,'2026-03-04',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(7,1,'2026-03-04',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(8,1,'2026-03-05',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(9,1,'2026-03-05',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(10,1,'2026-03-05',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(11,1,'2026-03-06',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(12,1,'2026-03-06',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(13,1,'2026-03-06',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(14,1,'2026-03-09',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(15,1,'2026-03-09',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(16,1,'2026-03-09',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(17,1,'2026-03-09',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(18,1,'2026-03-10',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(19,1,'2026-03-10',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(20,1,'2026-03-10',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(21,1,'2026-03-11',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(22,1,'2026-03-11',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(23,1,'2026-03-12',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(24,1,'2026-03-12',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(25,1,'2026-03-13',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(26,1,'2026-03-16',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(27,1,'2026-03-16',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(28,1,'2026-03-17',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(29,1,'2026-03-17',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(30,1,'2026-03-17',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(31,1,'2026-03-18',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(32,1,'2026-03-18',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(33,1,'2026-03-18',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(34,1,'2026-03-19',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(35,1,'2026-03-19',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(36,1,'2026-03-19',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(37,1,'2026-03-20',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(38,1,'2026-03-20',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(39,1,'2026-03-23',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(40,1,'2026-03-24',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(41,1,'2026-03-24',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(42,1,'2026-03-24',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(43,1,'2026-03-25',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(44,1,'2026-03-25',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(45,1,'2026-03-26',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(46,1,'2026-03-26',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(47,1,'2026-03-26',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(48,1,'2026-03-26',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(49,1,'2026-03-27',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(50,1,'2026-03-27',NULL,NULL,NULL,'Project',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(51,1,'2026-03-30',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(52,1,'2026-03-30',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(53,1,'2026-03-30',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(54,1,'2026-03-31',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(55,1,'2026-03-31',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(56,1,'2026-03-31',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(57,2,'2026-03-02',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(58,2,'2026-03-03',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(59,2,'2026-03-04',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(60,2,'2026-03-05',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(61,2,'2026-03-06',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(62,2,'2026-03-09',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(63,2,'2026-03-10',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(64,2,'2026-03-11',NULL,NULL,NULL,'Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(65,2,'2026-03-11',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(66,2,'2026-03-12',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(67,2,'2026-03-13',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(68,2,'2026-03-16',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(69,2,'2026-03-17',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(70,2,'2026-03-18',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(71,2,'2026-03-19',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(72,2,'2026-03-19',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(73,2,'2026-03-20',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(74,2,'2026-03-23',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(75,2,'2026-03-24',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(76,2,'2026-03-25',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(77,2,'2026-03-26',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(78,2,'2026-03-26',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(79,2,'2026-03-27',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(80,2,'2026-03-30',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(81,2,'2026-03-31',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(82,3,'2026-03-02',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(83,3,'2026-03-03',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(84,3,'2026-03-04',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(85,3,'2026-03-05',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(86,3,'2026-03-05',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(87,3,'2026-03-06',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(88,3,'2026-03-06',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(89,3,'2026-03-09',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(90,3,'2026-03-09',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(91,3,'2026-03-10',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(92,3,'2026-03-11',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(93,3,'2026-03-12',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(94,3,'2026-03-12',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(95,3,'2026-03-13',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(96,3,'2026-03-16',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(97,3,'2026-03-17',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(98,3,'2026-03-18',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(99,3,'2026-03-19',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(100,3,'2026-03-20',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(101,3,'2026-03-23',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(102,3,'2026-03-24',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(103,3,'2026-03-25',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(104,3,'2026-03-25',NULL,NULL,NULL,'Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(105,3,'2026-03-26',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(106,3,'2026-03-26',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(107,3,'2026-03-27',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(108,3,'2026-03-30',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(109,3,'2026-03-31',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(110,3,'2026-03-31',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(111,4,'2026-03-02',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(112,4,'2026-03-02',NULL,NULL,NULL,'Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(113,4,'2026-03-03',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(114,4,'2026-03-04',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(115,4,'2026-03-05',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(116,4,'2026-03-05',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(117,4,'2026-03-06',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(118,4,'2026-03-09',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(119,4,'2026-03-10',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(120,4,'2026-03-11',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(121,4,'2026-03-12',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(122,4,'2026-03-13',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(123,4,'2026-03-16',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(124,4,'2026-03-16',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(125,4,'2026-03-17',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(126,4,'2026-03-17',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(127,4,'2026-03-18',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(128,4,'2026-03-18',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(129,4,'2026-03-19',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(130,4,'2026-03-20',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(131,4,'2026-03-23',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(132,4,'2026-03-24',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(133,4,'2026-03-24',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(134,4,'2026-03-25',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(135,4,'2026-03-26',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(136,4,'2026-03-26',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(137,4,'2026-03-27',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(138,4,'2026-03-27',NULL,NULL,NULL,'Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(139,4,'2026-03-30',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(140,4,'2026-03-31',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(141,4,'2026-03-31',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(142,5,'2026-03-02',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(143,5,'2026-03-02',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(144,5,'2026-03-03',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(145,5,'2026-03-04',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(146,5,'2026-03-05',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(147,5,'2026-03-06',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(148,5,'2026-03-09',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(149,5,'2026-03-09',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(150,5,'2026-03-10',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(151,5,'2026-03-11',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(152,5,'2026-03-12',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(153,5,'2026-03-13',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(154,5,'2026-03-16',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(155,5,'2026-03-16',NULL,NULL,NULL,'Project',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(156,5,'2026-03-17',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(157,5,'2026-03-17',NULL,NULL,NULL,'Project',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(158,5,'2026-03-17',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(159,5,'2026-03-18',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(160,5,'2026-03-19',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(161,5,'2026-03-20',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(162,5,'2026-03-23',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(163,5,'2026-03-24',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(164,5,'2026-03-25',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(165,5,'2026-03-26',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(166,5,'2026-03-27',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(167,5,'2026-03-30',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(168,5,'2026-03-31',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(169,6,'2026-03-02',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(170,6,'2026-03-03',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(171,6,'2026-03-04',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(172,6,'2026-03-05',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(173,6,'2026-03-06',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(174,6,'2026-03-09',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(175,6,'2026-03-10',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(176,6,'2026-03-11',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(177,6,'2026-03-12',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(178,6,'2026-03-13',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(179,6,'2026-03-16',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(180,6,'2026-03-17',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(181,6,'2026-03-18',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(182,6,'2026-03-19',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(183,6,'2026-03-20',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(184,6,'2026-03-23',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(185,6,'2026-03-24',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(186,6,'2026-03-25',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(187,6,'2026-03-26',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(188,6,'2026-03-27',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(189,6,'2026-03-30',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(190,6,'2026-03-31',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(191,7,'2026-03-02',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(192,7,'2026-03-03',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(193,7,'2026-03-04',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(194,7,'2026-03-05',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(195,7,'2026-03-06',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(196,7,'2026-03-09',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(197,7,'2026-03-10',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(198,7,'2026-03-11',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(199,7,'2026-03-11',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(200,7,'2026-03-12',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(201,7,'2026-03-16',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(202,7,'2026-03-17',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(203,7,'2026-03-18',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(204,7,'2026-03-19',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(205,7,'2026-03-19',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(206,7,'2026-03-20',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(207,7,'2026-03-20',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(208,7,'2026-03-21',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(209,7,'2026-03-22',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(210,7,'2026-03-23',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(211,7,'2026-03-24',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(212,7,'2026-03-25',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(213,7,'2026-03-25',NULL,NULL,NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(214,7,'2026-03-27',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(215,7,'2026-03-27',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(216,7,'2026-03-30',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(217,7,'2026-03-31',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(218,8,'2026-03-02',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(219,8,'2026-03-03',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(220,8,'2026-03-04',NULL,NULL,NULL,'Project',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(221,8,'2026-03-04',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(222,8,'2026-03-05',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(223,8,'2026-03-06',NULL,NULL,NULL,'Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(224,8,'2026-03-06',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(225,8,'2026-03-09',NULL,NULL,NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(226,8,'2026-03-10',NULL,NULL,NULL,'Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(227,8,'2026-03-10',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(228,8,'2026-03-11',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(229,8,'2026-03-11',NULL,NULL,NULL,'Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(230,8,'2026-03-12',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(231,8,'2026-03-12',NULL,NULL,NULL,'Support',7.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(232,8,'2026-03-13',NULL,NULL,NULL,'Support',7.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(233,8,'2026-03-13',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(234,8,'2026-03-16',NULL,NULL,NULL,'Support',7.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(235,8,'2026-03-16',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(236,8,'2026-03-17',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(237,8,'2026-03-18',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(238,8,'2026-03-18',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(239,8,'2026-03-19',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(240,8,'2026-03-20',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(241,8,'2026-03-23',NULL,NULL,NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(242,8,'2026-03-23',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(243,8,'2026-03-24',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(244,8,'2026-03-24',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(245,8,'2026-03-25',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(246,8,'2026-03-25',NULL,NULL,NULL,'Project',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(247,8,'2026-03-25',NULL,NULL,NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(248,8,'2026-03-26',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(249,8,'2026-03-27',NULL,NULL,NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(250,8,'2026-03-27',NULL,NULL,NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(251,8,'2026-03-30',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(252,8,'2026-03-31',NULL,NULL,NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(253,9,'2026-03-02',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(254,9,'2026-03-03',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(255,9,'2026-03-04',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(256,9,'2026-03-05',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(257,9,'2026-03-06',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(258,9,'2026-03-09',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(259,9,'2026-03-10',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(260,9,'2026-03-11',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(261,9,'2026-03-12',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(262,9,'2026-03-13',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(263,9,'2026-03-16',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(264,9,'2026-03-17',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(265,9,'2026-03-18',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(266,9,'2026-03-19',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(267,9,'2026-03-20',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(268,9,'2026-03-23',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(269,9,'2026-03-24',NULL,NULL,NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(270,9,'2026-03-25',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(271,9,'2026-03-26',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(272,9,'2026-03-27',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(273,9,'2026-03-30',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO "vendor_timesheets" VALUES(274,9,'2026-03-31',NULL,NULL,NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
CREATE INDEX idx_vt_consultant ON vendor_timesheets(consultant_id);
CREATE INDEX idx_vt_date ON vendor_timesheets(entry_date);
CREATE INDEX idx_vt_project ON vendor_timesheets(project_key);
CREATE INDEX idx_pm_sse ON project_mapping(sse_key);
CREATE INDEX idx_pm_ete ON project_mapping(ete_project_id);
CREATE INDEX idx_pc_project ON project_comments(project_id);
CREATE INDEX idx_pa_project ON project_attachments(project_id);
CREATE INDEX idx_pal_project ON project_audit_log(project_id);
CREATE INDEX idx_pms_project ON project_milestones(project_id);
CREATE INDEX idx_pms_due ON project_milestones(due_date);
CREATE INDEX idx_pt_project ON project_tasks(project_id);
CREATE INDEX idx_pt_milestone ON project_tasks(milestone_id);
CREATE INDEX idx_pt_parent ON project_tasks(parent_task_id);
CREATE INDEX idx_pt_assignee ON project_tasks(assignee);
CREATE INDEX idx_td_task ON task_dependencies(task_id);
CREATE INDEX idx_td_dep ON task_dependencies(depends_on_id);
CREATE INDEX idx_app_settings_category ON app_settings(category);
CREATE INDEX idx_init_status ON initiatives(status);
COMMIT;
