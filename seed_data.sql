PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE schema_info (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);
INSERT INTO schema_info VALUES('version','1');
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
, budget REAL DEFAULT 0.0, actual_cost REAL DEFAULT 0.0, forecast_cost REAL DEFAULT 0.0);
INSERT INTO projects VALUES('ETE-83','Customer Master Data Cleanup','Key Initiative','Sales & Distribution','Tom Vierling','NEEDS TECHNICAL SPEC',0.4000000000000000222,'High','2025-10-14','2026-06-01',NULL,'Systems Applications','Emily Fridley','Audrey Debaere',NULL,NULL,'Alex Young','XXL: > 640 Hours',1480.0,'Completed Q1',1,'2026-04-02 03:35:22','2026-04-02 15:19:42',0.0,74000.0,185000.0);
INSERT INTO projects VALUES('ETE-48','System Connection Syteline-VKS','Key Initiative','Engineering','Ray Trumble','NOT STARTED',0.1000000000000000055,'High','2026-02-15','2026-06-30',NULL,'Synnergie','Emily Fridley','Jim Young','Ajay Kumar','Sangamesh Koti','Alex Young','L: 160-320 Hours',240.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,3000.0,30000.0);
INSERT INTO projects VALUES('ETE-68','Catalog API Rust2Python','Key Initiative','Information Technology','Jim Koscielniak','🟢 ON TRACK',0.5,'High','2025-11-17','2026-04-24',NULL,'Systems Applications','Emily Fridley','Audrey Debaere',NULL,NULL,'Colin Olson','XXL: > 640 Hours',640.0,NULL,1,'2026-04-02 03:35:22','2026-04-02T07:28:54.815415',0.0,40000.0,80000.0);
INSERT INTO projects VALUES('ETE-43','Data Security - Microsoft Purview','Key Initiative','Information Technology','Jim Koscielniak','🟢 ON TRACK',0.0,'High','2026-02-02','2026-06-30',NULL,'Infrastructure','Emily Fridley','Audrey Debaere','Deepak Gudwani','Sarath Yeturu','Alex Young',NULL,320.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,0.0,40000.0);
INSERT INTO projects VALUES('ETE-19','Changes to AR Aging Report','Enhancement','Finance','Tom Newell','NEEDS TECHNICAL SPEC',0.1000000000000000055,'High','2026-02-23','2026-04-17',NULL,'Synnergie','Emily Fridley','Audrey Debaere','Ajay Kumar','Bhavya Reddy','Alex Young','M: 80-160 Hours',120.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 20:42:28',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-49','Marketing: STE Rewards Tier','Enhancement','Sales & Distribution','Tom Vierling','NEEDS TECHNICAL SPEC',0.0,'Medium','2026-04-01','2026-09-16',NULL,'Systems Applications','Emily Fridley','Audrey Debaere','Ajay Kumar','Sarath Yeturu','Alex Young','L: 160-320 Hours',240.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 19:53:49',0.0,0.0,30000.0);
INSERT INTO projects VALUES('ETE-7','Outsourced Unit Core Accounting','Enhancement','Finance','Tom Newell','NOT STARTED',0.0,'Medium','2026-04-01','2026-05-20',NULL,'Synnergie','Emily Fridley','Audrey Debaere','Ajay Kumar','Bhavya Reddy','Alex Young','XXL: > 640 Hours',640.0,'8-9 month project',1,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,80000.0);
INSERT INTO projects VALUES('ETE-52','SWIMS/Syteline Reporting','Enhancement','Supply Chain','Jon Besherse','NOT STARTED',0.0,'Medium','2026-04-01','2026-04-29',NULL,'Systems Applications','Emily Fridley','Audrey Debaere','Ajay Kumar','Bhavya Reddy','Alex Young','S: < 80 Hours',40.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 19:53:49',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-16','Partial Pay w/ CC from WMERP','Enhancement','Finance','Tom Newell','⚪ NOT STARTED',0.0,'Medium','2026-04-01','2026-06-24',NULL,'Synnergie','Emily Fridley','Audrey Debaere','Deepak Gudwani','Ravindra Reddy','Alex Young','M: 80-160 Hours',120.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-37','Magic Search in BuyETE','Enhancement','Sales & Distribution','Tom Vierling','NEEDS TECHNICAL SPEC',0.0,'Highest','2026-04-01','2026-06-17',NULL,'Systems Applications','Emily Fridley','Audrey Debaere','Ajay Kumar','Sarath Yeturu','Alex Young','S: < 80 Hours',40.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 19:53:49',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-97','Standard Order Process Notifications','Enhancement','Sales & Distribution','Tom Vierling','NOT STARTED',0.0,'Highest','2026-04-01','2026-06-17',NULL,'Systems Applications','Emily Fridley','Audrey Debaere','Ajay Kumar','Bhavya Reddy','Alex Young',NULL,200.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,25000.0);
INSERT INTO projects VALUES('ETE-100','ATSG Expired Members Self-Payment','Enhancement','Sales & Distribution','Tom Vierling','NEEDS FUNCTIONAL SPEC',0.0,'Medium','2026-04-01','2026-05-27',NULL,'Systems Applications','Emily Fridley','Audrey Debaere','Deepak Gudwani','Ravindra Reddy','Alex Young',NULL,200.0,NULL,1,'2026-04-02 03:35:22','2026-04-03 19:53:49',0.0,0.0,25000.0);
INSERT INTO projects VALUES('ETE-124','Clean Up Return Loads','Enhancement','Finance','Tom Newell','NOT STARTED',0.0,'Highest','2026-04-01','2026-05-20',NULL,'Synnergie','Emily Fridley','Audrey Debaere','Ajay Kumar','Sarath Yeturu','Alex Young',NULL,200.0,NULL,1,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,25000.0);
INSERT INTO projects VALUES('ETE-58','Transfer Order Moved Items to Transit Location','Enhancement','Finance','Jim Young','POSTPONED',0.0,NULL,'2026-04-01','2026-09-23',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-51','RMA Credit Memo on Ghost Check-In','Enhancement','Finance','Tom Newell','POSTPONED',0.0,NULL,'2026-04-01','2026-08-26',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-59','Reconcile BridgePay CC Transactions ','Enhancement','Finance','Tom Newell','POSTPONED',0.0,NULL,'2026-04-01','2026-05-13',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-60','EDI Payments Not Posting on Background','Enhancement','Finance','Tom Newell','POSTPONED',0.0,NULL,'2026-04-01','2026-09-02',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-61','Accum Deposits Received Field','Bug','Finance','Tom Newell','POSTPONED',0.0,NULL,'2026-04-01','2026-07-29',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-86','Allow TCM Core Receiving to Post ','Enhancement','Engineering','Ray Trumble','POSTPONED',0.0,NULL,'2026-04-01','2026-05-06',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-34','Salesforce BDR Application & Process Implementation','Enhancement','Sales & Distribution','Tom Vierling','POSTPONED',0.0,NULL,'2026-04-01','2026-04-29',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-35','BuyETE Ability for Customers to Save Quotes','Enhancement','Sales & Distribution','Tom Vierling','POSTPONED',0.0,NULL,'2026-04-01','2026-05-13',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-33','EDI 3PL Locations','Enhancement','Sales & Distribution','Tom Vierling','🔴 NEEDS HELP',0.0,'High','2026-04-01','2026-06-10',NULL,'Systems Applications','Brett Anderson','Jim Young','Deepak Gudwani','Sarath Yeturu',NULL,'M: 80-160 Hours',120.0,NULL,2,'2026-04-02 03:35:22','2026-04-02 16:04:25',0.0,0.0,0.0);
INSERT INTO projects VALUES('ETE-67','Avalara Tax Issues','Enhancement','Finance','Tom Newell','✅ COMPLETE',1.0,'Highest','2026-02-04','2026-02-27',NULL,'Synnergie','Emily Fridley','Audrey Debaere','Deepak Gudwani','Sangamesh Koti',NULL,'M: 80-160 Hours',120.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,15000.0,15000.0);
INSERT INTO projects VALUES('ETE-14','Installed Return RMA Type','Enhancement','Supply Chain','Jon Besherse','✅ COMPLETE',1.0,'Highest','2026-03-02','2026-03-20',NULL,'Synnergie','Bettina Kotico','Audrey Debaere','Ajay Kumar','Sarath Yeturu',NULL,'M: 80-160 Hours',120.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,15000.0,15000.0);
INSERT INTO projects VALUES('ETE-70','Nutanix (Replace VMware)','Key Initiative','Information Technology','Jim Koscielniak','✅ COMPLETE',1.0,'Highest','2025-12-01','2026-03-21',NULL,'Infrastructure','Emily Fridley','Ryan Picado','Ajay Kumar','Michael House',NULL,NULL,120.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,15000.0,15000.0);
INSERT INTO projects VALUES('ETE-65','Rebuild Vendor Portal','Enhancement','Sales & Distribution','Tom Vierling','✅ COMPLETE',1.0,'High','2025-10-27','2026-01-09','2026-02-15','Systems Applications','Brett Anderson','Jim Young','Deepak Gudwani','Jonathon Gonzalez',NULL,'S: < 80 Hours',60.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,12000.0,12000.0);
INSERT INTO projects VALUES('ETE-69','Core Plan Optimization','Key Initiative','Supply Chain','Jon Besherse','✅ COMPLETE',1.0,'High','2025-11-12','2026-01-23','2026-01-23','Synnergie','Emily Fridley','Audrey Debaere','Ajay Kumar','Ravindra Reddy',NULL,'L: 160-320 Hours',360.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,45000.0,45000.0);
INSERT INTO projects VALUES('ETE-31','Restocking Fees Added to RMA Credit Memo','Enhancement','Finance','Tom Newell','✅ COMPLETE',1.0,'High','2024-12-22','2026-02-06','2026-02-28','Synnergie','Brett Anderson','Audrey Debaere','Deepak Gudwani','Bhavya Reddy',NULL,'L: 160-320 Hours',310.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,38750.0,38750.0);
INSERT INTO projects VALUES('ETE-45','VB Bin Printer Integration','Enhancement','Engineering','Ray Trumble','✅ COMPLETE',1.0,'High','2025-10-20','2026-02-20','2026-02-20','Synnergie','Brett Anderson','Cristian Varelas','Deepak Gudwani','Sangamesh Koti',NULL,'M: 80-160 Hours',160.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,20000.0,20000.0);
INSERT INTO projects VALUES('ETE-42','Gear Screen - Improved Production Oversight','Key Initiative','Production','Ari Rosengarten','COMPLETE',1.0,'High','2026-01-12','2026-02-05','2026-02-28','Synnergie','Bettina Kotico','Cristian Varelas','Deepak Gudwani','Vishnu Premen',NULL,'M: 80-160 Hours',120.0,'NAPA not ready',3,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,10000.0,10000.0);
INSERT INTO projects VALUES('ETE-72','Fortigate ZTNA - EMS Setup','Key Initiative','Information Technology','Jim Koscielniak','✅ COMPLETE',1.0,'High','2025-12-12','2025-12-31','2026-02-27','Infrastructure',NULL,NULL,NULL,'Justin Senour',NULL,NULL,0.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,8000.0,8000.0);
INSERT INTO projects VALUES('ETE-71','One Drive Migration','Key Initiative','Information Technology','Jim Koscielniak','✅ COMPLETE',1.0,'High','2025-12-22','2026-02-06','2026-02-15','Infrastructure',NULL,NULL,NULL,'Michael House',NULL,NULL,0.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,10000.0,10000.0);
INSERT INTO projects VALUES('ETE-87','Production Dashboard','Enhancement','Production','Ari Rosengarten','COMPLETE',1.0,'High','2026-04-01','2026-06-17',NULL,'Systems Applications','Emily Fridley','Cristian Varelas','Ajay Kumar','Vishnu Premen',NULL,'S: < 80 Hours',40.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,12000.0,12000.0);
INSERT INTO projects VALUES('ETE-88','Return Load Phase 2','Key Initiative','Finance','Tom Newell','COMPLETE',1.0,'High','2025-10-27','2025-12-29','2026-01-09','Synnergie','Brett Anderson','Audrey Debaere','Deepak Gudwani','Sangamesh Koti',NULL,NULL,320.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 15:40:39',0.0,40000.0,40000.0);
INSERT INTO projects VALUES('ETE-73','Teal Parts Daily Inventory Feed','Enhancement','Sales & Distribution','Tom Vierling','✅ COMPLETE',1.0,'Highest','2026-04-01','2026-08-19',NULL,'Systems Applications','Brett Anderson','Cristian Varelas','Deepak Gudwani','Sarath Yeturu',NULL,'S: < 80 Hours',40.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,8000.0,8000.0);
INSERT INTO projects VALUES('ETE-10','Upload Utility for Planning Fields','Enhancement','Supply Chain','Tom Green','✅ COMPLETE',1.0,'Highest','2026-04-01','2026-09-09',NULL,'Synnergie','Emily Fridley','Audrey Debaere','Deepak Gudwani','Bhavya Reddy','Alex Young','S: < 80 Hours',80.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 15:19:42',0.0,8000.0,8000.0);
INSERT INTO projects VALUES('ETE-32','Form: Cash App SQL Fix','Enhancement','Finance','Tom Newell','✅ COMPLETE',1.0,'High','2026-04-01','2026-04-29',NULL,'Synnergie','Bettina Kotico','Audrey Debaere','Deepak Gudwani','Vishnu Premen',NULL,'L: 160-320 Hours',320.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,40000.0,40000.0);
INSERT INTO projects VALUES('ETE-76','FedEx Web Services API','Enhancement','Information Technology','Jim Koscielniak','✅ COMPLETE',0.0,'High','2026-03-03','2026-03-13',NULL,'Systems Applications','Emily Fridley','Audrey Debaere','Deepak Gudwani','Alex Young','Alex Young','S: < 80 Hours',40.0,NULL,3,'2026-04-02 03:35:22','2026-04-02 03:35:22',0.0,0.0,0.0);
CREATE TABLE project_role_allocations (
    project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role_key    TEXT NOT NULL,
    allocation  REAL DEFAULT 0.0,
    PRIMARY KEY (project_id, role_key)
);
INSERT INTO project_role_allocations VALUES('ETE-83','pm',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-83','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-83','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-83','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-83','developer',0.5);
INSERT INTO project_role_allocations VALUES('ETE-83','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-83','dba',0.05000000000000000277);
INSERT INTO project_role_allocations VALUES('ETE-83','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-48','pm',0.25);
INSERT INTO project_role_allocations VALUES('ETE-48','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-48','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-48','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-48','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-48','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-48','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-48','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-68','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-68','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-68','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-68','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-68','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-68','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-68','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-68','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-43','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-43','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-43','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-43','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-43','developer',0.5);
INSERT INTO project_role_allocations VALUES('ETE-43','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-43','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-43','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-19','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-19','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-19','functional',0.25);
INSERT INTO project_role_allocations VALUES('ETE-19','technical',0.6500000000000000222);
INSERT INTO project_role_allocations VALUES('ETE-19','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-19','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-19','dba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-19','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-49','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-49','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-49','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-49','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-49','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-49','infrastructure',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-49','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-49','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-7','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-7','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-7','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-7','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-7','developer',0.5999999999999999778);
INSERT INTO project_role_allocations VALUES('ETE-7','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-7','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-7','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-52','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-52','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-52','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-52','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-52','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-52','infrastructure',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-52','dba',0.05000000000000000277);
INSERT INTO project_role_allocations VALUES('ETE-52','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-16','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-16','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-16','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-16','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-16','developer',0.5999999999999999778);
INSERT INTO project_role_allocations VALUES('ETE-16','infrastructure',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-16','dba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-16','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-37','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-37','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-37','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-37','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-37','developer',0.6500000000000000222);
INSERT INTO project_role_allocations VALUES('ETE-37','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-37','dba',0.05000000000000000277);
INSERT INTO project_role_allocations VALUES('ETE-37','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-97','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-97','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-97','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-97','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-97','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-97','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-97','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-97','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-100','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-100','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-100','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-100','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-100','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-100','infrastructure',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-100','dba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-100','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-124','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-124','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-124','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-124','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-124','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-124','infrastructure',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-124','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-124','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-58','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-58','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-58','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-58','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-58','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-58','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-58','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-58','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-51','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-51','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-51','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-51','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-51','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-51','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-51','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-51','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-59','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-59','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-59','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-59','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-59','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-59','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-59','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-59','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-60','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-60','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-60','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-60','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-60','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-60','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-60','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-60','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-61','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-61','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-61','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-61','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-61','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-61','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-61','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-61','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-86','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-86','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-86','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-86','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-86','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-86','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-86','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-86','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-34','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-34','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-34','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-34','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-34','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-34','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-34','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-34','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-35','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-35','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-35','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-35','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-35','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-35','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-35','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-35','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-33','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-33','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-33','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-33','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-33','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-33','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-33','dba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-33','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-67','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-67','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-67','functional',0.25);
INSERT INTO project_role_allocations VALUES('ETE-67','technical',0.75);
INSERT INTO project_role_allocations VALUES('ETE-67','developer',0.5);
INSERT INTO project_role_allocations VALUES('ETE-67','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-67','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-67','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-14','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-14','ba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-14','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-14','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-14','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-14','infrastructure',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-14','dba',0.05000000000000000277);
INSERT INTO project_role_allocations VALUES('ETE-14','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-70','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-70','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-70','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-70','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-70','developer',0.5);
INSERT INTO project_role_allocations VALUES('ETE-70','infrastructure',0.5);
INSERT INTO project_role_allocations VALUES('ETE-70','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-70','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-65','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-65','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-65','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-65','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-65','developer',0.5);
INSERT INTO project_role_allocations VALUES('ETE-65','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-65','dba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-65','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-69','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-69','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-69','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-69','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-69','developer',0.5999999999999999778);
INSERT INTO project_role_allocations VALUES('ETE-69','infrastructure',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-69','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-69','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-31','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-31','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-31','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-31','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-31','developer',0.5999999999999999778);
INSERT INTO project_role_allocations VALUES('ETE-31','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-31','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-31','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-45','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-45','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-45','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-45','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-45','developer',0.4000000000000000222);
INSERT INTO project_role_allocations VALUES('ETE-45','infrastructure',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-45','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-45','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-42','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-42','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-42','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-42','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-42','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-42','infrastructure',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-42','dba',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-42','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-72','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-72','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-72','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-72','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-72','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-72','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-72','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-72','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-71','pm',0.0);
INSERT INTO project_role_allocations VALUES('ETE-71','ba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-71','functional',0.0);
INSERT INTO project_role_allocations VALUES('ETE-71','technical',0.0);
INSERT INTO project_role_allocations VALUES('ETE-71','developer',0.0);
INSERT INTO project_role_allocations VALUES('ETE-71','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-71','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-71','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-87','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-87','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-87','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-87','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-87','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-87','infrastructure',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-87','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-87','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-88','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-88','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-88','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-88','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-88','developer',0.4000000000000000222);
INSERT INTO project_role_allocations VALUES('ETE-88','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-88','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-88','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-73','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-73','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-73','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-73','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-73','developer',0.5);
INSERT INTO project_role_allocations VALUES('ETE-73','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-73','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-73','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-10','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-10','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-10','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-10','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-10','developer',0.5);
INSERT INTO project_role_allocations VALUES('ETE-10','infrastructure',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-10','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-10','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-32','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-32','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-32','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-32','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-32','developer',0.75);
INSERT INTO project_role_allocations VALUES('ETE-32','infrastructure',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-32','dba',0.0);
INSERT INTO project_role_allocations VALUES('ETE-32','wms',0.0);
INSERT INTO project_role_allocations VALUES('ETE-76','pm',0.1000000000000000055);
INSERT INTO project_role_allocations VALUES('ETE-76','ba',0.1499999999999999945);
INSERT INTO project_role_allocations VALUES('ETE-76','functional',0.2000000000000000111);
INSERT INTO project_role_allocations VALUES('ETE-76','technical',0.25);
INSERT INTO project_role_allocations VALUES('ETE-76','developer',0.5999999999999999778);
INSERT INTO project_role_allocations VALUES('ETE-76','infrastructure',0.0);
INSERT INTO project_role_allocations VALUES('ETE-76','dba',0.05000000000000000277);
INSERT INTO project_role_allocations VALUES('ETE-76','wms',0.0);
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
);
INSERT INTO team_members VALUES('Ajay Kumar','Functional','functional','ERP','Synnergie','MSA',65.0,35.0,0.4000000000000000222);
INSERT INTO team_members VALUES('Ravindra Reddy','Technical','technical','ERP','Synnergie','MSA',65.0,35.0,0.4000000000000000222);
INSERT INTO team_members VALUES('Vishnu Premen','Technical','technical','ERP','Synnergie','T&M',65.0,35.0,0.4000000000000000222);
INSERT INTO team_members VALUES('Deepak Gudwani','Functional','functional','ERP','Synnergie','T&M',65.0,35.0,0.4000000000000000222);
INSERT INTO team_members VALUES('Sangamesh Koti','Technical','technical','ERP','Synnergie','T&M',65.0,35.0,0.0);
INSERT INTO team_members VALUES('Bhavya Reddy','Technical','technical','ERP','Synnergie','T&M',65.0,35.0,0.0);
INSERT INTO team_members VALUES('Sarath Yeturu','Technical','technical','ERP','Synnergie','MSA',65.0,35.0,0.5999999999999999778);
INSERT INTO team_members VALUES('Vinod Bollepally','DBA','dba','ERP','Synnergie','MSA',65.0,35.0,0.8000000000000000444);
INSERT INTO team_members VALUES('Jim Young','Business Analyst','ba','Business Analysts','ETE',NULL,65.0,40.0,0.5999999999999999778);
INSERT INTO team_members VALUES('Alex Young','Developer','developer','Systems Applications','ETE',NULL,65.0,25.0,0.0);
INSERT INTO team_members VALUES('Nick Smith','Developer','developer','Systems Applications','ETE',NULL,65.0,25.0,0.4000000000000000222);
INSERT INTO team_members VALUES('Colin Olson','Developer','developer','Systems Applications','ETE',NULL,65.0,25.0,0.1000000000000000055);
INSERT INTO team_members VALUES('Jonathon Gonzalez','Developer','developer','Systems Applications','ETE',NULL,65.0,25.0,0.25);
INSERT INTO team_members VALUES('Audrey Debaere','Business Analyst','ba','Business Analysts','ETE',NULL,65.0,35.0,0.5);
INSERT INTO team_members VALUES('Cristian Varelas','Business Analyst','ba','Business Analysts','ETE',NULL,65.0,35.0,0.2000000000000000111);
INSERT INTO team_members VALUES('Ryan Picado','Business Analyst','ba','Business Analysts','ETE',NULL,65.0,35.0,0.5);
INSERT INTO team_members VALUES('Emily Fridley','Project Manager','pm','PMO','ETE',NULL,65.0,35.0,0.5);
INSERT INTO team_members VALUES('Brett Anderson','Project Manager','pm','PMO','ETE',NULL,65.0,35.0,0.25);
INSERT INTO team_members VALUES('Bettina Kotico','Project Manager','pm','PMO','Kayana','T&M',65.0,32.0,0.6800000000000000488);
INSERT INTO team_members VALUES('Donna Wiedemeier','WMS Consultant','wms','WMS','Watermark','T&M',65.0,35.0,0.5999999999999999778);
INSERT INTO team_members VALUES('Justin Senour','Infrastructure','infrastructure','Infrastructure','ETE',NULL,65.0,40.0,0.5999999999999999778);
INSERT INTO team_members VALUES('Michael House','Infrastructure','infrastructure','Infrastructure','ETE',NULL,65.0,40.0,0.5999999999999999778);
INSERT INTO team_members VALUES('Andrew Shaefer','Infrastructure','infrastructure','Infrastructure','ETE',NULL,65.0,40.0,0.5999999999999999778);
INSERT INTO team_members VALUES('Akhilesh Mishra','Technical','technical','ERP','Synnergie','T&M',65.0,35.0,0.0);
CREATE TABLE project_assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    person_name     TEXT NOT NULL,
    role_key        TEXT NOT NULL,
    allocation_pct  REAL DEFAULT 1.0,
    UNIQUE(project_id, person_name, role_key)
);
INSERT INTO project_assignments VALUES(1,'ETE-83','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(2,'ETE-83','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(3,'ETE-83','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(4,'ETE-83','Bhavya Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(5,'ETE-83','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(6,'ETE-48','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(7,'ETE-48','Jim Young','ba',1.0);
INSERT INTO project_assignments VALUES(8,'ETE-48','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(9,'ETE-48','Sangamesh Koti','technical',1.0);
INSERT INTO project_assignments VALUES(10,'ETE-48','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(11,'ETE-68','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(12,'ETE-68','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(13,'ETE-68','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(14,'ETE-68','Colin Olson','technical',1.0);
INSERT INTO project_assignments VALUES(15,'ETE-68','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(16,'ETE-43','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(17,'ETE-43','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(18,'ETE-43','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(19,'ETE-43','Sarath Yeturu','technical',1.0);
INSERT INTO project_assignments VALUES(20,'ETE-43','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(21,'ETE-19','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(22,'ETE-19','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(23,'ETE-19','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(24,'ETE-19','Bhavya Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(25,'ETE-19','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(26,'ETE-49','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(27,'ETE-49','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(28,'ETE-49','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(29,'ETE-49','Sarath Yeturu','technical',1.0);
INSERT INTO project_assignments VALUES(30,'ETE-49','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(31,'ETE-7','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(32,'ETE-7','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(33,'ETE-7','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(34,'ETE-7','Bhavya Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(35,'ETE-7','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(36,'ETE-52','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(37,'ETE-52','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(38,'ETE-52','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(39,'ETE-52','Bhavya Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(40,'ETE-52','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(41,'ETE-16','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(42,'ETE-16','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(43,'ETE-16','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(44,'ETE-16','Ravindra Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(45,'ETE-16','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(46,'ETE-37','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(47,'ETE-37','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(48,'ETE-37','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(49,'ETE-37','Sarath Yeturu','technical',1.0);
INSERT INTO project_assignments VALUES(50,'ETE-37','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(51,'ETE-97','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(52,'ETE-97','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(53,'ETE-97','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(54,'ETE-97','Bhavya Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(55,'ETE-97','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(56,'ETE-100','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(57,'ETE-100','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(58,'ETE-100','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(59,'ETE-100','Ravindra Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(60,'ETE-100','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(61,'ETE-124','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(62,'ETE-124','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(63,'ETE-124','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(64,'ETE-124','Sarath Yeturu','technical',1.0);
INSERT INTO project_assignments VALUES(65,'ETE-124','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(66,'ETE-33','Brett Anderson','pm',1.0);
INSERT INTO project_assignments VALUES(67,'ETE-33','Jim Young','ba',1.0);
INSERT INTO project_assignments VALUES(68,'ETE-33','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(69,'ETE-33','Sarath Yeturu','technical',1.0);
INSERT INTO project_assignments VALUES(70,'ETE-67','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(71,'ETE-67','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(72,'ETE-67','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(73,'ETE-67','Sangamesh Koti','technical',1.0);
INSERT INTO project_assignments VALUES(74,'ETE-14','Bettina Kotico','pm',1.0);
INSERT INTO project_assignments VALUES(75,'ETE-14','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(76,'ETE-14','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(77,'ETE-14','Sarath Yeturu','technical',1.0);
INSERT INTO project_assignments VALUES(78,'ETE-70','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(79,'ETE-70','Ryan Picado','ba',1.0);
INSERT INTO project_assignments VALUES(80,'ETE-70','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(81,'ETE-70','Michael House','technical',1.0);
INSERT INTO project_assignments VALUES(82,'ETE-65','Brett Anderson','pm',1.0);
INSERT INTO project_assignments VALUES(83,'ETE-65','Jim Young','ba',1.0);
INSERT INTO project_assignments VALUES(84,'ETE-65','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(85,'ETE-65','Jonathon Gonzalez','technical',1.0);
INSERT INTO project_assignments VALUES(86,'ETE-69','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(87,'ETE-69','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(88,'ETE-69','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(89,'ETE-69','Ravindra Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(90,'ETE-31','Brett Anderson','pm',1.0);
INSERT INTO project_assignments VALUES(91,'ETE-31','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(92,'ETE-31','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(93,'ETE-31','Bhavya Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(94,'ETE-45','Brett Anderson','pm',1.0);
INSERT INTO project_assignments VALUES(95,'ETE-45','Cristian Varelas','ba',1.0);
INSERT INTO project_assignments VALUES(96,'ETE-45','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(97,'ETE-45','Sangamesh Koti','technical',1.0);
INSERT INTO project_assignments VALUES(98,'ETE-42','Bettina Kotico','pm',1.0);
INSERT INTO project_assignments VALUES(99,'ETE-42','Cristian Varelas','ba',1.0);
INSERT INTO project_assignments VALUES(100,'ETE-42','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(101,'ETE-42','Vishnu Premen','technical',1.0);
INSERT INTO project_assignments VALUES(102,'ETE-72','Justin Senour','technical',1.0);
INSERT INTO project_assignments VALUES(103,'ETE-71','Michael House','technical',1.0);
INSERT INTO project_assignments VALUES(104,'ETE-87','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(105,'ETE-87','Cristian Varelas','ba',1.0);
INSERT INTO project_assignments VALUES(106,'ETE-87','Ajay Kumar','functional',1.0);
INSERT INTO project_assignments VALUES(107,'ETE-87','Vishnu Premen','technical',1.0);
INSERT INTO project_assignments VALUES(108,'ETE-88','Brett Anderson','pm',1.0);
INSERT INTO project_assignments VALUES(109,'ETE-88','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(110,'ETE-88','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(111,'ETE-88','Sangamesh Koti','technical',1.0);
INSERT INTO project_assignments VALUES(112,'ETE-73','Brett Anderson','pm',1.0);
INSERT INTO project_assignments VALUES(113,'ETE-73','Cristian Varelas','ba',1.0);
INSERT INTO project_assignments VALUES(114,'ETE-73','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(115,'ETE-73','Sarath Yeturu','technical',1.0);
INSERT INTO project_assignments VALUES(116,'ETE-10','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(117,'ETE-10','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(118,'ETE-10','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(119,'ETE-10','Bhavya Reddy','technical',1.0);
INSERT INTO project_assignments VALUES(120,'ETE-10','Alex Young','developer',1.0);
INSERT INTO project_assignments VALUES(121,'ETE-32','Bettina Kotico','pm',1.0);
INSERT INTO project_assignments VALUES(122,'ETE-32','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(123,'ETE-32','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(124,'ETE-32','Vishnu Premen','technical',1.0);
INSERT INTO project_assignments VALUES(125,'ETE-76','Emily Fridley','pm',1.0);
INSERT INTO project_assignments VALUES(126,'ETE-76','Audrey Debaere','ba',1.0);
INSERT INTO project_assignments VALUES(127,'ETE-76','Deepak Gudwani','functional',1.0);
INSERT INTO project_assignments VALUES(128,'ETE-76','Alex Young','technical',1.0);
INSERT INTO project_assignments VALUES(129,'ETE-76','Alex Young','developer',1.0);
CREATE TABLE rm_assumptions (
    key     TEXT PRIMARY KEY,
    value   REAL NOT NULL
);
INSERT INTO rm_assumptions VALUES('base_hours_per_week',40.0);
INSERT INTO rm_assumptions VALUES('admin_pct',0.1000000000000000055);
INSERT INTO rm_assumptions VALUES('breakfix_pct',0.1000000000000000055);
INSERT INTO rm_assumptions VALUES('project_pct',0.8000000000000000444);
INSERT INTO rm_assumptions VALUES('available_project_hrs',32.0);
INSERT INTO rm_assumptions VALUES('max_projects_per_person',3.0);
INSERT INTO rm_assumptions VALUES('annual_budget',1000000.0);
CREATE TABLE sdlc_phase_weights (
    phase   TEXT PRIMARY KEY,
    weight  REAL NOT NULL
);
INSERT INTO sdlc_phase_weights VALUES('discovery',0.1000000000000000055);
INSERT INTO sdlc_phase_weights VALUES('planning',0.1000000000000000055);
INSERT INTO sdlc_phase_weights VALUES('design',0.1499999999999999945);
INSERT INTO sdlc_phase_weights VALUES('build',0.2999999999999999889);
INSERT INTO sdlc_phase_weights VALUES('test',0.2000000000000000111);
INSERT INTO sdlc_phase_weights VALUES('deploy',0.1499999999999999945);
CREATE TABLE role_phase_efforts (
    role_key    TEXT NOT NULL,
    phase       TEXT NOT NULL,
    effort      REAL NOT NULL,
    PRIMARY KEY (role_key, phase)
);
INSERT INTO role_phase_efforts VALUES('pm','discovery',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('pm','planning',0.25);
INSERT INTO role_phase_efforts VALUES('pm','design',0.1499999999999999945);
INSERT INTO role_phase_efforts VALUES('pm','build',0.2000000000000000111);
INSERT INTO role_phase_efforts VALUES('pm','test',0.2000000000000000111);
INSERT INTO role_phase_efforts VALUES('pm','deploy',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('dba','discovery',0.05000000000000000277);
INSERT INTO role_phase_efforts VALUES('dba','planning',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('dba','design',0.2999999999999999889);
INSERT INTO role_phase_efforts VALUES('dba','build',0.25);
INSERT INTO role_phase_efforts VALUES('dba','test',0.2000000000000000111);
INSERT INTO role_phase_efforts VALUES('dba','deploy',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('ba','discovery',0.2999999999999999889);
INSERT INTO role_phase_efforts VALUES('ba','planning',0.2000000000000000111);
INSERT INTO role_phase_efforts VALUES('ba','design',0.2000000000000000111);
INSERT INTO role_phase_efforts VALUES('ba','build',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('ba','test',0.1499999999999999945);
INSERT INTO role_phase_efforts VALUES('ba','deploy',0.05000000000000000277);
INSERT INTO role_phase_efforts VALUES('functional','discovery',0.2000000000000000111);
INSERT INTO role_phase_efforts VALUES('functional','planning',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('functional','design',0.2999999999999999889);
INSERT INTO role_phase_efforts VALUES('functional','build',0.1499999999999999945);
INSERT INTO role_phase_efforts VALUES('functional','test',0.1499999999999999945);
INSERT INTO role_phase_efforts VALUES('functional','deploy',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('technical','discovery',0.05000000000000000277);
INSERT INTO role_phase_efforts VALUES('technical','planning',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('technical','design',0.2000000000000000111);
INSERT INTO role_phase_efforts VALUES('technical','build',0.4000000000000000222);
INSERT INTO role_phase_efforts VALUES('technical','test',0.1499999999999999945);
INSERT INTO role_phase_efforts VALUES('technical','deploy',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('developer','discovery',0.0);
INSERT INTO role_phase_efforts VALUES('developer','planning',0.05000000000000000277);
INSERT INTO role_phase_efforts VALUES('developer','design',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('developer','build',0.5);
INSERT INTO role_phase_efforts VALUES('developer','test',0.25);
INSERT INTO role_phase_efforts VALUES('developer','deploy',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('infrastructure','discovery',0.05000000000000000277);
INSERT INTO role_phase_efforts VALUES('infrastructure','planning',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('infrastructure','design',0.1499999999999999945);
INSERT INTO role_phase_efforts VALUES('infrastructure','build',0.2000000000000000111);
INSERT INTO role_phase_efforts VALUES('infrastructure','test',0.1499999999999999945);
INSERT INTO role_phase_efforts VALUES('infrastructure','deploy',0.3499999999999999778);
INSERT INTO role_phase_efforts VALUES('wms','discovery',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('wms','planning',0.1499999999999999945);
INSERT INTO role_phase_efforts VALUES('wms','design',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('wms','build',0.1000000000000000055);
INSERT INTO role_phase_efforts VALUES('wms','test',0.05000000000000000277);
INSERT INTO role_phase_efforts VALUES('wms','deploy',0.5);
CREATE TABLE vendor_consultants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,
    billing_type    TEXT NOT NULL DEFAULT 'MSA',   -- 'MSA' or 'T&M'
    hourly_rate     REAL NOT NULL DEFAULT 0.0,     -- 0 for MSA-covered
    role_key        TEXT,
    active          INTEGER NOT NULL DEFAULT 1
);
INSERT INTO vendor_consultants VALUES(1,'Ajay Kumar','MSA',65.0,'functional',1);
INSERT INTO vendor_consultants VALUES(2,'Bhavya Reddy','T&M',60.0,'technical',1);
INSERT INTO vendor_consultants VALUES(3,'Deepak Gudwani','T&M',65.0,'functional',1);
INSERT INTO vendor_consultants VALUES(4,'Ravindra Reddy','MSA',65.0,'technical',1);
INSERT INTO vendor_consultants VALUES(5,'Sangamesh Koti','T&M',65.0,'technical',1);
INSERT INTO vendor_consultants VALUES(6,'Sarath Yeturu','MSA',200.0,'technical',1);
INSERT INTO vendor_consultants VALUES(7,'Vinod Bollepally','MSA',65.0,'dba',1);
INSERT INTO vendor_consultants VALUES(8,'Vishnu Premen','T&M',65.0,'technical',1);
INSERT INTO vendor_consultants VALUES(9,'Akhilesh Mishra','T&M',65.0,'technical',1);
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
INSERT INTO vendor_timesheets VALUES(1,1,'2026-03-02','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',5.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(2,1,'2026-03-02','SSE-493','Monthly - Customer Statement Report generation pre activity','Monthly - Customer Statement Report generation pre activity','Support',2.0,'Verification','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(3,1,'2026-03-02','SSE-491','Monthly - Inventory Data Extract','Monthly - Inventory Data Extract','Support',1.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(4,1,'2026-03-03','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',6.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(5,1,'2026-03-03','SSE-544','SL enhancement Request: WMERP Warehouse to Warehouse Bulk Transfer Seriall Logs','SL enhancement Request: WMERP Warehouse to Warehouse Bulk Transfer Seriall Logs','Project',2.0,'Testing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(6,1,'2026-03-04','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',5.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(7,1,'2026-03-04','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',1.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(8,1,'2026-03-05','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',5.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(9,1,'2026-03-05','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(10,1,'2026-03-05','SSE-571','Order JR00000345 in Syteline Not Able To Receive Core Lines','Order JR00000345 in Syteline Not Able To Receive Core Lines','Support',1.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(11,1,'2026-03-06','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',3.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(12,1,'2026-03-06','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',3.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(13,1,'2026-03-06','SSE-571','Order JR00000345 in Syteline Not Able To Receive Core Lines','Order JR00000345 in Syteline Not Able To Receive Core Lines','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(14,1,'2026-03-09','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',2.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(15,1,'2026-03-09','SSE-571','Order JR00000345 in Syteline Not Able To Receive Core Lines','Order JR00000345 in Syteline Not Able To Receive Core Lines','Support',2.0,'Fix','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(16,1,'2026-03-09','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(17,1,'2026-03-09','SSE-563','SR-57772 Mass data change / SQL script request (Delete Unused/Unnecessary Locations)','SR-57772 Mass data change / SQL script request (Delete Unused/Unnecessary Locations)','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(18,1,'2026-03-10','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',4.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(19,1,'2026-03-10','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(20,1,'2026-03-10','SSE-545','Installed New Return Type MFDN ETE_TEST','Installed New Return Type MFDN ETE_TEST','Project',2.0,'Testing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(21,1,'2026-03-11','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',6.0,'Process, Planning failed','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(22,1,'2026-03-11','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(23,1,'2026-03-12','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',5.0,'Process, Planning failed','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(24,1,'2026-03-12','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',3.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(25,1,'2026-03-13','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',8.0,'Process,','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(26,1,'2026-03-16','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',4.0,'Process,','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(27,1,'2026-03-16','SSE-591','FW: Outstanding EVO PO''s reconciliation','FW: Outstanding EVO PO''s reconciliation','Support',4.0,'Fix','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(28,1,'2026-03-17','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',4.0,'Process, ','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(29,1,'2026-03-17','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(30,1,'2026-03-17','SSE-402','ETE Core Plan issues fix','ETE Core Plan issues fix','Project',2.0,'Response scenario help & call','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(31,1,'2026-03-18','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',4.0,'Process, Planning failed','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(32,1,'2026-03-18','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',3.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(33,1,'2026-03-18','SSE-594','Component Pick Plan -- Mfg Items','Component Pick Plan -- Mfg Items','Support',1.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(34,1,'2026-03-19','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',4.0,'Process, Planning failed','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(35,1,'2026-03-19','SSE-596','Urgent Task: Corrupted PO/Core Charge Clean up','Urgent Task: Corrupted PO/Core Charge Clean up','Support',2.0,'Fix','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(36,1,'2026-03-19','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(37,1,'2026-03-20','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',6.0,'Process, Planning failed','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(38,1,'2026-03-20','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',2.0,'Issue reproduced','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(39,1,'2026-03-23','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',8.0,'Process, Planning failed - Call','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(40,1,'2026-03-24','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',2.0,'Process, Planning failed','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(41,1,'2026-03-24','SSE-591','FW: Outstanding EVO PO''s reconciliation','FW: Outstanding EVO PO''s reconciliation','Support',2.0,'Fix','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(42,1,'2026-03-24','SSE-602','APS Planning failed 3/24','APS Planning failed 3/24','Support',4.0,'Fix','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(43,1,'2026-03-25','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',4.0,'Process, Monitor','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(44,1,'2026-03-25','SSE-602','APS Planning failed 3/24','APS Planning failed 3/24','Support',4.0,'Monitor & Rerun','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(45,1,'2026-03-26','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',3.0,'Process, Monitor','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(46,1,'2026-03-26','SSE-604','Delete Items from WM_Truckloads_mst','Delete Items from WM_Truckloads_mst','Support',1.0,'Fix','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(47,1,'2026-03-26','SSE-605','Modify WMERP Truckload Transfer To Prevent Issues with Serial Numbers Scanned to Multiple Transfers','Modify WMERP Truckload Transfer To Prevent Issues with Serial Numbers Scanned to Multiple Transfers','Support',2.0,'Test','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(48,1,'2026-03-26','SSE-402','ETE Core Plan issues fix','ETE Core Plan issues fix','Project',2.0,'Test','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(49,1,'2026-03-27','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',5.0,'Process, Monitor','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(50,1,'2026-03-27','SSE-402','ETE Core Plan issues fix','ETE Core Plan issues fix','Project',3.0,'Test','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(51,1,'2026-03-30','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',4.0,'Process, Monitor','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(52,1,'2026-03-30','SSE-559',' ETE Production Oversight - Dyno Data Bug',' ETE Production Oversight - Dyno Data Bug','Support',2.0,'Resolution','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(53,1,'2026-03-30','SSE-611','Fuel Surcharge Notification','Fuel Surcharge Notification','Project',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(54,1,'2026-03-31','SSE-401','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Unposted, JMT Clear,  Planning, get ATP, invoicing, etc, ','Support',3.0,'Process, Monitor','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(55,1,'2026-03-31','SSE-492','Monthly - Vouchers payable write off','Monthly - Vouchers payable write off','Support',3.0,'Process','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(56,1,'2026-03-31','SSE-611','Fuel Surcharge Notification','Fuel Surcharge Notification','Project',2.0,'work with Dev','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(57,2,'2026-03-02','SSE-526','Changes to Accounts Receivable Aging Report','Development (CSV Report)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(58,2,'2026-03-03','SSE-526','Changes to Accounts Receivable Aging Report','Development (CSV Report)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(59,2,'2026-03-04','SSE-526','Changes to Accounts Receivable Aging Report','Development (CSV Report)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(60,2,'2026-03-05','SSE-526','Changes to Accounts Receivable Aging Report','Development (CSV Report)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(61,2,'2026-03-06','SSE-526','Changes to Accounts Receivable Aging Report','Development (CSV Report)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(62,2,'2026-03-09','SSE-526','Changes to Accounts Receivable Aging Report','Development (CSV Report)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(63,2,'2026-03-10','SSE-526','Changes to Accounts Receivable Aging Report','Development (Data View)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(64,2,'2026-03-11','SSE-526','Changes to Accounts Receivable Aging Report','Development (Data View)','Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(65,2,'2026-03-11','SSE-526','DEVELOPMENT - Tax Issues - Do not allow credits to credit tax if tax was not charged on the original invoice ETE_Test','Fix issue','Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(66,2,'2026-03-12','SSE-526','Changes to Accounts Receivable Aging Report','Development (Data View)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(67,2,'2026-03-13','SSE-526','Changes to Accounts Receivable Aging Report','Development (Data View)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(68,2,'2026-03-16','SSE-526','Changes to Accounts Receivable Aging Report','Development (Data View)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(69,2,'2026-03-17','SSE-526','Changes to Accounts Receivable Aging Report','Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(70,2,'2026-03-18','SSE-526','Changes to Accounts Receivable Aging Report','Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(71,2,'2026-03-19','SSE-553','Change GL Acct to 20410 for WEX Payments from Service Orders Module','Development & Testing','Support',6.0,'Default Account to 20410 for Service Orders(Payment Type: WEX)','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(72,2,'2026-03-19','SSE-526','Changes to Accounts Receivable Aging Report','Testing','Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(73,2,'2026-03-20','SSE-526','Changes to Accounts Receivable Aging Report','Adjusting Core and Unit Buckets','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(74,2,'2026-03-23','SSE-526','Changes to Accounts Receivable Aging Report','Adjusting Core and Unit Buckets','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(75,2,'2026-03-24','SSE-526','Changes to Accounts Receivable Aging Report','Adjusting Core and Unit Buckets','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(76,2,'2026-03-25','SSE-526','Changes to Accounts Receivable Aging Report','Adjusting Core and Unit Buckets','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(77,2,'2026-03-26','SSE-526','Changes to Accounts Receivable Aging Report','Testing','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(78,2,'2026-03-26','SSE-495','DEVELOPMENT - Tax Issues - Do not allow credits to credit tax if tax was not charged on the original invoice ETE_Test','Changes moved to Live','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(79,2,'2026-03-27','SSE-526','Changes to Accounts Receivable Aging Report','Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(80,2,'2026-03-30','SSE-526','Changes to Accounts Receivable Aging Report','Fixing issues','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(81,2,'2026-03-31','SSE-526','Changes to Accounts Receivable Aging Report','Deploying changes to AR Test for user testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(82,3,'2026-03-02','SSE-496','Cash App issues requiring SQL programming to fix','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(83,3,'2026-03-03','SSE-557','Clear Temp_Mass_Journal For Feb_2026','Month-end activity','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(84,3,'2026-03-04','SSE-339','FIXED: Issues running A/R aging report','Testing & Analyzing the issue','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(85,3,'2026-03-05','SSE-571','Order JR00000345 in Syteline Not Able To Receive Core Lines','Updated the Unit code 1','Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(86,3,'2026-03-05','SSE-339','FIXED: Issues running A/R aging report','Testing & Analyzing the issue','Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(87,3,'2026-03-06','SSE-553','Change GL Acct to 20410 for WEX Payments from Service Orders Module','Analysis the Process','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(88,3,'2026-03-06','SSE-555','AP vendor checks','Analysis & resolved the Issue','Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(89,3,'2026-03-09','SSE-555','AP vendor checks','Analysis & resolved the Issue','Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(90,3,'2026-03-09','SSE-471','DELIVERY - Spend Report for Dean - Analyze Spend Data by GL Acct last 365 days',NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(91,3,'2026-03-10','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(92,3,'2026-03-11','SSE-496','Cash Application','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(93,3,'2026-03-12','SSE-526','DEVELOPMENT - Tax Issues - Do not allow credits to credit tax if tax was not charged on the original invoice ETE_Test','Functional Testing','Project',4.0,' ','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(94,3,'2026-03-12','SSE-471','DELIVERY - Spend Report for Dean - Analyze Spend Data by GL Acct last 365 days',NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(95,3,'2026-03-13','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(96,3,'2026-03-16','SSE-496','Cash Application','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(97,3,'2026-03-17','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(98,3,'2026-03-18','SSE-553','Change GL Acct to 20410 for WEX Payments from Service Orders Module','Analysis the Process & Developement Support','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(99,3,'2026-03-19','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(100,3,'2026-03-20','SSE-553','Change GL Acct to 20410 for WEX Payments from Service Orders Module','Functional Testing','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(101,3,'2026-03-23','SSE-553','Change GL Acct to 20410 for WEX Payments from Service Orders Module','Functional Testing','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(102,3,'2026-03-24','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(103,3,'2026-03-25',unistr('SSE-598\u000a\u000a\u000a'),'Urgent Task: GL account Voucher Clean up','Functional Testing','Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(104,3,'2026-03-25','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(105,3,'2026-03-26','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(106,3,'2026-03-26','SSE-526','Question on RMA Return Transaction journal entries created from wmerp rma daily returns workbench','Analysis the Issue/Questions','Project',4.0,'Clarification provided for the Journal Entries','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(107,3,'2026-03-27','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(108,3,'2026-03-30','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(109,3,'2026-03-31','SSE-526','Changes to Accounts Receivable Aging Report','Functional Testing','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(110,3,'2026-03-31','SSE-566','Outsourced Unit Core Accounting Proposed Change','Analyzing the Requirement','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(111,4,'2026-03-02','SSE-491','Extract inventory file','Extraxcted the inventory file and sent it to Dean','Support',2.0,'Data extraction','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(112,4,'2026-03-02','SSE-544','Warehouse to warehouse bulk transfer','Warehouse to warehouse bulk transfer','Project',6.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(113,4,'2026-03-03','SSE-544','Warehouse to warehouse bulk transfer','Warehouse to warehouse bulk transfer','Project',8.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(114,4,'2026-03-04','SSE-544','Warehouse to warehouse bulk transfer','Warehouse to warehouse bulk transfer','Project',8.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(115,4,'2026-03-05','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',6.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(116,4,'2026-03-05','SSE-538','Including transit location when generating parts plan','Including transit location when generating parts plan','Support',2.0,'Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(117,4,'2026-03-06','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',8.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(118,4,'2026-03-09','SSE-563','Mass delete of ISL & locations records','Mass delete of ISL & locations records','Support',8.0,'Mass update','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(119,4,'2026-03-10','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',8.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(120,4,'2026-03-11','SSE-563','Mass delete of ISL & locations records','Mass delete of ISL & locations records','Support',8.0,'Mass update','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(121,4,'2026-03-12','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',8.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(122,4,'2026-03-13','SSE-402','ETE Core Plan issues fix','ETE Core Plan issues fix','Project',8.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(123,4,'2026-03-16','SSE-563','Mass delete of ISL & locations records in the prod','Mass delete of ISL & locations records in the prod','Support',5.0,'Mass update','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(124,4,'2026-03-16','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',3.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(125,4,'2026-03-17','SSE-563','ISL & locations issue fix','ISL & locations issue fix','Support',3.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(126,4,'2026-03-17','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',5.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(127,4,'2026-03-18','SSE-538','Issue fix & analysis on parts plan','Issue fix & analysis on parts plan','Support',5.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(128,4,'2026-03-18','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',3.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(129,4,'2026-03-19','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',8.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(130,4,'2026-03-20','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',8.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(131,4,'2026-03-23','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',8.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(132,4,'2026-03-24','SSE-591','Outstanding EVO PO''s reconciliation','Outstanding EVO PO''s reconciliation','Support',4.0,'Table update','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(133,4,'2026-03-24','SSE-402','Core plan change request','Core plan change request','Project',4.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(134,4,'2026-03-25','SSE-402','Core plan change request','Core plan change request','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(135,4,'2026-03-26','SSE-604','delete items in wm_truckload transfer table','delete items in wm_truckload transfer table','Support',4.0,'Table update','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(136,4,'2026-03-26','SSE-402','Core plan change request','Core plan change request','Project',4.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(137,4,'2026-03-27','SSE-606','Rules when Po Lines are added Automatically for the core','Rules when Po Lines are added Automatically for the core','Support',2.0,'Debug & Analysis','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(138,4,'2026-03-27','SSE-402','Core plan change request','Core plan change request','Project',6.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(139,4,'2026-03-30','SSE-559','ETE Production Oversight - Dyno Data Bug','ETE Production Oversight - Dyno Data Bug','Support',8.0,'Issue fix','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(140,4,'2026-03-31','SSE-492','Monthly - Vouchers payable write off','Monthly - Vouchers payable write off','Support',4.0,'Mass update','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(141,4,'2026-03-31','SSE-611','Fuel Surcharge Notification','Fuel Surcharge Notification','Project',4.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(142,5,'2026-03-02','SSE-557','Clear Temp_Mass_Journal For Feb_2026','Clearing the Mass Journal posting fo rthe Feb Month','Support',4.0,'Feb Month','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(143,5,'2026-03-02','SSE-561','SL Task Request: Bulk Adding 720 accounts into Syteline','Creating scripts','Support',4.0,'Creating scripts','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(144,5,'2026-03-03','SSE-561','SL Task Request: Bulk Adding 720 accounts into Syteline','Creating scripts','Support',8.0,'Creating scripts','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(145,5,'2026-03-04','SSE-561','SL Task Request: Bulk Adding 720 accounts into Syteline','Creating scripts','Support',8.0,'Creating scripts','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(146,5,'2026-03-05','SSE-561','SL Task Request: Bulk Adding 720 accounts into Syteline','Creating scripts','Support',8.0,'Creating scripts','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(147,5,'2026-03-06','SSE-561','SL Task Request: Bulk Adding 720 accounts into Syteline','Creating scripts','Support',8.0,'Creating scripts','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(148,5,'2026-03-09','SSE-561','SL Task Request: Bulk Adding 720 accounts into Syteline','Deployment to Prod','Support',4.0,'Deployment to Prod','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(149,5,'2026-03-09','SSE-496','Cash Application','Additional Changes','Project',4.0,'Additional Changes','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(150,5,'2026-03-10','SSE-496','Cash Application','Additional Changes','Project',8.0,'Additional Changes','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(151,5,'2026-03-11','SSE-567','Customer Orders - PO Vendor Rejected Cancellations','Analysis and discussed on the requirement','Support',4.0,'Analysis and discussed on the requirement','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(152,5,'2026-03-12','SSE-496','Cash Application','Issues fixing','Project',8.0,'Issues fixing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(153,5,'2026-03-13','SSE-567','Customer Orders - PO Vendor Rejected Cancellations','Development and Testing','Support',8.0,'Development and Testing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(154,5,'2026-03-16','SSE-567','Customer Orders - PO Vendor Rejected Cancellations','Development and Testing','Support',3.0,'Text Message changing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(155,5,'2026-03-16','SSE-496','Cash Application','Development and Testing','Project',5.0,'Adding new field in ARTran and updating the reference','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(156,5,'2026-03-17','SSE-567','Customer Orders - PO Vendor Rejected Cancellations','Deployment to Prod','Support',1.0,'Deployment to Prod','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(157,5,'2026-03-17','SSE-496','Cash Application','Development and Testing','Project',3.0,'Adding new field in ARTran and updating the reference','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(158,5,'2026-03-17','SSE-534','Create Syteline Field in ISL for new location','Requirement analysis and meeting','Support',4.0,'Requirement analysis and meeting, have proposed other solution','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(159,5,'2026-03-18','SSE-496','Cash Application','Development and Testing','Project',8.0,'Prod deployments and monitoring','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(160,5,'2026-03-19','SSE-496','Cash Application','Development and Testing','Project',8.0,'Post deployment issues and monitoring','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(161,5,'2026-03-20','SSE-496','Cash Application','Development and Testing','Project',8.0,'Post deployment issues and monitoring','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(162,5,'2026-03-23','SSE-599','Bridgepay taking payment but not applying deposit or saving approval','Debuggin and fixing the issue','Support',8.0,'Debuggin and fixing the issue','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(163,5,'2026-03-24','SSE-599','Bridgepay taking payment but not applying deposit or saving approval','Debuggin and fixing the issue','Support',8.0,'Debuggin and fixing the issue','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(164,5,'2026-03-25','SSE-599','Bridgepay taking payment but not applying deposit or saving approval','APS Issues','Support',8.0,'Debuggin and fixing the issue','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(165,5,'2026-03-26','SSE-534','Create Syteline Field in ISL for new location','Development','Support',8.0,'Development','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(166,5,'2026-03-27','SSE-534','Create Syteline Field in ISL for new location','Testing','Support',8.0,'Testing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(167,5,'2026-03-30','SSE-534','Create Syteline Field in ISL for new location','Testing','Support',8.0,'Testing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(168,5,'2026-03-31','SSE-534','Create Syteline Field in ISL for new location','Testing','Support',8.0,'Testing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(169,6,'2026-03-02',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team.','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(170,6,'2026-03-03',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team. Worked with Jim on EDI Issues','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(171,6,'2026-03-04',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team. Attended weekly mmeeting with Finance team and ETE BAs','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(172,6,'2026-03-05',NULL,NULL,NULL,'Support',2.0,'Attended meeting India team. Attended Weekly meeting with Jim K and Kishore','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(173,6,'2026-03-06',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team. Attended meeting with Audrey to Explain the Cash Application form. Attended Nutanix call to understand the Server migration','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(174,6,'2026-03-09',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India team. Attended Nutanix meeting','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(175,6,'2026-03-10',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India team. Attended Nutanix meeting. Attended weekly meeting with Jim on EDI topics','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(176,6,'2026-03-11',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India team. Attended Nutanix meeting. Attended weekly meeting with Jim k and ETE BA team','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(177,6,'2026-03-12',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India team. Attended Nutanix meeting. Attended weekly meeting with Jim K and Kishore.','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(178,6,'2026-03-13',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India team. Attended Nutanix meeting. Attended weekly meeting with Brett and Jim Y','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(179,6,'2026-03-16',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team. Attended Nutanix meeting. Worked with Akilesh and Vishnu on EDI Issues. Was availabe to support from 8 AM to 5 PM CST','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(180,6,'2026-03-17',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team. Attended Nutanix meeting. Worked with Akilesh and Vishnu on EDI Issues. Attended weekly meeting with Jim on EDI Issues. Was availabe to support from 8 AM to 5 PM CST','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(181,6,'2026-03-18',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team. Attended Nutanix meeting. Worked with Akilesh and Vishnu on EDI Issues. Attended weekly meeting with Jim K and ETE BA and PMO Team. Was availabe to support from 8 AM to 5 PM CST. Attnded meeting with finance team and India team on AR Aging report changes. Worked 3 hours with Vishnu and Ajay to address the APSResync Issue','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(182,6,'2026-03-19',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team. Attended Nutanix meeting. Worked with Akilesh and Vishnu on EDI Issues. Attended weekly meeting with Jim K and Kishore. Was availabe to support from 8 AM to 5 PM CST. Worked 3 hours with Vishnu and Ajay to address the APSResync Issue and resolved the issue','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(183,6,'2026-03-20',NULL,NULL,NULL,'Support',5.0,'Attended meeting India team. Attended Nutanix meeting. Worked with Akilesh and Vishnu on EDI Issues. Attended weekly meeting with Tom N and Jim K. Was availabe to support from 8 AM to 5 PM CST','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(184,6,'2026-03-23',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India Team. Worked on Nutanix project support. Available to support from 8 AM to 5 PM','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(185,6,'2026-03-24',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India Team. Worked on Nutanix project Support. Available to support from 8 AM to 5 PM','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(186,6,'2026-03-25',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India team. Attended weekly meeting Jim K, ETE BA and PMO Team. Available to support from 8 AM to 5 PM','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(187,6,'2026-03-26',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India Team. Attended weekly meeting Jim K and Kishore. Attended meeting with Audrey on Core accounitng. Available to support from 8 AM to 5 PM','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(188,6,'2026-03-27',NULL,NULL,NULL,'Support',5.0,'Attended meeting with India Team. Attended weekly meeting with Brett and JiJim to discuss Credit cared processing. Attended weekly meeting with Tom and Jim on weekly touchbase. Attended meeting with Audrey on Core accounting. Available to support from 8 AM to 5 PM.','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(189,6,'2026-03-30',NULL,NULL,NULL,'Support',4.0,'Attended meeting with India team. Worked with the team to provide estimate for automation of Applying Credit memos to Deduction Invoices','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(190,6,'2026-03-31',NULL,NULL,NULL,'Support',4.0,'Attended meetign with India Team. Attended weekly meeting with Jim K on EDI Issues. Workign with Team on Providing estimate for Core accounting changes project.','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(191,7,'2026-03-02',NULL,NULL,'Performed systematic review of SQL Agent job execution histories, including backup, maintenance, and monitoring jobs, and proactively addressed failures to prevent operational disruptions.','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(192,7,'2026-03-03',NULL,NULL,'APSResync job failure','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(193,7,'2026-03-04',NULL,NULL,'Monitored database file growth, disk utilization, and autogrowth configurations to support capacity planning and prevent storage-related risks.','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(194,7,'2026-03-05',NULL,NULL,'Database file shrink performed to reclaim unused space','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(195,7,'2026-03-06','SSE-569',NULL,'DB Clone for Nutanix Project','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(196,7,'2026-03-09',NULL,NULL,'Performed systematic review of SQL Agent job execution histories, including backup, maintenance, and monitoring jobs, and proactively addressed failures to prevent operational disruptions.','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(197,7,'2026-03-10','SSE-569',NULL,'Nutanix (Replace VMWare)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(198,7,'2026-03-11','SSE-569',NULL,'Nutanix (Replace VMWare)','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(199,7,'2026-03-11',NULL,NULL,'Scheduling job failure, worked on Aps server','Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(200,7,'2026-03-12','SSE-569',NULL,'Nutanix (Replace VMWare)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(201,7,'2026-03-16',NULL,NULL,'Performed systematic review of SQL Agent job execution histories, including backup, maintenance, and monitoring jobs, and proactively addressed failures to prevent operational disruptions.','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(202,7,'2026-03-17','SSE-569',NULL,'Nutanix (Replace VMWare)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(203,7,'2026-03-18','SSE-569',NULL,'Nutanix (Replace VMWare)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(204,7,'2026-03-19',NULL,NULL,'APSResync job failure','Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(205,7,'2026-03-19','SSE-569',NULL,'Nutanix (Replace VMWare)','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(206,7,'2026-03-20',NULL,NULL,'APSResync job failure','Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(207,7,'2026-03-20','SSE-569',NULL,'Nutanix (Replace VMWare)','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(208,7,'2026-03-21','SSE-569','SQL servers Migration','Nutanix (Replace VMWare)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(209,7,'2026-03-22','SSE-569','post migration BI  issues','Nutanix (Replace VMWare)','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(210,7,'2026-03-23',NULL,'SSRS reports and DB mail configuration','Nutanix (Replace VMWare)','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(211,7,'2026-03-24','#INC-58903','LSRestore SQL Job on ETE-DATAW Failures',NULL,'Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(212,7,'2026-03-25','#INC-58938','Disk Space Alert: E Drive Reached Full Capacity - ETE-DATAW',NULL,'Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(213,7,'2026-03-25','#INC-58949','Request for System Administrator Access on ETE-ERPAPS','Scheduling Job failed on server','Project',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(214,7,'2026-03-27',NULL,NULL,'Disk Space addition on ETE-ERPDB','Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(215,7,'2026-03-27','#INC-59011',NULL,'Log shipping Jobs verified and worked on Backup failures on ETE-ERPDB','Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(216,7,'2026-03-30',NULL,NULL,'Performed systematic review of SQL Agent job execution histories, including backup, maintenance, and monitoring jobs, and proactively addressed failures to prevent operational disruptions.','Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(217,7,'2026-03-31',NULL,NULL,unistr('Investigated log shipping delays and validated restore and recovery times on secondary server\u0009'),'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(218,8,'2026-03-02','SSE-545','Installed New Return Type MFDN','Development','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(219,8,'2026-03-03','SSE-545','Installed New Return Type MFDN','Development','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(220,8,'2026-03-04','SSE-545','Installed New Return Type MFDN','Development','Project',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(221,8,'2026-03-04','SSE-570','Napa Stores To Update and Re-send','Development','Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(222,8,'2026-03-05','SSE-545','Installed New Return Type MFDN','Development','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(223,8,'2026-03-06','SSE-545','Installed New Return Type MFDN','Development','Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(224,8,'2026-03-06','SSE-471','DELIVERY - Spend Report for Dean - Analyze Spend Data by GL Acct last 365 days',NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(225,8,'2026-03-09','SSE-545','Installed New Return Type MFDN','Development','Project',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(226,8,'2026-03-10','SSE-545','Installed New Return Type MFDN','Development','Project',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(227,8,'2026-03-10','SSE-574','NAPA Resends for 3/9',NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(228,8,'2026-03-11','SSE-516','BGTask Error When sending Credit Card Receipts worked before 10/2024',NULL,'Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(229,8,'2026-03-11','SSE-514',' Planning Fields Upload Utility ETE_Test','Moving to prodution','Project',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(230,8,'2026-03-12','SSE-580','NAPA Resends 3/12',NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(231,8,'2026-03-12','SSE-471','DELIVERY - Spend Report for Dean - Analyze Spend Data by GL Acct last 365 days',NULL,'Support',7.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(232,8,'2026-03-13','SSE-577','Allow ASN to be sent for one order at a time',NULL,'Support',7.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(233,8,'2026-03-13','SSE-581','NAPA Resends 3/13',NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(234,8,'2026-03-16','SSE-577','Allow ASN to be sent for one order at a time',NULL,'Support',7.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(235,8,'2026-03-16','SSE-592','NAPA Resends 3/16',NULL,'Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(236,8,'2026-03-17','SSE-576','Modify the EDI Profile and Customer Ship-To''s to enable Customer Service to self-Manage EDI Corrections',NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(237,8,'2026-03-18','SSE-577','Allow ASN to be sent for one order at a time',NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(238,8,'2026-03-18','SSE-592','NAPA Resends 3/17',NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(239,8,'2026-03-19','SSE-594','Component Pick Plan -- Mfg Items',NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(240,8,'2026-03-20','SSE-595','SL Generate Parts Plan -- Formula Change',NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(241,8,'2026-03-23','SSE-600','3PL Labels - Not Being Generated','Debugging and fixing the issue','Support',6.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(242,8,'2026-03-23','SSE-599','Bridgepay taking payment but not applying deposit or saving approval',NULL,'Support',2.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(243,8,'2026-03-24',NULL,NULL,'EDI Support','Support',5.0,'Query to extract missing EDI profile','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(244,8,'2026-03-24','SSE-595','SL Generate Parts Plan -- Formula Change',NULL,'Support',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(245,8,'2026-03-25','SSE-602','APS Planning failed 3/24',NULL,'Support',4.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(246,8,'2026-03-25','SSE-545','Installed New Return Type MFDN ETE_TEST','Production Move','Project',3.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(247,8,'2026-03-25','SSE-595','SL Generate Parts Plan -- Formula Change','Production Move','Support',1.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(248,8,'2026-03-26','SSE-605','Modify WMERP Truckload Transfer To Prevent Issues with Serial Numbers Scanned to Multiple Transfers',NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(249,8,'2026-03-27','SSE-607','Urgent Enhancement Request: SL generate Parts Plan -- Formula Change Alteration',NULL,'Support',5.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(250,8,'2026-03-27',NULL,NULL,'EDI Support','Support',3.0,'Missing profile for Advance','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(251,8,'2026-03-30','SSE-607','Urgent Enhancement Request: SL generate Parts Plan -- Formula Change Alteration',NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(252,8,'2026-03-31','SSE-612','Sending ASN and Invoice Without Having Already Sent One',NULL,'Support',8.0,NULL,'2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(253,9,'2026-03-02',NULL,NULL,NULL,'Support',2.0,'Worked on Resending Napa Invoices','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(254,9,'2026-03-03',NULL,NULL,NULL,'Support',4.0,'Worked on Resending Napa Invoices','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(255,9,'2026-03-04',NULL,NULL,NULL,'Support',4.0,'Worked with SPS to understand why Car Quest Inovices are failing','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(256,9,'2026-03-05',NULL,NULL,NULL,'Support',4.0,'identified another Issue with Car Quest Invoices not being send to SPS','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(257,9,'2026-03-06',NULL,NULL,NULL,'Support',2.0,'Working with Vishnu to resolve the Car Quest invoices not sending to SPS','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(258,9,'2026-03-09',NULL,NULL,NULL,'Support',2.0,'Worked on EDI Resends','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(259,9,'2026-03-10',NULL,NULL,NULL,'Support',4.0,'Worked on EDI Resends','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(260,9,'2026-03-11',NULL,NULL,NULL,'Support',4.0,'Worked on EDI Resends','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(261,9,'2026-03-12',NULL,NULL,NULL,'Support',4.0,'Worked on EDI Resends','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(262,9,'2026-03-13',NULL,NULL,NULL,'Support',2.0,'Worked on EDI Resends','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(263,9,'2026-03-16',NULL,NULL,NULL,'Support',4.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(264,9,'2026-03-17',NULL,NULL,NULL,'Support',4.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(265,9,'2026-03-18',NULL,NULL,NULL,'Support',4.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(266,9,'2026-03-19',NULL,NULL,NULL,'Support',2.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(267,9,'2026-03-20',NULL,NULL,NULL,'Support',2.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(268,9,'2026-03-23',NULL,NULL,NULL,'Support',2.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(269,9,'2026-03-24',NULL,NULL,NULL,'Support',2.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(270,9,'2026-03-25',NULL,NULL,NULL,'Support',4.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(271,9,'2026-03-26',NULL,NULL,NULL,'Support',4.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(272,9,'2026-03-27',NULL,NULL,NULL,'Support',4.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(273,9,'2026-03-30',NULL,NULL,NULL,'Support',4.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
INSERT INTO vendor_timesheets VALUES(274,9,'2026-03-31',NULL,NULL,NULL,'Support',4.0,'EDI Support','2026-04-03 21:49:01','2026-04-03 21:49:01');
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
INSERT INTO approved_work VALUES(1,'SSE-538','Enhancement Request: Adding ''T'' or transit into Part Planning Logic','Enhancement','Support','2026-02-17','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(2,'SSE-526','Changes to Accounts Receivable Aging Report','Project','CapEx','2026-01-16','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(3,'SSE-496','Form for Cash App Issues Requiring SQL Programming to Fix','Project','CapEx','2026-01-16','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(4,'SSE-495','Tax Issues- Disallow Credits to Credit Tax if Not Charged on Original Invoice','Project','CapEx','2026-01-16','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(5,'SSE-538','Adding T or Transit Into Planing Logic','Enhancement','Support','2026-02-17','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(6,'SSE-516','BG Tastk Error When Sending CC Receipts Worked Before 10/2024','Break/Fix','Support','2026-01-29','Jim Young',NULL);
INSERT INTO approved_work VALUES(7,'SSE-537','New Owner Field on SL Daily Workbench Issues','Break/Fix','Support','2026-02-17','Jim Young','This looks like a bug to me (Brett)');
INSERT INTO approved_work VALUES(8,'SSE-453','Develop Gear Screen Functionality and Requirements','Project','CapEx','2026-01-12','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(9,'SSE-527','PCR Gear Screen Additional Needs','Project','CapEx','2026-02-09','Brett Anderson','Small PCR Update to the Gear Screen Project');
INSERT INTO approved_work VALUES(10,'SSE-440','Restocking Fees Added to RMA Credit Memo','Project','CapEx','2026-12-22','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(11,'SSE-402','Execute Development for Spec Core Plan Changes','Project','CapEx','2026-12-12','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(12,'SSE-490','WMERP Production JIT POsting Form Update','Enhancement','Support','2026-01-15','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(13,'SSE-553','SL Enhancement: Adding Column to the Job Transaction Form','Enhancement','Support','2026-02-13','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(14,'SSE-489','Logic Change Request - Enable Post-Invoice Editing on WMERP Customer QE Form','Enhancement','Support','2026-01-15','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(15,'SSE-339','Issues Running A/R Aging Report','Bug','Support','2025-10-08','Jim Young',NULL);
INSERT INTO approved_work VALUES(16,'SSE-494','ETE-DataW Restore Job - One Off Long Runtime New Example','Enhancement','Support','2026-01-19','Jim Young',NULL);
INSERT INTO approved_work VALUES(17,'SSE-401','Monitor for Unposted Background Transactions','Enhancement','Support','2026-12-10','Jim Young','Ongoning Monitoring - This is a generic reporting card');
INSERT INTO approved_work VALUES(18,'SSE-491','Monthly Inventory Data Extract','Enhancement','Support','2026-01-16','Jim Young','Ongoing Monthly Data Extract (Recurring)');
INSERT INTO approved_work VALUES(19,'SSE-492','Monthly Vouchers Payable Write Off','Enhancement','Support','2026-01-16','Jim Young','Ongoing Monthly Task (Recurring)');
INSERT INTO approved_work VALUES(20,'SSE-493','Monthly Custome Statement Report ','Enhancement','Support','2026-01-16','Jim Young','Ongoing Monthly Report Task (Recurring)');
INSERT INTO approved_work VALUES(21,'SSE-540','Weekly EDI Invoice Resends','Enhancement','Support','2026-02-18','Jim Young','Ongoing Weekly Invoice Resends');
INSERT INTO approved_work VALUES(22,'SSE-514','Planning Fields Upload Utility','Project','CapEx','2026-02-04','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(23,'SSE-488','Investigate Setup Bridgepay to Pilot Environment','Enhancement','Support','2026-01-14','Jim Young',NULL);
INSERT INTO approved_work VALUES(24,'SSE-539','Urgent Task - Slow Printing 8100 in Syteline','Bug','Support','2026-02-18','Jim Young',NULL);
INSERT INTO approved_work VALUES(25,'SSE-534','Create Syteline Field in ISL for New Location','Enhancement','Support',NULL,NULL,'NOT YET APPROVED');
INSERT INTO approved_work VALUES(26,'SSE-530','ETE_Test - Purple Icon on PO Lines PO ETE356','Bug','Support',NULL,NULL,'NOT YET APPROVED');
INSERT INTO approved_work VALUES(27,'SSE-444','Document Customer Policy (Restocking Fees Added to Credit Memos)','Project','CapEx',NULL,NULL,'NOT YET APPROVED');
INSERT INTO approved_work VALUES(28,'SSE-543','EDI Customer Name Cleanup','Enhancement','Support','2026-02-20','Jim Young',NULL);
INSERT INTO approved_work VALUES(29,'SSE-553','Change GL Acct to 20410 for Wex Payments','Enhancement','Support','2026-02-25','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(30,'SSE-545','Installed New Return Type MFDN','Project','CapEx','2026-02-27','Brett Anderson',NULL);
INSERT INTO approved_work VALUES(31,'SSE-569','Nutanix (replace VMware) Vinod','Project','CapEx','2026-03-03','Brett Anderson',NULL);
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
INSERT INTO vendor_invoices VALUES(1,'2026-03',50000.0,51680.0,101680.0,'INV-ETEMar26','2026-04-02',0,'MSA flat fee + T&M: Bhavya 176h@$60, Sarath 105h@$200, Akhilesh 72h@$65');
INSERT INTO sqlite_sequence VALUES('project_assignments',129);
INSERT INTO sqlite_sequence VALUES('vendor_consultants',9);
INSERT INTO sqlite_sequence VALUES('vendor_timesheets',274);
INSERT INTO sqlite_sequence VALUES('approved_work',31);
INSERT INTO sqlite_sequence VALUES('vendor_invoices',1);
CREATE INDEX idx_vt_consultant ON vendor_timesheets(consultant_id);
CREATE INDEX idx_vt_date ON vendor_timesheets(entry_date);
CREATE INDEX idx_vt_project ON vendor_timesheets(project_key);
COMMIT;
