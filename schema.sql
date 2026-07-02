-- SV派单记录系统 数据库Schema
-- Database: sqlite3

CREATE TABLE IF NOT EXISTS dispatch_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL DEFAULT 2026,
    serial_number TEXT,
    customer_name TEXT NOT NULL,
    address TEXT,
    contact_person TEXT,
    contact_phone TEXT,
    order_no TEXT,
    service_type TEXT,
    product_model TEXT,
    quantity INTEGER DEFAULT 0,
    service_content TEXT,
    implement_no TEXT,
    sales_person TEXT,
    sales_phone TEXT,
    status TEXT DEFAULT '待处理',
    start_date TEXT,
    expected_end_date TEXT,
    actual_end_date TEXT,
    implement_manager TEXT,
    implement_manager_phone TEXT,
    product_category TEXT,
    task_source TEXT,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monthly_settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT,
    record_no TEXT,
    demand_date TEXT,
    mu_department TEXT,
    initiator TEXT,
    pm TEXT,
    customer TEXT,
    project_name TEXT,
    demand_type TEXT,
    service_location TEXT,
    device_model TEXT,
    demand_detail TEXT,
    quantity INTEGER DEFAULT 0,
    service_type TEXT,
    count_value INTEGER DEFAULT 0,
    count_confirm TEXT,
    work_order_no TEXT,
    cost_collect_no TEXT,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inspection_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT,
    customer_name TEXT,
    address TEXT,
    contact_person TEXT,
    contact_phone TEXT,
    order_no TEXT,
    service_type TEXT,
    product_model TEXT,
    quantity INTEGER DEFAULT 0,
    requirement_detail TEXT,
    implement_no TEXT,
    sales_person TEXT,
    sales_phone TEXT,
    status TEXT,
    start_date TEXT,
    end_date TEXT,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS duty_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT,
    customer_name TEXT,
    address TEXT,
    contact_person TEXT,
    contact_phone TEXT,
    product_category TEXT,
    task_source TEXT,
    order_no TEXT,
    service_type TEXT,
    product_model TEXT,
    quantity INTEGER DEFAULT 0,
    service_content TEXT,
    implement_no TEXT,
    sales_person TEXT,
    sales_phone TEXT,
    status TEXT,
    start_date TEXT,
    expected_end_date TEXT,
    actual_end_date TEXT,
    implement_manager TEXT,
    implement_manager_phone TEXT,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS person_day_aggregation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT,
    customer_name TEXT,
    address TEXT,
    contact_person TEXT,
    contact_phone TEXT,
    order_no TEXT,
    service_type TEXT,
    product_model TEXT,
    quantity INTEGER DEFAULT 0,
    service_content TEXT,
    implement_no TEXT,
    sales_person TEXT,
    sales_phone TEXT,
    status TEXT,
    start_date TEXT,
    expected_end_date TEXT,
    actual_end_date TEXT,
    implement_manager TEXT,
    implement_manager_phone TEXT,
    remark TEXT,
    product_category TEXT,
    task_source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS service_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT,
    model TEXT,
    product_name TEXT,
    serial_number TEXT,
    demand_level1 TEXT,
    demand_level2 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建视图：统一派单记录视图
CREATE VIEW IF NOT EXISTS v_all_dispatch AS
SELECT '派单' as record_type, year, id, serial_number, customer_name, address,
       contact_person, contact_phone, order_no, service_type, product_model,
       quantity, service_content, implement_no, sales_person, sales_phone,
       status, start_date, expected_end_date, actual_end_date,
       implement_manager, implement_manager_phone, product_category, task_source, remark
FROM dispatch_orders
UNION ALL
SELECT '巡检' as record_type, NULL as year, id, serial_number, customer_name, address,
       contact_person, contact_phone, order_no, service_type, product_model,
       quantity, requirement_detail, implement_no, sales_person, sales_phone,
       status, start_date, end_date, end_date,
       NULL, NULL, NULL, NULL, remark
FROM inspection_tasks
UNION ALL
SELECT '值守' as record_type, NULL as year, id, serial_number, customer_name, address,
       contact_person, contact_phone, order_no, service_type, product_model,
       quantity, service_content, implement_no, sales_person, sales_phone,
       status, start_date, expected_end_date, actual_end_date,
       implement_manager, implement_manager_phone, product_category, task_source, remark
FROM duty_tasks;

