CREATE DATABASE IF NOT EXISTS exchange_rate_db CHARACTER SET utf8mb4;

USE exchange_rate_db;

CREATE TABLE IF NOT EXISTS `raw_rates` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '連番',
    `date` DATE NOT NULL COMMENT 'レートの日付',
    `base` CHAR(3) NOT NULL COMMENT '基準通貨（ISO 4217の3文字固定）',
    `quote` CHAR(3) NOT NULL COMMENT '相手通貨（ISO 4217の3文字固定）',
    `rate` DECIMAL(18,6) NOT NULL COMMENT '為替レート',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '取込日時',
    UNIQUE KEY uq_raw_rates_date_pair (`date`,`base`,`quote`)
) COMMENT='為替レート生データ（raw層）';

CREATE TABLE IF NOT EXISTS `agg_rates` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '連番',
    `date` DATE NOT NULL COMMENT 'レートの日付',
    `base` CHAR(3) NOT NULL COMMENT '基準通貨（ISO 4217の3文字固定）',
    `quote` CHAR(3) NOT NULL COMMENT '相手通貨（ISO 4217の3文字固定）',
    `rate` DECIMAL(18,6) NOT NULL COMMENT 'その日のレート（raw_ratesから複製）',
    `diff_prev` DECIMAL(18,6) NULL COMMENT '前日比（差）。系列初日はNULL',
    `pct_change` DECIMAL(9,6) NULL COMMENT '前日比（変化率, %）。系列初日はNULL',
    `ma_7` DECIMAL(18,6) NULL COMMENT '7日移動平均。最初の6日はNULL',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '算出日時',
    UNIQUE KEY uq_agg_rates_date_pair (`date`,`base`,`quote`)
) COMMENT='為替レート集計データ（集計層）';