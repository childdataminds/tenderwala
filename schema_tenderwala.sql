-- TenderWala schema (MySQL)
-- Generated to match the table names/column order referenced in databases.py

CREATE DATABASE IF NOT EXISTS tenderwala_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE tenderwala_db;

CREATE TABLE IF NOT EXISTS users_table (
  phone VARCHAR(20) NOT NULL,
  email VARCHAR(255) NULL,
  status VARCHAR(30) NULL,
  joitn_date VARCHAR(64) NULL,
  subs_date VARCHAR(64) NULL,
  name VARCHAR(255) NULL,
  lang VARCHAR(10) NULL,
  last_texted_on VARCHAR(64) NULL,
  PRIMARY KEY (phone),
  KEY idx_users_status (status),
  KEY idx_users_lang (lang)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS manage_images (
  title VARCHAR(120) NOT NULL,
  img_id VARCHAR(255) NULL,
  expiry_date VARCHAR(64) NULL,
  PRIMARY KEY (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS federal_table (
  id VARCHAR(191) NOT NULL,
  title TEXT NULL,
  department VARCHAR(255) NULL,
  document TEXT NULL,
  date_published VARCHAR(64) NULL,
  date_opening VARCHAR(64) NULL,
  city VARCHAR(191) NULL,
  category VARCHAR(191) NULL,
  type VARCHAR(60) NULL,
  sent_to LONGTEXT NULL,
  PRIMARY KEY (id),
  KEY idx_federal_city (city),
  KEY idx_federal_category (category),
  KEY idx_federal_opening (date_opening)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS punjab_table (
  id VARCHAR(191) NOT NULL,
  title TEXT NULL,
  department VARCHAR(255) NULL,
  document TEXT NULL,
  date_published VARCHAR(64) NULL,
  date_opening VARCHAR(64) NULL,
  city VARCHAR(191) NULL,
  category VARCHAR(191) NULL,
  type VARCHAR(60) NULL,
  sent_to LONGTEXT NULL,
  PRIMARY KEY (id),
  KEY idx_punjab_city (city),
  KEY idx_punjab_category (category),
  KEY idx_punjab_opening (date_opening)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sindh_table (
  id VARCHAR(191) NOT NULL,
  title TEXT NULL,
  department VARCHAR(255) NULL,
  document TEXT NULL,
  date_published VARCHAR(64) NULL,
  date_opening VARCHAR(64) NULL,
  city VARCHAR(191) NULL,
  category VARCHAR(191) NULL,
  estimated_cost VARCHAR(120) NULL,
  sent_to LONGTEXT NULL,
  PRIMARY KEY (id),
  KEY idx_sindh_city (city),
  KEY idx_sindh_category (category),
  KEY idx_sindh_opening (date_opening)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS kpk_table (
  id VARCHAR(191) NOT NULL,
  title TEXT NULL,
  department VARCHAR(255) NULL,
  document TEXT NULL,
  date_published VARCHAR(64) NULL,
  date_opening VARCHAR(64) NULL,
  city VARCHAR(191) NULL,
  category VARCHAR(191) NULL,
  type VARCHAR(60) NULL,
  sent_to LONGTEXT NULL,
  PRIMARY KEY (id),
  KEY idx_kpk_city (city),
  KEY idx_kpk_category (category),
  KEY idx_kpk_opening (date_opening)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ajk_table (
  id VARCHAR(191) NOT NULL,
  title TEXT NULL,
  department VARCHAR(255) NULL,
  document TEXT NULL,
  date_published VARCHAR(64) NULL,
  date_opening VARCHAR(64) NULL,
  city VARCHAR(191) NULL,
  category VARCHAR(191) NULL,
  type VARCHAR(60) NULL,
  sent_to LONGTEXT NULL,
  PRIMARY KEY (id),
  KEY idx_ajk_city (city),
  KEY idx_ajk_category (category),
  KEY idx_ajk_opening (date_opening)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gilgit_table (
  id VARCHAR(191) NOT NULL,
  title TEXT NULL,
  department VARCHAR(255) NULL,
  document TEXT NULL,
  date_published VARCHAR(64) NULL,
  date_opening VARCHAR(64) NULL,
  city VARCHAR(191) NULL,
  category VARCHAR(191) NULL,
  type VARCHAR(60) NULL,
  sent_to LONGTEXT NULL,
  PRIMARY KEY (id),
  KEY idx_gilgit_city (city),
  KEY idx_gilgit_category (category),
  KEY idx_gilgit_opening (date_opening)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS balochistan_table (
  id VARCHAR(191) NOT NULL,
  title TEXT NULL,
  department VARCHAR(255) NULL,
  document TEXT NULL,
  date_published VARCHAR(64) NULL,
  date_opening VARCHAR(64) NULL,
  city VARCHAR(191) NULL,
  category VARCHAR(191) NULL,
  type VARCHAR(60) NULL,
  sent_to LONGTEXT NULL,
  PRIMARY KEY (id),
  KEY idx_balochistan_city (city),
  KEY idx_balochistan_category (category),
  KEY idx_balochistan_opening (date_opening)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS filters_table (
  phone VARCHAR(20) NOT NULL,
  provinces VARCHAR(100) NULL,
  types VARCHAR(100) NULL,
  punjab_cities TEXT NULL,
  sindh_cities TEXT NULL,
  kpk_cities TEXT NULL,
  ajk_cities TEXT NULL,
  balochistan_cities TEXT NULL,
  gilgit_cities TEXT NULL,
  categories TEXT NULL,
  PRIMARY KEY (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS all_tenders_table (
  id VARCHAR(191) NOT NULL,
  title TEXT NULL,
  city VARCHAR(191) NULL,
  category VARCHAR(191) NULL,
  publish_date VARCHAR(64) NULL,
  opening_datetime VARCHAR(64) NULL,
  details LONGTEXT NULL,
  doc_link TEXT NULL,
  department VARCHAR(255) NULL,
  PRIMARY KEY (id),
  KEY idx_all_tenders_city (city),
  KEY idx_all_tenders_category (category),
  KEY idx_all_tenders_opening (opening_datetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_tenders_table (
  user_phone VARCHAR(20) NOT NULL,
  tender_ids LONGTEXT NULL,
  PRIMARY KEY (user_phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS visitors_table (
  name VARCHAR(255) NULL,
  phone VARCHAR(20) NOT NULL,
  date VARCHAR(64) NULL,
  PRIMARY KEY (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS remind_table (
  id BIGINT NOT NULL AUTO_INCREMENT,
  phone VARCHAR(20) NOT NULL,
  tender_id VARCHAR(191) NOT NULL,
  tender_table VARCHAR(80) NOT NULL,
  reminder_time VARCHAR(64) NULL,
  message TEXT NULL,
  status VARCHAR(30) NULL,
  sent_on VARCHAR(64) NULL,
  created_on VARCHAR(64) NULL,
  PRIMARY KEY (id),
  KEY idx_remind_phone (phone),
  KEY idx_remind_status (status),
  KEY idx_remind_time (reminder_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_summary_usage_table (
  id BIGINT NOT NULL AUTO_INCREMENT,
  phone VARCHAR(20) NOT NULL,
  month_key VARCHAR(7) NOT NULL,
  used_count INT NOT NULL DEFAULT 0,
  updated_on VARCHAR(64) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ai_summary_phone_month (phone, month_key),
  KEY idx_ai_summary_month (month_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reminder_me_table (
  id BIGINT NOT NULL AUTO_INCREMENT,
  phone VARCHAR(20) NOT NULL,
  tender_id VARCHAR(191) NOT NULL,
  tender_table VARCHAR(80) NOT NULL,
  reminder_time VARCHAR(64) NULL,
  message TEXT NULL,
  status VARCHAR(30) NULL,
  sent_on VARCHAR(64) NULL,
  created_on VARCHAR(64) NULL,
  PRIMARY KEY (id),
  KEY idx_reminder_me_phone (phone),
  KEY idx_reminder_me_status (status),
  KEY idx_reminder_me_time (reminder_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
